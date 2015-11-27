from enum import Enum, unique


@unique
class AuditTypes(Enum):

    contact_update = "contact_update"
    supplier_update = "supplier_update"
    create_draft_service = "create_draft_service"
    update_draft_service = "update_draft_service"
    complete_draft_service = "complete_draft_service"
    publish_draft_service = "publish_draft_service"
    delete_draft_service = "delete_draft_service"
    update_service = "update_service"
    import_service = "import_service"
    update_service_status = "update_service_status"
    user_auth_failed = "user_auth_failed"
    create_user = "create_user"
    update_user = "update_user"
    answer_selection_questions = "answer_selection_questions"
    register_framework_interest = "register_framework_interest"
    invite_user = "invite_user"
    send_clarification_question = "send_clarification_question"
    view_clarification_questions = "view_clarification_questions"
    send_application_question = "send_application_question"
    send_g7_application_question = "send_g7_application_question"
    snapshot_framework_stats = "snapshot_framework_stats"
    framework_update = "framework_update"

    @staticmethod
    def is_valid_audit_type(test_audit_type):

        for name, audit_type in AuditTypes.__members__.items():
            if audit_type.value == test_audit_type:
                return True
        return False
