from celery import shared_task
import requests
from django.core.cache import cache

@shared_task
def fetch_and_cache_data():
    """
    Pulls external data and stores it in Redis cache
    """

    # url = "https://jsonplaceholder.typicode.com/posts"

    # try:
    #     response = requests.get(url, timeout=10)
    #     response.raise_for_status()
    #     data = response.json()

    #     # Store in Redis cache for 10 minutes
    #     cache.set("external_posts", data, timeout=600)

    #     return f"Cached {len(data)} records"

    # except Exception as e:
    #     return f"Error: {str(e)}"

    return "This is a placeholder task. Replace with actual data fetching logic."