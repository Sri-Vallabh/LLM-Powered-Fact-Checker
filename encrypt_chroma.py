import os
from cryptography.fernet import Fernet

KEY_FILE = "app/chroma_key.key"
CHROMA_PATH = "app/chroma_db"

# Generate the key if it doesn't exist
if not os.path.exists(KEY_FILE):
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    print(f"Encryption key generated and saved as {KEY_FILE}.")
else:
    with open(KEY_FILE, "rb") as f:
        key = f.read()

def encrypt_chroma_files():
    with open(KEY_FILE, "rb") as f:
        key = f.read()
    fernet = Fernet(key)
    encrypted_count = 0
    skipped_count = 0

    for root, _, files in os.walk(CHROMA_PATH):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".enc"):
                continue
            try:
                with open(file_path, "rb") as f:
                    data = f.read()
                encrypted = fernet.encrypt(data)
                with open(f"{file_path}.enc", "wb") as f:
                    f.write(encrypted)
                os.remove(file_path)
                print(f"Encrypted and removed: {file_path}")
                encrypted_count += 1
            except PermissionError:
                print(f"Skipped (file in use): {file_path}")
                skipped_count += 1
            except Exception as e:
                print(f"Error encrypting {file_path}: {e}")
                skipped_count += 1

    print(f"\nEncryption complete. {encrypted_count} files encrypted, {skipped_count} files skipped.")

if __name__ == "__main__":
    encrypt_chroma_files()
