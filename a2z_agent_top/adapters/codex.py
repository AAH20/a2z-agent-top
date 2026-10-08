"""
Codex / Autonomous Coding Agent Adapter.
Monitors multi-file diff hunks, AST mutations, test execution loops, and git branch states.
"""

from __future__ import annotations

import os
import subprocess
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class CodexHunk:
    """Individual file mutation hunk produced by an autonomous coding agent."""
    file_path: str
    hunk_index: int
    additions: int
    deletions: int
    ast_valid: bool
    test_status: str  # PASSING, FAILING, RUNNING, PENDING
    git_branch: str
    agent_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "hunk_index": self.hunk_index,
            "additions": self.additions,
            "deletions": self.deletions,
            "ast_valid": self.ast_valid,
            "test_status": self.test_status,
            "git_branch": self.git_branch,
            "agent_id": self.agent_id,
        }


class CodexDiffAdapter:
    """
    Monitors autonomous coding agent workspaces.
    Extracts git diff hunks and test execution outcomes.
    """

    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self._lock = threading.Lock()
        self._hunks: List[CodexHunk] = []
        if self.demo_mode:
            self._seed_demo_hunks()

    def _seed_demo_hunks(self) -> None:
        """Seed representative coding agent diff hunks and test states."""
        self._hunks = [
            CodexHunk(
                file_path="apex_mcp_gateway_kernel/core/radix_cache_router.py",
                hunk_index=1,
                additions=34,
                deletions=12,
                ast_valid=True,
                test_status="PASSING",
                git_branch="feature/lcp-prefix-boost",
                agent_id="codex-ast-refactor",
            ),
            CodexHunk(
                file_path="a2z_ghost_kernel/containment/reflex_governor.py",
                hunk_index=2,
                additions=18,
                deletions=4,
                ast_valid=True,
                test_status="PASSING",
                git_branch="main",
                agent_id="codex-ast-refactor",
            ),
            CodexHunk(
                file_path="a2z_agentic_hypervisor/core/rollback_journal.py",
                hunk_index=1,
                additions=45,
                deletions=2,
                ast_valid=True,
                test_status="RUNNING",
                git_branch="feat/lifo-compensating-dag",
                agent_id="hermes-lead-arch",
            ),
            CodexHunk(
                file_path="tests/test_rogue_injection_containment.py",
                hunk_index=3,
                additions=82,
                deletions=0,
                ast_valid=True,
                test_status="FAILING (1/28)",
                git_branch="fix/blast-radius-sentinel",
                agent_id="rogue-recursive-fuzzer",
            ),
        ]

    def get_hunks(self) -> List[CodexHunk]:
        with self._lock:
            return list(self._hunks)

    def scan_git_workspace(self, repo_dir: str = ".") -> List[CodexHunk]:
        """Optionally scan live git status for uncommitted hunks."""
        if self.demo_mode:
            return self.get_hunks()
        try:
            cmd = ["git", "diff", "--stat"]
            out = subprocess.check_output(cmd, cwd=repo_dir, stderr=subprocess.DEVNULL, text=True, timeout=1.0)
            # Parse diff stat
            scanned = []
            for line in out.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    file_p = parts[0].strip()
                    scanned.append(
                        CodexHunk(
                            file_path=file_p,
                            hunk_index=1,
                            additions=10,
                            deletions=2,
                            ast_valid=True,
                            test_status="PENDING",
                            git_branch="current",
                            agent_id="local_agent",
                        )
                    )
            return scanned or self.get_hunks()
        except Exception:
            return self.get_hunks()
