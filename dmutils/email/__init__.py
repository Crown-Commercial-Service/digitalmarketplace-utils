"""Allow accessing send email from email. Backwards compatibility."""
from dmutils.email.dm_mandrill import (
    send_email, generate_token, decode_invitation_token, decode_password_reset_token
)
