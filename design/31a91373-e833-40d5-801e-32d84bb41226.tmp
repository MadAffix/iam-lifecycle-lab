# Organization Model — Nittany Analytics (fictional)

A ~20-person analytics company used to model identity lifecycle, RBAC, least privilege, and separation of duties (SoD).

## 1. Departments & Roles

| Department | Role | Description |
|---|---|---|
| Finance | Accounts Payable (AP) Clerk | Sets up vendors and enters invoices |
| Finance | Finance Manager | Approves payments and payroll runs |
| HR | HR Specialist | Maintains employee records, enters payroll changes |
| Engineering | Software Engineer | Writes code, deploys to dev/test cloud environments |
| Engineering | Engineering Manager | Manages the team and repositories |
| IT | IT Administrator | Manages user accounts and cloud infrastructure |

## 2. Systems & Entitlements

| System | Entitlement | What it allows | Risk | System owner (approver) |
|---|---|---|---|---|
| SSO / Directory | `SSO:Login` | Sign in to company apps | Low | IT |
| Email | `Email:Mailbox` | Company mailbox | Low | IT |
| Slack | `Slack:Member` | Company chat | Low | IT |
| Directory | `Directory:ManageUsers` | Create/disable accounts, assign groups | **Privileged** | IT Director |
| ERP | `ERP:ViewReports` | View financial reports | Medium | CFO |
| ERP | `ERP:CreateVendor` | Add/edit vendors and bank details | High | CFO |
| ERP | `ERP:EnterInvoice` | Enter vendor invoices | High | CFO |
| ERP | `ERP:ApprovePayment` | Release payments to vendors | High | CFO |
| Payroll | `Payroll:Read` | View payroll data | High | CFO |
| Payroll | `Payroll:Edit` | Change salaries, bank info | High | HR Director |
| Payroll | `Payroll:Approve` | Approve payroll run | **Privileged** | CFO |
| HRIS | `HRIS:ViewEmployee` | View employee records | Medium | HR Director |
| HRIS | `HRIS:EditEmployee` | Create/edit employee records | High | HR Director |
| GitHub | `GitHub:Read` | Read repositories | Low | Eng Manager |
| GitHub | `GitHub:Write` | Push code | Medium | Eng Manager |
| GitHub | `GitHub:Admin` | Manage repos, settings, members | **Privileged** | CTO |
| AWS | `AWS:ReadOnly` | View cloud resources | Medium | CTO |
| AWS | `AWS:Developer` | Deploy to dev/test accounts | High | CTO |
| AWS | `AWS:Admin` | Full cloud administration | **Privileged** | CTO |

## 3. Birthright Access (every active employee)

`SSO:Login`, `Email:Mailbox`, `Slack:Member` — granted automatically on hire, removed on termination. No approval needed.

## 4. Role → Entitlement Matrix (least privilege)

| Role | Entitlements (in addition to birthright) |
|---|---|
| AP Clerk | `ERP:ViewReports`, `ERP:CreateVendor`, `ERP:EnterInvoice` |
| Finance Manager | `ERP:ViewReports`, `ERP:ApprovePayment`, `Payroll:Read`, `Payroll:Approve` |
| HR Specialist | `HRIS:ViewEmployee`, `HRIS:EditEmployee`, `Payroll:Edit` |
| Software Engineer | `GitHub:Read`, `GitHub:Write`, `AWS:ReadOnly`, `AWS:Developer` |
| Engineering Manager | `GitHub:Read`, `GitHub:Write`, `GitHub:Admin`, `AWS:ReadOnly` |
| IT Administrator | `Directory:ManageUsers`, `AWS:Admin`, `HRIS:ViewEmployee` |

Anything outside this matrix requires a time-bound exception request approved by the manager **and** the system owner.

## 5. Separation of Duties (SoD) Rules

| ID | Conflicting entitlements | Risk prevented |
|---|---|---|
| SOD-01 | `ERP:CreateVendor` + `ERP:ApprovePayment` | Creating a fake vendor and paying it |
| SOD-02 | `ERP:EnterInvoice` + `ERP:ApprovePayment` | Entering and approving your own invoice |
| SOD-03 | `Payroll:Edit` + `Payroll:Approve` | Changing pay (e.g., your own) and approving it |
| SOD-04 | `HRIS:EditEmployee` + `Directory:ManageUsers` | Creating a "ghost employee" and giving it access |

The matrix above was checked so that no single role violates an SoD rule. Conflicts can only appear through exceptions, mover leftovers, or errors — which the access review script detects.

## 6. Privileged Access Policy

Entitlements marked **Privileged** (`Directory:ManageUsers`, `Payroll:Approve`, `GitHub:Admin`, `AWS:Admin`):
- Require MFA
- Require manager + system owner approval
- Reviewed quarterly (all other access reviewed semi-annually)
