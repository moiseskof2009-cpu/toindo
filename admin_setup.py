from getpass import getpass
import secrets
from werkzeug.security import generate_password_hash
from cryptography.fernet import Fernet

username = input("Admin username: ").strip()
password = getpass("Create a strong admin password (14+ characters): ")
confirm = getpass("Repeat password: ")
if not username or len(password) < 14 or password != confirm:
    raise SystemExit("Invalid username/password.")
print("ADMIN_USERNAME=" + username)
print("ADMIN_PASSWORD_HASH=" + generate_password_hash(password))
print("ADMIN_SESSION_SECRET=" + secrets.token_urlsafe(48))
print("PUBLIC_SESSION_SECRET=" + secrets.token_urlsafe(48))
print("PII_ENCRYPTION_KEY=" + Fernet.generate_key().decode())
