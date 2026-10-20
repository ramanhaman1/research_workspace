
import pytest

from services.resource_service import database


@pytest.fixture
def db(tmp_path, monkeypatch):
    test_path = tmp_path / "test.db"

    monkeypatch.setattr(database, "DB_PATH", test_path)
    database.init_db()

    return database


def test_create_dataset(db):
    dataset_id = db.create_dataset(
        "ali",
        "Student Survey",
        [{"participant": 1, "score": 80}]
    )

    dataset = db.get_dataset(dataset_id, "ali")

    assert dataset["id"] == dataset_id
    assert dataset["owner_username"] == "ali"
    assert dataset["name"] == "Student Survey"
    assert dataset["rows"][0]["score"] == 80


def test_dataset_ownership(db):
    dataset_id = db.create_dataset(
        "ali",
        "Private Data",
        [{"value": 100}]
    )

    assert db.get_dataset(dataset_id, "ali") is not None
    assert db.get_dataset(dataset_id, "Raman") is None


def test_nonexistent_dataset(db):
    result = db.get_dataset(999, "ali")

    assert result is None


def test_invalid_dataset_name(db):
    with pytest.raises(ValueError):
        db.create_dataset(
            "ali",
            "",
            [{"value": 10}]
        )
