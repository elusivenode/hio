"""T-0014 P-3: the second copy and the restore exercise, on synthetic receipts and fake stores only.

A world is captured, built and published into a local store (and a fake blob store). It is copied with a
sealed inventory, restored into an empty store without the primary, and rebuilt from the pinned code
reference; the manifests and payload bytes are compared, and the catalogue is compared as canonical rows."""

from __future__ import annotations

import importlib.util
import inspect
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from hio.contracts.canonical import canonical_json, instant_str, sha256_hex
from hio.jobs.s1a import publish_releases
from hio.jobs.s1b1 import build_releases
from hio.rights.gate import RightsGate
from hio.rights.register import load_genuine
from hio.storage.blobstore import BlobObjectStore
from hio.storage.fakeblob import FakeBlobBackend
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import AllowAllGate
from tests.test_s1b1_releases import NSW, RITS, build_world

REPO = Path(__file__).resolve().parent.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


second_copy = _load("second_copy")
restore_exercise = _load("restore_exercise")

T_SOURCE = datetime(2026, 10, 30, 1, 0, tzinfo=UTC)
T_COPY = datetime(2026, 11, 2, 2, 0, tzinfo=UTC)
T_RESTORE = datetime(2026, 12, 7, 3, 0, tzinfo=UTC)
RUN = datetime(2026, 11, 2, 2, 30, tzinfo=UTC)


def blob(at: datetime, immutable: bool = True) -> BlobObjectStore:
    return BlobObjectStore(FakeBlobBackend(immutable=immutable, clock=lambda: at))


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    """Receipts, records, vintages and published releases (built with the genuine rights register)."""
    store, cals, vs, cutoff, _allow_all, code, _ = build_world(
        LocalObjectStore(tmp_path_factory.mktemp("primary") / "store")
    )
    rights = load_genuine(REPO / "registers" / "sources.yaml")
    releases = build_releases(vs, RightsGate(rights), rights, cals, cutoff, code)
    publish_releases(vs, AllowAllGate(), releases, cutoff)
    return SimpleNamespace(store=store, cals=cals, cutoff=cutoff, rights=rights, code=code, releases=releases)


@pytest.fixture(scope="module")
def blob_world():
    store, *_ = build_world(blob(T_SOURCE))
    return store


def copy_to(source, dest, clock_at: datetime = RUN) -> dict:
    return second_copy.copy_store(source, dest, label="primary-test", clock=lambda: clock_at)


def sealed(inventory: dict) -> bytes:
    return canonical_json(inventory)


def rebuild_for(world, store):
    def rebuild(pins):
        return restore_exercise.rebuild_s1b1(
            store,
            rits=RITS,
            nsw=NSW,
            rights=world.rights,
            gate=RightsGate(world.rights),
            pins=pins,
            cutoff_at=world.cutoff,
        )

    return rebuild


def a_release_file(store, name: str = "data.csv") -> str:
    return next(k for k in store.list("releases/") if k.endswith(f"/{name}"))


# --- the inventory is complete and sealed -------------------------------------------------------


def test_the_inventory_lists_every_object_with_its_hash_size_and_original_metadata(world, tmp_path):
    inv = copy_to(world.store, LocalObjectStore(tmp_path / "second"))
    snapshot = world.store.snapshot()
    assert [e["key"] for e in inv["entries"]] == sorted(snapshot)
    for e in inv["entries"]:
        assert e["sha256"] == snapshot[e["key"]] and e["size"] == len(world.store.get(e["key"]))
        assert e["provider"]["kind"] == "local-file" and e["copy"]["kind"] == "local-file"
    assert inv["totals"]["objects"] == len(snapshot) and inv["totals"]["bytes"] == sum(
        e["size"] for e in inv["entries"]
    )
    kinds = set(inv["totals"]["by_prefix"])
    assert {"receipts", "releases", "catalogue"} <= kinds  # raw bytes, releases and every catalogue record
    assert second_copy.load_inventory(sealed(inv)) == inv


def test_the_inventory_is_deterministic(blob_world):
    a = copy_to(blob_world, blob(T_COPY))
    b = copy_to(blob_world, blob(T_COPY))
    assert sealed(a) == sealed(b)


@pytest.mark.parametrize("edit", ["entry", "dropped", "totals", "format", "not_canonical"])
def test_an_altered_inventory_is_refused(world, tmp_path, edit):
    inv = copy_to(world.store, LocalObjectStore(tmp_path / "second"))
    if edit == "entry":
        inv["entries"][0]["sha256"] = "0" * 64
    elif edit == "dropped":
        inv["entries"].pop()
    elif edit == "totals":
        inv["totals"]["objects"] += 1
    elif edit == "format":
        inv["format"] = "other"
    raw = sealed(inv) if edit != "not_canonical" else json.dumps(inv, indent=1).encode()
    with pytest.raises(second_copy.InventoryError):
        second_copy.load_inventory(raw)


def test_an_entry_dropped_and_resealed_is_caught_as_an_unlisted_object(world, tmp_path):
    second = LocalObjectStore(tmp_path / "second")
    inv = copy_to(world.store, second)
    dropped = inv["entries"].pop()
    entries = inv["entries"]
    inv = second_copy.seal({**inv, "entries": entries, "totals": second_copy._totals(entries)})
    report = second_copy.check_store(second, inv)
    assert report["unlisted"] == [dropped["key"]] and not report["ok"]


# --- original provider metadata is kept ---------------------------------------------------------


def test_the_copy_keeps_the_original_provider_metadata_and_records_its_own_separately(blob_world):
    second = blob(T_COPY)
    inv = copy_to(blob_world, second)
    for e in inv["entries"]:
        original = blob_world.backend.stat(e["key"])
        assert e["provider"] == {
            "kind": "blob",
            "size": original.size,
            "version_id": original.version_id,
            "written_at": instant_str(T_SOURCE),
        }
        assert e["copy"]["written_at"] == instant_str(T_COPY) != e["provider"]["written_at"]
    assert second.write_time(inv["entries"][0]["key"]) == T_COPY  # the copy's own time is not the original's


def test_a_restore_leaves_the_original_provider_metadata_in_the_inventory(blob_world):
    second, target = blob(T_COPY), blob(T_RESTORE)
    inv = copy_to(blob_world, second)
    report = restore_exercise.restore(second, sealed(inv), target)
    originals = {e["key"]: e["provider"] for e in inv["entries"]}
    assert report["provider_metadata"] == {
        "original_entries": len(originals),
        "original_sha256": sha256_hex(canonical_json(originals)),
        "restored_write_times_are_witnesses": False,
    }
    key = inv["entries"][0]["key"]
    assert target.write_time(key) == T_RESTORE != blob_world.write_time(key)  # a new time, never a witness
    assert all(e["provider"]["written_at"] == instant_str(T_SOURCE) for e in inv["entries"])


def test_audit_references_survive_byte_for_byte(world, tmp_path):
    second, target = LocalObjectStore(tmp_path / "second"), LocalObjectStore(tmp_path / "target")
    inv = copy_to(world.store, second)
    restore_exercise.restore(second, sealed(inv), target)
    for prefix in ("catalogue/attempts/", "catalogue/captures/", "catalogue/links/", "catalogue/status/"):
        keys = list(world.store.list(prefix))
        assert keys, prefix
        assert keys == list(target.list(prefix))
        assert all(world.store.get(k) == target.get(k) for k in keys)


# --- a store copy that is wrong is detected -----------------------------------------------------


def test_a_tampered_object_is_detected_and_blocks_the_restore(world, tmp_path):
    second, target = LocalObjectStore(tmp_path / "second"), LocalObjectStore(tmp_path / "target")
    inv = copy_to(world.store, second)
    path = second.root / a_release_file(second)
    path.chmod(0o644)
    path.write_bytes(path.read_bytes() + b"x")
    report = second_copy.check_store(second, inv)
    assert [t["key"] for t in report["tampered"]] == [a_release_file(second)] and not report["ok"]
    with pytest.raises(restore_exercise.ExerciseError, match="does not match its inventory"):
        restore_exercise.restore(second, sealed(inv), target)
    assert list(target.list()) == []  # nothing was written


def test_a_tampered_receipt_is_detected_by_its_content_address(world, tmp_path):
    second = LocalObjectStore(tmp_path / "second")
    inv = copy_to(world.store, second)
    key = next(second.list("receipts/"))
    (second.root / key).chmod(0o644)
    (second.root / key).write_bytes(b"not the receipt")
    report = second_copy.check_store(second, inv)
    assert report["tampered"] and report["tampered"][0]["key"] == key
    assert "IntegrityError" in report["tampered"][0]["reason"]


def test_a_missing_object_is_detected_and_blocks_the_restore(world, tmp_path):
    second, target = LocalObjectStore(tmp_path / "second"), LocalObjectStore(tmp_path / "target")
    inv = copy_to(world.store, second)
    key = next(second.list("catalogue/attempts/"))
    (second.root / key).unlink()
    report = second_copy.check_store(second, inv)
    assert report["missing"] == [key] and not report["ok"]
    with pytest.raises(restore_exercise.ExerciseError):
        restore_exercise.restore(second, sealed(inv), target)
    assert list(target.list()) == []


def test_an_injected_object_is_detected(world, tmp_path):
    second = LocalObjectStore(tmp_path / "second")
    inv = copy_to(world.store, second)
    second.put("artefacts/injected.txt", b"not in the inventory")
    assert second_copy.check_store(second, inv)["unlisted"] == ["artefacts/injected.txt"]


def test_a_blob_second_copy_detects_an_overwrite_and_a_delete(blob_world):
    second = blob(T_COPY, immutable=False)  # the server-side policy is off, as on a misconfigured account
    inv = copy_to(blob_world, second)
    keys = list(second.list("releases/")) or list(second.list("receipts/"))
    second.backend.overwrite(keys[0], b"replaced")
    second.backend.delete(keys[1])
    report = second_copy.check_store(second, inv)
    assert [t["key"] for t in report["tampered"]] == [keys[0]] and "2 versions" in report["tampered"][0][
        "reason"
    ]
    assert report["missing"] == [keys[1]]


def test_a_copy_into_a_destination_holding_different_bytes_refuses(world, tmp_path):
    dest = LocalObjectStore(tmp_path / "second")
    key = a_release_file(world.store)
    dest.put(key, b"different bytes at the same key")
    with pytest.raises(Exception, match="different bytes"):
        copy_to(world.store, dest)


def test_an_interrupted_copy_resumes_to_the_same_inventory(world, tmp_path):
    dest = LocalObjectStore(tmp_path / "second")
    keys = sorted(world.store.snapshot())
    for key in keys[: len(keys) // 2]:  # a partial copy from an earlier run
        dest.put(key, world.store.get(key))
    inv = copy_to(world.store, dest)
    assert second_copy.check_store(dest, inv)["ok"] and dest.snapshot() == world.store.snapshot()


# --- restore without the primary, then rebuild --------------------------------------------------


def test_restore_without_the_primary_then_rebuild_is_byte_identical(world, tmp_path):
    primary_root = tmp_path / "primary"
    primary = LocalObjectStore(primary_root)
    for key in world.store.snapshot():
        primary.put(key, world.store.get(key))
    expected = primary.snapshot()
    second = blob(T_COPY)
    inv = copy_to(primary, second)
    shutil.rmtree(primary_root)  # the primary is gone: nothing below can read it
    assert not primary_root.exists()

    target = blob(T_RESTORE)
    report = restore_exercise.restore(second, sealed(inv), target)
    assert report["ok"] and report["restored_objects"] == len(expected)
    assert target.snapshot() == expected  # every key, every byte
    assert report["catalogue"]["identical"] and report["target_check"]["ok"]

    outcome = restore_exercise.rebuild_and_compare(
        target, rebuild_for(world, target), instant_str(world.cutoff), world.code
    )
    assert outcome["ok"] and outcome["running_code_matches_pin"] is True
    assert {r["dataset_id"] for r in outcome["releases"]} == set(world.releases)
    for r in outcome["releases"]:
        assert r["identical"] and r["manifest_identical"] and all(r["files"].values())
        assert r["stored_content_sha256"] == r["rebuilt_content_sha256"]
    assert outcome["pins"]["code_ref"] == world.code and outcome["pins"]["spec_refs"]


def test_the_restore_has_no_way_to_name_the_primary():
    assert list(inspect.signature(restore_exercise.restore).parameters) == [
        "second",
        "inventory_raw",
        "target",
    ]


def test_restoring_into_a_non_empty_store_is_refused(world, tmp_path):
    second, target = LocalObjectStore(tmp_path / "second"), LocalObjectStore(tmp_path / "target")
    inv = copy_to(world.store, second)
    target.put("artefacts/existing.txt", b"x")
    with pytest.raises(restore_exercise.ExerciseError, match="not empty"):
        restore_exercise.restore(second, sealed(inv), target)
    assert list(target.list()) == ["artefacts/existing.txt"]


def test_a_catalogue_that_differs_from_the_inventory_is_reported(world, tmp_path):
    second, target = LocalObjectStore(tmp_path / "second"), LocalObjectStore(tmp_path / "target")
    inv = copy_to(world.store, second)
    inv = second_copy.seal({**inv, "catalogue_sha256": "1" * 64})
    report = restore_exercise.restore(second, sealed(inv), target)
    assert report["target_check"]["ok"] and not report["catalogue"]["identical"] and not report["ok"]


def test_the_catalogue_is_compared_as_rows_not_file_bytes(world, tmp_path):
    rows = second_copy.catalogue_rows(world.store)
    assert rows["releases"] and rows["status_events"] and rows["captures"] and rows["vintages"]
    path = tmp_path / "second"
    copy_to(world.store, LocalObjectStore(path))
    assert second_copy.catalogue_sha256(LocalObjectStore(path)) == sha256_hex(canonical_json(rows))
    assert not list(path.rglob("*.duckdb"))  # no database file is part of the copy


def test_a_rebuild_from_a_different_code_reference_is_reported_as_different(world, tmp_path):
    second, target = LocalObjectStore(tmp_path / "second"), LocalObjectStore(tmp_path / "target")
    inv = copy_to(world.store, second)
    restore_exercise.restore(second, sealed(inv), target)
    pins_code = {"commit": "f" * 40, "lock_sha256": "1" * 64}

    def rebuild(pins):
        return restore_exercise.rebuild_s1b1(
            target,
            rits=RITS,
            nsw=NSW,
            rights=world.rights,
            gate=RightsGate(world.rights),
            pins={**pins, "code_ref": pins_code},
            cutoff_at=world.cutoff,
        )

    outcome = restore_exercise.rebuild_and_compare(target, rebuild, instant_str(world.cutoff), pins_code)
    assert not outcome["ok"] and not outcome["identical"]
    assert all(not r["identical"] for r in outcome["releases"])
    again = restore_exercise.rebuild_and_compare(
        target, rebuild_for(world, target), instant_str(world.cutoff), pins_code
    )
    assert again["identical"] and again["running_code_matches_pin"] is False and not again["ok"]


def test_a_changed_payload_in_the_restored_store_is_a_rebuild_difference(world, tmp_path):
    second, target = LocalObjectStore(tmp_path / "second"), LocalObjectStore(tmp_path / "target")
    inv = copy_to(world.store, second)
    restore_exercise.restore(second, sealed(inv), target)
    key = a_release_file(target)
    (target.root / key).chmod(0o644)
    (target.root / key).write_bytes(b"period_start\n")
    outcome = restore_exercise.rebuild_and_compare(
        target, rebuild_for(world, target), instant_str(world.cutoff)
    )
    assert not outcome["identical"]
    assert [name for r in outcome["releases"] for name, same in r.get("files", {}).items() if not same] == [
        "data.csv"
    ]


def test_no_pinned_release_at_the_cutoff_refuses(world):
    with pytest.raises(restore_exercise.ExerciseError, match="no release manifest"):
        restore_exercise.release_pins(world.store, "2001-01-01T00:00:00.000000Z")


# --- the command lines --------------------------------------------------------------------------


def test_the_command_lines_copy_restore_and_rebuild(world, tmp_path, capsys):
    inventory = tmp_path / "inventory.json"
    assert (
        second_copy.main(
            [
                "copy",
                "--source",
                str(world.store.root),
                "--dest",
                str(tmp_path / "second"),
                "--inventory",
                str(inventory),
                "--label",
                "cli-test",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["objects"] == len(world.store.snapshot())
    verify = ["verify", "--store", str(tmp_path / "second"), "--inventory", str(inventory)]
    assert second_copy.main(verify) == 0 and json.loads(capsys.readouterr().out)["ok"] is True
    again = ["copy", "--source", "x", "--dest", "y", "--inventory", str(inventory), "--label", "l"]
    assert second_copy.main(again) == 2  # an existing inventory is never replaced
    capsys.readouterr()

    restore = ["restore", "--second", str(tmp_path / "second"), "--inventory", str(inventory)]
    assert restore_exercise.main([*restore, "--target", str(tmp_path / "target")]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert restore_exercise.main([*restore, "--target", str(tmp_path / "target")]) == 2  # no longer empty
    capsys.readouterr()

    fixtures = REPO / "tests" / "fixtures" / "synthetic" / "s1b1"
    rebuild = [
        "rebuild",
        "--store",
        str(tmp_path / "target"),
        "--cutoff",
        instant_str(world.cutoff),
        "--rits-calendar",
        str(fixtures / "calendar_rits.yaml"),
        "--nsw-calendar",
        str(fixtures / "calendar_nsw.yaml"),
        "--allow-synthetic",
    ]
    # The running code is always checked: the pin is 'test', not this commit, so the byte-identical rebuild is
    # still not a success (F-REVIEW-2026-10-29-t0014-1-2).
    assert restore_exercise.main(rebuild) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["identical"] is True and out["running_code_matches_pin"] is False and out["ok"] is False


def test_the_verify_command_reports_a_tampered_second_copy(world, tmp_path, capsys):
    inventory = tmp_path / "inventory.json"
    args = ["--source", str(world.store.root), "--dest", str(tmp_path / "second")]
    assert second_copy.main(["copy", *args, "--inventory", str(inventory), "--label", "t"]) == 0
    capsys.readouterr()
    path = tmp_path / "second" / a_release_file(world.store)
    path.chmod(0o644)
    path.write_bytes(b"changed")
    assert (
        second_copy.main(["verify", "--store", str(tmp_path / "second"), "--inventory", str(inventory)]) == 1
    )
    assert json.loads(capsys.readouterr().out)["tampered"]


def test_an_absent_running_code_reference_is_never_ok(world):
    """F-REVIEW-2026-10-29-t0014-1-2: with no running reference, the rebuild is not from pinned code."""
    target = world.store
    outcome = restore_exercise.rebuild_and_compare(
        target, rebuild_for(world, target), instant_str(world.cutoff)
    )
    assert outcome["identical"] and outcome["running_code_matches_pin"] is None and outcome["ok"] is False


def test_a_rebuild_that_is_not_the_cutoff_pin_is_never_identical(world):
    """F-REVIEW-2026-10-29-t0014-1-1: the comparison is against the pinned release, not whichever stored
    release has the rebuilt hash. The old comparison read the rebuilt hash's path and reported identical."""
    target = world.store
    pins = restore_exercise.release_pins(target, instant_str(world.cutoff))
    rebuilt = rebuild_for(world, target)(pins)
    assert restore_exercise.compare_rebuild(target, rebuilt, pins)["identical"]
    elsewhere = {**pins, "releases": {ds: "0" * 64 for ds in pins["releases"]}}
    result = restore_exercise.compare_rebuild(target, rebuilt, elsewhere)
    assert not result["identical"]
    assert all(r["note"] == "rebuilt hash differs from the cutoff pin" for r in result["releases"])
