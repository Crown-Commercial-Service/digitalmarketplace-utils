from datetime import datetime

DOS6_OPEN = datetime(2022, 1, 14, 12, 0, 0)
DOS6_CLOSE = datetime(2022, 2, 24, 15, 0, 0)


def are_new_frameworks_live(params) -> bool:
    return DOS6_OPEN <= datetime.now() <= DOS6_CLOSE or params.get('show_dmp_so_banner') == 'true'
