import os
from cryptography.fernet import Fernet

KEY_FILE = "app/chroma_key.key"
CHROMA_PATH = "app/chroma_db"

def decrypt_chroma_files():
    # Load key
    with open(KEY_FILE, "rb") as f:
        key = f.read()
    fernet = Fernet(key)
    
    # Decrypt all .enc files
    for root, _, files in os.walk(CHROMA_PATH):
        for file in files:
            if not file.endswith(".enc"):
                continue
                
            encrypted_path = os.path.join(root, file)
            original_path = encrypted_path[:-4]  # Remove .enc
            
            try:
                with open(encrypted_path, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = fernet.decrypt(encrypted_data)
                with open(original_path, "wb") as f:
                    f.write(decrypted_data)
                os.remove(encrypted_path)
                print(f"Decrypted: {original_path}")
            except Exception as e:
                print(f"Error decrypting {encrypted_path}: {e}")

if __name__ == "__main__":
    decrypt_chroma_files()
    print("Decryption complete. ChromaDB ready for use.")
