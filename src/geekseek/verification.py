from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .workflow import WorkflowContext


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    reason: str = ""
    hint: str = ""


class Verifier(Protocol):
    async def verify(self, frame: bytes | None, context: WorkflowContext) -> VerificationResult: ...


class LocalVerifier:
    """P0 verifier. Alignment stability is established before this is called."""

    async def verify(self, frame: bytes | None, context: WorkflowContext) -> VerificationResult:
        return VerificationResult(passed=True)
