"""Publication: the only code that writes releases, artefacts and status events (architecture §1).

Every write is preceded by the rights gate, and multi-object writes are staged, so a refusal
leaves no partial output (rights standard §3).
"""
