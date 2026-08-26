from typing import Optional
from api.services.device_detection import parse_user_agent

def enhance_session_metadata(
    session,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    city: Optional[str] = None,
    country_code: Optional[str] = None,
    region: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> None:
    """
    Enhances the session metadata by parsing user_agent and setting location/geolocation.
    """
    if user_agent:
        device_info = parse_user_agent(user_agent)
        session.device_type = device_info.device_type
        session.device_name = device_info.get_friendly_name()
        session.browser = device_info.browser
        session.browser_version = device_info.browser_version
        session.os = device_info.os
        session.os_version = device_info.os_version

    if ip_address:
        session.ip_address = ip_address

    if city:
        session.city = city
    if country_code:
        session.country_code = country_code
    if region:
        session.region = region
    if latitude is not None:
        session.latitude = latitude
    if longitude is not None:
        session.longitude = longitude

    # Construct formatted location
    loc_parts = []
    if city:
        loc_parts.append(city)
    if region:
        loc_parts.append(region)
    if country_code:
        loc_parts.append(country_code)
    if loc_parts:
        session.location = ", ".join(loc_parts)
