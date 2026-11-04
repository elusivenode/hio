"""The RBA historical fetch, on a fake getter and invented rows only."""

import importlib.util
from pathlib import Path

import pytest

from hio.contracts.rights import Operation, RightsRefused
from hio.rights.gate import RightsGate
from hio.rights.register import load_genuine

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("rba_history_fetch", REPO / "tools" / "rba_history_fetch.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)
GATE = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"))
XLS = tool.XLS_MAGIC + b"invented"


def test_one_request_and_a_manifest(tmp_path):
    calls = []

    def get(url):
        calls.append(url)
        return 200, XLS

    manifest = tool.fetch(tmp_path / "out", gate=GATE, commit="c", get=get)
    assert calls == [tool.URL] and manifest["notice"].startswith("Source: Reserve Bank")
    assert (tmp_path / "out" / tool.FILE_NAME).read_bytes() == XLS


def test_a_rerun_cannot_download_again(tmp_path):
    tool.fetch(tmp_path / "out", gate=GATE, commit="c", get=lambda _u: (200, XLS))
    with pytest.raises(ValueError, match="absent or empty"):
        tool.fetch(tmp_path / "out", gate=GATE, commit="c", get=lambda _u: pytest.fail("requested"))


@pytest.mark.parametrize("answer, why", [((404, b""), "HTTP 404"), ((200, b"<html>"), "not a spreadsheet")])
def test_a_surprise_writes_nothing(tmp_path, answer, why):
    with pytest.raises(ValueError, match=why):
        tool.fetch(tmp_path / "out", gate=GATE, commit="c", get=lambda _u: answer)
    assert not (tmp_path / "out").exists()


def test_inside_the_repository_refuses():
    with pytest.raises(ValueError, match="outside the repository"):
        tool.fetch(REPO / "data" / "x", gate=GATE, commit="c", get=lambda _u: pytest.fail("requested"))


def test_headers_exclude_data_rows():
    rows = [
        ["Title", "Cash Rate", "Bank bill"],
        ["Source", "RBA", "ASX"],
        ["Series ID", "A", "B"],
        ["01-Jan-2000", "9.99", "8.88"],
    ]
    columns = tool.header_rows(rows)
    assert columns[0] == {"title": "Cash Rate", "source": "RBA", "series id": "A"}
    assert columns[1]["source"] == "ASX"
    assert "9.99" not in str(columns)


def test_the_record_allows_this_file_only_and_no_consumer():
    for op in (Operation.FETCH, Operation.STORE_RAW, Operation.BUILD, Operation.REBUILD):
        GATE.authorise(op, [tool.SOURCE_ID])
    GATE.authorise(Operation.PUBLISH, [tool.SOURCE_ID], "hio_internal")
    with pytest.raises(RightsRefused):
        GATE.authorise(Operation.PUBLISH, [tool.SOURCE_ID], "smsf_trustee_pack")
