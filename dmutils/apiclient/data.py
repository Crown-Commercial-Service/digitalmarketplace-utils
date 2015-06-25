from .base import BaseAPIClient, logger
from .errors import HTTPError


class DataAPIClient(BaseAPIClient):
    def init_app(self, app):
        self.base_url = app.config['DM_DATA_API_URL']
        self.auth_token = app.config['DM_DATA_API_AUTH_TOKEN']

    # Audit Events

    def find_audit_events(
            self,
            audit_type=None,
            audit_date=None,
            page=None,
            acknowledged=None):

        params = {}
        if audit_type:
            params["audit-type"] = audit_type
        if page is not None:
            params['page'] = page
        if audit_date is not None:
            params['audit-date'] = audit_date
        if acknowledged is not None:
            params['acknowledged'] = acknowledged

        return self._get(
            "/audit-events",
            params
        )

    def acknowledge_audit_event(self, audit_event_id, user):
        return self._post(
            "/audit-events/{}/acknowledge".format(audit_event_id),
            data={
                "update_details": {
                    "updated_by": user
                }
            })

    # Suppliers

    def find_suppliers(self, prefix=None, page=None, framework=None):
        params = {}
        if prefix:
            params["prefix"] = prefix
        if page is not None:
            params['page'] = page
        if framework is not None:
            params['framework'] = framework

        return self._get(
            "/suppliers",
            params=params
        )

    def get_supplier(self, supplier_id):
        return self._get(
            "/suppliers/{}".format(supplier_id)
        )

    def create_supplier(self, supplier_id, supplier):
        return self._put(
            "/suppliers/{}".format(supplier_id),
            data={"suppliers": supplier},
        )

    def update_supplier(self, supplier_id, supplier, user):
        return self._post(
            "/suppliers/{}".format(supplier_id),
            data={
                "suppliers": supplier,
                "updated_by": user,
            },
        )

    def update_contact_information(self, supplier_id, contact_id,
                                   contact, user):
        return self._post(
            "/suppliers/{}/contact-information/{}".format(
                supplier_id, contact_id),
            data={
                "contactInformation": contact,
                "updated_by": user,
            },
        )

    # Users

    def create_user(self, user):
        return self._post(
            "/users",
            data={
                "users": user,
            })

    def get_user(self, user_id=None, email_address=None):
        if user_id is not None and email_address is not None:
            raise ValueError(
                "Cannot get user by both user_id and email_address")
        elif user_id is not None:
            url = "{}/users/{}".format(self.base_url, user_id)
            params = {}
        elif email_address is not None:
            url = "{}/users".format(self.base_url)
            params = {"email": email_address}
        else:
            raise ValueError("Either user_id or email_address must be set")

        try:
            return self._get(url, params=params)
        except HTTPError as e:
            if e.status_code != 404:
                raise
        return None

    def authenticate_user(self, email_address, password, supplier=True):
        try:
            response = self._post(
                '/users/auth',
                data={
                    "authUsers": {
                        "emailAddress": email_address,
                        "password": password,
                    }
                })
            if not supplier or "supplier" in response['users']:
                return response
        except HTTPError as e:
            if e.status_code not in [400, 403, 404]:
                raise
        return None

    def update_user_password(self, user_id, new_password):
        try:
            self._post(
                '/users/{}'.format(user_id),
                data={"users": {"password": new_password}}
            )

            logger.info("Updated password for user %s", user_id)
            return True
        except HTTPError as e:
            logger.info("Password update failed for user %s: %s",
                        user_id, e.status_code)
            return False

    # Services

    def find_draft_services(
            self, supplier_id, service_id=None, framework=None):

        url = "/draft-services?supplier_id={}".format(supplier_id)

        if service_id:
            url = "{}&service_id={}".format(url, service_id)

        if framework:
            url = "{}&framework={}".format(url, framework)

        return self._get(url)

    def get_draft_service(self, draft_id):
        return self._get(
            "/draft-services/{}".format(draft_id)
        )

    def delete_draft_service(self, draft_id, user):
        return self._delete(
            "/draft-services/{}".format(draft_id),
            data={
                "update_details": {
                    "updated_by": user,
                    "update_reason": "deprecated",
                },
            })

    def copy_draft_service_from_existing_service(self, service_id, user):
        return self._put(
            "/draft-services/copy-from/{}".format(service_id),
            data={
                "update_details": {
                    "updated_by": user,
                    "update_reason": "deprecated",
                },
            })

    def update_draft_service(self, draft_id, service, user):
        return self._post(
            "/draft-services/{}".format(draft_id),
            data={
                "update_details": {
                    "updated_by": user,
                    "update_reason": "deprecated",
                },
                "services": service,
            })

    def publish_draft_service(self, draft_id, user):
        return self._post(
            "/draft-services/{}/publish".format(draft_id),
            data={
                "update_details": {
                    "updated_by": user,
                    "update_reason": "deprecated",
                },
            })

    def create_new_draft_service(self, framework_slug, supplier_id, user, lot):
        return self._post(
            "/draft-services/{}/create".format(framework_slug),
            data={
                "update_details": {
                    "updated_by": user
                },
                "services": {
                    "supplierId": supplier_id,
                    "lot": lot
                }

            })

    def get_archived_service(self, archived_service_id):
        return self._get("/archived-services/{}".format(archived_service_id))

    def get_service(self, service_id):
        try:
            return self._get(
                "/services/{}".format(service_id))
        except HTTPError as e:
            if e.status_code != 404:
                raise
        return None

    def find_services(self, supplier_id=None, page=None):
        params = {}
        if supplier_id is not None:
            params['supplier_id'] = supplier_id
        if page is not None:
            params['page'] = page

        return self._get(
            self.base_url + "/services",
            params=params)

    def import_service(self, service_id, service, user, reason):
        return self._put(
            "/services/{}".format(service_id),
            data={
                "update_details": {
                    "updated_by": user,
                    "update_reason": reason,
                },
                "services": service,
            })

    def update_service(self, service_id, service, user, reason):
        return self._post(
            "/services/{}".format(service_id),
            data={
                "update_details": {
                    "updated_by": user,
                    "update_reason": reason,
                },
                "services": service,
            })

    def update_service_status(self, service_id, status, user, reason):
        return self._post(
            "/services/{}/status/{}".format(service_id, status),
            data={
                "update_details": {
                    "updated_by": user,
                    "update_reason": reason,
                },
            })
