# Terraform Policy Repository

## Purpose
This repository contains all AWS Service Control Policies (SCPs) and 
Terraform Sentinel policies used to enforce NIST compliance requirements.

## Structure
- `scps/` - AWS Service Control Policies organized by NIST family
- `sentinel/` - Terraform Sentinel policies organized by NIST family
- `scripts/` - Automation tools for deployment and reporting

## NIST Control Families Covered
- **AC** - Access Control
- **SC** - System and Communications Protection  
- **CM** - Configuration Management
- **AU** - Audit and Accountability
- *(add more as you implement them)*

## How to Use This Repository

### For Engineers
1. Find your NIST control (e.g., AC-3)
2. Go to the corresponding folder (e.g., `scps/AC/` or `sentinel/AC/`)
3. Read the README to understand existing policies
4. Review or modify the policy files as needed

### For Auditors
1. See `compliance-mapping.yml` for complete coverage overview
2. Navigate to specific control folders to review policy code
3. Each README shows what's implemented and where it's applied

### Making Changes
1. Create a new branch for your changes
2. Add/modify policy files in the appropriate folder
3. Update the folder's README with your changes
4. Submit a pull request for review
5. After approval, changes are deployed automatically

## Contact
Platform Team: 
Policy Questions: 