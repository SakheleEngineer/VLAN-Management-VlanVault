
from django.db import transaction
from company.models import Company
from tag.models import Tag
from tag_set.models import TagRange
from region.models import Region
import re
import requests
import json
from decouple import config

SNOW_URL = config("SNOW_URL")
CLIENT_ID = config("CLIENT_ID")
CLIENT_SECRETE = config("CLIENT_SECRETE")


def allocate_first_free_tag_from_ranges(serviceData, tag_ranges):

    for tag_range in tag_ranges:
        tags = Tag.objects.filter(vlan_range=tag_range).order_by('vlan')
        first_free_vlan = None
        if tags.exists():
            
            prev = tag_range.vlan_start - 1

            for tag in tags:
                vlan = tag.vlan
                if vlan <= prev:
                    continue

                if vlan > prev + 1:
                    first_free_vlan = prev + 1
                    break

                prev = vlan

            if first_free_vlan is None and prev < tag_range.vlan_end:
                first_free_vlan = prev + 1

        else:
            # No tags in range → use start VLAN
            first_free_vlan = tag_range.vlan_start

        # Create tag only if valid VLAN found inside range
        if first_free_vlan is not None and first_free_vlan <= tag_range.vlan_end:

            with transaction.atomic():
                return Tag.objects.create(
                    vlan=first_free_vlan,
                    vlan_range=tag_range,
                    name=serviceData["end_company_name"],
                    division="CN",
                    customer=serviceData["name"],
                    access_hs=serviceData["access_hs"],
                    sector=serviceData["sector"],
                    usage="SVLAN",
                    service=serviceData["service"],
                    speed=serviceData["speed"],
                    circ_no=serviceData["circuit_id"],
                    Service_id=serviceData["service_id"],
                    comment="Reserved TMF716 via api"
                )
    return None


def search_and_reserve_vlan(serviceData):
    print(serviceData)
    
    company = get_account(serviceData["name"],serviceData["number"])
    region = normalize_string(serviceData["province"])
    data_center = get_data_center(region)

    tag_ranges = TagRange.objects.filter(
        datacenter=data_center.id,
        company=company

    )
    if tag_ranges:
        return allocate_first_free_tag_from_ranges(serviceData,tag_ranges)
    else:
        company = get_account("primary")
        comsol_ranges = TagRange.objects.filter(
            datacenter=data_center.id,
            company=company
        )
        print(comsol_ranges)
        return allocate_first_free_tag_from_ranges(serviceData,comsol_ranges)
        
        
def get_account(account, code=None):
    if code:
        # If code is provided, match both name and code
        company, created = Company.objects.get_or_create(
            name=account,
            code=code,
            defaults={
                'country': 'ZA',
            }
        )
    else:
        # If code is not provided, match only by name
        company, created = Company.objects.get_or_create(
            companytype=account,
            defaults={
                'country': 'ZA',
                'code': '',  # optional: set a default code if needed
            }
        )
    return company

def get_data_center(region_name):
    try:
        region = Region.objects.select_related("datacenter").get(
            name__iexact=region_name
        )

        if region.datacenter:
            return region.datacenter

        return None

    except Region.DoesNotExist:
        return None


def normalize_string(value: str) -> str:
    """
    Keep only alphabetic characters, replace everything else with spaces,
    and capitalize each word.
    """
    # Replace non-letter characters with space
    cleaned = re.sub(r"[^A-Za-z]", " ", value)

    # Normalize spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned.title()

def get_snow_session_token():
    url = f'{SNOW_URL}oauth_token.do'
    
    payload = f'grant_type=client_credentials&client_secret={CLIENT_SECRETE}&client_id={CLIENT_ID}'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    data = response.json()
    token = data.get("access_token")
    print(token)

    return token


def get_snow_service_data(token, service_id):
    try:
        url = f"{SNOW_URL}api/now/table/u_comsol_provisioning_and_planning?sysparm_fields=u_initiated_from.u_end_company_name,u_initiated_from.company.sys_id,u_initiated_from.company.name,u_initiated_from.u_link_size,u_initiated_from.cat_item.name,u_initiated_from.u_circuit_number,u_initiated_from.u_service_id,u_initiated_from.location.state,u_initiated_from.u_broadband_delivery_type,u_sector.name,u_highsite_name_ref.name,u_number&sysparm_query=u_service_id={service_id}"

        payload = {}
        headers = {
        'Authorization': f'Bearer {token}'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
        print(response.text)
        data = response.json()
        print("Parsed JSON:", data)
        results = data.get("result", [])

        if not results:
            return None

        # If only one record → use it
        if len(results) == 1:
            item = results[0]
        else:
            # If multiple → find first record where circuit number exists
            item = next(
                (r for r in results if r.get("u_circuit_number")),
                results[0]
            )

        return {
            "end_company_name": item.get("u_initiated_from.u_end_company_name", ""),
            "access_hs": item.get("u_highsite_name_ref.name", ""),
            "speed": item.get("u_initiated_from.u_link_size", ""),
            "sector": item.get("u_sector.name", ""),
            "service": item.get("u_initiated_from.cat_item.name", ""),
            "circuit_id": item.get("u_initiated_from.u_circuit_number", ""),
            "service_id": item.get("u_initiated_from.u_service_id", ""),
            "delevary_type": item.get("u_initiated_from.u_broadband_delivery_type", ""),
            "province": item.get("u_initiated_from.location.state") or "Gauteng",
            "name": item.get("u_initiated_from.company.name", ""),
            "number": item.get("u_initiated_from.company.sys_id", "")
        }

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except ValueError:
        print("JSON decode error")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None


