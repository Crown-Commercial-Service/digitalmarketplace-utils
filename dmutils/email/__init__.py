"""Allow accessing send email from email. Backwards compatibility."""
from dmutils.email.dm_mandrill import send_email
from dmutils.email.tokens import (
    generate_token, decode_invitation_token, decode_password_reset_token
)

from .exceptions import EmailError
from .dm_notify import DMNotifyClient
from .create_user_email import CreateUserEmail
