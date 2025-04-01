from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Get the SECRET_KEY from the environment
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise Exception("SECRET_KEY not found in environment variables!")

# Create a Fernet object using the key
fernet = Fernet(secret_key)

# Example: Encrypt a message
message = "This is a secret message."
encrypted_message = fernet.encrypt(message.encode())
print("Encrypted:", encrypted_message)

# Decrypt the message
decrypted_message = fernet.decrypt(encrypted_message).decode()
print("Decrypted:", decrypted_message)
