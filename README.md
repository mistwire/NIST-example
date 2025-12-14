# NIST 800-53 Compliance POC: AWS SCPs + Terraform Sentinel

## What This Is

This is a **proof-of-concept** demonstrating a dual-layer policy enforcement approach for NIST 800-53 compliance in AWS environments. It combines:

1. **AWS Service Control Policies (SCPs)** - Organization-level guardrails that prevent non-compliant actions at the AWS API level
2. **Terraform Sentinel Policies** - Infrastructure-as-code validation that prevents non-compliant resources from being provisioned

**Note:** This POC is intentionally incomplete and serves as an architectural example, not production-ready code.

## The Problem This Solves

Organizations need to prove NIST 800-53 compliance across their cloud infrastructure. Traditional approaches have gaps:

- **SCPs alone**: Can't validate resource configurations (e.g., "is this RDS instance encrypted?")
- **Sentinel alone**: Can't prevent console/CLI actions outside Terraform
- **Manual audits**: Slow, error-prone, and don't prevent violations

This POC shows how using both together creates defense-in-depth.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   NIST Control (e.g., AC-3)             │
│              "Enforce Access Controls"                   │
└─────────────────┬───────────────────────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
┌──────────────┐   ┌──────────────────┐
│   AWS SCP    │   │ Terraform        │
│              │   │ Sentinel Policy  │
│ Prevents:    │   │                  │
│ • Public S3  │   │ Validates:       │
│   via API    │   │ • S3 bucket      │
│ • Console    │   │   configs        │
│ • CloudForm  │   │ • Encryption     │
└──────────────┘   └──────────────────┘
         │                 │
         └────────┬────────┘
                  ▼
         ✓ Compliant Infrastructure
```

### Why Both?

| Scenario | SCP | Sentinel |
|----------|-----|----------|
| Engineer uses AWS Console to create public S3 bucket | ✓ Blocks | ✗ Not involved |
| Terraform deploys unencrypted RDS database | ✗ Can't inspect resource config | ✓ Blocks |
| CloudFormation creates bucket without encryption | ✓ Blocks API call | ✗ Not involved |
| Terraform creates private S3 bucket correctly | ✗ Allows | ✓ Validates & approves |

## Repository Structure

```
.
├── scps/                        # AWS Service Control Policies
│   ├── AC/                      # Access Control family
│   │   ├── AC-3-deny-public-s3.json
│   │   ├── AC-3-require-mfa.json
│   │   └── AC-6-least-privilege.json
│   └── SC/                      # System & Communications Protection
│       ├── SC-7-require-vpc-endpoints.json
│       └── SC-13-require-encryption.json
│
├── sentinel/                    # Terraform Sentinel Policies
│   ├── AC/
│   │   ├── nist-ac3-s3-controls.sentinel
│   │   ├── nist-ac3-rds-private.sentinel
│   │   ├── nist-ac6-iam-validation.sentinel
│   │   └── tests/
│   └── SC/
│       ├── nist-sc7-network-segmentation.sentinel
│       └── nist-sc13-encryption.sentinel
│
├── compliance-mapping.yml       # Single source of truth
├── scripts/
│   ├── generate-reports.py      # Creates compliance reports
│   └── validate-mapping.py      # Validates policy coverage
└── reports/                     # Generated compliance artifacts
```

## Key Concept: The Mapping File

The [`compliance-mapping.yml`](compliance-mapping.yml) file is the heart of this approach. It maps each NIST control to specific technical implementations:

```yaml
- control_id: "AC-3"
  control_name: "Access Enforcement"

  technical_requirements:
    - requirement_id: "AC-3.1"
      description: "Prevent public access to S3 buckets"

      scp_policy:
        enabled: true
        policy_file: "scps/AC/AC-3-deny-public-s3.json"
        applied_to: ["Production OU", "Staging OU"]
        enforcement_level: "hard-deny"

      sentinel_policy:
        enabled: true
        policy_file: "sentinel/AC/nist-ac3-s3-controls.sentinel"
        applied_to: ["All production workspaces"]
        enforcement_level: "mandatory"
```

This creates:
- **Traceability**: Auditors can see exactly how each control is enforced
- **Coverage gaps**: Easy to spot controls without implementation
- **Audit trail**: Track when/who implemented each control

## NIST Control Families Covered (POC)

- **AC** - Access Control (4 controls)
  - AC-3: Access Enforcement
  - AC-6: Least Privilege

- **SC** - System and Communications Protection (2 controls)
  - SC-7: Boundary Protection
  - SC-13: Cryptographic Protection

- **AU** - Audit and Accountability (planned, not implemented)

## How This Would Work (If It Were Complete)

### For Security Engineers

1. **Find your NIST control**: Check [`compliance-mapping.yml`](compliance-mapping.yml)
2. **Implement at both layers**:
   - Create SCP in [`scps/{FAMILY}/`](scps/)
   - Create Sentinel policy in [`sentinel/{FAMILY}/`](sentinel/)
3. **Update mapping**: Document both in `compliance-mapping.yml`
4. **Test**: Run Sentinel tests, deploy SCP to test OU
5. **Deploy**: Merge to main, automation applies policies

### For Compliance/Auditors

1. **Review coverage**: Run `python scripts/generate-reports.py`
2. **Audit policies**: Each policy file references its NIST control
3. **Test evidence**: Sentinel tests prove policies work
4. **Production proof**: SCP deployment logs show enforcement

### For Developers

- Terraform plans automatically checked against Sentinel policies
- Non-compliant infrastructure blocked before `terraform apply`
- Clear error messages reference NIST control (e.g., "Violates NIST AC-3: S3 bucket must be private")

## What's Missing (Because It's a POC)

1. **Actual policy code**: The `.json` and `.sentinel` files are mostly empty
2. **CI/CD pipeline**: No GitHub Actions to deploy SCPs or register Sentinel policies
3. **Terraform Cloud integration**: Sentinel policies would need to be uploaded to TFC/TFE
4. **Complete coverage**: Only ~6 controls, real compliance needs 50+
5. **Testing framework**: Sentinel tests are stubbed out
6. **Drift detection**: No monitoring for manual changes that bypass policies
7. **Exception handling**: No process for approved deviations

## How to Actually Use This

### Running the Report Generator

```bash
# Install dependencies (would need requirements.txt)
pip install pyyaml

# Generate compliance report
python scripts/generate-reports.py

# View report
open reports/compliance-report.html
```

### Deploying SCPs (Conceptual)

```bash
# This would require AWS Organizations setup
aws organizations create-policy \
  --name "AC-3-deny-public-s3" \
  --type SERVICE_CONTROL_POLICY \
  --content file://scps/AC/AC-3-deny-public-s3.json

aws organizations attach-policy \
  --policy-id <policy-id> \
  --target-id <ou-id>
```

### Deploying Sentinel (Conceptual)

```bash
# Upload to Terraform Cloud organization
terraform login

# This would be done via Terraform Cloud API or UI
# sentinel/AC/nist-ac3-s3-controls.sentinel → TFC Policy Set
```

## Example: How AC-3 Works

**NIST AC-3**: "The information system enforces approved authorizations for logical access"

**Translation**: Don't let people make S3 buckets public

**Implementation**:

1. **SCP Layer** ([`scps/AC/AC-3-deny-public-s3.json`](scps/AC/AC-3-deny-public-s3.json)):
   - Denies `s3:PutBucketPublicAccessBlock` with public settings
   - Denies `s3:PutBucketPolicy` with `"*"` principals
   - Applied to Production and Staging OUs

2. **Sentinel Layer** ([`sentinel/AC/nist-ac3-s3-controls.sentinel`](sentinel/AC/nist-ac3-s3-controls.sentinel)):
   - Validates `aws_s3_bucket` resources in Terraform
   - Checks `acl != "public-read"`
   - Checks `public_access_block` is enabled
   - Enforcement: mandatory (hard fail)

**Result**: Public S3 buckets are impossible to create, whether via Console, CLI, CloudFormation, or Terraform.

## Why This Approach Is Valuable

1. **Defense in Depth**: Multiple enforcement points
2. **Shift Left**: Catches issues in Terraform plans before deployment
3. **Continuous Compliance**: Policies always enforced, not periodic audits
4. **Audit Ready**: Clear mapping from controls to technical implementation
5. **Developer Friendly**: Fast feedback in Terraform workflow
6. **Organization Wide**: SCPs protect against all access methods

## Real-World Deployment Considerations

To make this production-ready, you'd need:

- **Policy testing**: Automated tests for all Sentinel policies
- **SCP testing**: Staging environment to validate SCPs don't break legitimate workflows
- **Exception workflow**: Process for approved deviations (break-glass)
- **Monitoring**: Alerts when SCP blocks occur (might indicate policy issue or attack)
- **Documentation**: Per-policy READMEs explaining rationale
- **Version control**: Tag policy versions matching audit periods
- **Change management**: Require security review for policy changes

## Learning Resources

- [AWS Service Control Policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)
- [Terraform Sentinel](https://docs.hashicorp.com/sentinel/terraform)
- [NIST 800-53 Rev 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [Policy as Code Best Practices](https://www.hashicorp.com/resources/policy-as-code-best-practices)

