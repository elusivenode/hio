"""Factor construction from released observations, per spec (return accounting standard).

Pure computation: imports contracts and reference only, never storage or publish
(architecture §1). Arithmetic is Decimal at 50 significant digits, so identities that the
standard calls exact hold to far better than its 1e-12 tolerance.
"""
