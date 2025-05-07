import hashlib
import getpass
import base64
from cryptography.fernet import Fernet

def generate_password_hash(password):
    """Generate a SHA-256 hash from a password string"""
    return hashlib.sha256(password.encode()).hexdigest()

def encrypt_hash(hash_value, key=None):
    """Encrypt a hash value using Fernet"""
    if key is None:
        # Generate a key if not provided
        key = Fernet.generate_key()
    
    f = Fernet(key)
    encrypted_hash = f.encrypt(hash_value.encode())
    return encrypted_hash, key

if __name__ == "__main__":
    print("Password Hash Generator for Fixed Deposit Calculator")
    print("----------------------------------------")

    # Get password from user (hidden input)
    password = getpass.getpass("Enter the password you want to use: ")

    # Generate the hash
    password_hash = generate_password_hash(password)
    
    # Ask if user wants to use an existing key or generate a new one
    use_existing = input("Do you have an existing fernet_key in your secrets? (y/n): ").lower().strip() == 'y'
    
    if use_existing:
        key_str = getpass.getpass("Enter your existing fernet_key: ")
        key = key_str.encode()
    else:
        key = Fernet.generate_key()
        print("\nA new encryption key has been generated.")
    
    # Encrypt the hash
    encrypted_hash, used_key = encrypt_hash(password_hash, key)
    
    # Display results and instructions
    print("\nAdd the following to your .streamlit/secrets.toml file:")
    
    if not use_existing:
        print("\n[cryptography]")
        print(f'fernet_key = "{used_key.decode()}"')
    
    print("\n[authentication]")
    print(f'encrypted_password_hash = "{encrypted_hash.decode()}"')
    print(f'# For reference only (not needed in production): password_hash = "{password_hash}"')
