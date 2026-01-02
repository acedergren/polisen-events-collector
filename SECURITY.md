# Security Guidelines

## OCI Vault Integration

This project uses **OCI Vault** to securely manage credentials instead of storing them in local config files. This prevents accidental exposure of secrets in git repositories.

### Vault Configuration

All vault details are configured via environment variables (never hardcoded in public repos):

- **Vault Name**: Set via `OCI_VAULT_NAME` environment variable (e.g., `export OCI_VAULT_NAME="my-vault"`)
- **Region**: Set via `OCI_VAULT_REGION` environment variable (defaults to `eu-frankfurt-1`)
- **Compartment**: Set via `OCI_VAULT_COMPARTMENT_ID` environment variable

### Required Secrets in Vault

Create the following secrets in your OCI Vault:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `oci-user-ocid` | User OCID for API authentication | `ocid1.user.oc1..aaaa...` |
| `oci-tenancy-ocid` | Tenancy OCID | `ocid1.tenancy.oc1..aaaa...` |
| `oci-fingerprint` | API key fingerprint | `aa:bb:cc:dd:ee:ff:...` |
| `oci-private-key` | Private key in PEM format | `-----BEGIN RSA PRIVATE KEY-----\n...` |
| `oci-region` | (Optional) OCI region | `eu-stockholm-1` |

### Setting Up Secrets in OCI Vault

#### Using OCI Console

1. Navigate to **Identity & Security** → **Vault**
2. Select vault `AC-vault` in `eu-frankfurt-1` region
3. Click **Secrets** → **Create Secret**
4. For each secret:
   - **Name**: Use exact names from table above
   - **Encryption Key**: Select your vault's master encryption key
   - **Secret Contents**: Paste the value
   - Click **Create Secret**

#### Using OCI CLI

```bash
# Set your vault and compartment IDs
VAULT_ID="ocid1.vault.oc1.eu-frankfurt-1.xxxxxxx"
COMPARTMENT_ID="ocid1.compartment.oc1..xxxxxxx"
KEY_ID="ocid1.key.oc1.eu-frankfurt-1.xxxxxxx"

# Create secrets
oci vault secret create-base64 \
    --compartment-id "$COMPARTMENT_ID" \
    --vault-id "$VAULT_ID" \
    --key-id "$KEY_ID" \
    --secret-name "oci-user-ocid" \
    --secret-content-content "$(echo -n 'ocid1.user.oc1..aaaa...' | base64)"

oci vault secret create-base64 \
    --compartment-id "$COMPARTMENT_ID" \
    --vault-id "$VAULT_ID" \
    --key-id "$KEY_ID" \
    --secret-name "oci-tenancy-ocid" \
    --secret-content-content "$(echo -n 'ocid1.tenancy.oc1..aaaa...' | base64)"

oci vault secret create-base64 \
    --compartment-id "$COMPARTMENT_ID" \
    --vault-id "$VAULT_ID" \
    --key-id "$KEY_ID" \
    --secret-name "oci-fingerprint" \
    --secret-content-content "$(echo -n 'aa:bb:cc:...' | base64)"

# For private key (multi-line)
oci vault secret create-base64 \
    --compartment-id "$COMPARTMENT_ID" \
    --vault-id "$VAULT_ID" \
    --key-id "$KEY_ID" \
    --secret-name "oci-private-key" \
    --secret-content-content "$(cat ~/.oci/oci_api_key.pem | base64 -w 0)"
```

### Authentication Methods

The application supports two authentication methods:

#### 1. Instance Principal (Recommended for Production)

When running on OCI Compute instances:

```bash
# Set environment variable
export USE_INSTANCE_PRINCIPAL=true

# Run the collector
python3 collect_events.py
```

**Setup**: Configure Dynamic Group and IAM policy to allow instance to read from vault.

#### 2. Config File (Local Development Only)

For local testing, use a minimal config file that **only contains vault access credentials**:

```bash
# ~/.oci/config
[DEFAULT]
user=ocid1.user.oc1..aaaa...
fingerprint=aa:bb:cc:...
tenancy=ocid1.tenancy.oc1..aaaa...
region=eu-frankfurt-1
key_file=~/.oci/vault_access_key.pem
```

⚠️ **Important**: This config file should ONLY have permissions to read from the vault, not full OCI access.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_INSTANCE_PRINCIPAL` | Use instance principal auth | `false` |
| `USE_VAULT` | Load credentials from vault | `true` |
| `OCI_VAULT_COMPARTMENT_ID` | Vault compartment OCID | (hardcoded) |
| `OCI_PROFILE` | OCI config profile name | `DEFAULT` |

### Testing Vault Integration

```bash
# Test vault access
python3 -c "from secrets_manager import SecretsManager; sm = SecretsManager(); print(sm.get_vault_id())"

# Test full config retrieval
python3 -c "from secrets_manager import get_oci_config_from_vault; print('Success!')"

# Test collector with vault (dry run)
USE_VAULT=true python3 collect_events.py
```

### Security Best Practices

1. ✅ **Never commit credentials** to git
2. ✅ **Use vault for all secrets** in production
3. ✅ **Use instance principal** when running on OCI
4. ✅ **Rotate secrets regularly** in the vault
5. ✅ **Audit vault access** using OCI audit logs
6. ✅ **Limit vault access** using IAM policies
7. ✅ **Encrypt vault** using customer-managed keys

### .gitignore Protection

The `.gitignore` file is configured to block common secret file patterns:

- `*.pem`, `*.key` - Private keys
- `.oci/`, `config` - OCI config directories and files
- `*secret*`, `*credential*` - Any files with these keywords
- `.env*` - Environment files

### Incident Response

If credentials are accidentally committed:

1. **Immediately rotate** all exposed credentials in OCI Console
2. **Delete secrets** from vault and create new ones
3. **Revoke API keys** in OCI IAM
4. **Review audit logs** for unauthorized access
5. **Update git history** to remove sensitive data (contact maintainer)

### IAM Policy for Vault Access

Grant the application permission to read secrets:

```
Allow dynamic-group polisen-collector-instances to read secret-bundles in compartment id <compartment-ocid> where target.vault.id = '<vault-ocid>'
Allow dynamic-group polisen-collector-instances to read secrets in compartment id <compartment-ocid> where target.vault.id = '<vault-ocid>'
Allow dynamic-group polisen-collector-instances to read vaults in compartment id <compartment-ocid> where target.vault.id = '<vault-ocid>'
```

## Reporting Security Issues

<<<<<<< HEAD
If you discover a security vulnerability, please email alex@solutionsedge.io. Do not open a public issue.

## Security Best Practices for Deployment

### Production Deployment

1. **Always use OCI Vault** for credential management
2. **Enable instance principal authentication** when running on OCI Compute
3. **Use least-privilege IAM policies** - grant only necessary permissions
4. **Enable audit logging** in OCI to track all API access
5. **Rotate credentials regularly** (at least every 90 days)
6. **Monitor logs** for suspicious activity
7. **Keep dependencies updated** - regularly check for security patches
8. **Use HTTPS only** - never disable SSL/TLS verification

### File Permissions

Ensure proper file permissions are set:

```bash
# Configuration files (readable only by owner)
chmod 600 .env

# Log directory (owner read/write, group read)
chmod 750 logs/
chmod 640 logs/*.log

# Scripts (executable by owner only)
chmod 700 collect_events.py
chmod 700 secrets_manager.py
```

### Network Security

- **Firewall Rules**: Only allow outbound HTTPS (443) to polisen.se and OCI endpoints
- **No Inbound Connections**: This application only makes outbound requests
- **VPN/Bastion**: Access production systems through secure channels only

### Monitoring and Alerting

Set up alerts for:
- Failed authentication attempts
- Unusual API access patterns
- High error rates
- Disk space exhaustion
- Log file tampering
=======
If you discover a security vulnerability, please email alex@solutionsedge.io. Do not open a public issue.
>>>>>>> main
