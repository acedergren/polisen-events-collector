# Infrastructure as Code (Terraform) Templates
**Polisen Events Collector - OCI Resource Automation**

---

## Overview

This guide provides production-ready Terraform templates for automating OCI resource provisioning. Move from manual console operations to declarative infrastructure management.

**Benefits:**
- Reproducible infrastructure
- Version-controlled configurations
- Automated state tracking
- Consistent environments
- Easy disaster recovery

---

## Project Structure

```
terraform/
├── main.tf                 # Root module configuration
├── variables.tf           # Input variables
├── outputs.tf             # Output values
├── terraform.tfvars      # Variable values (gitignored)
├── versions.tf            # Provider versions
│
├── modules/
│   ├── vault/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   │
│   ├── object_storage/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   │
│   └── iam/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── README.md
│
├── environments/
│   ├── development/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   │
│   ├── staging/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   │
│   └── production/
│       ├── main.tf
│       ├── terraform.tfvars
│       └── backend.tf
│
└── .gitignore            # Ignore state files
```

---

## 1. Versions Configuration

### File: `terraform/versions.tf`

```hcl
terraform {
  required_version = ">= 1.5"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }

  # Backend configuration for remote state management
  # Uncomment after creating backend bucket
  # backend "s3" {
  #   bucket         = "polisen-tf-state"
  #   key            = "terraform.tfstate"
  #   region         = "eu-stockholm-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-lock"
  # }
}

provider "oci" {
  tenancy_ocid = var.tenancy_ocid
  region       = var.oci_region

  # If using instance principal (recommended for production)
  # auth = "InstancePrincipal"
}

# Terraform Cloud configuration (optional)
# terraform {
#   cloud {
#     organization = "your-org"
#
#     workspaces {
#       name = "${var.environment}-polisen"
#     }
#   }
# }
```

---

## 2. Root Module Configuration

### File: `terraform/variables.tf`

```hcl
variable "tenancy_ocid" {
  description = "The OCID of the tenancy"
  type        = string
  sensitive   = true
}

variable "user_ocid" {
  description = "The OCID of the user"
  type        = string
  sensitive   = true
}

variable "fingerprint" {
  description = "The fingerprint of the API key"
  type        = string
  sensitive   = true
}

variable "private_key_path" {
  description = "Path to the private key file"
  type        = string
  sensitive   = true
}

variable "oci_region" {
  description = "OCI region for primary resources"
  type        = string
  default     = "eu-stockholm-1"
}

variable "vault_region" {
  description = "OCI region for vault (should be different from primary)"
  type        = string
  default     = "eu-frankfurt-1"
}

variable "compartment_ocid" {
  description = "The OCID of the compartment"
  type        = string
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "polisen-collector"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "polisen-collector"
    ManagedBy   = "Terraform"
    CreatedDate = "2026-01-02"
  }
}

# Vault Configuration
variable "vault_display_name" {
  description = "Display name for the vault"
  type        = string
  default     = "polisen-collector-vault"
}

variable "enable_vault_deletion" {
  description = "Allow vault deletion (WARNING: destructive)"
  type        = bool
  default     = false
}

# Object Storage Configuration
variable "bucket_name" {
  description = "Name of the object storage bucket"
  type        = string
  default     = "polisen-events-collector"
}

variable "enable_bucket_versioning" {
  description = "Enable versioning on the bucket"
  type        = bool
  default     = true
}

variable "enable_bucket_encryption" {
  description = "Enable server-side encryption"
  type        = bool
  default     = true
}

variable "bucket_retention_days" {
  description = "Object retention period in days (0 = no retention)"
  type        = number
  default     = 0
}

variable "enable_cross_region_replication" {
  description = "Enable cross-region replication for DR"
  type        = bool
  default     = var.environment == "production" ? true : false
}

variable "dr_region" {
  description = "DR region for cross-region replication"
  type        = string
  default     = "eu-central-1"
}

# IAM Configuration
variable "instance_principals" {
  description = "List of instance principal display names"
  type        = list(string)
  default     = ["polisen-collector-instances"]
}
```

### File: `terraform/outputs.tf`

```hcl
output "vault_id" {
  description = "OCID of the created vault"
  value       = module.vault.vault_id
}

output "vault_url" {
  description = "URL to access the vault"
  value       = module.vault.vault_url
}

output "bucket_name" {
  description = "Name of the created bucket"
  value       = module.object_storage.bucket_name
}

output "bucket_namespace" {
  description = "Namespace of the bucket"
  value       = module.object_storage.namespace
}

output "dynamic_group_id" {
  description = "OCID of the dynamic group"
  value       = module.iam.dynamic_group_id
}

output "policy_ids" {
  description = "OCIDs of created IAM policies"
  value       = module.iam.policy_ids
}

output "environment_info" {
  description = "Environment information"
  value = {
    environment        = var.environment
    region            = var.oci_region
    vault_region      = var.vault_region
    compartment_ocid  = var.compartment_ocid
  }
}
```

### File: `terraform/main.tf`

```hcl
# Get current user
data "oci_identity_user" "current" {
  user_id = var.user_ocid
}

# Get namespace
data "oci_objectstorage_namespace" "current" {
  compartment_id = var.compartment_ocid
}

# Vault Module
module "vault" {
  source = "./modules/vault"

  compartment_ocid           = var.compartment_ocid
  vault_display_name        = "${var.project_name}-vault-${var.environment}"
  vault_region              = var.vault_region
  enable_deletion           = var.enable_vault_deletion
  enable_automatic_key_rotation = var.environment == "production" ? true : false

  tags = merge(
    var.tags,
    {
      Environment = var.environment
      Component   = "Vault"
    }
  )
}

# Object Storage Module
module "object_storage" {
  source = "./modules/object_storage"

  compartment_ocid               = var.compartment_ocid
  namespace                      = data.oci_objectstorage_namespace.current.namespace
  bucket_name                    = var.bucket_name
  region                         = var.oci_region
  enable_versioning              = var.enable_bucket_versioning
  enable_encryption              = var.enable_bucket_encryption
  retention_days                 = var.bucket_retention_days
  enable_cross_region_replication = var.enable_cross_region_replication
  dr_region                      = var.dr_region
  environment                    = var.environment

  tags = merge(
    var.tags,
    {
      Environment = var.environment
      Component   = "ObjectStorage"
    }
  )

  depends_on = [module.vault]
}

# IAM Module
module "iam" {
  source = "./modules/iam"

  compartment_ocid   = var.compartment_ocid
  instance_principals = var.instance_principals
  vault_ocid         = module.vault.vault_id
  environment        = var.environment

  tags = merge(
    var.tags,
    {
      Environment = var.environment
      Component   = "IAM"
    }
  )

  depends_on = [module.vault, module.object_storage]
}
```

---

## 3. Vault Module

### File: `terraform/modules/vault/main.tf`

```hcl
# Create Vault
resource "oci_vault_vault" "polisen_vault" {
  compartment_id = var.compartment_ocid
  display_name   = var.vault_display_name
  vault_type     = "DEFAULT"

  tags = merge(
    var.tags,
    {
      Name = var.vault_display_name
    }
  )

  lifecycle {
    prevent_destroy = true
  }
}

# Create Master Encryption Key
resource "oci_kms_key" "vault_key" {
  compartment_id      = var.compartment_ocid
  display_name        = "${var.vault_display_name}-key"
  key_shape {
    algorithm = "AES"
    length    = 256
  }

  management_placement_config {
    placement_region = var.vault_region
  }

  # Auto-rotation policy
  auto_key_rotation_details {
    auto_rotate_enabled   = var.enable_automatic_key_rotation
    rotation_period_in_days = var.enable_automatic_key_rotation ? 365 : null
  }

  tags = var.tags

  lifecycle {
    prevent_destroy = true
  }
}

# Secret: OCI User OCID (placeholder)
resource "oci_vault_secret" "oci_user_ocid" {
  compartment_id   = var.compartment_ocid
  vault_id         = oci_vault_vault.polisen_vault.id
  key_id           = oci_kms_key.vault_key.id
  secret_name      = "oci-user-ocid"
  secret_content {
    content_type = "text/plain"
    content      = "ocid1.user.oc1.${var.vault_region}.placeholder"  # Update with actual value
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [secret_content]  # Don't recreate on content changes
  }
}

# Secret: OCI Tenancy OCID (placeholder)
resource "oci_vault_secret" "oci_tenancy_ocid" {
  compartment_id   = var.compartment_ocid
  vault_id         = oci_vault_vault.polisen_vault.id
  key_id           = oci_kms_key.vault_key.id
  secret_name      = "oci-tenancy-ocid"
  secret_content {
    content_type = "text/plain"
    content      = "ocid1.tenancy.oc1.${var.vault_region}.placeholder"  # Update with actual value
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [secret_content]
  }
}

# Secret: OCI Fingerprint (placeholder)
resource "oci_vault_secret" "oci_fingerprint" {
  compartment_id   = var.compartment_ocid
  vault_id         = oci_vault_vault.polisen_vault.id
  key_id           = oci_kms_key.vault_key.id
  secret_name      = "oci-fingerprint"
  secret_content {
    content_type = "text/plain"
    content      = "aa:bb:cc:dd:ee:ff:placeholder"  # Update with actual value
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [secret_content]
  }
}

# Secret: OCI Private Key (placeholder)
resource "oci_vault_secret" "oci_private_key" {
  compartment_id   = var.compartment_ocid
  vault_id         = oci_vault_vault.polisen_vault.id
  key_id           = oci_kms_key.vault_key.id
  secret_name      = "oci-private-key"
  secret_content {
    content_type = "text/plain"
    content      = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpQIBAAKCAQEA...placeholder\n-----END RSA PRIVATE KEY-----"  # Update with actual value
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [secret_content]
  }
}

# Enable vault deletion policy (only for non-production)
resource "oci_vault_vault" "vault_deletion_policy" {
  count = var.enable_deletion ? 1 : 0
  depends_on = [oci_vault_vault.polisen_vault]

  # Documented for awareness; actual deletion requires console override
}
```

### File: `terraform/modules/vault/variables.tf`

```hcl
variable "compartment_ocid" {
  description = "Compartment OCID"
  type        = string
}

variable "vault_display_name" {
  description = "Display name for the vault"
  type        = string
}

variable "vault_region" {
  description = "Region for vault placement"
  type        = string
  default     = "eu-frankfurt-1"
}

variable "enable_deletion" {
  description = "Allow vault deletion (DANGEROUS!)"
  type        = bool
  default     = false
}

variable "enable_automatic_key_rotation" {
  description = "Enable automatic key rotation"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
```

### File: `terraform/modules/vault/outputs.tf`

```hcl
output "vault_id" {
  description = "OCID of the vault"
  value       = oci_vault_vault.polisen_vault.id
}

output "vault_url" {
  description = "URL of the vault"
  value       = "https://vault.${var.vault_region}.oci.oraclecloud.com"
}

output "key_id" {
  description = "OCID of the master encryption key"
  value       = oci_kms_key.vault_key.id
}

output "secrets" {
  description = "Secret OCIDs"
  value = {
    user_ocid    = oci_vault_secret.oci_user_ocid.id
    tenancy_ocid = oci_vault_secret.oci_tenancy_ocid.id
    fingerprint  = oci_vault_secret.oci_fingerprint.id
    private_key  = oci_vault_secret.oci_private_key.id
  }
}
```

---

## 4. Object Storage Module

### File: `terraform/modules/object_storage/main.tf`

```hcl
# Create Object Storage Bucket
resource "oci_objectstorage_bucket" "polisen_bucket" {
  compartment_id = var.compartment_ocid
  namespace      = var.namespace
  name           = var.bucket_name
  access_type    = "NoPublicAccess"

  versioning = var.enable_versioning ? "Enabled" : "Suspended"

  # Enable encryption
  encryption_config {
    dynamic "encryption_config" {
      for_each = var.enable_encryption ? [1] : []
      content {
        key_id = oci_kms_key.bucket_key[0].id
      }
    }
  }

  tags = merge(
    var.tags,
    {
      Name = var.bucket_name
    }
  )

  lifecycle {
    prevent_destroy = true
  }
}

# Create encryption key for bucket
resource "oci_kms_key" "bucket_key" {
  count               = var.enable_encryption ? 1 : 0
  compartment_id      = var.compartment_ocid
  display_name        = "${var.bucket_name}-key"
  key_shape {
    algorithm = "AES"
    length    = 256
  }

  management_placement_config {
    placement_region = var.region
  }

  tags = var.tags

  lifecycle {
    prevent_destroy = true
  }
}

# Bucket Lifecycle Policy - Archive old objects
resource "oci_objectstorage_object_lifecycle_policy" "polisen_lifecycle" {
  bucket    = oci_objectstorage_bucket.polisen_bucket.name
  namespace = var.namespace

  rules {
    # Transition to Archive Storage after 90 days
    name                                        = "ArchiveOldObjects"
    target                                      = "Archive"
    time_amount_in_days                        = 90
    is_enabled                                 = true

    # Apply to all objects with metadata filter
    filter_by_metrics_objects_greater_than_in_gb = 0
  }

  rules {
    # Delete archived objects after 1 year
    name                    = "DeleteArchivedObjects"
    target                  = "Delete"
    time_amount_in_days    = 365
    is_enabled             = true
  }
}

# Object Retention Policy (if required)
resource "oci_objectstorage_retention_rule" "polisen_retention" {
  count      = var.retention_days > 0 ? 1 : 0
  bucket     = oci_objectstorage_bucket.polisen_bucket.name
  namespace  = var.namespace
  duration_amount = var.retention_days
  duration_time_unit = "DAYS"

  retention_rule_type = "Governance"
}

# Cross-region Replication
resource "oci_objectstorage_bucket" "polisen_bucket_dr" {
  count          = var.enable_cross_region_replication ? 1 : 0
  compartment_id = var.compartment_ocid
  namespace      = var.namespace
  name           = "${var.bucket_name}-dr"
  access_type    = "NoPublicAccess"

  versioning = var.enable_versioning ? "Enabled" : "Suspended"

  tags = merge(
    var.tags,
    {
      Name        = "${var.bucket_name}-dr"
      Purpose     = "Disaster Recovery"
    }
  )

  lifecycle {
    prevent_destroy = true
  }
}

# Replication Policy
resource "oci_objectstorage_replication_policy" "to_dr" {
  count                          = var.enable_cross_region_replication ? 1 : 0
  bucket                         = oci_objectstorage_bucket.polisen_bucket.name
  namespace                      = var.namespace
  destination_bucket_name        = oci_objectstorage_bucket.polisen_bucket_dr[0].name
  destination_region_name        = var.dr_region
  replication_policy_display_name = "${var.bucket_name}-to-${var.dr_region}"

  status = "Enabled"

  depends_on = [oci_objectstorage_bucket.polisen_bucket_dr]
}
```

### File: `terraform/modules/object_storage/variables.tf`

```hcl
variable "compartment_ocid" {
  description = "Compartment OCID"
  type        = string
}

variable "namespace" {
  description = "Object storage namespace"
  type        = string
}

variable "bucket_name" {
  description = "Name of the bucket"
  type        = string
}

variable "region" {
  description = "Primary region"
  type        = string
}

variable "dr_region" {
  description = "DR region for replication"
  type        = string
  default     = "eu-central-1"
}

variable "enable_versioning" {
  description = "Enable versioning"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Enable encryption"
  type        = bool
  default     = true
}

variable "retention_days" {
  description = "Object retention days (0 = no retention)"
  type        = number
  default     = 0
}

variable "enable_cross_region_replication" {
  description = "Enable cross-region replication"
  type        = bool
  default     = false
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
```

### File: `terraform/modules/object_storage/outputs.tf`

```hcl
output "bucket_name" {
  description = "Name of the bucket"
  value       = oci_objectstorage_bucket.polisen_bucket.name
}

output "bucket_id" {
  description = "OCID of the bucket"
  value       = oci_objectstorage_bucket.polisen_bucket.id
}

output "namespace" {
  description = "Namespace of the bucket"
  value       = var.namespace
}

output "bucket_url" {
  description = "URL to access the bucket"
  value       = "https://${var.namespace}.objectstorage.${var.region}.oci.customer-oci.com/n/${var.namespace}/b/${oci_objectstorage_bucket.polisen_bucket.name}/o"
}

output "dr_bucket_name" {
  description = "Name of the DR replica bucket"
  value       = var.enable_cross_region_replication ? oci_objectstorage_bucket.polisen_bucket_dr[0].name : null
}
```

---

## 5. IAM Module

### File: `terraform/modules/iam/main.tf`

```hcl
# Create Dynamic Group for instances
resource "oci_identity_dynamic_group" "polisen_instances" {
  compartment_ocid = var.compartment_ocid
  name            = "polisen-collector-${var.environment}-instances"
  description     = "Dynamic group for Polisen collector instances"

  matching_rule = "instance.compartment.id = '${var.compartment_ocid}' AND instance.state = 'RUNNING' AND any(instance.metadata.get('ssh_authorized_keys'), 'polisen-collector')"

  tags = var.tags
}

# Policy: Allow instances to read vault secrets
resource "oci_identity_policy" "vault_access" {
  compartment_ocid = var.compartment_ocid
  name            = "polisen-collector-${var.environment}-vault-access"
  description     = "Allow Polisen instances to read secrets from vault"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.polisen_instances.name} to read secret-bundles in compartment id ${var.compartment_ocid} where target.vault.id = '${var.vault_ocid}'",
    "Allow dynamic-group ${oci_identity_dynamic_group.polisen_instances.name} to read secrets in compartment id ${var.compartment_ocid} where target.vault.id = '${var.vault_ocid}'",
    "Allow dynamic-group ${oci_identity_dynamic_group.polisen_instances.name} to read vaults in compartment id ${var.compartment_ocid} where target.vault.id = '${var.vault_ocid}'"
  ]

  tags = var.tags
}

# Policy: Allow instances to write to object storage
resource "oci_identity_policy" "object_storage_access" {
  compartment_ocid = var.compartment_ocid
  name            = "polisen-collector-${var.environment}-object-storage-access"
  description     = "Allow Polisen instances to read/write objects"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.polisen_instances.name} to manage objects in compartment id ${var.compartment_ocid}"
  ]

  tags = var.tags
}

# Policy: Allow instances to emit metrics
resource "oci_identity_policy" "metrics_access" {
  compartment_ocid = var.compartment_ocid
  name            = "polisen-collector-${var.environment}-metrics-access"
  description     = "Allow Polisen instances to emit metrics to Monitoring"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.polisen_instances.name} to use monitoring-family in compartment id ${var.compartment_ocid}"
  ]

  tags = var.tags
}

# Policy: Allow instances to write logs
resource "oci_identity_policy" "logging_access" {
  compartment_ocid = var.compartment_ocid
  name            = "polisen-collector-${var.environment}-logging-access"
  description     = "Allow Polisen instances to write logs"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.polisen_instances.name} to use log-content in compartment id ${var.compartment_ocid}"
  ]

  tags = var.tags
}

# Optional: Policy for audit logging
resource "oci_identity_policy" "audit_access" {
  compartment_ocid = var.compartment_ocid
  name            = "polisen-collector-${var.environment}-audit-access"
  description     = "Allow accessing audit logs"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.polisen_instances.name} to read audit-events in compartment id ${var.compartment_ocid}"
  ]

  tags = var.tags
}
```

### File: `terraform/modules/iam/variables.tf`

```hcl
variable "compartment_ocid" {
  description = "Compartment OCID"
  type        = string
}

variable "instance_principals" {
  description = "List of instance principal names"
  type        = list(string)
}

variable "vault_ocid" {
  description = "Vault OCID for policy"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
```

### File: `terraform/modules/iam/outputs.tf`

```hcl
output "dynamic_group_id" {
  description = "OCID of the dynamic group"
  value       = oci_identity_dynamic_group.polisen_instances.id
}

output "dynamic_group_name" {
  description = "Name of the dynamic group"
  value       = oci_identity_dynamic_group.polisen_instances.name
}

output "policy_ids" {
  description = "OCIDs of created policies"
  value = {
    vault_access            = oci_identity_policy.vault_access.id
    object_storage_access   = oci_identity_policy.object_storage_access.id
    metrics_access          = oci_identity_policy.metrics_access.id
    logging_access          = oci_identity_policy.logging_access.id
    audit_access            = oci_identity_policy.audit_access.id
  }
}
```

---

## 6. Environment Configuration Examples

### File: `terraform/environments/production/terraform.tfvars`

```hcl
environment             = "production"
oci_region              = "eu-stockholm-1"
vault_region            = "eu-frankfurt-1"
dr_region               = "eu-central-1"

vault_display_name      = "polisen-collector-vault-prod"
bucket_name             = "polisen-events-collector"

enable_vault_deletion              = false
enable_bucket_versioning           = true
enable_bucket_encryption           = true
enable_cross_region_replication    = true
bucket_retention_days              = 0

tags = {
  Environment = "production"
  Project     = "polisen-collector"
  ManagedBy   = "Terraform"
  CostCenter  = "engineering"
  Compliance  = "true"
}
```

### File: `terraform/environments/production/main.tf`

```hcl
# This file pulls in the root module configuration
# You would run terraform from here with:
# terraform init -backend-config="bucket=polisen-tf-state"
# terraform plan -var-file=terraform.tfvars
# terraform apply

module "polisen" {
  source = "../../"

  tenancy_ocid    = var.tenancy_ocid
  user_ocid       = var.user_ocid
  fingerprint     = var.fingerprint
  private_key_path = var.private_key_path
  compartment_ocid = var.compartment_ocid

  # Pass through all other variables
  environment             = var.environment
  oci_region              = var.oci_region
  vault_region            = var.vault_region
  dr_region              = var.dr_region
  vault_display_name      = var.vault_display_name
  bucket_name             = var.bucket_name
  enable_vault_deletion   = var.enable_vault_deletion
  enable_bucket_versioning = var.enable_bucket_versioning
  enable_bucket_encryption = var.enable_bucket_encryption
  enable_cross_region_replication = var.enable_cross_region_replication
  bucket_retention_days   = var.bucket_retention_days

  tags = var.tags
}

output "vault_id" {
  value = module.polisen.vault_id
}

output "bucket_name" {
  value = module.polisen.bucket_name
}
```

### File: `terraform/environments/development/terraform.tfvars`

```hcl
environment             = "development"
oci_region              = "eu-stockholm-1"
vault_region            = "eu-frankfurt-1"
dr_region               = null

vault_display_name      = "polisen-collector-vault-dev"
bucket_name             = "polisen-events-collector-dev"

enable_vault_deletion              = false
enable_bucket_versioning           = true
enable_bucket_encryption           = false  # Optional for dev
enable_cross_region_replication    = false  # Not needed for dev
bucket_retention_days              = 30    # 30-day retention for dev

tags = {
  Environment = "development"
  Project     = "polisen-collector"
  ManagedBy   = "Terraform"
  Temporary   = "true"
}
```

---

## 7. Initialization and Deployment Guide

### Step 1: Initialize Terraform

```bash
cd terraform

# Initialize terraform
terraform init

# Verify structure
terraform validate

# Format files
terraform fmt -recursive
```

### Step 2: Plan Infrastructure

```bash
# For development
cd environments/development
terraform plan -var-file=terraform.tfvars

# For production
cd environments/production
terraform plan -var-file=terraform.tfvars
```

### Step 3: Apply Configuration

```bash
# Always review the plan first!
terraform apply -var-file=terraform.tfvars

# This will prompt for confirmation. Review carefully.
```

### Step 4: Save Terraform Outputs

```bash
# Get outputs
terraform output

# Save to file
terraform output -json > outputs.json

# Use specific output
terraform output vault_id
```

---

## 8. Secrets Initialization

After creating infrastructure with Terraform, manually set secret values:

```bash
#!/bin/bash
# scripts/init-secrets.sh

VAULT_ID=$(terraform -chdir=environments/production output -raw vault_id)
COMPARTMENT_ID="your-compartment-ocid"

# Get secret values
read -sp "Enter OCI User OCID: " USER_OCID
echo

read -sp "Enter OCI Tenancy OCID: " TENANCY_OCID
echo

read -sp "Enter API Key Fingerprint: " FINGERPRINT
echo

read -sp "Enter Private Key Path: " KEY_PATH
PRIVATE_KEY=$(cat "$KEY_PATH")
echo

# Update secrets in vault
oci vault secret update-secret-by-name \
  --vault-id "$VAULT_ID" \
  --secret-name "oci-user-ocid" \
  --secret-content-type "text/plain" \
  --secret-content "$USER_OCID"

# Repeat for other secrets...
```

---

## 9. Terraform Best Practices

### .gitignore
```bash
# terraform/.gitignore
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl
terraform.tfvars
terraform.tfvars.json
crash.log
override.tf
override.tf.json
*_override.tf
*_override.tf.json
.terraformrc
terraform.rc
.DS_Store
*.swp
*.swo
```

### CI/CD Integration

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  push:
    branches: [main]
    paths:
      - 'terraform/**'
  pull_request:
    branches: [main]
    paths:
      - 'terraform/**'

env:
  TF_VERSION: 1.5.0

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: ${{ env.TF_VERSION }}
      - run: terraform -chdir=terraform fmt -check
      - run: terraform -chdir=terraform init
      - run: terraform -chdir=terraform validate

  plan:
    runs-on: ubuntu-latest
    needs: validate
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      - run: |
          cd terraform/environments/production
          terraform plan -var-file=terraform.tfvars -out=tfplan

  apply:
    runs-on: ubuntu-latest
    needs: plan
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      - run: |
          cd terraform/environments/production
          terraform apply -var-file=terraform.tfvars -auto-approve
```

---

## 10. Maintenance Operations

### State Management
```bash
# Show current state
terraform state list

# Show specific resource
terraform state show oci_vault_vault.polisen_vault

# Remove resource from state (for manual cleanup)
terraform state rm oci_vault_vault.polisen_vault

# Refresh state without changes
terraform refresh
```

### Upgrade Providers
```bash
# Check for new provider versions
terraform init -upgrade

# Plan to see what changes
terraform plan
```

### Backup State
```bash
# Regular backups
terraform state pull > terraform.tfstate.backup

# Encrypted backup
terraform state pull | gpg --symmetric > terraform.tfstate.backup.gpg
```

---

## Summary

This Terraform implementation provides:
- Declarative infrastructure automation
- Environment-specific configurations
- Security-first defaults
- Disaster recovery capabilities
- Audit-friendly resource tagging
- Easy reproducibility

**Next Steps:**
1. Customize variables for your environment
2. Initialize Terraform
3. Review and apply configuration
4. Monitor with Terraform Cloud (optional)
5. Integrate with CI/CD pipeline

---

**Total Implementation Time:** 8-12 hours (including testing and validation)
**Risk Level:** MEDIUM (requires careful testing)
**Impact:** HIGH - Enables reproducible, version-controlled infrastructure
