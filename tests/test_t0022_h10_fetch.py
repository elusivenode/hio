"""The H.10 one-off fetch, on a fake getter only."""

import importlib.util
import json
from pathlib import Path

import pytest

from hio.contracts.rights import Operation, RightsRefused
from hio.rights.gate import GateContext, RightsGate
from hio.rights.register import load_genuine

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("h10_fetch", REPO / "tools" / "h10_fetch.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)
GATE = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"))
ZIP = b"PK\x03\x04invented"


def test_one_request_and_a_manifest(tmp_path):
    calls = []

    def get(url):
        calls.append(url)
        return 200, ZIP

    manifest = tool.fetch(tmp_path / "out", gate=GATE, commit="c", get=get)
    assert calls == [tool.URL]
    assert manifest["notice"].startswith("Source: Board of Governors")
    assert (tmp_path / "out" / "FRB_h10_xml.zip").read_bytes() == ZIP
    assert json.loads((tmp_path / "out" / "manifest.json").read_text())["sha256"] == manifest["sha256"]


def test_a_used_output_refuses_so_a_rerun_cannot_download_again(tmp_path):
    tool.fetch(tmp_path / "out", gate=GATE, commit="c", get=lambda _u: (200, ZIP))
    with pytest.raises(ValueError, match="absent or empty"):
        tool.fetch(tmp_path / "out", gate=GATE, commit="c", get=lambda _u: pytest.fail("requested"))


@pytest.mark.parametrize("answer, why", [((404, b""), "HTTP 404"), ((200, b"<html>"), "not a zip")])
def test_a_surprise_writes_nothing(tmp_path, answer, why):
    with pytest.raises(ValueError, match=why):
        tool.fetch(tmp_path / "out", gate=GATE, commit="c", get=lambda _u: answer)
    assert not (tmp_path / "out").exists()


def test_inside_the_repository_refuses():
    with pytest.raises(ValueError, match="outside the repository"):
        tool.fetch(REPO / "data" / "h10", gate=GATE, commit="c", get=lambda _u: pytest.fail("requested"))


def test_the_gate_allows_this_series_and_still_refuses_the_parent_and_consumers():
    for op in (
        Operation.FETCH,
        Operation.STORE_RAW,
        Operation.BUILD,
        Operation.STORE_DERIVED,
        Operation.REBUILD,
    ):
        GATE.authorise(op, [tool.SOURCE_ID])
    GATE.authorise(Operation.PUBLISH, [tool.SOURCE_ID], "hio_internal")
    with pytest.raises(RightsRefused):
        GATE.authorise(Operation.PUBLISH, [tool.SOURCE_ID], "smsf_trustee_pack")
    with pytest.raises(RightsRefused, match="verification is unverified"):
        GATE.authorise(Operation.FETCH, ["frb_h10"])
    RightsGate(GATE.records, GateContext(on_external_host=True)).authorise(Operation.BUILD, [tool.SOURCE_ID])
