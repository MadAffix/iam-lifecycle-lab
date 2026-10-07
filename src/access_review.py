"""
Access review script for the IAM lifecycle lab.

Compares what access people actually have (data/access.csv) against the
HR source of truth (data/employees.csv) and the role matrix
(data/role_matrix.csv), and flags:

  1. Leavers who still have access
  2. Access not allowed for the person's current role
     (mover leftovers, privilege creep)
  3. Access unused for 90+ days
  4. Separation-of-duties (SoD) conflicts

Results are written to output/access_review_findings.csv.

Run:  python src/access_review.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"

STALE_DAYS = 90

# From design/org-model.md, section 5
SOD_RULES = [
    ("SOD-01", "ERP:CreateVendor", "ERP:ApprovePayment", "Could create a fake vendor and pay it"),
    ("SOD-02", "ERP:EnterInvoice", "ERP:ApprovePayment", "Could enter and approve their own invoice"),
    ("SOD-03", "Payroll:Edit", "Payroll:Approve", "Could change pay and approve the payroll run"),
    ("SOD-04", "HRIS:EditEmployee", "Directory:ManageUsers", "Could create a ghost employee and give it access"),
]

# From design/org-model.md, section 6
PRIVILEGED = {"Directory:ManageUsers", "Payroll:Approve", "GitHub:Admin", "AWS:Admin"}

SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
COLUMNS = ["employee_id", "name", "role", "manager_id", "check",
           "entitlement", "severity", "detail"]


def load_data(data_dir=DATA_DIR):
    """Load the three input CSVs."""
    employees = pd.read_csv(data_dir / "employees.csv", dtype=str, keep_default_na=False)
    access = pd.read_csv(data_dir / "access.csv", dtype=str, keep_default_na=False)
    matrix = pd.read_csv(data_dir / "role_matrix.csv", dtype=str, keep_default_na=False)
    access["last_used"] = pd.to_datetime(access["last_used"])
    return employees, access, matrix


def make_finding(row, check, entitlement, severity, detail):
    return {
        "employee_id": row["employee_id"],
        "name": row["name"],
        "role": row["role"],
        "manager_id": row["manager_id"],
        "check": check,
        "entitlement": entitlement,
        "severity": severity,
        "detail": detail,
    }


def check_leavers(df):
    """Rule: leavers must have zero access."""
    findings = []
    for _, r in df[df["status"] == "terminated"].iterrows():
        findings.append(make_finding(
            r, "Leaver still has access", r["entitlement"], "Critical",
            f"Terminated on {r['termination_date']}"))
    return findings


def check_role_matrix(df, matrix):
    """Rule: access follows the role (catches mover leftovers and privilege creep)."""
    allowed = set(zip(matrix["role"], matrix["entitlement"]))
    findings = []
    for _, r in df[df["status"] == "active"].iterrows():
        ent = r["entitlement"]
        if (r["role"], ent) not in allowed and ("*", ent) not in allowed:
            severity = "High" if ent in PRIVILEGED else "Medium"
            findings.append(make_finding(
                r, "Access not in current role", ent, severity,
                f"Not in role matrix for {r['role']}"))
    return findings


def check_stale(df, today):
    """Rule: access should be used. Flags access unused for STALE_DAYS or more."""
    active = df[df["status"] == "active"].copy()
    active["days_unused"] = (today - active["last_used"]).dt.days
    findings = []
    for _, r in active[active["days_unused"] >= STALE_DAYS].iterrows():
        severity = "High" if r["entitlement"] in PRIVILEGED else "Low"
        findings.append(make_finding(
            r, "Unused access", r["entitlement"], severity,
            f"Not used in {r['days_unused']} days"))
    return findings


def check_sod(df):
    """Rule: no one may hold both entitlements in an SoD pair."""
    findings = []
    active = df[df["status"] == "active"]
    for _, group in active.groupby("employee_id"):
        held = set(group["entitlement"])
        person = group.iloc[0]
        for rule_id, a, b, risk in SOD_RULES:
            if a in held and b in held:
                findings.append(make_finding(
                    person, "SoD conflict", f"{a} + {b}", "High",
                    f"{rule_id}: {risk}"))
    return findings


def run_review(employees, access, matrix, today=None):
    """Run all checks and return findings as a DataFrame, most severe first."""
    if today is None:
        today = pd.Timestamp.today().normalize()

    df = access.merge(employees, on="employee_id", how="left")

    findings = (check_leavers(df)
                + check_role_matrix(df, matrix)
                + check_stale(df, today)
                + check_sod(df))

    result = pd.DataFrame(findings, columns=COLUMNS)
    result["_order"] = result["severity"].map(SEVERITY_ORDER)
    return (result.sort_values(["_order", "employee_id"])
                  .drop(columns="_order")
                  .reset_index(drop=True))


def main():
    employees, access, matrix = load_data()
    findings = run_review(employees, access, matrix)

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / "access_review_findings.csv"
    findings.to_csv(out_path, index=False)

    print(f"Access review complete: {len(findings)} findings "
          f"across {findings['employee_id'].nunique()} employees\n")
    print("By check:")
    print(findings["check"].value_counts().to_string(), "\n")
    print("By severity:")
    print(findings["severity"].value_counts()
          .reindex(SEVERITY_ORDER.keys(), fill_value=0).to_string(), "\n")
    print(f"Full report saved to {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
