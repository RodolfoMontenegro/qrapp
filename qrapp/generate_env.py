from cryptography.fernet import Fernet

# Generate a new encryption key
key = Fernet.generate_key()
print("ENCRYPTION_KEY=", key.decode())

# Create a Fernet object with the key
fernet = Fernet(key)

# Set your default admin password (change this to your desired password)
default_password = "YourSecureAdminPassword"  # Replace with your desired password

# Encrypt the default admin password
encrypted_password = fernet.encrypt(default_password.encode())
print("DEFAULT_ADMIN_PASSWORD_ENC=", encrypted_password.decode())
