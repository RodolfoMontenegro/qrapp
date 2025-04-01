from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env

# Retrieve the encryption key and encrypted password from the environment
encryption_key = os.getenv("ENCRYPTION_KEY").strip()
encrypted_password = os.getenv("DEFAULT_ADMIN_PASSWORD_ENC").strip()

if not encryption_key or not encrypted_password:
    raise Exception("Missing ENCRYPTION_KEY or DEFAULT_ADMIN_PASSWORD_ENC in .env file!")

# Initialize Fernet with the key
fernet = Fernet(encryption_key)

# Decrypt the password
decrypted_password = fernet.decrypt(encrypted_password.encode()).decode()
print("The default admin password is:", decrypted_password)
