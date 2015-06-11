from dmutils.audit import AuditTypes


def test_should_allow_valid_audit_type():
    assert AuditTypes.is_valid_audit_type("contact_update")


def test_should_reject_invalid_audit_type():
    assert not AuditTypes.is_valid_audit_type("not valid")
