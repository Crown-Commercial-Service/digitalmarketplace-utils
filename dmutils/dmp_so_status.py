from datetime import datetime

G13_OPEN = datetime(2022, 3, 9, 10, 0, 0)
G13_CLOSE = datetime(2022, 5, 18, 15, 0, 0)


def are_new_frameworks_live(_params) -> bool:
    # return G13_OPEN <= datetime.now() <= G13_CLOSE or params.get('show_dmp_so_banner') == 'true'
    return True
