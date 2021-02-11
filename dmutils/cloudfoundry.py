"""
Support for running on a CloudFoundry platform such as GOV.UK PaaS.
"""

import json
import os
from typing import Dict, List, cast


def get_vcap_services() -> dict:
    return cast(dict, json.loads(os.environ["VCAP_SERVICES"]))


def get_service_by_name_from_vcap_services(vcap_services: Dict[str, List[dict]], name: str) -> dict:
    """Returns the first service from a VCAP_SERVICES json object that has name"""
    for services in vcap_services.values():
        for service in services:
            if service["name"] == name:
                return service

    raise RuntimeError(f"Unable to find service with name {name} in VCAP_SERVICES")
