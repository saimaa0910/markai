"""
Standardized Service Cache Key Generators.
"""


def get_service_cache_key(service_name: str, resource_id: str) -> str:
    return f"eaimos:service:{service_name}:{resource_id}"
