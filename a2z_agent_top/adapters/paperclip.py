"""
Paperclip Company OS Adapter.
Integrates with AAH20/paperclip and hermes-paperclip-adapter to monitor AI employees, departments, and budgets.
"""

from __future__ import annotations

import os
import json
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class EmployeeAgent:
    """An AI agent managed as an employee within Paperclip Company OS."""
    id: str
    name: str
    department: str
    role: str
    ticket_id: str
    status: str  # ACTIVE, IDLE, BLOCKED, REVIEWING
    budget_usd: float
    spent_usd: float
    active_pid: Optional[int] = None
    assigned_skills: List[str] = field(default_factory=list)

    @property
    def budget_util_pct(self) -> float:
        if self.budget_usd <= 0:
            return 0.0
        return min(100.0, (self.spent_usd / self.budget_usd) * 100.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "role": self.role,
            "ticket_id": self.ticket_id,
            "status": self.status,
            "budget_usd": self.budget_usd,
            "spent_usd": round(self.spent_usd, 2),
            "budget_util_pct": round(self.budget_util_pct, 1),
            "active_pid": self.active_pid,
            "assigned_skills": self.assigned_skills,
        }


class PaperclipAdapter:
    """
    Adapter for Paperclip Company OS (github.com/AAH20/paperclip).
    Discovers employees, departments, tickets, and corporate spend burn.
    """

    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self._lock = threading.Lock()
        self._employees: List[EmployeeAgent] = []
        if self.demo_mode:
            self._seed_demo_company()

    def _seed_demo_company(self) -> None:
        """Seed representative corporate hierarchy from Paperclip OS."""
        self._employees = [
            EmployeeAgent(
                id="emp-001",
                name="Hermes Lead Architect",
                department="Engineering",
                role="Principal Systems Architect",
                ticket_id="ENG-1049 (Kernel Zeroize)",
                status="ACTIVE",
                budget_usd=500.0,
                spent_usd=142.50,
                active_pid=41021,
                assigned_skills=["arch_design", "code_review", "system_audit"],
            ),
            EmployeeAgent(
                id="emp-002",
                name="Hermes Matrix Auditor",
                department="Security & GRC",
                role="AI Security Assessor",
                ticket_id="SEC-302 (ActionLedger Merkle Check)",
                status="ACTIVE",
                budget_usd=300.0,
                spent_usd=88.20,
                active_pid=41022,
                assigned_skills=["grc_eval", "sql_inspector", "crypto_sign"],
            ),
            EmployeeAgent(
                id="emp-003",
                name="Codex Refactor Specialist",
                department="Engineering",
                role="Core Systems Dev",
                ticket_id="ENG-1082 (Radix LCP Cache Optimization)",
                status="ACTIVE",
                budget_usd=600.0,
                spent_usd=312.40,
                active_pid=41023,
                assigned_skills=["ast_rewrite", "pytest_runner", "git_blame"],
            ),
            EmployeeAgent(
                id="emp-004",
                name="Sovereign Compliance Agent",
                department="Legal & Compliance",
                role="Regulatory Verifier",
                ticket_id="REG-104 (EU AI Act Sovereign Gate)",
                status="REVIEWING",
                budget_usd=250.0,
                spent_usd=45.00,
                active_pid=None,
                assigned_skills=["policy_diff", "pdf_parse"],
            ),
            EmployeeAgent(
                id="emp-005",
                name="Adversarial RedTeam Fuzzer",
                department="Security & GRC",
                role="Automated Penetration Tester",
                ticket_id="SEC-991 (MCP Gateway Stress Test)",
                status="BLOCKED",
                budget_usd=400.0,
                spent_usd=388.90,
                active_pid=41025,
                assigned_skills=["prompt_fuzz", "tool_shadow_probe"],
            ),
        ]

    def get_employees(self) -> List[EmployeeAgent]:
        with self._lock:
            return list(self._employees)

    def get_department_spend_summary(self) -> Dict[str, Dict[str, float]]:
        """Returns spend and budget totals aggregated by department."""
        summary: Dict[str, Dict[str, float]] = {}
        with self._lock:
            for emp in self._employees:
                if emp.department not in summary:
                    summary[emp.department] = {"spent": 0.0, "budget": 0.0}
                summary[emp.department]["spent"] += emp.spent_usd
                summary[emp.department]["budget"] += emp.budget_usd
        return summary
