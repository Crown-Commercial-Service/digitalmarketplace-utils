def user_has_role(user, role):
    try:
        return user['users']['role'] == role
    except (KeyError, TypeError):
        return False


class User():
    def __init__(self, user_id, email_address, supplier_id, supplier_name,
                 locked, active):
        self.id = user_id
        self.email_address = email_address
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.locked = locked
        self.active = active

    def is_authenticated(self):
        return self.is_active()

    def is_active(self):
        return self.active and not self.locked

    def is_locked(self):
        return self.locked

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def serialize(self):
        return {
            'id': self.id,
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
            locked=user['locked'],
            active=user['active']
        )

    @staticmethod
    def load_user(data_api_client, user_id):
        """Load a user from the API and hydrate the User model"""
        user_json = data_api_client.get_user(user_id=int(user_id))

        if user_json:
            user = User.from_json(user_json)
            if user.is_active():
                return user
