"""Tests for tools/lake_backup.py: invented files only, no git, no network."""

import hashlib
import importlib
import json
import os
import stat
import sys
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
tool = importlib.import_module("lake_backup")

NOW = datetime(2030, 1, 9, 12, 30, 45, tzinfo=UTC)
FILES = {
    "raw/s1/manifest.json": b'{"a": 1}\n',
    "raw/s1/eod.json": b"[1, 2, 3]\n" * 50,
    "silver/ZZZ.US/abc/closes.csv": b"date,close\n2030-01-07,100.0000\n",
    "gold/f/0.1.0/b1/series.csv": b"period_start,period_end\n",
    "top.txt": b"",
}


@pytest.fixture(autouse=True)
def private_tmp(tmp_path):
    tmp_path.chmod(0o700)


def make_tree(root, files=FILES):
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


def source_tree(tmp_path, files=FILES):
    return make_tree(tmp_path / "lake", files)


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def inventory_of(files):
    return [
        {"path": name, "bytes": len(files[name]), "sha256": hashlib.sha256(files[name]).hexdigest()}
        for name in sorted(files)
    ]


def hash_part(files):
    canonical = json.dumps(inventory_of(files), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def make_backup(tmp_path, files=FILES, now=NOW, **kwargs):
    source = source_tree(tmp_path, files) if not (tmp_path / "lake").exists() else tmp_path / "lake"
    report = tool.backup(source, tmp_path / "backups", now=now, **kwargs)
    return source, tmp_path / "backups" / report["backup_id"], report


def modes(root):
    return {str(p.relative_to(root)): stat.S_IMODE(p.stat().st_mode) for p in [root, *root.rglob("*")]}


def test_a_round_trip_restores_a_byte_identical_tree(tmp_path):
    source, backup_dir, report = make_backup(tmp_path)
    assert report["passed"] and report["files"] == len(FILES) and not report["existed"]
    assert report["bytes"] == sum(len(v) for v in FILES.values())
    assert tool.verify(backup_dir)["passed"]
    restored = tmp_path / "restored"
    restore_report = tool.restore(backup_dir, restored)
    assert restore_report["passed"]
    assert snapshot(restored) == snapshot(source) == FILES


def test_the_backup_id_follows_the_formula_for_a_fixed_now(tmp_path):
    _, backup_dir, report = make_backup(tmp_path)
    assert report["backup_id"] == f"20300109T123045Z-{hash_part(FILES)}"
    assert backup_dir.name == report["backup_id"]
    stored = json.loads((backup_dir / "inventory.json").read_text())
    assert stored == {
        "schema": "hio.backup/1",
        "backup_id": report["backup_id"],
        "source": "lake",
        "created_at": "2030-01-09T12:30:45Z",
        "files": inventory_of(FILES),
        "total_bytes": sum(len(v) for v in FILES.values()),
    }
    assert (backup_dir / "inventory.json").read_text().endswith("}\n")


def test_the_time_is_taken_in_utc(tmp_path):
    source = source_tree(tmp_path)
    plus_ten = NOW.astimezone(timezone(timedelta(hours=10)))
    report = tool.backup(source, tmp_path / "backups", now=plus_ten)
    assert report["backup_id"].startswith("20300109T123045Z-")
    with pytest.raises(ValueError, match="time zone"):
        tool.backup(source, tmp_path / "backups", now=NOW.replace(tzinfo=None))


def test_the_source_name_is_recorded_without_its_path(tmp_path):
    _, backup_dir, _ = make_backup(tmp_path)
    text = (backup_dir / "inventory.json").read_text()
    assert str(tmp_path) not in text


def test_two_backups_of_the_same_tree_share_the_hash_part(tmp_path):
    source = source_tree(tmp_path)
    first = tool.backup(source, tmp_path / "backups", now=NOW)
    second = tool.backup(source, tmp_path / "backups", now=NOW + timedelta(days=3, seconds=7))
    assert first["backup_id"] != second["backup_id"]
    assert first["backup_id"].split("-")[1] == second["backup_id"].split("-")[1] == hash_part(FILES)
    assert sorted(p.name for p in (tmp_path / "backups").iterdir()) == sorted(
        [first["backup_id"], second["backup_id"]]
    )


def test_the_same_backup_twice_is_already_built_and_changed_content_gets_a_new_hash(tmp_path):
    source, backup_dir, first = make_backup(tmp_path)
    before = snapshot(backup_dir)
    again = tool.backup(source, tmp_path / "backups", now=NOW)
    assert again["existed"] and again["backup_id"] == first["backup_id"]
    assert snapshot(backup_dir) == before
    (source / "top.txt").write_bytes(b"changed")
    other = tool.backup(source, tmp_path / "backups", now=NOW)
    assert other["backup_id"] != first["backup_id"]
    assert snapshot(backup_dir) == before


def test_a_different_backup_under_the_same_id_is_refused_and_not_touched(tmp_path):
    source, backup_dir, _ = make_backup(tmp_path)
    (backup_dir / "data" / "top.txt").write_bytes(b"tampered")
    before = snapshot(backup_dir)
    with pytest.raises(ValueError, match="different backup"):
        tool.backup(source, tmp_path / "backups", now=NOW)
    assert snapshot(backup_dir) == before


def test_a_symlink_in_the_source_is_refused_and_nothing_is_created(tmp_path):
    source = source_tree(tmp_path)
    (source / "link").symlink_to(source / "top.txt")
    with pytest.raises(ValueError, match="symlink"):
        tool.backup(source, tmp_path / "backups", now=NOW)
    assert not (tmp_path / "backups").exists()


def test_a_symlinked_directory_in_the_source_is_refused(tmp_path):
    source = source_tree(tmp_path)
    (source / "dirlink").symlink_to(source / "raw")
    with pytest.raises(ValueError, match="symlink"):
        tool.backup(source, tmp_path / "backups", now=NOW)


def test_a_symlinked_source_is_refused(tmp_path):
    real = source_tree(tmp_path)
    (tmp_path / "alias").symlink_to(real)
    with pytest.raises(ValueError, match="symlink"):
        tool.backup(tmp_path / "alias", tmp_path / "backups", now=NOW)


def test_a_special_file_in_the_source_is_refused(tmp_path):
    source = source_tree(tmp_path)
    os.mkfifo(source / "pipe")
    with pytest.raises(ValueError, match="special"):
        tool.backup(source, tmp_path / "backups", now=NOW)


def test_a_target_inside_the_source_is_refused(tmp_path):
    source = source_tree(tmp_path)
    for target in (source / "backups", source):
        with pytest.raises(ValueError, match="outside --source"):
            tool.backup(source, target, now=NOW)
    assert not (source / "backups").exists()


def test_paths_inside_the_repository_are_refused(tmp_path):
    source = source_tree(tmp_path)
    inside = REPO / "zz_lake_backup_test_never_created"
    with pytest.raises(ValueError, match="repository"):
        tool.backup(source, inside, now=NOW)
    with pytest.raises(ValueError, match="repository"):
        tool.backup(REPO / "tools", tmp_path / "backups", now=NOW)
    with pytest.raises(ValueError, match="repository"):
        tool.compare(REPO / "tools", tmp_path)
    _, backup_dir, _ = make_backup(tmp_path)
    with pytest.raises(ValueError, match="repository"):
        tool.restore(backup_dir, inside)
    assert not inside.exists()


def test_a_missing_or_non_directory_source_is_refused(tmp_path):
    with pytest.raises(ValueError, match="not a directory"):
        tool.backup(tmp_path / "absent", tmp_path / "backups", now=NOW)
    (tmp_path / "file").write_bytes(b"x")
    with pytest.raises(ValueError, match="not a directory"):
        tool.backup(tmp_path / "file", tmp_path / "backups", now=NOW)
    with pytest.raises(ValueError, match="not a directory"):
        tool.backup(source_tree(tmp_path), tmp_path / "file", now=NOW)


def test_restore_refuses_a_non_empty_directory_and_writes_nothing(tmp_path):
    _, backup_dir, _ = make_backup(tmp_path)
    into = tmp_path / "occupied"
    into.mkdir()
    (into / "keep.txt").write_bytes(b"mine")
    with pytest.raises(ValueError, match="not empty"):
        tool.restore(backup_dir, into)
    assert snapshot(into) == {"keep.txt": b"mine"}
    file_target = tmp_path / "afile"
    file_target.write_bytes(b"x")
    with pytest.raises(ValueError, match="not a directory"):
        tool.restore(backup_dir, file_target)


def test_restore_into_an_existing_empty_directory_works(tmp_path):
    source, backup_dir, _ = make_backup(tmp_path)
    into = tmp_path / "empty"
    into.mkdir()
    tool.restore(backup_dir, into)
    assert snapshot(into) == snapshot(source)


def test_restore_refuses_a_backup_that_does_not_verify_and_creates_nothing(tmp_path):
    _, backup_dir, _ = make_backup(tmp_path)
    (backup_dir / "data" / "top.txt").write_bytes(b"x")
    into = tmp_path / "restored"
    with pytest.raises(ValueError, match="does not verify"):
        tool.restore(backup_dir, into)
    assert not into.exists()


def test_restore_refuses_a_target_inside_the_backup(tmp_path):
    _, backup_dir, _ = make_backup(tmp_path)
    with pytest.raises(ValueError, match="outside the backup"):
        tool.restore(backup_dir, backup_dir / "data" / "sub")


def test_verify_catches_a_flipped_byte(tmp_path):
    _, backup_dir, _ = make_backup(tmp_path)
    target = backup_dir / "data" / "raw" / "s1" / "eod.json"
    data = bytearray(target.read_bytes())
    data[3] ^= 0x01
    target.write_bytes(bytes(data))
    report = tool.verify(backup_dir)
    assert not report["passed"]
    assert report["problems"] == [("changed", "raw/s1/eod.json")]


def test_verify_catches_a_same_length_change_and_a_length_change(tmp_path):
    _, backup_dir, _ = make_backup(tmp_path)
    (backup_dir / "data" / "top.txt").write_bytes(b"longer now")
    assert tool.verify(backup_dir)["problems"] == [("changed", "top.txt")]


def test_verify_catches_a_missing_file(tmp_path):
    _, backup_dir, _ = make_backup(tmp_path)
    (backup_dir / "data" / "top.txt").unlink()
    report = tool.verify(backup_dir)
    assert not report["passed"] and report["problems"] == [("missing", "top.txt")]


def test_verify_catches_an_extra_file_a_link_and_a_stray_entry(tmp_path):
    _, backup_dir, _ = make_backup(tmp_path)
    (backup_dir / "data" / "raw" / "extra.txt").write_bytes(b"new")
    (backup_dir / "data" / "link").symlink_to(backup_dir / "data" / "top.txt")
    (backup_dir / "stray").write_bytes(b"x")
    report = tool.verify(backup_dir)
    assert not report["passed"]
    assert ("extra", "raw/extra.txt") in report["problems"]
    assert ("extra", "link") in report["problems"]
    assert ("unexpected_entry", "stray") in report["problems"]


def test_verify_catches_a_backup_id_that_disagrees_with_the_directory_or_the_inventory(tmp_path):
    _, backup_dir, _ = make_backup(tmp_path)
    renamed = backup_dir.with_name("20300109T123045Z-000000000000")
    backup_dir.rename(renamed)
    assert ("backup_id", "directory") in tool.verify(renamed)["problems"]
    inventory_path = renamed / "inventory.json"
    stored = json.loads(inventory_path.read_text())
    stored["backup_id"] = renamed.name
    inventory_path.write_text(json.dumps(stored))
    assert ("backup_id", "inventory") in tool.verify(renamed)["problems"]


def test_verify_catches_an_edited_inventory(tmp_path):
    _, backup_dir, _ = make_backup(tmp_path)
    path = backup_dir / "inventory.json"
    stored = json.loads(path.read_text())
    stored["total_bytes"] += 1
    path.write_text(json.dumps(stored))
    assert ("inventory", "total_bytes") in tool.verify(backup_dir)["problems"]
    stored["files"][0]["path"] = "../escape"
    path.write_text(json.dumps(stored))
    assert tool.verify(backup_dir)["problems"] == [("inventory", "files")]
    path.write_text("not json")
    assert tool.verify(backup_dir)["problems"] == [("inventory", "unparseable")]
    path.unlink()
    assert tool.verify(backup_dir)["problems"] == [("inventory", "missing")]


def test_verify_of_a_partial_or_absent_directory_fails(tmp_path):
    assert not tool.verify(tmp_path / "nothing")["passed"]
    _, backup_dir, _ = make_backup(tmp_path)
    partial = backup_dir.with_name(backup_dir.name + ".partial")
    backup_dir.rename(partial)
    assert ("backup_id", "directory") in tool.verify(partial)["problems"]


def test_a_copy_failure_leaves_only_a_partial_directory(tmp_path, monkeypatch):
    source = source_tree(tmp_path)
    real = tool._copy_file
    calls = []

    def flaky(src, dst, base):
        calls.append(dst.name)
        if len(calls) == 3:
            raise OSError("disk full")
        return real(src, dst, base)

    monkeypatch.setattr(tool, "_copy_file", flaky)
    with pytest.raises(ValueError, match="partial directory left"):
        tool.backup(source, tmp_path / "backups", now=NOW)
    names = [p.name for p in (tmp_path / "backups").iterdir()]
    assert len(names) == 1 and names[0].endswith(".partial")
    assert snapshot(source) == FILES
    monkeypatch.setattr(tool, "_copy_file", real)
    with pytest.raises(ValueError, match="partial backup exists"):
        tool.backup(source, tmp_path / "backups", now=NOW)


def test_a_copy_that_does_not_match_leaves_a_partial_directory(tmp_path, monkeypatch):
    source = source_tree(tmp_path)
    real = tool._copy_file

    def corrupting(src, dst, base):
        result = real(src, dst, base)
        if dst.name == "top.txt":
            return result
        if dst.name == "closes.csv":
            dst.write_bytes(b"corrupted after the copy")
        return result

    monkeypatch.setattr(tool, "_copy_file", corrupting)
    with pytest.raises(ValueError, match="does not match"):
        tool.backup(source, tmp_path / "backups", now=NOW)
    assert [p.name.endswith(".partial") for p in (tmp_path / "backups").iterdir()] == [True]


def test_a_source_that_changes_during_the_copy_is_refused(tmp_path, monkeypatch):
    source = source_tree(tmp_path)
    real = tool._copy_file

    def racing(src, dst, base):
        if dst.name == "eod.json":
            src.write_bytes(b"changed under us")
        return real(src, dst, base)

    monkeypatch.setattr(tool, "_copy_file", racing)
    with pytest.raises(ValueError, match="changed while"):
        tool.backup(source, tmp_path / "backups", now=NOW)
    assert [p.name.endswith(".partial") for p in (tmp_path / "backups").iterdir()] == [True]


def test_exclude_skips_any_path_with_that_component(tmp_path):
    source = source_tree(tmp_path)
    make_tree(source, {"cache/x.bin": b"1", "raw/cache/y.bin": b"2", "cachefile": b"3"})
    report = tool.backup(source, tmp_path / "backups", now=NOW, exclude=["cache"])
    restored = tmp_path / "restored"
    tool.restore(tmp_path / "backups" / report["backup_id"], restored)
    assert set(snapshot(restored)) == set(FILES) | {"cachefile"}
    assert tool.compare(source, tmp_path / "backups" / report["backup_id"], exclude=["cache"])["passed"]
    assert not tool.compare(source, tmp_path / "backups" / report["backup_id"])["passed"]


def test_exclude_can_skip_a_symlink_but_not_hide_one_elsewhere(tmp_path):
    source = source_tree(tmp_path)
    (source / ".cache").symlink_to(source / "top.txt")
    tool.backup(source, tmp_path / "backups", now=NOW, exclude=[".cache"])
    with pytest.raises(ValueError, match="symlink"):
        tool.backup(source, tmp_path / "other", now=NOW)


@pytest.mark.parametrize("bad", ["", "a/b", "..", "."])
def test_a_bad_exclude_is_refused(tmp_path, bad):
    with pytest.raises(ValueError, match="one path component"):
        tool.backup(source_tree(tmp_path), tmp_path / "backups", now=NOW, exclude=[bad])


def test_compare_counts_identical_changed_and_one_sided_files(tmp_path):
    source, backup_dir, _ = make_backup(tmp_path)
    same = tool.compare(source, backup_dir)
    assert same["passed"] and same["identical"] == len(FILES)
    (source / "top.txt").write_bytes(b"now not empty")
    (source / "raw/s1/manifest.json").write_bytes(b'{"a": 2}\n')
    (source / "new1.txt").write_bytes(b"n")
    (source / "sub").mkdir()
    (source / "sub" / "new2.txt").write_bytes(b"n")
    (source / "sub" / "new3.txt").write_bytes(b"n")
    (source / "gold/f/0.1.0/b1/series.csv").unlink()
    report = tool.compare(source, backup_dir)
    assert (report["identical"], report["changed"]) == (len(FILES) - 3, 2)
    assert (report["only_in_source"], report["only_in_backup"]) == (3, 1)
    assert not report["passed"]


def test_compare_refuses_a_backup_with_an_invalid_inventory(tmp_path):
    source, backup_dir, _ = make_backup(tmp_path)
    (backup_dir / "inventory.json").write_text("nope")
    with pytest.raises(ValueError, match="not valid"):
        tool.compare(source, backup_dir)


def test_files_are_0600_and_directories_0700_in_the_backup_and_the_restore(tmp_path):
    _, backup_dir, _ = make_backup(tmp_path)
    restored = tmp_path / "restored"
    tool.restore(backup_dir, restored)
    for root in (backup_dir, restored):
        for name, mode in modes(root).items():
            is_dir = (root / name).is_dir() if name != "." else True
            assert mode == (0o700 if is_dir else 0o600), (root.name, name)
    assert stat.S_IMODE((tmp_path / "backups").stat().st_mode) == 0o700


def test_modes_are_private_whatever_the_umask_or_the_source_modes(tmp_path):
    source = source_tree(tmp_path)
    (source / "top.txt").chmod(0o644)
    old = os.umask(0)
    try:
        _, backup_dir, _ = make_backup(tmp_path)
    finally:
        os.umask(old)
    assert stat.S_IMODE((backup_dir / "data" / "top.txt").stat().st_mode) == 0o600
    assert stat.S_IMODE((backup_dir / "data" / "raw").stat().st_mode) == 0o700
    assert stat.S_IMODE((backup_dir / "inventory.json").stat().st_mode) == 0o600
    assert stat.S_IMODE(backup_dir.stat().st_mode) == 0o700


def test_names_with_spaces_and_unicode_round_trip(tmp_path):
    files = {
        "dir with spaces/a file.csv": b"1\n",
        "café/日本語.txt": b"2\n",
        "emoji \U0001f4c8.txt": b"3\n",
        "quote'\"name": b"4\n",
    }
    source, backup_dir, report = make_backup(tmp_path, files)
    assert report["files"] == 4
    assert tool.verify(backup_dir)["passed"]
    restored = tmp_path / "restored"
    tool.restore(backup_dir, restored)
    assert snapshot(restored) == snapshot(source) == files
    assert [r["path"] for r in json.loads((backup_dir / "inventory.json").read_text())["files"]] == sorted(
        files
    )


def test_an_empty_source_backs_up_and_restores_to_an_empty_directory(tmp_path):
    (tmp_path / "lake").mkdir()
    (tmp_path / "lake" / "emptydir").mkdir()
    source, backup_dir, report = make_backup(tmp_path)
    assert (report["files"], report["bytes"]) == (0, 0)
    restored = tmp_path / "restored"
    tool.restore(backup_dir, restored)
    assert list(restored.iterdir()) == []
    assert source.is_dir()


def test_a_large_file_is_copied_in_chunks(tmp_path):
    big = {"big.bin": os.urandom(tool.CHUNK * 2 + 17)}
    source, backup_dir, _ = make_backup(tmp_path, big)
    tool.restore(backup_dir, tmp_path / "restored")
    assert snapshot(tmp_path / "restored") == big
    assert snapshot(source) == big


def test_the_source_is_untouched_by_a_backup(tmp_path):
    source = source_tree(tmp_path)
    before = {p: p.stat().st_mtime_ns for p in source.rglob("*")}
    tool.backup(source, tmp_path / "backups", now=NOW)
    assert snapshot(source) == FILES
    assert {p: p.stat().st_mtime_ns for p in source.rglob("*")} == before


def test_the_cli_round_trip_prints_ids_and_counts_only(tmp_path, capsys):
    source = source_tree(tmp_path)
    secret = {"2030-01-07": b"2030-01-07,123.456789\n"}
    make_tree(source, {"prices/p.csv": secret["2030-01-07"]})
    assert tool.main(["backup", "--source", str(source), "--target", str(tmp_path / "b")], now=NOW) == 0
    out = capsys.readouterr().out
    backup_id = f"20300109T123045Z-{hash_part({**FILES, 'prices/p.csv': secret['2030-01-07']})}"
    assert f"backup_id: {backup_id}" in out
    assert f"files: {len(FILES) + 1}" in out and out.rstrip().endswith("pass")
    backup_dir = tmp_path / "b" / backup_id
    assert tool.main(["backup", "--source", str(source), "--target", str(tmp_path / "b")], now=NOW) == 0
    assert "already built" in capsys.readouterr().out
    assert tool.main(["verify", "--backup", str(backup_dir)]) == 0
    verify_out = capsys.readouterr().out
    assert tool.main(["restore", "--backup", str(backup_dir), "--into", str(tmp_path / "r")]) == 0
    restore_out = capsys.readouterr().out
    assert tool.main(["compare", "--source", str(source), "--backup", str(backup_dir)]) == 0
    compare_out = capsys.readouterr().out
    for text in (out, verify_out, restore_out, compare_out):
        for leak in ("123.456789", "2030-01-07", "prices", "p.csv", "closes", "manifest", str(tmp_path)):
            assert leak not in text
    assert "identical: 6" in compare_out and compare_out.rstrip().endswith("pass")


def test_the_cli_reports_fail_with_counts_and_exits_1(tmp_path, capsys):
    _, backup_dir, _ = make_backup(tmp_path)
    (backup_dir / "data" / "top.txt").write_bytes(b"x")
    (backup_dir / "data" / "extra.txt").write_bytes(b"x")
    assert tool.main(["verify", "--backup", str(backup_dir)]) == 1
    out = capsys.readouterr().out
    assert "problems: 2" in out and "changed: 1" in out and "extra: 1" in out
    assert out.rstrip().endswith("fail")
    assert "top.txt" not in out and "extra.txt" not in out
    (tmp_path / "lake" / "new.txt").write_bytes(b"n")
    assert tool.main(["compare", "--source", str(tmp_path / "lake"), "--backup", str(backup_dir)]) == 1
    assert "only_in_source: 1" in capsys.readouterr().out


def test_the_cli_refusal_prints_to_stderr_and_exits_2(tmp_path, capsys):
    source = source_tree(tmp_path)
    (source / "link").symlink_to(source / "top.txt")
    assert tool.main(["backup", "--source", str(source), "--target", str(tmp_path / "b")], now=NOW) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.startswith("refused: ValueError: ")
    assert tool.main(["backup", "--source", str(source), "--target", str(REPO / "zz_nope")], now=NOW) == 2
    assert "repository" in capsys.readouterr().err
    assert not (REPO / "zz_nope").exists()
    assert tool.main(["verify", "--backup", str(tmp_path / "absent")]) == 1
    assert tool.main(["restore", "--backup", str(tmp_path / "absent"), "--into", str(tmp_path / "r")]) == 2
