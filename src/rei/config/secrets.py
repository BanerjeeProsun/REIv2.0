import keyring

class SecretManager:
    SERVICE_NAME = "ReiAssistant"
    
    def __init__(self) -> None:
        pass
        
    def get_secret(self, key: str) -> str | None:
        return keyring.get_password(self.SERVICE_NAME, key)
        
    def set_secret(self, key: str, value: str) -> None:
        keyring.set_password(self.SERVICE_NAME, key, value)
        
    def delete_secret(self, key: str) -> None:
        try:
            keyring.delete_password(self.SERVICE_NAME, key)
        except keyring.errors.PasswordDeleteError:
            pass
