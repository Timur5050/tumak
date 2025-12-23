import hashlib
import json
from cryptography.fernet import Fernet

def setup_project():
    print("--- Setup: Generating security keys and Admin account ---")
    
    # Створюємо ключ
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)
    
    # Створюємо адміна
    admin_login = input("Create Admin Username: ")
    admin_password = input("Create Admin Password: ")
    pw_hash = hashlib.sha256(admin_password.encode()).hexdigest()
    
    users_data = {
        admin_login: {"password_hash": pw_hash, "role": "admin"}
    }
    
    with open("users.json", "w") as f:
        json.dump(users_data, f, indent=4)
    
    print("\n[DONE] 'secret.key' and 'users.json' created successfully!")

if __name__ == "__main__":
    setup_project()