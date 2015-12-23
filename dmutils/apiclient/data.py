from __future__ import unicode_literals
from ..audit import AuditTypes
from .base import BaseAPIClient, logger, make_iter_method
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
            per_page=None,
            acknowledged=None,
            object_type=None,
            object_id=None):

        params = {}
        if audit_type:
            if not isinstance(audit_type, AuditTypes):
                raise TypeError("Must be an AuditTypes")
            params["audit-type"] = audit_type.value
        if page is not None:
            params['page'] = page
        if per_page is not None:
            params['per_page'] = per_page
        if audit_date is not None:
            params['audit-date'] = audit_date
        if acknowledged is not None:
            params['acknowledged'] = acknowledged
        if object_type is not None:
            params['object-type'] = object_type
        if object_id is not None:
            params['object-id'] = object_id

        return self._get(
            "/audit-events",
            params=params
        )

    find_audit_events_iter = make_iter_method('find_audit_events', 'auditEvents', 'audit-events')

    def acknowledge_audit_event(self, audit_event_id, user):
        return self._post(
            "/audit-events/{}/acknowledge".format(audit_event_id),
            data={
                "update_details": {
                    "updated_by": user
                }
            })

    def create_audit_event(self, audit_type, user=None, data=None, object_type=None, object_id=None):
        if not isinstance(audit_type, AuditTypes):
            raise TypeError("Must be an AuditTypes")
        if data is None:
            data = {}
        payload = {
            "type": audit_type.value,
            "data": data,
        }
        if user is not None:
            payload['user'] = user
        if object_type is not None:
            payload['objectType'] = object_type
        if object_id is not None:
            payload['objectId'] = object_id

        return self._post(
            '/audit-events',
            data={'auditEvents': payload})

    # Suppliers

    def find_suppliers(self, prefix=None, page=None, framework=None, duns_number=None):
        params = {}
        if prefix:
            params["prefix"] = prefix
        if page is not None:
            params['page'] = page
        if framework is not None:
            params['framework'] = framework
        if duns_number is not None:
            params['duns_number'] = duns_number

        return self._get(
            "/suppliers",
            params=params
        )

    find_suppliers_iter = make_iter_method('find_suppliers', 'suppliers', 'suppliers')

    def get_supplier(self, supplier_id):
        return self._get(
            "/suppliers/{}".format(supplier_id)
        )

    def import_supplier(self, supplier_id, supplier):
        return self._put(
            "/suppliers/{}".format(supplier_id),
            data={"suppliers": supplier},
        )

    def create_supplier(self, supplier):
        return self._post(
            "/suppliers",
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

    def get_framework_interest(self, supplier_id):
        return self._get(
            "/suppliers/{}/frameworks/interest".format(supplier_id)
        )

    def register_framework_interest(self, supplier_id, framework_slug, user):
        return self._put(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "update_details": {
                    "updated_by": user
                }
            },
        )

    def get_supplier_declaration(self, supplier_id, framework_slug):
        response = self._get(
            "/suppliers/{}/frameworks/{}".format(supplier_id, framework_slug)
        )
        return {'declaration': response['frameworkInterest']['declaration']}

    def set_supplier_declaration(self, supplier_id, framework_slug, declaration, user):
        return self._put(
            "/suppliers/{}/frameworks/{}/declaration".format(supplier_id, framework_slug),
            data={
                "updated_by": user,
                "declaration": declaration
            }
        )

    def get_supplier_frameworks(self, supplier_id):
        return self._get(
            "/suppliers/{}/frameworks".format(supplier_id)
        )

    def get_supplier_framework_info(self, supplier_id, framework_slug):
        return self._get(
            "/suppliers/{}/frameworks/{}".format(supplier_id, framework_slug)
        )

    def set_framework_result(self, supplier_id, framework_slug, is_on_framework, user):
        return self._post(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"onFramework": is_on_framework},
                "update_details": {
                    "updated_by": user
                }
            },
        )

    def register_framework_agreement_returned(self, supplier_id, framework_slug, user):
        return self._post(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"agreementReturned": True},
                "update_details": {
                    "updated_by": user
                }
            },
        )

    def find_framework_suppliers(self, framework_slug, agreement_returned=None):
        params = {}
        if agreement_returned is not None:
            params['agreement_returned'] = bool(agreement_returned)
        return self._get(
            '/frameworks/{}/suppliers'.format(framework_slug),
            params=params
        )

    # Users

    def create_user(self, user):
        return self._post(
            "/users",
            data={
                "users": user,
            })

    def find_users(self, supplier_id=None, page=None):
        params = {}
        if supplier_id is not None:
            params['supplier_id'] = supplier_id
        if page is not None:
            params['page'] = page
        return self._get("/users", params=params)

    find_users_iter = make_iter_method('find_users', 'users', 'users')

    def get_user(self, user_id=None, email_address=None):
        if user_id is not None and email_address is not None:
            raise ValueError(
                "Cannot get user by both user_id and email_address")
        elif user_id is not None:
            url = "/users/{}".format(user_id)
            params = {}
        elif email_address is not None:
            url = "/users"
            params = {"email_address": email_address}
        else:
            raise ValueError("Either user_id or email_address must be set")

        try:
            user = self._get(url, params=params)

            if isinstance(user['users'], list):
                user['users'] = user['users'][0]

            return user

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

    def update_user_password(self, user_id, new_password, updater="no logged-in user"):
        try:
            self._post(
                '/users/{}'.format(user_id),
                data={
                    "users": {"password": new_password},
                    "update_details": {
                        "updated_by": updater
                    }
                }
            )
            return True
        except HTTPError as e:
            return False

    def update_user(self,
                    user_id,
                    locked=None,
                    active=None,
                    role=None,
                    supplier_id=None,
                    updater="no logged-in user"):
        fields = {}
        if locked is not None:
            fields.update({
                'locked': locked
            })

        if active is not None:
            fields.update({
                'active': active
            })

        if role is not None:
            fields.update({
                'role': role
            })

        if supplier_id is not None:
            fields.update({
                'supplierId': supplier_id
            })

        params = {
            "users": fields,
            "update_details": {
                "updated_by": updater
            }
        }

        user = self._post(
            '/users/{}'.format(user_id),
            data=params
        )

        logger.info("Updated user {user_id} fields {params}",
                    extra={"user_id": user_id, "params": params})
        return user

    def export_users(self, framework_slug):
        return self._get(
            "/users/export/{}".format(framework_slug)
        )

    # Services

    def find_draft_services(self, supplier_id, service_id=None, framework=None):

        params = {
            'supplier_id': supplier_id
        }
        if service_id is not None:
            params['service_id'] = service_id
        if framework is not None:
            params['framework'] = framework

        return self._get('/draft-services', params=params)

    find_draft_services_iter = make_iter_method('find_draft_services', 'services', 'draft-services')

    def get_draft_service(self, draft_id):
        return self._get(
            "/draft-services/{}".format(draft_id)
        )

    def delete_draft_service(self, draft_id, user):
        return self._delete(
            "/draft-services/{}".format(draft_id),
            data={
                "update_details": {
                    "updated_by": user
                },
            })

    def copy_draft_service_from_existing_service(self, service_id, user):
        return self._put(
            "/draft-services/copy-from/{}".format(service_id),
            data={
                "update_details": {
                    "updated_by": user
                },
            })

    def copy_draft_service(self, draft_id, user):
        return self._post(
            "/draft-services/{}/copy".format(draft_id),
            data={
                "update_details": {
                    "updated_by": user
                }
            })

    def update_draft_service(self, draft_id, service, user, page_questions=None):
        data = {
            "update_details": {
                "updated_by": user
            },
            "services": service,
        }

        if page_questions is not None:
            data['page_questions'] = page_questions

        return self._post("/draft-services/{}".format(draft_id), data=data)

    def complete_draft_service(self, draft_id, user):
        return self._post(
            "/draft-services/{}/complete".format(draft_id),
            data={
                "update_details": {
                    "updated_by": user
                }
            })

    def publish_draft_service(self, draft_id, user):
        return self._post(
            "/draft-services/{}/publish".format(draft_id),
            data={
                "update_details": {
                    "updated_by": user
                },
            })

    def create_new_draft_service(self, framework_slug, lot, supplier_id, data, user, page_questions=None):
        service_data = data.copy()
        service_data.update({
            "frameworkSlug": framework_slug,
            "lot": lot,
            "supplierId": supplier_id,
        })

        return self._post(
            "/draft-services",
            data={
                "update_details": {
                    "updated_by": user
                },

                "services": service_data,
                "page_questions": page_questions or [],
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

    def find_services(self, supplier_id=None, framework=None, status=None, page=None):
        params = {
            'supplier_id': supplier_id,
            'framework': framework,
            'status': status,
            'page': page,
        }

        return self._get("/services", params=params)

    find_services_iter = make_iter_method('find_services', 'services', 'services')

    def import_service(self, service_id, service, user):
        return self._put(
            "/services/{}".format(service_id),
            data={
                "update_details": {
                    "updated_by": user
                },
                "services": service,
            })

    def update_service(self, service_id, service, user):
        return self._post(
            "/services/{}".format(service_id),
            data={
                "update_details": {
                    "updated_by": user
                },
                "services": service,
            })

    def update_service_status(self, service_id, status, user):
        return self._post(
            "/services/{}/status/{}".format(service_id, status),
            data={
                "update_details": {
                    "updated_by": user
                },
            })

    def find_frameworks(self):
        return self._get("/frameworks")

    find_frameworks_iter = make_iter_method('find_frameworks', 'frameworks', 'frameworks')

    def get_framework(self, slug):
        return self._get("/frameworks/{}".format(slug))

    def get_interested_suppliers(self, framework_slug):
        return self._get(
            "/frameworks/{}/interest".format(framework_slug)
        )

    def get_framework_stats(self, framework_slug):
        return self._get(
            "/frameworks/{}/stats".format(framework_slug))
