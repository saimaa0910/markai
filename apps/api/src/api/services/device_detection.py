"""Sprint 8.3.1 Phase 2 - Device Detection Service

Parses User-Agent strings to extract device, browser, and OS information.
Provides user-friendly device names and classifications.

Usage:
    from api.services.device_detection import parse_user_agent
    
    device_info = parse_user_agent(request.headers.get("user-agent"))
    # Returns: DeviceInfo(
    #     device_type='mobile',
    #     device_name='iPhone',
    #     browser='Safari',
    #     browser_version='17.0',
    #     os='iOS',
    #     os_version='17.0'
    # )
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceInfo:
    """Parsed device information from User-Agent string."""
    device_type: str  # mobile, tablet, desktop, bot, unknown
    device_name: Optional[str] = None  # iPhone, Galaxy S24, MacBook Pro, etc.
    browser: Optional[str] = None  # Chrome, Safari, Firefox, Edge, etc.
    browser_version: Optional[str] = None
    os: Optional[str] = None  # iOS, Android, Windows, macOS, Linux
    os_version: Optional[str] = None
    is_bot: bool = False
    
    def get_friendly_name(self) -> str:
        """
        Generate user-friendly device name.
        Examples:
            - "iPhone (iOS 17.0)"
            - "Chrome on Windows"
            - "Samsung Galaxy (Android 14)"
        """
        if self.is_bot:
            return f"Bot: {self.browser or 'Unknown'}"
        
        if self.device_name:
            if self.os and self.os_version:
                return f"{self.device_name} ({self.os} {self.os_version})"
            elif self.os:
                return f"{self.device_name} ({self.os})"
            return self.device_name
        
        if self.browser and self.os:
            return f"{self.browser} on {self.os}"
        
        if self.browser:
            return f"{self.browser} Browser"
        
        if self.os:
            return f"{self.os} Device"
        
        return "Unknown Device"


def parse_user_agent(user_agent: Optional[str]) -> DeviceInfo:
    """
    Parse User-Agent string and extract device information.
    
    This is a simple parser that handles common cases. For production,
    consider using a library like `user-agents` or `python-user-agents`.
    
    Args:
        user_agent: User-Agent header string
        
    Returns:
        DeviceInfo with parsed information
    """
    if not user_agent:
        return DeviceInfo(device_type="unknown")
    
    ua = user_agent.lower()
    
    # Check for bots
    if _is_bot(ua):
        bot_name = _extract_bot_name(user_agent)
        return DeviceInfo(
            device_type="bot",
            browser=bot_name,
            is_bot=True
        )
    
    # Detect device type and name
    device_type = _detect_device_type(ua)
    device_name = _extract_device_name(user_agent, device_type)
    
    # Detect OS
    os_name, os_version = _extract_os(user_agent)
    
    # Detect browser
    browser, browser_version = _extract_browser(user_agent)
    
    return DeviceInfo(
        device_type=device_type,
        device_name=device_name,
        browser=browser,
        browser_version=browser_version,
        os=os_name,
        os_version=os_version,
        is_bot=False
    )


def _is_bot(ua: str) -> bool:
    """Check if User-Agent indicates a bot/crawler."""
    bot_indicators = [
        'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
        'python-requests', 'http', 'java', 'apache', 'php'
    ]
    return any(indicator in ua for indicator in bot_indicators)


def _extract_bot_name(ua: str) -> str:
    """Extract bot name from User-Agent."""
    # Common bot patterns
    bot_patterns = [
        (r'googlebot', 'Googlebot'),
        (r'bingbot', 'Bingbot'),
        (r'slackbot', 'Slackbot'),
        (r'twitterbot', 'Twitterbot'),
        (r'facebookexternalhit', 'Facebook Bot'),
        (r'linkedinbot', 'LinkedIn Bot'),
        (r'curl/(\S+)', 'cURL'),
        (r'python-requests/(\S+)', 'Python Requests'),
    ]
    
    ua_lower = ua.lower()
    for pattern, name in bot_patterns:
        if re.search(pattern, ua_lower):
            return name
    
    return "Unknown Bot"


def _detect_device_type(ua: str) -> str:
    """Detect device type: mobile, tablet, desktop."""
    if 'ipad' in ua or 'tablet' in ua or 'kindle' in ua:
        return 'tablet'
    
    mobile_indicators = [
        'mobile', 'iphone', 'android', 'blackberry',
        'windows phone', 'opera mini', 'iemobile'
    ]
    if any(indicator in ua for indicator in mobile_indicators):
        return 'mobile'
    
    return 'desktop'


def _extract_device_name(ua: str, device_type: str) -> Optional[str]:
    """Extract specific device name/model."""
    # iPhone
    if 'iphone' in ua.lower():
        return 'iPhone'
    
    # iPad
    if 'ipad' in ua.lower():
        return 'iPad'
    
    # Android devices
    android_match = re.search(r'(samsung|pixel|galaxy|nexus|huawei|oneplus|xiaomi|oppo|vivo)\s*([\w\s-]+)?', ua, re.I)
    if android_match:
        brand = android_match.group(1).title()
        model = android_match.group(2).strip() if android_match.group(2) else ''
        return f"{brand} {model}".strip() if model else brand
    
    # macOS
    if 'macintosh' in ua.lower() or 'mac os' in ua.lower():
        return 'Mac'
    
    # Windows
    if 'windows' in ua.lower():
        return 'Windows PC'
    
    # Linux
    if 'linux' in ua.lower():
        return 'Linux PC'
    
    return None


def _extract_os(ua: str) -> tuple[Optional[str], Optional[str]]:
    """Extract OS name and version."""
    # iOS
    ios_match = re.search(r'(?:iPhone|iPad|iPod).*?OS\s+([0-9_]+)', ua, re.I)
    if ios_match:
        version = ios_match.group(1).replace('_', '.')
        return 'iOS', version
    
    # Android
    android_match = re.search(r'Android\s+([0-9.]+)', ua, re.I)
    if android_match:
        return 'Android', android_match.group(1)
    
    # Windows
    windows_match = re.search(r'Windows NT\s+([0-9.]+)', ua, re.I)
    if windows_match:
        nt_version = windows_match.group(1)
        windows_versions = {
            '10.0': '10/11',
            '6.3': '8.1',
            '6.2': '8',
            '6.1': '7',
            '6.0': 'Vista',
            '5.1': 'XP',
        }
        version = windows_versions.get(nt_version, nt_version)
        return 'Windows', version
    
    # macOS
    macos_match = re.search(r'Mac OS X\s+([0-9_]+)', ua, re.I)
    if macos_match:
        version = macos_match.group(1).replace('_', '.')
        return 'macOS', version
    
    # Linux
    if 'linux' in ua.lower():
        return 'Linux', None
    
    return None, None


def _extract_browser(ua: str) -> tuple[Optional[str], Optional[str]]:
    """Extract browser name and version."""
    # Edge (must check before Chrome, as Edge includes 'Chrome' in UA)
    edge_match = re.search(r'Edg(?:e|A|iOS)?/(\S+)', ua, re.I)
    if edge_match:
        return 'Edge', edge_match.group(1)
    
    # Chrome (must check before Safari, as Chrome includes 'Safari' in UA)
    chrome_match = re.search(r'Chrome/(\S+)', ua, re.I)
    if chrome_match and 'edg' not in ua.lower():
        return 'Chrome', chrome_match.group(1).split()[0]
    
    # Safari
    safari_match = re.search(r'Version/(\S+).*Safari', ua, re.I)
    if safari_match:
        return 'Safari', safari_match.group(1).split()[0]
    
    # Firefox
    firefox_match = re.search(r'Firefox/(\S+)', ua, re.I)
    if firefox_match:
        return 'Firefox', firefox_match.group(1)
    
    # Opera
    opera_match = re.search(r'(?:Opera|OPR)/(\S+)', ua, re.I)
    if opera_match:
        return 'Opera', opera_match.group(1)
    
    return None, None


def format_location(city: Optional[str], region: Optional[str], country_code: Optional[str]) -> Optional[str]:
    """
    Format location string for display.
    
    Examples:
        - city='San Francisco', region='California', country='US' → 'San Francisco, CA, US'
        - city='London', country='GB' → 'London, GB'
        - country='US' → 'US'
    
    Args:
        city: City name
        region: State/region name
        country_code: ISO 2-letter country code
        
    Returns:
        Formatted location string or None
    """
    parts = []
    
    if city:
        parts.append(city)
    
    if region:
        # Shorten US states to 2-letter codes if possible
        if country_code == 'US':
            region_abbrev = _us_state_to_abbrev(region)
            parts.append(region_abbrev)
        else:
            parts.append(region)
    
    if country_code:
        parts.append(country_code.upper())
    
    return ', '.join(parts) if parts else None


def _us_state_to_abbrev(state: str) -> str:
    """Convert US state name to 2-letter abbreviation."""
    state_abbrevs = {
        'california': 'CA', 'new york': 'NY', 'texas': 'TX', 'florida': 'FL',
        'illinois': 'IL', 'pennsylvania': 'PA', 'ohio': 'OH', 'georgia': 'GA',
        'north carolina': 'NC', 'michigan': 'MI', 'new jersey': 'NJ',
        'virginia': 'VA', 'washington': 'WA', 'arizona': 'AZ', 'massachusetts': 'MA',
        'tennessee': 'TN', 'indiana': 'IN', 'missouri': 'MO', 'maryland': 'MD',
        'wisconsin': 'WI', 'colorado': 'CO', 'minnesota': 'MN', 'south carolina': 'SC',
        'alabama': 'AL', 'louisiana': 'LA', 'kentucky': 'KY', 'oregon': 'OR',
        'oklahoma': 'OK', 'connecticut': 'CT', 'utah': 'UT', 'iowa': 'IA',
        'nevada': 'NV', 'arkansas': 'AR', 'mississippi': 'MS', 'kansas': 'KS',
        'new mexico': 'NM', 'nebraska': 'NE', 'west virginia': 'WV', 'idaho': 'ID',
        'hawaii': 'HI', 'new hampshire': 'NH', 'maine': 'ME', 'montana': 'MT',
        'rhode island': 'RI', 'delaware': 'DE', 'south dakota': 'SD',
        'north dakota': 'ND', 'alaska': 'AK', 'vermont': 'VT', 'wyoming': 'WY',
    }
    return state_abbrevs.get(state.lower(), state)
