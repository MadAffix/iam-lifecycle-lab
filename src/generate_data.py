"""
Generate sample HR and access data for the IAM lifecycle lab.

Creates:
  data/employees.csv  - the HR "source of truth"
  data/access.csv     - what access each person actually has

Most access follows the role matrix correctly. A few problems are planted
on purpose so the access review script (Step 5) has something to find.
See docs/expected-findings.md for the full answer key.

Run from anywhere:  python src/generate_data.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

# Fixed seeds so the same data is generated every run
random.seed(42)
Faker.seed(42)
fake = Faker()

TODAY = date.today()
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def days_ago(n):
    return (TODAY - timedelta(days=n)).isoformat()


# ---------------------------------------------------------------------------
# 1. Load the role matrix (from Step 2)
# ---------------------------------------------------------------------------
role_matrix = {}
with open(DATA_DIR / "role_matrix.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        role_matrix.setdefault(row["role"], []).append(row["entitlement"])

BIRTHRIGHT = role_matrix.pop("*")  # SSO, Email, Slack for everyone

# ---------------------------------------------------------------------------
# 2. Employee roster
#    (id, role, department, manager_id, status, terminated_days_ago, name)
# ---------------------------------------------------------------------------
ROSTER = [
    ("E001", "Finance Manager",     "Finance",     "",     "active",     None, None),
    ("E002", "Engineering Manager", "Engineering", "",     "active",     None, None),
    ("E003", "AP Clerk",            "Finance",     "E001", "active",     None, None),
    ("E004", "AP Clerk",            "Finance",     "E001", "active",     None, None),
    ("E005", "AP Clerk",            "Finance",     "E001", "active",     None, None),
    ("E006", "HR Specialist",       "HR",          "E001", "active",     None, None),
    ("E007", "HR Specialist",       "HR",          "E001", "active",     None, None),
    ("E008", "Software Engineer",   "Engineering", "E002", "active",     None, None),
    ("E009", "Software Engineer",   "Engineering", "E002", "active",     None, None),
    ("E010", "Software Engineer",   "Engineering", "E002", "active",     None, None),
    ("E011", "Software Engineer",   "Engineering", "E002", "active",     None, None),
    ("E012", "Software Engineer",   "Engineering", "E002", "active",     None, None),
    ("E013", "Software Engineer",   "Engineering", "E002", "active",     None, None),
    ("E014", "IT Administrator",    "IT",          "E002", "active",     None, None),
    ("E015", "IT Administrator",    "IT",          "E002", "active",     None, None),
    # Planted: mover. Promoted from AP Clerk, kept old access (see lifecycle.md)
    ("E016", "Finance Manager",     "Finance",     "E001", "active",     None, "Priya Shah"),
    # Planted: leaver who still has access
    ("E017", "Software Engineer",   "Engineering", "E002", "terminated", 30,   None),
    # Control case: leaver offboarded correctly. Should produce NO findings
    ("E018", "AP Clerk",            "Finance",     "E001", "terminated", 60,   None),
    # Planted: privilege creep (gets an extra entitlement below)
    ("E019", "Software Engineer",   "Engineering", "E002", "active",     None, None),
    # Planted: SoD conflict (gets an extra entitlement below)
    ("E020", "HR Specialist",       "HR",          "E001", "active",     None, None),
]

employees = []
for eid, role, dept, mgr, status, term_ago, name in ROSTER:
    employees.append({
        "employee_id": eid,
        "name": name or fake.name(),
        "department": dept,
        "role": role,
        "manager_id": mgr,
        "status": status,
        "termination_date": days_ago(term_ago) if term_ago else "",
    })

# ---------------------------------------------------------------------------
# 3. Correct access: birthright + role entitlements
# ---------------------------------------------------------------------------
access = []


def grant(eid, entitlement, granted_ago=None, used_ago=None):
    access.append({
        "employee_id": eid,
        "system": entitlement.split(":")[0],
        "entitlement": entitlement,
        "granted_date": days_ago(granted_ago or random.randint(100, 700)),
        "last_used": days_ago(used_ago if used_ago is not None else random.randint(0, 60)),
    })


for emp in employees:
    eid = emp["employee_id"]
    if eid == "E018":
        continue  # correctly offboarded: no access left
    used = 35 if eid == "E017" else None  # leaver hasn't logged in since leaving
    for ent in BIRTHRIGHT + role_matrix[emp["role"]]:
        grant(eid, ent, used_ago=used)

# ---------------------------------------------------------------------------
# 4. Planted problems
# ---------------------------------------------------------------------------
# Mover: Priya kept her AP Clerk access -> not in role + SOD-01 + SOD-02
grant("E016", "ERP:CreateVendor", granted_ago=500)
grant("E016", "ERP:EnterInvoice", granted_ago=500)

# Privilege creep: engineer has finance reporting access
grant("E019", "ERP:ViewReports", granted_ago=200)

# SoD: HR Specialist can also manage directory accounts -> SOD-04
grant("E020", "Directory:ManageUsers", granted_ago=150)

# Stale access: not used in 90+ days
for row in access:
    if (row["employee_id"], row["entitlement"]) in {("E010", "AWS:Developer"),
                                                     ("E014", "AWS:Admin")}:
        row["granted_date"] = days_ago(400)
        row["last_used"] = days_ago(200 if row["employee_id"] == "E010" else 150)

# ---------------------------------------------------------------------------
# 5. Write the CSVs
# ---------------------------------------------------------------------------
def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


write_csv(DATA_DIR / "employees.csv", employees)
write_csv(DATA_DIR / "access.csv", access)

print(f"Wrote {len(employees)} employees to data/employees.csv")
print(f"Wrote {len(access)} access records to data/access.csv")
