from enum import Enum, unique


@unique
class AuditTypes(Enum):

    contact_update = "contact_update"
    supplier_update = "supplier_update"
