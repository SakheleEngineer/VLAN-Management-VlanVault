
from django.db import transaction
from django.core.cache import cache
from company.models import Company
from tag.models import Tag, ConfigurationSettings
from tag_set.models import TagRange
from region.models import Region
import re
import requests
import json
from decouple import config
import csv
from io import TextIOWrapper
from django.core.exceptions import ValidationError
import subprocess
import platform
import socket
import json
from psycopg2.extras import execute_values
from celery import shared_task
from django.db import connection

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
    company = get_account(serviceData["name"],serviceData["number"])
    province = normalize_string(serviceData["province"])
    data_center = get_data_center(province)
    print("data_center: "+str(company.name)+" "+str(data_center))

    tag_ranges = TagRange.objects.filter(
        datacenter=data_center.id,
        company=company
    )
    configuration_settings = ConfigurationSettings.objects.filter(
    product_name=serviceData["service"],delivery_type=serviceData["delevary_type"],configuration_type="vpls").first()
    if tag_ranges:
        #getting a shared VLAN
        if configuration_settings:
            existing_tag = Tag.objects.filter(
                vlan_range__in=tag_ranges,
                configuration_settings=configuration_settings
            ).first()
            if existing_tag:
                return existing_tag

        return allocate_first_free_tag_from_ranges(serviceData,tag_ranges)
    else:
        #get primary company 
        primary_company = None
        try:
            primary_company = Company.objects.get(companytype="primary")
        except Company.DoesNotExist:
            primary_company = None
   
        company = get_account(primary_company.name,code=primary_company.code)
        #getting comsol or primary company shared VLAN
        if configuration_settings:
            existing_tag = Tag.objects.filter(
                vlan_range__in=tag_ranges,
                configuration_settings=configuration_settings
            ).first()
            if existing_tag:
               return existing_tag
            
        comsol_ranges = TagRange.objects.filter(
            datacenter=data_center.id,
            company=company
        )
        
        return allocate_first_free_tag_from_ranges(serviceData,comsol_ranges)
        
def get_account(account, code=None):
    company, created = Company.objects.get_or_create(
        name=account)
  
    return company
# def get_account(account, code=None):
#     company, created = Company.objects.get_or_create(
#         name=account,
#         defaults={
#             'country': 'ZA',
#             'code': code or '',
#         }
#     )

#     if not created and code and company.code != code:
#         company.code = code
#         company.save(update_fields=['code'])

#     return company

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

def create_tags_from_csv(tag_range, csv_file):
    """
    Upload tags from CSV and return:
    - successfully created tags
    - skipped/occupied tags
    - validation errors
    """

    audit_tag_list = []
    occupied = []
    errors = []

    # Get already used VLANs in this range
    existing_vlans = set(
        Tag.objects.filter(vlan_range=tag_range)
        .values_list("vlan", flat=True)
    )

    # Start VLAN allocation from range start
    current_vlan = tag_range.vlan_start

    # Read CSV
    file_data = TextIOWrapper(csv_file.file, encoding="utf-8")
    reader = csv.DictReader(file_data)

    with transaction.atomic():

        for row in reader:

            # Skip occupied VLANs
            while current_vlan in existing_vlans:
                occupied.append(current_vlan)
                current_vlan += 1

            # Stop if range exceeded
            if current_vlan > tag_range.vlan_end:
                errors.append({
                    "name": row.get("Name", ""),
                    "error": "No VLANs left in range"
                })
                break

            try:

                tag = Tag(
                    vlan=current_vlan,
                    division=row.get("Division", "").strip(),
                    customer=row.get("Customer", "").strip(),
                    name=row.get("Name", "").strip(),
                    access_hs=row.get("Access HS", "").strip(),
                    sector=row.get("", "").strip(),  # Empty column F in sheet
                    usage=row.get("Usage", "").strip(),
                    service=row.get("Service", "").strip(),
                    speed=row.get("Speed", "").strip(),
                    circ_no=row.get("Circ No", "").strip(),
                    vlan_range=tag_range,
                )

                temp_result = audit_tag(tag)
                if temp_result == "success":
                    tag.full_clean()
                    tag.save()

                    audit_tag_list.append({
                        "vlan": current_vlan,
                        "tag": tag,
                        "status": temp_result,
                    })

                else:
                    audit_tag_list.append({
                        "vlan": current_vlan,
                        "tag": tag,
                        "status": temp_result,
                    })


                existing_vlans.add(current_vlan)
                current_vlan += 1

            except ValidationError as e:
                errors.append({
                    "name": row.get("Name", ""),
                    "error": e.message_dict if hasattr(e, "message_dict") else str(e)
                })

            except Exception as e:
                errors.append({
                    "name": row.get("Name", ""),
                    "error": str(e)
                })

    return {
        "audit_list": audit_tag_list,
        "occupied": occupied,
        "errors": errors,
    }


def audit_tag(tag):
    #check if tag is not in use and if it is not reserved for another service
    tag_value = cache.get(tag.Service_id)

    if Tag.objects.filter(Service_id=tag.Service_id).exists():
        return "The ServiceID is in use"

    if tag_value:
        if tag_value["status"] == "Decommissioned" and tag_value["cpe_reachable"] == True:
            return "The CPE is reachable, but the service is decommissioned, please investigate further"

        if tag_value["cpe_reachable"] == False:
            return "The CPE is not reachable"

        if tag_value["status"] == "Decommissioned" and tag_value["cpe_reachable"] == False:
            return "Decommissioned"
        else:
            return "success"
    else:
        return "The service has no TS or SHF on Service Now, please investigate further"


def get_service_handover_form_data(token):

    import requests

    url = f"{SNOW_URL}api/now/table/u_comsol_networks_shf?sysparm_fields=u_svid%2C%20u_svid_2%2C%20u_client_radio_ip%2C%20u_circuit_id%2C%20u_service_id&sysparm_limit=5"

    payload = {}
    headers = {
       'Authorization': f'Bearer {token}'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json().get("result", [])

def get_terminal_station_data(token, service_id):

    url = f"{SNOW_URL}api/now/table/u_cmdb_comsol_terminal_station?sysparm_query=u_service_id%3D{service_id}&sysparm_fields=u_initiated_from.cat_item.name%2Cu_service_id%2Cu_state&sysparm_limit=10"

    payload = {}
    headers = {
       'Authorization': f'Bearer {token}'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json().get("result", [])


def get_existing_services():

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT
                service_id,
                service_data
            FROM service_cache
        """)

        return {
            row[0]: row[1]
            for row in cursor.fetchall()
        }

def check_cpe_reachable(ip, ports=(80, 443, 23, 22), timeout=2):
    """
    Returns True if any of the specified ports are reachable.
    """
    if not ip:
        return False

    for port in ports:
        try:
            with socket.create_connection((ip, port), timeout=timeout):
                return True
        except Exception:
            continue

    return False



def bulk_upsert_services(merged_list):
    """
    Bulk upsert all merged services into PostgreSQL RDS.
    """
    rows = []
    for item in merged_list:

        rows.append(
            (
                item.get("u_service_id"),
                item.get("u_svid") or item.get("u_svid_2"),
                json.dumps(item),
                item.get("cpe_reachable", False),
            )
        )

    if not rows:
        return

    # New service → INSERT
    # Existing service with changed data → UPDATE
    # Existing service with identical data → DO NOTHING

    sql = """
        INSERT INTO service_cache (
            service_id,
            svid,
            service_data,
            cpe_reachable
        )
        VALUES %s
        ON CONFLICT (service_id)
        DO UPDATE SET
            svid = EXCLUDED.svid,
            service_data = EXCLUDED.service_data,
            cpe_reachable = EXCLUDED.cpe_reachable,
            updated_at = NOW()
        WHERE
            service_cache.service_data IS DISTINCT FROM EXCLUDED.service_data
            OR service_cache.cpe_reachable IS DISTINCT FROM EXCLUDED.cpe_reachable
    """

    with connection.cursor() as cursor:
        execute_values(
            cursor,
            sql,
            rows,
            page_size=1000
        )

def get_all_services():

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT service_data
            FROM service_cache
            ORDER BY service_id
        """)

        return [row[0] for row in cursor.fetchall()]



def Build_Global_Audit_Catch(aws_merged_list):
    for item in aws_merged_list:
        cache_key = item.get("u_service_id")
        # Cache individual service
        cache.set(
            cache_key,
            item,
            timeout=3600
        )
    
    redis_client = cache.client.get_client()
