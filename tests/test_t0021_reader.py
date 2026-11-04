"""T-0021: the research reader's refusals and its one success, on S1a's synthetic releases only."""

import importlib.util
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from hio.contracts.rights import RightsRefused
from hio.contracts.status import Status
from hio.contracts.temporal import KnowledgeMode
from hio.publish.lineage import LineageError
from hio.publish.status import RefusedUse, append_status
from hio.rights.gate import RightsGate
from hio.storage.objectstore import IntegrityError
from tests.test_t0014_consumer_contract import AUD, CUTOFF, RIGHTS, USD, build, rights_with

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("research_reader", REPO / "tools" / "research_reader.py")
reader = importlib.util.module_from_spec(_spec)
sys.modules["research_reader"] = reader
_spec.loader.exec_module(reader)

MODE = KnowledgeMode.AS_CAPTURED_BY_HIO
FX = "fx.usd_cash_vs_aud.excess"


@pytest.fixture
def world(tmp_path):
    return build(tmp_path)


def pin(releases, sleeve, dataset_id, **kw):
    return reader.Pin(sleeve, dataset_id, releases[dataset_id].content_sha256, **kw)


def read(store, pins, *, mode=MODE, cutoff=CUTOFF, gate=None):
    return reader.read_panel(store, pins, mode=mode, cutoff=cutoff, gate=gate or RightsGate(RIGHTS))


def test_a_pinned_read_aligns_and_says_what_it_read(world):
    store, releases = world
    panel, record = read(store, [pin(releases, "x", USD), pin(releases, "y", USD)])
    assert panel.sleeves == ("x", "y")
    assert panel.returns.shape == (len(panel.dates) - 1, 2)
    assert {r["content_sha256"] for r in record} == {releases[USD].content_sha256}
    assert {r["knowledge_mode"] for r in record} == {MODE.value}


def test_the_wrong_hash_refuses(world):
    store, _ = world
    with pytest.raises((RefusedUse, LineageError)):
        read(store, [reader.Pin("x", USD, "0" * 64)])


def test_a_hash_of_another_dataset_refuses(world):
    store, releases = world
    with pytest.raises(RefusedUse, match="belongs to"):
        read(store, [reader.Pin("x", USD, releases[AUD].content_sha256)])


def test_tampered_bytes_refuse(world):
    store, releases = world
    target = store.root / f"{releases[USD].prefix}/data.csv"
    target.chmod(0o644)
    target.write_bytes(target.read_bytes().replace(b"0.0", b"0.1", 1))
    with pytest.raises((LineageError, IntegrityError)):
        read(store, [pin(releases, "x", USD)])


def test_a_withdrawn_release_refuses_at_the_next_read(world):
    store, releases = world
    read(store, [pin(releases, "x", USD)])
    sha = releases[USD].content_sha256
    append_status(store, sha, Status.WITHDRAWN, "owner", "test", datetime(2026, 2, 1, tzinfo=UTC))
    with pytest.raises(RefusedUse, match="withdrawn"):
        read(store, [pin(releases, "x", USD)])


def test_current_rights_are_rechecked_and_refuse(world):
    store, releases = world
    denied = rights_with(distribution__hio_internal="deny")
    with pytest.raises(RightsRefused):
        read(store, [pin(releases, "x", USD)], gate=denied)


def test_another_knowledge_mode_refuses(world):
    store, releases = world
    with pytest.raises(reader.ReaderRefused, match="not the requested latest"):
        read(store, [pin(releases, "x", USD)], mode=KnowledgeMode.LATEST)


def test_another_cutoff_refuses(world):
    store, releases = world
    with pytest.raises(reader.ReaderRefused, match="knowledge cutoff"):
        read(store, [pin(releases, "x", USD)], cutoff=datetime(2026, 1, 28, tzinfo=UTC))


@pytest.mark.parametrize("basis", ["schedule_only", "rule_inferred"])
def test_a_weak_basis_can_never_be_read_as_market_knowledge(basis):
    core = {
        "dataset_id": "d",
        "knowledge_mode": "as_known_by_market",
        "knowledge_cutoff": "2026-01-29T00:00:00.000000Z",
        "weakest_knowable_basis": basis,
    }
    with pytest.raises(reader.ReaderRefused, match="can't support"):
        reader.check_knowledge(core, KnowledgeMode.AS_KNOWN_BY_MARKET, CUTOFF)


@pytest.mark.parametrize("declared", ["latest", "reconstructed"])
def test_latest_or_reconstructed_data_is_never_point_in_time(declared):
    core = {
        "dataset_id": "d",
        "knowledge_mode": declared,
        "knowledge_cutoff": "2026-01-29T00:00:00.000000Z",
        "weakest_knowable_basis": "captured_on_schedule",
    }
    for asked in (KnowledgeMode.AS_KNOWN_BY_MARKET, KnowledgeMode.AS_CAPTURED_BY_HIO):
        with pytest.raises(reader.ReaderRefused, match="not the requested"):
            reader.check_knowledge(core, asked, CUTOFF)


def test_mixed_numeraires_refuse(world):
    store, releases = world
    with pytest.raises(reader.ReaderRefused, match="mixed numeraires"):
        read(store, [pin(releases, "aud", AUD), pin(releases, "usd", USD)])


def test_mixed_series_classes_refuse(world):
    store, releases = world
    with pytest.raises(reader.ReaderRefused, match="mixed series classes"):
        read(store, [pin(releases, "aud", AUD), pin(releases, "fx", FX, return_column="X")])


def test_a_series_that_is_not_a_return_refuses():
    with pytest.raises(reader.ReaderRefused, match="not a return series"):
        reader.check_basis({"p": ("price_only", "USD")})


def test_a_missing_column_refuses(world):
    store, releases = world
    with pytest.raises(reader.ReaderRefused, match="no column"):
        read(store, [pin(releases, "x", USD, return_column="nope")])


def test_a_missing_file_refuses(world):
    store, releases = world
    with pytest.raises(reader.ReaderRefused, match="no file"):
        read(store, [pin(releases, "x", USD, data_file="other.csv")])


def test_one_sleeve_named_twice_refuses(world):
    store, releases = world
    with pytest.raises(reader.ReaderRefused, match="one sleeve"):
        read(store, [pin(releases, "x", USD), pin(releases, "x", AUD)])


def test_the_run_record_holds_identities_and_counts_but_no_value(world):
    store, releases = world
    panel, record = read(store, [pin(releases, "x", USD)])
    code = {"commit": "c" * 40, "lock_sha256": "l" * 64}
    body = reader.run_record(record, panel, parameters={"seed": 1}, code=code)
    loaded = json.loads(body)
    assert loaded["code"] == code
    assert loaded["parameters"] == {"seed": 1}
    assert loaded["periods"] == panel.returns.shape[0]
    text = json.dumps(loaded)
    assert not any(f"{value:.6f}"[:8] in text for value in panel.returns[:, 0] if abs(value) > 1e-3)
    assert reader.run_record(record, panel, parameters={"seed": 1}, code=code) == body


def test_a_dirty_tree_refuses_a_code_identity(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "uv.lock").write_text("x")
    with pytest.raises(ValueError, match="uncommitted"):
        reader.code_identity(tmp_path)


def test_capture_does_not_import_numpy_or_the_portfolio_package():
    """NumPy reaches capture's environment through the lock (OD-0159); it must not reach its code."""
    probe = (
        "import sys; import hio.jobs.s1b1_capture; "
        "bad = [m for m in sys.modules if m == 'numpy' or m.startswith('hio.portfolio')]; "
        "print(bad); sys.exit(1 if bad else 0)"
    )
    done = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr


def test_the_portfolio_package_imports_no_other_hio_package():
    source = (REPO / "src" / "hio" / "portfolio" / "fixed_allocation.py").read_text()
    assert "from hio" not in source
    assert "import hio" not in source
