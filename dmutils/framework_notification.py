from datetime import date

# Go Live Dates
DOS6_GO_LIVE_DATE = '2022-01-14'


def dos6_live(params) -> bool:
    return date.today().strftime('%Y-%m-%d') >= DOS6_GO_LIVE_DATE or params.get('show_dos6_live') == 'true'
