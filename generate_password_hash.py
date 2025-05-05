import hashlib
import getpass

def generate_password_hash(password):
    """Generate a SHA-256 hash from a password string"""
    return hashlib.sha256(password.encode()).hexdigest()

if __name__ == "__main__":
    print("Password Hash Generator for Fixed Deposit Calculator")
    print("----------------------------------------")

    # Get password from user (hidden input)
    password = getpass.getpass("Enter the password you want to use: ")

    # Generate and display the hash
    password_hash = generate_password_hash(password)
    print("\nAdd the following to your .streamlit/secrets.toml file:")
    print("\n[authentication]")
    print(f'password_hash = "{password_hash}"\n')
