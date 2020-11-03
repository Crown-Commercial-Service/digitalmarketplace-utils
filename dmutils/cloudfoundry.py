"""
Support for running on a CloudFoundry platform such as GOV.UK PaaS.
"""

import json


def get_vcap_services(app, default=None) -> dict:
    if app.config.get("VCAP_SERVICES") is None:
        return default

    vcap_services = json.loads(app.config["VCAP_SERVICES"])

    return vcap_services


def get_service_by_name_from_vcap_services(vcap_services: dict, name: str) -> dict:
    """Returns the first service from a VCAP_SERVICES json object that has name"""
    for services in vcap_services.values():
        for service in services:
            if service["name"] == name:
                return service

    raise RuntimeError(f"Unable to find service with name {name} in VCAP_SERVICES")
