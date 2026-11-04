"""T-0020 X-3: the one-off fetch, on a fake getter only. Nothing here touches the network."""

import importlib.util
import json
from pathlib import Path

import pytest

from hio.contracts.rights import Operation, RightsRefused
from hio.rights.gate import RightsGate
from hio.rights.register import load_genuine

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("treasury_par_fetch", REPO / "tools" / "treasury_par_fetch.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)
GATE = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"))
BODY = b"<feed><entry>invented</entry></feed>"


def getter(calls, answers=None):
    def get(url):
        calls.append(url)
        return (answers or {}).get(len(calls), (200, BODY))

    return get


def run(tmp_path, years, get, gate=GATE):
    return tool.fetch(tmp_path / "out", years, gate=gate, commit="c" * 40, get=get, pause=0)


def test_the_gate_allows_fetch_and_raw_storage_but_nothing_else_yet():
    GATE.authorise(Operation.FETCH, [tool.SOURCE_ID])
    GATE.authorise(Operation.STORE_RAW, [tool.SOURCE_ID])
    for op in (Operation.BUILD, Operation.STORE_DERIVED, Operation.REBUILD):
        with pytest.raises(RightsRefused):
            GATE.authorise(op, [tool.SOURCE_ID])


def test_the_parent_row_still_refuses_bills_and_all():
    with pytest.raises(RightsRefused, match="verification is unverified"):
        GATE.authorise(Operation.FETCH, ["us_treasury_rates"])


def test_one_request_a_year_with_the_manifest(tmp_path):
    calls = []
    manifest = run(tmp_path, [1990, 1991], getter(calls))
    assert len(calls) == 2 and "field_tdr_date_value=1990" in calls[0]
    assert manifest["stopped"] is None
    assert manifest["notice"].startswith("Source: US Department of the Treasury")
    stored = json.loads((tmp_path / "out" / "manifest.json").read_text())
    assert [f["year"] for f in stored["files"]] == [1990, 1991]
    assert (tmp_path / "out" / "raw" / "1990.xml").read_bytes() == BODY


def test_over_the_limit_refuses_before_any_request(tmp_path):
    calls = []
    with pytest.raises(ValueError, match="over the limit"):
        run(tmp_path, list(range(1950, 1991)), getter(calls))
    assert calls == []


@pytest.mark.parametrize(
    "answer, why", [((500, b""), "HTTP 500"), ((200, b"<html>no</html>"), "not the expected")]
)
def test_the_first_surprise_stops_with_no_retry_and_keeps_what_it_has(tmp_path, answer, why):
    calls = []
    manifest = run(tmp_path, [1990, 1991, 1992], getter(calls, {2: answer}))
    assert len(calls) == 2
    assert why in manifest["stopped"]
    assert [f["year"] for f in manifest["files"]] == [1990]


def test_a_network_error_stops_and_names_only_its_type(tmp_path):
    def broken(_url):
        raise TimeoutError("provider text")

    manifest = run(tmp_path, [1990], broken)
    assert manifest["stopped"] == "1990: TimeoutError"


def test_a_used_output_refuses_so_a_rerun_cannot_download_again(tmp_path):
    run(tmp_path, [1990], getter([]))
    calls = []
    with pytest.raises(ValueError, match="absent or empty"):
        run(tmp_path, [1990], getter(calls))
    assert calls == []


def test_output_inside_the_repository_refuses():
    with pytest.raises(ValueError, match="outside the repository"):
        tool.check_output(REPO / "data" / "e0001")


def test_a_refused_gate_stops_before_any_request(tmp_path):
    calls = []
    with pytest.raises(RightsRefused):
        run(tmp_path, [1990], getter(calls), gate=RightsGate({}))
    assert calls == []
