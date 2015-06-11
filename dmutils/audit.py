from enum import Enum, unique


@unique
class AuditTypes(Enum):

    contact_update = "contact_update"
    supplier_update = "supplier_update"

    @staticmethod
    def is_valid_audit_type(test_audit_type):

        for name, audit_type in AuditTypes.__members__.items():
            if audit_type.value == test_audit_type:
                return True
        return False
