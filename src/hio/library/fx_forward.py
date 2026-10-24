"""Cash-versus-forward currency positions on the same capital (RA §4.2; RA-INV-021).

These are identities used to normalise a later forward-based triangulation. S1a has no
forward data; the functions are checked against the standard's fixtures only.
"""

from __future__ import annotations

from decimal import Decimal

from hio.library.numeric import CTX

ONE = Decimal(1)


def cip_forward(s0: Decimal, r_home: Decimal, r_foreign: Decimal) -> Decimal:
    """F = S_0 (1 + r^h)/(1 + r^f) under covered interest parity."""
    return CTX.divide(CTX.multiply(s0, CTX.add(ONE, r_home)), CTX.add(ONE, r_foreign))


def funded_cash_excess(s0: Decimal, s_t: Decimal, r_home: Decimal, r_foreign: Decimal) -> Decimal:
    """Excess per unit of home capital K: (1 + r^f) S_T/S_0 − (1 + r^h)."""
    return CTX.subtract(CTX.divide(CTX.multiply(CTX.add(ONE, r_foreign), s_t), s0), CTX.add(ONE, r_home))


def forward_excess_per_capital(s0: Decimal, s_t: Decimal, forward: Decimal, r_foreign: Decimal) -> Decimal:
    """Buy N = K(1 + r^f)/S_0 forward at F: excess per unit of K is (1 + r^f)(S_T − F)/S_0."""
    return CTX.divide(CTX.multiply(CTX.add(ONE, r_foreign), CTX.subtract(s_t, forward)), s0)


def forward_return_per_notional(s_t: Decimal, forward: Decimal) -> Decimal:
    """S_T/F − 1: a return per unit of forward notional, NOT per unit of capital."""
    return CTX.subtract(CTX.divide(s_t, forward), ONE)


def notional_to_capital(per_notional: Decimal, r_home: Decimal) -> Decimal:
    """(1 + r^h)(S_T/F − 1): the normalisation, a certain factor, not market basis."""
    return CTX.multiply(CTX.add(ONE, r_home), per_notional)
