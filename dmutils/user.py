def user_has_role(user, role):
    try:
        return user['users']['role'] == role
    except (KeyError, TypeError):
        return False


class User():
    def __init__(self, user_id, email_address, supplier_id, supplier_name,
                 locked, active, name):
        self.id = user_id
        self.email_address = email_address
        self.name = name
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.locked = locked
        self.active = active

    @staticmethod
    def is_authenticated():
        return True

    def is_active(self):
        return self.active

    def is_locked(self):
        return self.locked

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'emailAddress': self.email_address,
            'supplierId': self.supplier_id,
            'supplierName': self.supplier_name,
            'locked': self.locked,
        }

    @staticmethod
    def from_json(user_json):
        user = user_json["users"]
        supplier_id = None
        supplier_name = None
        if "supplier" in user:
            supplier_id = user["supplier"]["supplierId"]
            supplier_name = user["supplier"]["name"]
        return User(
            user_id=user["id"],
            email_address=user['emailAddress'],
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            locked=user.get('locked', False),
            active=user.get('active', True),
            name=user['name']
        )
