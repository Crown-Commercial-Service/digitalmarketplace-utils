from dmutils import cloudfoundry
import json


def test_cloudfoundry_vcap_parser():
    vcap_json = """
    {
        "gds-prometheus": [{
            "binding_name": null,
            "credentials": null,
            "instance_name": "digitalmarketplace_prometheus",
            "label": "gds-prometheus",
            "name": "digitalmarketplace_prometheus",
            "plan": "prometheus",
            "provider": null,
            "syslog_drain_url": null,
            "tags": [],
            "volume_mounts": []
        }],
        "redis": [{
            "binding_name": null,
            "credentials": null,
            "instance_name": "digitalmarketplace_redis",
            "label": "splunk",
            "name": "digitalmarketplace_redis",
            "plan": "unlimited",
            "provider": null,
            "tags": [],
            "volume_mounts": []
        }]
    }
            """
    expected_dict = {'binding_name': None,
                     'credentials': None,
                     'instance_name': 'digitalmarketplace_redis',
                     'label': 'splunk',
                     'name': 'digitalmarketplace_redis',
                     'plan': 'unlimited',
                     'provider': None,
                     'tags': [],
                     'volume_mounts': []}
    assert cloudfoundry.get_service_by_name_from_vcap_services(json.loads(vcap_json),
                                                               'digitalmarketplace_redis') == expected_dict
