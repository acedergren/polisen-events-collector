#!/usr/bin/env python3
"""
OCI Vault Secrets Manager
Retrieves secrets from OCI Vault instead of local config files
"""

import base64
import logging
import os
from typing import Dict, Optional

import oci

logger = logging.getLogger(__name__)

# Vault Configuration - DO NOT hardcode vault names in public repos!
VAULT_NAME = os.getenv("OCI_VAULT_NAME")  # Required: Set via environment variable
VAULT_REGION = os.getenv("OCI_VAULT_REGION", "eu-frankfurt-1")  # Default to FRA
VAULT_COMPARTMENT_ID = os.getenv("OCI_VAULT_COMPARTMENT_ID")  # Required


class SecretsManager:
    """Manages secrets retrieval from OCI Vault"""

    def __init__(self, use_instance_principal: bool = False):
        """
        Initialize secrets manager with OCI authentication

        Args:
            use_instance_principal: If True, use instance principal auth (for OCI Compute).
                                   If False, use minimal config file (for local dev).
        """
        try:
            if use_instance_principal:
                logger.info("Using instance principal authentication")
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                self.secrets_client = oci.secrets.SecretsClient(
                    config={},
                    signer=signer
                )
                self.vaults_client = oci.vault.VaultsClient(
                    config={},
                    signer=signer
                )
            else:
                logger.info("Using config file authentication for vault access")
                # Minimal config - only for accessing vault
                # This file should only contain vault access credentials
                config = oci.config.from_file(profile_name=os.getenv("OCI_PROFILE", "DEFAULT"))
                config["region"] = VAULT_REGION
                self.secrets_client = oci.secrets.SecretsClient(config)
                self.vaults_client = oci.vault.VaultsClient(config)

            logger.info(f"Secrets manager initialized (region: {VAULT_REGION})")

        except Exception as e:
            logger.error(f"Failed to initialize secrets manager: {e}")
            raise

    def get_vault_id(self) -> str:
        """Get the OCID of the vault by name"""
        if not VAULT_NAME:
            raise ValueError(
                "OCI_VAULT_NAME environment variable is required but not set. "
                "Please set it to your vault name (e.g., 'my-vault')"
            )
        if not VAULT_COMPARTMENT_ID:
            raise ValueError(
                "OCI_VAULT_COMPARTMENT_ID environment variable is required but not set. "
                "Please set it to your vault's compartment OCID"
            )
        
        try:
            vaults = self.vaults_client.list_vaults(
                compartment_id=VAULT_COMPARTMENT_ID
            ).data

            for vault in vaults:
                if vault.display_name == VAULT_NAME and vault.lifecycle_state == "ACTIVE":
                    logger.info(f"Found vault: {VAULT_NAME} ({vault.id})")
                    return vault.id

            raise ValueError(f"Vault '{VAULT_NAME}' not found or not active")

        except Exception as e:
            logger.error(f"Failed to get vault ID: {e}")
            raise

    def get_secret(self, secret_name: str) -> str:
        """
        Retrieve a secret value from OCI Vault

        Args:
            secret_name: Name of the secret in the vault

        Returns:
            Decoded secret value as string
        """
        try:
            # List secrets in the vault
            vault_id = self.get_vault_id()

            # Find the secret by name
            secrets = self.vaults_client.list_secrets(
                compartment_id=VAULT_COMPARTMENT_ID,
                vault_id=vault_id,
                name=secret_name
            ).data

            if not secrets:
                raise ValueError(f"Secret '{secret_name}' not found in vault")

            secret = secrets[0]

            if secret.lifecycle_state != "ACTIVE":
                raise ValueError(f"Secret '{secret_name}' is not active")

            # Get the secret bundle (actual secret content)
            secret_bundle = self.secrets_client.get_secret_bundle(secret.id).data

            # Decode the secret content
            secret_content_base64 = secret_bundle.secret_bundle_content.content
            secret_value = base64.b64decode(secret_content_base64).decode('utf-8')

            logger.info(f"Retrieved secret: {secret_name}")
            return secret_value

        except Exception as e:
            logger.error(f"Failed to retrieve secret '{secret_name}': {e}")
            raise

    def get_oci_config(self) -> Dict:
        """
        Build OCI config from vault secrets

        Expected secrets in vault:
        - oci-user-ocid
        - oci-tenancy-ocid
        - oci-fingerprint
        - oci-private-key (PEM format)
        - oci-region (optional, defaults to eu-stockholm-1)

        Returns:
            OCI config dictionary
        """
        try:
            logger.info("Building OCI config from vault secrets")

            # Retrieve secrets
            user_ocid = self.get_secret("oci-user-ocid")
            tenancy_ocid = self.get_secret("oci-tenancy-ocid")
            fingerprint = self.get_secret("oci-fingerprint")
            private_key = self.get_secret("oci-private-key")
            region = self.get_secret_optional("oci-region", default="eu-stockholm-1")
            
            # Security: Validate OCID format
            if not user_ocid.startswith("ocid1.user."):
                raise ValueError("Invalid user OCID format from vault")
            if not tenancy_ocid.startswith("ocid1.tenancy."):
                raise ValueError("Invalid tenancy OCID format from vault")
            
            # Security: Validate fingerprint format (aa:bb:cc:... format)
            import re
            if not re.match(r'^([a-fA-F0-9]{2}:){15}[a-fA-F0-9]{2}$', fingerprint):
                raise ValueError("Invalid fingerprint format from vault")
            
            # Security: Validate private key format (PEM)
            if not private_key.startswith("-----BEGIN") or "PRIVATE KEY-----" not in private_key:
                raise ValueError("Invalid private key format from vault (must be PEM format)")

            config = {
                "user": user_ocid,
                "tenancy": tenancy_ocid,
                "fingerprint": fingerprint,
                "key_content": private_key,
                "region": region
            }

            logger.info("Successfully built OCI config from vault")
            return config

        except Exception as e:
            logger.error(f"Failed to build OCI config from vault: {e}")
            raise

    def get_secret_optional(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret, returning default if not found"""
        try:
            return self.get_secret(secret_name)
        except Exception:
            logger.info(f"Secret '{secret_name}' not found, using default: {default}")
            return default


def get_oci_config_from_vault() -> Dict:
    """
    Convenience function to get OCI config from vault

    Auto-detects whether to use instance principal or config file.
    Set environment variable USE_INSTANCE_PRINCIPAL=true for compute instances.

    Returns:
        OCI config dictionary
    """
    use_instance_principal = os.getenv("USE_INSTANCE_PRINCIPAL", "false").lower() == "true"

    secrets_mgr = SecretsManager(use_instance_principal=use_instance_principal)
    return secrets_mgr.get_oci_config()
