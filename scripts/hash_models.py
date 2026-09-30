import hashlib
import json
from pathlib import Path

def hash_models(models_dir: str = "models", lockfile: str = "models.lock") -> None:
    models_path = Path(models_dir)
    if not models_path.exists():
        print(f"Error: Directory '{models_dir}' does not exist.")
        return

    print(f"Scanning '{models_dir}' for models...")
    manifest = []
    
    for file_path in models_path.iterdir():
        if file_path.is_file() and file_path.name not in (".gitkeep", "README.md"):
            print(f"Hashing {file_path.name}... ", end="", flush=True)
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024 * 4), b""):  # 4MB chunks
                    hasher.update(chunk)
            
            sha256 = hasher.hexdigest()
            print("Done!")
            
            manifest.append({
                "name": file_path.name,
                "sha256": sha256
            })
            
    with open(lockfile, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"\nSuccessfully updated {lockfile} with {len(manifest)} models.")

if __name__ == "__main__":
    hash_models()
