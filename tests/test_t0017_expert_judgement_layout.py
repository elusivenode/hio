"""T-0017: the expert-judgement parser reads the live file's layout (first live run, OD-0145)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from hio.sources.datasets import DATASETS, Flag, MalformedPayload

LAYOUT = (
    Path(__file__).resolve().parent / "fixtures" / "synthetic" / "s1b1" / "rba_expert_judgement_layout.csv"
)
parse = DATASETS["rba.expert_judgement"].parse


def test_prose_before_the_header_is_not_taken_for_the_header():
    assert parse(LAYOUT.read_bytes()).flags == (
        Flag(date(2026, 7, 31), "A"),
        Flag(date(2026, 10, 2), "C"),
    )


def test_a_byte_order_mark_does_not_hide_the_header():
    assert len(parse(b"\xef\xbb\xbf" + LAYOUT.read_bytes()).flags) == 2


@pytest.mark.parametrize(
    "payload",
    [
        b"A paragraph with a date and a type in one cell\n31-Jul-2026,A\n",
        b"Date and type,Other\n31-Jul-2026,A\n",
        b"Date,Other\n31-Jul-2026,A\n",
        b"Date,Expert Judgement type\n31-Jul-2026,Z\n",
    ],
)
def test_anything_else_still_fails_closed_as_schema(payload):
    with pytest.raises(MalformedPayload) as caught:
        parse(payload)
    assert caught.value.error_class == "schema"
