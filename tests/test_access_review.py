"""
Tests for the access review script.

Regenerates the sample data, runs the review, and checks the results
against the answer key in docs/expected-findings.md.

Run:  python -m pytest -v
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import access_review as ar  # noqa: E402


@pytest.fixture(scope="module")
def findings():
    # Regenerate data so dates are relative to today
    subprocess.run([sys.executable, str(ROOT / "src" / "generate_data.py")], check=True)
    return ar.run_review(*ar.load_data())


def rows(findings, check):
    subset = findings[findings["check"] == check]
    return set(zip(subset["employee_id"], subset["entitlement"]))


def test_total_findings(findings):
    assert len(findings) == 16


def test_leaver_still_has_access(findings):
    leaver = findings[findings["check"] == "Leaver still has access"]
    assert set(leaver["employee_id"]) == {"E017"}
    assert len(leaver) == 7
    assert (leaver["severity"] == "Critical").all()


def test_access_not_in_role(findings):
    assert rows(findings, "Access not in current role") == {
        ("E016", "ERP:CreateVendor"),    # mover leftover
        ("E016", "ERP:EnterInvoice"),    # mover leftover
        ("E019", "ERP:ViewReports"),     # privilege creep
        ("E020", "Directory:ManageUsers"),
    }


def test_unused_access(findings):
    assert rows(findings, "Unused access") == {
        ("E010", "AWS:Developer"),
        ("E014", "AWS:Admin"),
    }


def test_privileged_unused_access_is_high(findings):
    stale_admin = findings[(findings["check"] == "Unused access")
                           & (findings["entitlement"] == "AWS:Admin")]
    assert stale_admin["severity"].iloc[0] == "High"


def test_sod_conflicts(findings):
    sod = findings[findings["check"] == "SoD conflict"]
    found = {(eid, detail.split(":")[0]) for eid, detail in zip(sod["employee_id"], sod["detail"])}
    assert found == {("E016", "SOD-01"), ("E016", "SOD-02"), ("E020", "SOD-04")}


def test_correctly_offboarded_leaver_not_flagged(findings):
    # Control case: E018 left and was offboarded properly
    assert "E018" not in set(findings["employee_id"])
