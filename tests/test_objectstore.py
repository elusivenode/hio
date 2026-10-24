"""Local object store: write-once, integrity, staged all-or-nothing writes (S1-A3, OBS-INV-004)."""

import hashlib

import pytest

from hio.storage.objectstore import IntegrityError, LocalObjectStore, StagedWrites, WriteOnceViolation


@pytest.fixture
def store(tmp_path):
    return LocalObjectStore(tmp_path / "store")


def receipt_key(data: bytes) -> str:
    return f"receipts/synthetic.src/2026/10/{hashlib.sha256(data).hexdigest()}"


def test_second_write_to_existing_key_is_refused(store):
    store.put("catalogue/runs/2026/10/r1.json", b"{}")
    with pytest.raises(WriteOnceViolation):
        store.put("catalogue/runs/2026/10/r1.json", b"{}")
    with pytest.raises(WriteOnceViolation):
        store.put("catalogue/runs/2026/10/r1.json", b"changed")


def test_objects_are_read_only_on_disk(store):
    store.put("a/b.json", b"{}")
    assert (store.root / "a/b.json").stat().st_mode & 0o222 == 0


def test_receipt_hash_verifies_on_write_and_read(store):
    data = b"payload"
    key = receipt_key(data)
    store.put(key, data)
    assert store.get(key) == data
    with pytest.raises(IntegrityError):
        store.put(receipt_key(b"other"), data)  # bytes do not match the key
    path = store.root / key
    path.chmod(0o644)
    path.write_bytes(b"tampered")
    with pytest.raises(IntegrityError):
        store.get(key)


def test_get_verifies_a_supplied_hash(store):
    store.put("x/y.csv", b"abc")
    store.get("x/y.csv", hashlib.sha256(b"abc").hexdigest())
    with pytest.raises(IntegrityError):
        store.get("x/y.csv", "0" * 64)


def test_duplicate_receipt_is_a_no_op(store):
    data = b"same"
    assert store.put_if_absent(receipt_key(data), data) is True
    assert store.put_if_absent(receipt_key(data), data) is False


@pytest.mark.parametrize("key", ["../escape", "/abs", "a//b", "A/upper", "a/../b", ""])
def test_invalid_keys_are_refused(store, key):
    with pytest.raises(ValueError):
        store.put(key, b"x")


def test_staged_writes_are_all_or_nothing(store):
    store.put("r/existing.json", b"{}")
    before = store.snapshot()
    staged = StagedWrites(store)
    staged.add("r/a.json", b"1")
    with pytest.raises(WriteOnceViolation):
        staged.add("r/existing.json", b"2")
    assert store.snapshot() == before  # nothing written before commit
    staged.commit()
    assert set(store.snapshot()) == {"r/existing.json", "r/a.json"}
