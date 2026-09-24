import json
import hashlib
from pathlib import Path

class ModelVerificationError(Exception):
    pass

class ModelLoader:
    def __init__(self, lockfile_path: str = "models.lock") -> None:
        self.lockfile_path = Path(lockfile_path)
        self.manifest = self._load_manifest()
        
    def _load_manifest(self) -> dict[str, str]:
        if not self.lockfile_path.exists():
            return {}
        with open(self.lockfile_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {item["name"]: item["sha256"] for item in data}
            
    def verify_and_get_path(self, model_dir: Path, model_name: str) -> Path:
        model_path = model_dir / model_name
        if not model_path.exists():
            raise FileNotFoundError(f"Model {model_name} not found")
            
        expected_hash = self.manifest.get(model_name)
        if not expected_hash:
            raise ModelVerificationError(f"Model {model_name} is not in models.lock")
            
        # Ban pickle explicitly by extension
        if model_name.endswith(".pkl") or model_name.endswith(".pt") or model_name.endswith(".bin"):
            raise ModelVerificationError(f"Model {model_name} uses a banned pickle format")
            
        hasher = hashlib.sha256()
        with open(model_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
                
        actual_hash = hasher.hexdigest()
        if actual_hash != expected_hash:
            raise ModelVerificationError(f"Hash mismatch for {model_name}")
            
        return model_path
