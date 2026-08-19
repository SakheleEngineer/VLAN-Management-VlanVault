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
import json
from psycopg2.extras import execute_values
from celery import shared_task
from django.core.cache import cache
from celery import shared_task
import socket
from django.db import connection

@shared_task
def fetch_and_cache_data():
    """
    Fetch SHF data, merge terminal station data using u_service_id,
    check CPE reachability.
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

            merged_item = {
                **shf,
                "cpe_reachable": False
            }

        merged_list.append(merged_item)

    # push the list to aws
    # bulk_upsert_services(merged_list)

    # aws_merged_list = get_all_services()
    # Build_Global_Audit_Catch(aws_merged_list)






