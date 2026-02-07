from app.settings import get_settings
from app.security.auth import verify_password
import bcrypt

s = get_settings()
print(f"Loaded Username: {s.admin_username}")
print(f"Loaded Hash: {s.admin_password_hash}")
print(f"Verify 'admin' vs Hash: {verify_password('admin', s.admin_password_hash)}")

# Direct check
try:
    print(f"Direct BCrypt Check: {bcrypt.checkpw(b'admin', s.admin_password_hash.encode())}")
except Exception as e:
    print(f"BCrypt Error: {e}")
