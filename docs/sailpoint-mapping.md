# Mapping the Lab to SailPoint Identity Security Cloud (ISC)

This document maps the Nittany Analytics lab design to the concepts used in **SailPoint Identity Security Cloud (ISC)**, an enterprise identity governance platform.

> **Scope note:** This is a concept mapping based on studying SailPoint's public documentation. The lab was built in Python and markdown; it was not implemented in a SailPoint tenant.

## 1. Concept Mapping

| SailPoint ISC concept | What it does in ISC | Lab equivalent | Lab file |
|---|---|---|---|
| **Source** | A connected system ISC reads accounts and entitlements from | Each system (ERP, Payroll, HRIS, GitHub, AWS, SSO) | `design/org-model.md` §2 |
| **Authoritative source** | The HR system that creates and updates identities | `employees.csv` (HR source of truth) | `data/employees.csv` |
| **Identity** | One person, linked to all their accounts | One row in `employees.csv` | `data/employees.csv` |
| **Identity profile** | Defines how identities are built from the authoritative source and which lifecycle states apply | The employee record schema (role, department, manager, status) | `data/employees.csv` |
| **Identity attributes** | Fields like department, title, manager used to drive access | `role`, `department`, `manager_id`, `status` | `data/employees.csv` |
| **Lifecycle states** | States such as pre-hire, active, leave of absence, terminated, archived; can enable/disable accounts and grant or remove access | `status` column + Joiner/Mover/Leaver design | `design/lifecycle.md` |
| **Entitlement** | A single permission on a source | `ERP:ApprovePayment`, `AWS:Admin`, etc. | `design/org-model.md` §2 |
| **Access profile** | A bundle of entitlements from one source | Grouping of a system's entitlements per role | `data/role_matrix.csv` |
| **Role** (with membership criteria) | Business role that bundles access profiles; can be auto-assigned based on identity attributes | Role → entitlement matrix | `data/role_matrix.csv` |
| **Birthright access** | Access everyone gets in a lifecycle state | `*` rows: SSO, Email, Slack | `data/role_matrix.csv` |
| **Access request + approvals** | Self-service requests routed to manager, owners, or governance groups | Exception request flow | `design/lifecycle.md` §7 |
| **SoD policy** | Defines conflicting access and flags violations | SOD-01 through SOD-04 | `design/org-model.md` §5 |
| **Certification campaign** | Periodic review where reviewers approve or revoke access | Access review schedule + `access_review.py` | `design/lifecycle.md` §8, `src/access_review.py` |
| **Workflows** | Automations triggered by identity events | Lifecycle flowcharts | `design/lifecycle.md` |

## 2. Joiner / Mover / Leaver in ISC Terms

### Joiner
1. A new employee appears in the **authoritative HR source**.
2. ISC creates an **identity** using the **identity profile**.
3. The identity enters the **active** (or **pre-hire**) **lifecycle state**, which grants **birthright access profiles** (SSO, Email, Slack).
4. **Role membership criteria** (e.g., `role = AP Clerk`) automatically assign the matching **role**, which provisions its access profiles.
5. High-risk or privileged access not covered by a role goes through an **access request** with approvals.

### Mover (Priya: AP Clerk → Finance Manager)
1. HR updates Priya's role attribute in the authoritative source.
2. **Role membership criteria** are re-evaluated: she gains the Finance Manager role and **loses the AP Clerk role**, so `ERP:CreateVendor` and `ERP:EnterInvoice` are removed.
3. **SoD policies** for SOD-01 and SOD-02 would flag any remaining conflict with `ERP:ApprovePayment`.
4. A **workflow** could notify her new manager to review her access.

### Leaver
1. HR marks the employee terminated.
2. The identity moves to the **terminated lifecycle state**, which is configured to **disable source accounts** and remove access.
3. Access profiles granted by the previous lifecycle state are revoked when the identity leaves that state.

## 3. Preventive vs. Detective Controls

The most important difference between the lab and a real ISC deployment:

| | SailPoint ISC | This lab |
|---|---|---|
| **Type of control** | Mostly **preventive**: removes or blocks access automatically when lifecycle state or role changes | **Detective**: finds problems after they exist |
| **Mover leftovers** | Role removal revokes old access automatically | `access_review.py` flags access not in the current role |
| **Leavers** | Terminated lifecycle state disables accounts | Script flags terminated users with access |
| **SoD** | Policies flag violations during requests and reviews | Script flags conflicting pairs |
| **Reviews** | Certification campaigns with reviewer decisions | Findings report grouped by manager |

In practice, organizations need both. Automated provisioning prevents most issues, and access reviews catch what slips through, such as manual grants made directly in a system, failed deprovisioning, or exceptions that were never removed. The lab's planted issues represent exactly those gaps.

## 4. How Nittany Analytics Would Be Configured in ISC

| ISC component | Configuration |
|---|---|
| Authoritative source | HR system (`employees.csv`) |
| Other sources | SSO/Directory, Email, Slack, ERP, Payroll, HRIS, GitHub, AWS |
| Identity profile | One profile for all employees |
| Lifecycle states | **Active**: grant birthright access profiles. **Terminated**: disable all source accounts, remove all access |
| Access profiles | One per system per role need, e.g. "ERP – Accounts Payable" (`CreateVendor`, `EnterInvoice`) |
| Roles | 6 roles, auto-assigned with membership criteria on the role attribute |
| SoD policies | SOD-01 to SOD-04 |
| Certification campaigns | Manager review semi-annually; privileged access quarterly |

## 5. References

- SailPoint ISC documentation: Setting Up Lifecycle States — https://documentation.sailpoint.com/saas/help/provisioning/lifecycle.html
- SailPoint Developer Community: Lifecycle States API — https://developer.sailpoint.com/docs/api/v3/lifecycle-states
- SailPoint ISC documentation home — https://documentation.sailpoint.com
