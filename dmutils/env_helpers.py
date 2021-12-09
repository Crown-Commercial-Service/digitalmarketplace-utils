import os


def get_api_endpoint_from_stage(stage: str, app: str = 'api') -> str:
    """Return the full URL of given API or Search API environment.

    :param stage: environment name. Can be 'production', 'dev' (aliases: 'local', 'development'), 'staging', 'preview',
                  or the name of any other environment
    :param app: should be either 'api' or 'search-api'

    """
    dev_ports = {
        "api": os.getenv("DM_API_PORT", 5000),
        "search-api": os.getenv("DM_SEARCH_API_PORT", 5009),
        "antivirus-api": os.getenv("DM_ANTIVIRUS_API_PORT", 5008),
    }

    if stage in ['local', 'dev', 'development']:
        return 'http://localhost:{}'.format(dev_ports[app])
    elif stage == "production":
        return f'https://{app}.digitalmarketplace.service.gov.uk'

    return f'https://{app}.{stage}.marketplace.team'


def get_web_url_from_stage(stage: str) -> str:
    """Return the full URL of given web environment.

    :param stage: environment name. Can be 'production', 'dev' (aliases: 'local', 'development'), 'staging', 'preview',
                  or the name of any other environment
    """
    if stage in ['local', 'dev', 'development']:
        return 'http://localhost'
    elif stage == "production":
        return 'https://www.digitalmarketplace.service.gov.uk'

    return f'https://www.{stage}.marketplace.team'


def get_assets_endpoint_from_stage(stage: str) -> str:
    if stage in ['local', 'dev', 'development']:
        # Static files are not served via nginx for local environments
        raise NotImplementedError()

    return get_api_endpoint_from_stage(stage, 'assets')
