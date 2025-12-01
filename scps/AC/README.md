# Access Control (AC) - AWS Service Control Policies

This folder contains AWS Service Control Policies (SCPs) that enforce NIST Access Control requirements at the AWS Organization level.

## 📋 Quick Reference

| NIST Control | Policy File | Applied To | Enforcement |
|--------------|-------------|------------|-------------|
| AC-3 | AC-3-deny-public-s3.json | Production OU, Staging OU | Hard Deny |
| AC-3 | AC-3-require-mfa.json | All OUs except Sandbox | Hard Deny |
| AC-6 | AC-6-least-privilege.json | All OUs | Hard Deny |

---

## 🔐 NIST AC-3: Access Enforcement

**NIST Description:** The information system enforces approved authorizations for logical access to information and system resources.

### Policy: AC-3-deny-public-s3.json

**Purpose:** Prevents creation of publicly accessible S3 buckets

**Technical Details:**
- Denies `s3:PutBucketPublicAccessBlock` API calls that would allow public access
- Denies `s3:PutAccountPublicAccessBlock` modifications
- Requires all buckets to maintain `PublicAccessBlockConfiguration`

**Applied To:**
- Production OU (ou-prod-123456)
- Staging OU (ou-staging-789012)

**Related Policies:**
- **Sentinel:** [`sentinel/AC/nist-ac3-s3-controls.sentinel`](../../sentinel/AC/nist-ac3-s3-controls.sentinel)
- Provides additional validation of S3 bucket encryption and tagging

**Deployment:**
```bash
# Deploy this SCP to Production OU
aws organizations attach-policy \
  --policy-id p-ac3-s3-public \
  --target-id ou-prod-123456
```

**Testing:**
Try creating a public S3 bucket in a production account - should be blocked:
```bash
aws s3api create-bucket \
  --bucket test-public-bucket \
  --acl public-read
# Expected: AccessDenied error due to SCP
```

**Last Updated:** 2025-11-20 by Chris Williams  
**Change Log:** Added staging OU to scope

---

### Policy: AC-3-require-mfa.json

**Purpose:** Requires multi-factor authentication for privileged AWS API operations

**Technical Details:**
- Denies high-risk API calls unless MFA is present
- Covers IAM changes, EC2 termination, RDS deletion, etc.
- Uses `aws:MultiFactorAuthPresent` condition

**Applied To:**
- All OUs except Sandbox OU

**Exemptions:**
- Sandbox OU (developers testing without MFA)
- Service accounts with `mufg:service-account=true` tag

**Deployment:**
```bash
# Deploy to root organization
aws organizations attach-policy \
  --policy-id p-ac3-mfa \
  --target-id r-root
```

**Testing:**
Attempt privileged operation without MFA - should be blocked:
```bash
# Without MFA session
aws iam delete-user --user-name test-user
# Expected: AccessDenied - MFA required
```

**Last Updated:** 2025-10-15 by Chris Williams

---

## 🔑 NIST AC-6: Least Privilege

**NIST Description:** The organization employs the principle of least privilege, allowing only authorized accesses for users (or processes acting on behalf of users) which are necessary to accomplish assigned tasks.

### Policy: AC-6-least-privilege.json

**Purpose:** Prevents creation of overly permissive IAM policies with wildcard actions

**Technical Details:**
- Denies IAM policy creation/modification with `Action: *` and `Resource: *`
- Blocks attachment of AWS-managed `*FullAccess` policies
- Requires policies to specify explicit actions and resources

**Applied To:**
- All OUs (organization-wide enforcement)

**Related Policies:**
- **Sentinel:** [`sentinel/AC/nist-ac6-iam-validation.sentinel`](../../sentinel/AC/nist-ac6-iam-validation.sentinel)
- Provides advisory warnings for borderline policies

**Deployment:**
```bash
# Already deployed at root level
aws organizations attach-policy \
  --policy-id p-ac6-least-priv \
  --target-id r-root
```

**Example Violation:**
```json
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
// This policy would be blocked by SCP
```

**Example Compliant:**
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject"
  ],
  "Resource": "arn:aws:s3:::specific-bucket/*"
}
// This policy follows least privilege
```

**Last Updated:** 2025-11-01 by Chris Williams

---

## 📁 File Structure
```
scps/AC/
├── README.md (this file)
├── AC-3-deny-public-s3.json
├── AC-3-require-mfa.json
└── AC-6-least-privilege.json
```

---

## 🔗 Related Documentation

- **Sentinel Policies:** [`../../sentinel/AC/`](../../sentinel/AC/)
- **Compliance Mapping:** [`../../compliance-mapping.yml`](../../compliance-mapping.yml)
- **Generated Report:** [`../../reports/compliance-report.html`](../../reports/compliance-report.html)

---

## 🛠️ Making Changes

When updating policies in this folder:

1. **Update the policy file** (e.g., `AC-3-deny-public-s3.json`)
2. **Update this README** with change details
3. **Update `compliance-mapping.yml`** with new deployment info
4. **Test the policy** in a sandbox environment first
5. **Submit PR** for team review
6. **Deploy to AWS** after approval
7. **Regenerate compliance report** by running `scripts/generate-reports.py`

---

## 📞 Contact

**Owner:** Chris Williams (Platform Security Team)  
**Questions:** platform-security@mufg.com  
**Emergency:** See runbook in Confluence