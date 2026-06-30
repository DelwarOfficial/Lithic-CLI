"""Production secrets management with multiple backends."""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)


class SecretBackend(ABC):
    """Abstract base for secret storage backends."""
    
    @abstractmethod
    def get_secret(self, key: str) -> str | None:
        """Retrieve a secret value by key."""
        pass
    
    @abstractmethod
    def list_secrets(self) -> list[str]:
        """List available secret keys."""
        pass


class EnvironmentSecretBackend(SecretBackend):
    """Read secrets from environment variables (default)."""
    
    def get_secret(self, key: str) -> str | None:
        return os.getenv(key)
    
    def list_secrets(self) -> list[str]:
        # Return known Lithic-related env vars
        known_keys = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY",
            "LITHIC_PROVIDER", "LITHIC_MODEL"
        ]
        return [k for k in known_keys if os.getenv(k) is not None]


class FileSecretBackend(SecretBackend):
    """Read secrets from JSON file (for development)."""
    
    def __init__(self, secrets_file: Path | str):
        self.secrets_file = Path(secrets_file)
        self._cache: dict[str, str] | None = None
    
    def _load_secrets(self) -> dict[str, str]:
        if self._cache is None:
            try:
                if self.secrets_file.exists():
                    self._cache = json.loads(self.secrets_file.read_text())
                else:
                    self._cache = {}
            except (json.JSONDecodeError, OSError):
                self._cache = {}
        return self._cache
    
    def get_secret(self, key: str) -> str | None:
        return self._load_secrets().get(key)
    
    def list_secrets(self) -> list[str]:
        return list(self._load_secrets().keys())


class VaultSecretBackend(SecretBackend):
    """Read secrets from HashiCorp Vault (production)."""
    
    def __init__(self, vault_url: str, vault_token: str, mount_path: str = "secret"):
        self.vault_url = vault_url.rstrip("/")
        self.vault_token = vault_token
        self.mount_path = mount_path
    
    def get_secret(self, key: str) -> str | None:
        try:
            import requests
            
            headers = {"X-Vault-Token": self.vault_token}
            url = f"{self.vault_url}/v1/{self.mount_path}/data/lithic/{key}"
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Vault KV v2 format
            return data.get("data", {}).get("data", {}).get("value")
            
        except Exception as e:
            # Fallback to environment if Vault fails
            _log.warning(f"Vault secret retrieval failed for key '{key}': {e}. Falling back to environment variable.")
            return os.getenv(key.upper())
    
    def list_secrets(self) -> list[str]:
        try:
            import requests
            
            headers = {"X-Vault-Token": self.vault_token}
            url = f"{self.vault_url}/v1/{self.mount_path}/metadata/lithic"
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 404:
                return []
            
            response.raise_for_status()
            data = response.json()
            
            return list(data.get("data", {}).get("keys", []))
            
        except Exception as e:
            _log.warning(f"Vault secret listing failed: {e}. Returning empty list.")
            return []


class KubernetesSecretBackend(SecretBackend):
    """Read secrets from Kubernetes secrets (production k8s)."""
    
    def __init__(self, secret_name: str = "lithic-secrets", namespace: str = "default"):
        self.secret_name = secret_name
        self.namespace = namespace
        self._secret_mount = Path("/var/secrets")
    
    def get_secret(self, key: str) -> str | None:
        # In k8s, secrets are mounted as files
        secret_file = self._secret_mount / key
        if secret_file.exists():
            try:
                return secret_file.read_text().strip()
            except OSError:
                pass
        
        # Fallback to environment
        return os.getenv(key.upper())
    
    def list_secrets(self) -> list[str]:
        if not self._secret_mount.exists():
            return []
        
        try:
            return [f.name for f in self._secret_mount.iterdir() if f.is_file()]
        except OSError:
            return []


class SecretManager:
    """Production secret management with multiple backend support."""
    
    def __init__(self, backend: SecretBackend | None = None):
        if backend is None:
            backend = self._auto_detect_backend()
        self.backend = backend
    
    def _auto_detect_backend(self) -> SecretBackend:
        """Auto-detect the appropriate backend for current environment."""
        
        # Production k8s (secrets mounted)
        if Path("/var/secrets").exists():
            return KubernetesSecretBackend()
        
        # HashiCorp Vault
        vault_url = os.getenv("VAULT_ADDR")
        vault_token = os.getenv("VAULT_TOKEN")
        if vault_url and vault_token:
            return VaultSecretBackend(vault_url, vault_token)
        
        # Development file-based secrets
        secrets_file = Path.home() / ".lithic" / "secrets.json"
        if secrets_file.exists():
            return FileSecretBackend(secrets_file)
        
        # Fallback to environment variables
        return EnvironmentSecretBackend()
    
    def get_api_key(self, provider: str) -> str | None:
        """Get API key for a specific provider."""
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY", 
            "openrouter": "OPENROUTER_API_KEY",
        }
        
        env_key = key_mapping.get(provider.lower())
        if not env_key:
            return None
        
        return self.backend.get_secret(env_key)
    
    def get_config_value(self, key: str, default: str | None = None) -> str | None:
        """Get configuration value (provider, model, etc.)."""
        value = self.backend.get_secret(key)
        return value if value is not None else default
    
    def list_available_secrets(self) -> list[str]:
        """List all available secret keys."""
        return self.backend.list_secrets()
    
    def health_check(self) -> dict[str, Any]:
        """Check if secret backend is healthy."""
        try:
            secrets = self.backend.list_secrets()
            return {
                "backend_type": type(self.backend).__name__,
                "healthy": True,
                "secret_count": len(secrets),
                "has_api_keys": any("API_KEY" in s for s in secrets),
            }
        except Exception as e:
            return {
                "backend_type": type(self.backend).__name__,
                "healthy": False,
                "error": str(e),
            }


# Global secret manager instance
_secret_manager: SecretManager | None = None


def get_secret_manager() -> SecretManager:
    """Get or create global secret manager."""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager