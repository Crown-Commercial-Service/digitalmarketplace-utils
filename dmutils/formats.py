DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DATE_FORMAT = "%Y-%m-%d"
DISPLAY_DATE_FORMAT = '%d/%m/%Y'
DISPLAY_TIME_FORMAT = '%H:%M:%S'
DISPLAY_DATETIME_FORMAT = '%A, %d %B %Y at %H:%M'

LOTS = [
    {
        'lot': 'saas',
        'lot_case': 'SaaS',
        'label': u'Software as a Service',
    },
    {
        'lot': 'paas',
        'lot_case': 'PaaS',
        'label': u'Platform as a Service',
    },
    {
        'lot': 'iaas',
        'lot_case': 'IaaS',
        'label': u'Infrastructure as a Service',
    },
    {
        'lot': 'scs',
        'lot_case': 'SCS',
        'label': u'Specialist Cloud Services',
    },
]


def lot_to_lot_case(lot_to_check):
    lot_i_found = [lot for lot in LOTS if lot['lot'] == lot_to_check]
    if lot_i_found:
        return lot_i_found[0]['lot_case']
    return None


def get_label_for_lot_param(lot_to_check):
    lot_i_found = [lot for lot in LOTS if lot['lot'] == lot_to_check]
    if lot_i_found:
        return lot_i_found[0]['label']
    return None
