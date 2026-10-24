"""Decimal context and identity checks for constructions."""

from __future__ import annotations

from decimal import Context, Decimal

CTX = Context(prec=50)
# The standard's tolerance is 1e-12 relative unless stated (RA §13). Constructions here carry
# 50 digits, so identities are checked far tighter: any difference above this is a defect.
IDENTITY_TOLERANCE = Decimal("1e-30")


def check_identity(lhs: Decimal, rhs: Decimal) -> Decimal:
    """Return |lhs − rhs|; raise if it exceeds IDENTITY_TOLERANCE."""
    diff = abs(CTX.subtract(lhs, rhs))
    if diff > IDENTITY_TOLERANCE:
        raise ArithmeticError(f"identity broken: {lhs} != {rhs} (diff {diff})")
    return diff
