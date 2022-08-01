import ipaddress

import ipinfo
from ipinfo.exceptions import RequestQuotaExceededError, TimeoutExceededError
from requests.exceptions import HTTPError

from .config import settings

handler = ipinfo.getHandler(settings.IPINFO_ACCESS_TOKEN)


def get_ip_address_details(ip_address: str) -> None | dict:
    if ipaddress.ip_address(ip_address).is_private:
        return None
    try:
        return handler.getDetails(ip_address).all
    except (RequestQuotaExceededError, TimeoutExceededError, HTTPError):
        return None
