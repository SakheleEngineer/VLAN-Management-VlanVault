from celery import shared_task
import requests
from django.core.cache import cache
from decouple import config
from taglib.tag_utility_library  import *
from django.core.cache import cache
from celery import shared_task
import subprocess
import platform
import socket

from celery import shared_task
from django.core.cache import cache
from celery import shared_task

import socket


def check_cpe_reachable(ip, ports=(80, 443, 23), timeout=2):
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


@shared_task
def fetch_and_cache_data():
    """
    Fetch SHF data, merge terminal station data using u_service_id,
    check CPE reachability, and cache each service individually using
    u_svid or u_svid_2 as the cache key.
    """
    token = get_snow_session_token()
    shf_list = get_service_handover_form_data(token)

    merged_list = []

    for shf in shf_list:
        service_id = shf.get("u_service_id")

        if not service_id:
            continue

        try:
            response = get_terminal_station_data(token, service_id)

            terminal_station = (
                response.get("result", [{}])[0]
                if isinstance(response, dict)
                else (response[0] if response else {})
            )

            client_radio_ip = terminal_station.get("u_client_radio_ip")

            merged_item = {
                **shf,
                **terminal_station,
                "cpe_reachable": check_cpe_reachable(client_radio_ip)
            }

        except Exception as e:
            print(f"Error processing service {service_id}: {e}")

            merged_item = {
                **shf,
                "cpe_reachable": False
            }

        merged_list.append(merged_item)

    #push the list to aws
    bulk_upsert_services(merged_list)
    aws_merged_list = get_all_services()


    for item in aws_merged_list:
        # Use u_svid first, then u_svid_2
        cache_key = item.get("u_service_id")
        # Cache individual service
        cache.set(
            cache_key,
            item,
            timeout=3600
        )

    redis_client = cache.client.get_client()
    print(redis_client.dbsize())
    print(f"Processed {len(merged_list)} services")




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
            service_cache.svid IS DISTINCT FROM EXCLUDED.svid
            OR service_cache.service_data IS DISTINCT FROM EXCLUDED.service_data
            OR service_cache.cpe_reachable IS DISTINCT FROM EXCLUDED.cpe_reachable
    """

    with connection.cursor() as cursor:
        execute_values(
            cursor,
            sql,
            rows,
            page_size=1000
        )

from django.db import connection


def get_all_services():

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT service_data
            FROM service_cache
            ORDER BY service_id
        """)

        return [row[0] for row in cursor.fetchall()]