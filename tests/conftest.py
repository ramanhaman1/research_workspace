
import os
import secrets

# Temporary credentials for automated tests
os.environ["RW_JWT_SECRET"] = secrets.token_urlsafe(48)
os.environ["RW_ALI_PASSWORD"] = secrets.token_urlsafe(18)
os.environ["RW_RAMAN_PASSWORD"] = secrets.token_urlsafe(18)
os.environ["RW_ADMIN_PASSWORD"] = secrets.token_urlsafe(18)

