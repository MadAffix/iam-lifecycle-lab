# Expected Findings (Answer Key)

`src/generate_data.py` creates mostly clean data with a few problems planted on purpose. The access review script (`src/access_review.py`) should find **every planted issue and nothing else**.

## Planted Issues

| # | Employee | Scenario | Planted problem | Lifecycle rule broken |
|---|---|---|---|---|
| 1 | E017 | Leaver | Terminated 30 days ago but still has all 7 entitlements | Leavers must have zero access |
| 2 | E016 (Priya Shah) | Mover | Promoted AP Clerk → Finance Manager, kept `ERP:CreateVendor` and `ERP:EnterInvoice` | Movers lose old-role access |
| 3 | E016 (Priya Shah) | SoD | `ERP:CreateVendor` + `ERP:ApprovePayment` (SOD-01) and `ERP:EnterInvoice` + `ERP:ApprovePayment` (SOD-02) | SoD checked before granting |
| 4 | E019 | Privilege creep | Software Engineer holds `ERP:ViewReports` | Access follows the role |
| 5 | E020 | SoD | HR Specialist holds `Directory:ManageUsers`, combined with `HRIS:EditEmployee` (SOD-04, "ghost employee") | SoD checked before granting |
| 6 | E010 | Stale access | `AWS:Developer` unused for 200 days | Access is reviewed and used |
| 7 | E014 | Stale privileged access | `AWS:Admin` unused for 150 days | Access is reviewed and used |

## Control Case

| Employee | Scenario | Expected result |
|---|---|---|
| E018 | Leaver offboarded correctly (no access) | **No findings.** Proves the script doesn't produce false positives |

## Expected Finding Counts

| Check | Findings | Who |
|---|---|---|
| Leaver still has access | 7 | E017 (one per entitlement) |
| Not in role matrix | 4 | E016 ×2, E019, E020 |
| Unused 90+ days | 2 | E010, E014 |
| SoD conflict | 3 | E016 ×2, E020 |
| **Total** | **16** | 6 employees |

The SoD count assumes the script includes all four SoD rules from `org-model.md`, not just SOD-01.
