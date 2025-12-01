# Access Control (AC) - Sentinel Policies

Terraform Sentinel policies that validate NIST Access Control requirements before infrastructure changes are applied.

## 📋 Quick Reference

| NIST Control | Policy File | Enforcement Level | Applied To |
|--------------|-------------|-------------------|------------|
| AC-3 | nist-ac3-s3-controls.sentinel | Mandatory | All prod/staging workspaces |
| AC-3 | nist-ac3-rds-private.sentinel | Mandatory | All workspaces |
| AC-6 | nist-ac6-iam-validation.sentinel | Advisory | All workspaces |

---

## 🔐 NIST AC-3: Access Enforcement

### Policy: nist-ac3-s3-controls.sentinel

**Purpose:** Validates S3 bucket configurations meet security requirements BEFORE Terraform creates them

**Requirements Enforced:**
1. ✅ Server-side encryption must be enabled (AES256 or aws:kms)
2. ✅ `DataClassification` tag must be present
3. ✅ Public access block must be configured
4. ✅ Versioning should be enabled (warning only)

**Enforcement Level:** **MANDATORY** (blocks Terraform apply if violated)

**Applied To:**
- All production workspaces (prefix: `prod-*`)
- All staging workspaces (prefix: `staging-*`)
- **Excluded:** Sandbox workspaces (advisory only)

**Related Policies:**
- **AWS SCP:** [`../../scps/AC/AC-3-deny-public-s3.json`](../../scps/AC/AC-3-deny-public-s3.json)
- Provides backstop if Sentinel is bypassed

**Example Violation:**
```hcl
# This Terraform code would FAIL the policy check:
resource "aws_s3_bucket" "user_data" {
  bucket = "mufg-user-data"
  # ❌ Missing encryption configuration
  # ❌ Missing DataClassification tag
}
```

**Error Message:**
```
Policy Violation: NIST AC-3 - S3 Access Controls

Resource: aws_s3_bucket.user_data
Issues:
  • Missing server_side_encryption_configuration
  • Missing required tag: DataClassification

Required configuration:
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"  # or "aws:kms"
      }
    }
  }
  
  tags = {
    DataClassification = "Confidential"  # or "Internal", "Public"
  }

This policy is MANDATORY and cannot be overridden.
```

**Example Compliant Code:**
```hcl
# This Terraform code would PASS the policy check:
resource "aws_s3_bucket" "user_data" {
  bucket = "mufg-user-data"
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "aws:kms"
        kms_master_key_id = aws_kms_key.s3.arn
      }
    }
  }
  
  versioning {
    enabled = true
  }
  
  tags = {
    DataClassification = "Confidential"
    Owner = "platform-team"
    Environment = "production"
  }
}

resource "aws_s3_bucket_public_access_block" "user_data" {
  bucket = aws_s3_bucket.user_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

**Testing Locally:**
```bash
# Test with passing configuration
cd sentinel/AC/tests/
sentinel test nist-ac3-s3-controls.sentinel

# Test with specific mock file
sentinel apply -config=../../config.json nist-ac3-s3-controls.sentinel tests/ac3-s3-pass.json

# Expected output:
# ✓ PASS - nist_ac3_s3_encryption
# ✓ PASS - nist_ac3_s3_tags
# ✓ PASS - main
```

**Last Updated:** 2025-11-28 by Chris Williams  
**Last Test:** 2025-11-28 - PASS

---

### Policy: nist-ac3-rds-private.sentinel

**Purpose:** Ensures RDS database instances are not publicly accessible

**Requirements Enforced:**
1. ✅ `publicly_accessible` must be `false`
2. ✅ RDS instance must be in a private subnet (checks subnet tags)
3. ✅ Security group must not allow 0.0.0.0/0 on database port

**Enforcement Level:** **MANDATORY**

**Applied To:** All workspaces (no exceptions)

**Example Violation:**
```hcl
# This would FAIL:
resource "aws_db_instance" "main" {
  identifier = "mufg-prod-db"
  engine     = "postgres"
  
  publicly_accessible = true  # ❌ VIOLATION
  
  db_subnet_group_name = "public-subnets"  # ❌ VIOLATION
}
```

**Error Message:**
```
Policy Violation: NIST AC-3 - RDS Private Endpoints

Resource: aws_db_instance.main
Issues:
  • publicly_accessible must be false
  • db_subnet_group must use private subnets only

RDS databases containing financial data must not be accessible from the internet.
```

**Example Compliant Code:**
```hcl
# This would PASS:
resource "aws_db_instance" "main" {
  identifier = "mufg-prod-db"
  engine     = "postgres"
  
  publicly_accessible = false  # ✅ CORRECT
  
  db_subnet_group_name = aws_db_subnet_group.private.name  # ✅ Private subnets
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  storage_encrypted = true
  
  tags = {
    DataClassification = "Confidential"
    Environment = "production"
  }
}

resource "aws_db_subnet_group" "private" {
  name = "mufg-private-subnet-group"
  subnet_ids = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id,
  ]
  
  tags = {
    Tier = "private"  # ✅ Policy checks for this tag
  }
}
```

**Testing:**
```bash
cd sentinel/AC/tests/
sentinel test nist-ac3-rds-private.sentinel

# Test individual scenarios:
sentinel apply nist-ac3-rds-private.sentinel tests/ac3-rds-public-fail.json
# Expected: FAIL

sentinel apply nist-ac3-rds-private.sentinel tests/ac3-rds-private-pass.json
# Expected: PASS
```

**Last Updated:** 2025-11-28 by Chris Williams  
**Last Test:** 2025-11-28 - PASS

---

## 🔑 NIST AC-6: Least Privilege

### Policy: nist-ac6-iam-validation.sentinel

**Purpose:** Validates IAM policies follow least privilege principles (advisory warnings)

**Requirements Checked:**
1. ⚠️ IAM policies should not use `Action: "*"` with `Resource: "*"`
2. ⚠️ IAM role trust policies should be scoped to specific principals
3. ⚠️ IAM policies should include descriptions
4. ⚠️ IAM policy names should follow naming convention: `mufg-[service]-[purpose]`

**Enforcement Level:** **ADVISORY** (warns but does not block)

**Applied To:** All workspaces

**Why Advisory?**
- Some legitimate use cases require broad permissions (admin roles, service accounts)
- Policy provides warnings to encourage best practices
- Can be upgraded to mandatory in the future

**Related Policies:**
- **AWS SCP:** [`../../scps/AC/AC-6-least-privilege.json`](../../scps/AC/AC-6-least-privilege.json)
- SCP provides hard enforcement for most egregious violations

**Example Warning:**
```hcl
# This code generates WARNINGS but still allows apply:
resource "aws_iam_policy" "admin" {
  name = "admin-policy"  # ⚠️ Should be "mufg-admin-assume-role"
  
  # ⚠️ Missing description
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "*"       # ⚠️ Overly broad
      Resource = "*"     # ⚠️ Overly broad
    }]
  })
}
```

**Warning Message:**
```
Advisory Warning: NIST AC-6 - Least Privilege

Resource: aws_iam_policy.admin
Recommendations:
  ⚠️ Policy name should follow convention: mufg-[service]-[purpose]
  ⚠️ Consider adding a description field
  ⚠️ Action "*" with Resource "*" grants excessive permissions
  ⚠️ Consider scoping to specific actions and resources

These are advisory warnings. Your Terraform apply will proceed.
Consider refactoring this policy to follow least privilege principles.
```

**Example Best Practice Code:**
```hcl
resource "aws_iam_policy" "s3_read" {
  name        = "mufg-s3-readonly-access"  # ✅ Follows naming convention
  description = "Read-only access to production S3 buckets"  # ✅ Has description
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [  # ✅ Specific actions
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Resource = [  # ✅ Specific resources
        "arn:aws:s3:::mufg-prod-*",
        "arn:aws:s3:::mufg-prod-*/*"
      ]
    }]
  })
}
```

**Testing:**
```bash
cd sentinel/AC/tests/
sentinel test nist-ac6-iam-validation.sentinel

# This policy has advisory enforcement, so tests check warnings, not failures
```

**Last Updated:** 2025-11-15 by Chris Williams  
**Last Test:** 2025-11-15 - PASS

---

## 📁 File Structure
```
sentinel/AC/
├── README.md (this file)
├── nist-ac3-s3-controls.sentinel
├── nist-ac3-rds-private.sentinel
├── nist-ac6-iam-validation.sentinel
└── tests/
    ├── ac3-s3-pass.json
    ├── ac3-s3-fail.json
    ├── ac3-rds-private-pass.json
    ├── ac3-rds-public-fail.json
    ├── ac6-iam-pass.json
    └── test-all.sh
```

---

## 🔗 Related Documentation

- **AWS SCPs:** [`../../scps/AC/`](../../scps/AC/)
- **Compliance Mapping:** [`../../compliance-mapping.yml`](../../compliance-mapping.yml)
- **Generated Report:** [`../../reports/compliance-report.html`](../../reports/compliance-report.html)
- **Sentinel Documentation:** https://docs.hashicorp.com/sentinel

---

## 🛠️ Making Changes

When updating Sentinel policies:

1. **Modify the .sentinel file**
2. **Update test mocks** in `tests/` folder
3. **Run local tests:** `sentinel test`
4. **Update this README** with changes
5. **Update `compliance-mapping.yml`**
6. **Submit PR** for review
7. **After merge:** Policy automatically applies to TFC policy sets via CI/CD
8. **Regenerate report:** `scripts/generate-reports.py`

---

## 🧪 Running All Tests
```bash
# Test all AC policies at once
cd tests/
./test-all.sh

# Expected output:
# Testing nist-ac3-s3-controls.sentinel...
# ✓ PASS (3/3 checks)
#
# Testing nist-ac3-rds-private.sentinel...
# ✓ PASS (2/2 checks)
#
# Testing nist-ac6-iam-validation.sentinel...
# ✓ PASS (4/4 checks)
#
# All tests passed!
```

---

## 📞 Contact

**Owner:** Chris Williams (Platform Security Team)  
**Questions:** platform-security@mufg.com  