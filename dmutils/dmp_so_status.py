from datetime import date

DMP_SO_GO_LIVE_DATE = '2022-01-14'


def are_new_frameworks_live(params) -> bool:
    return date.today().strftime('%Y-%m-%d') >= DMP_SO_GO_LIVE_DATE or params.get('show_dmp_so_banner') == 'true'
