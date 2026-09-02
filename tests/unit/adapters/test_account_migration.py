import importlib


def test_initial_account_migration_has_upgrade_and_downgrade(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    migration = importlib.import_module(
        "migrations.versions.20260902_01_create_account"
    )
    created: list[str] = []
    dropped: list[str] = []
    monkeypatch.setattr(
        migration.op, "create_table", lambda name, *args: created.append(name)
    )
    monkeypatch.setattr(migration.op, "drop_table", dropped.append)

    migration.upgrade()
    migration.downgrade()

    assert created == ["account"]
    assert dropped == ["account"]


def test_favourite_migration_has_upgrade_and_downgrade(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    migration = importlib.import_module(
        "migrations.versions.20260902_02_create_favourites"
    )
    created: list[str] = []
    dropped: list[str] = []
    monkeypatch.setattr(
        migration.op, "create_table", lambda name, *args: created.append(name)
    )
    monkeypatch.setattr(migration.op, "create_index", lambda *args, **kwargs: None)
    monkeypatch.setattr(migration.op, "drop_index", lambda *args, **kwargs: None)
    monkeypatch.setattr(migration.op, "drop_table", dropped.append)

    migration.upgrade()
    migration.downgrade()

    assert created == ["favourite_address_reference"]
    assert dropped == ["favourite_address_reference"]


def test_saved_comparison_migration_has_upgrade_and_downgrade(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    migration = importlib.import_module(
        "migrations.versions.20260902_03_create_saved_comparisons"
    )
    created: list[str] = []
    dropped: list[str] = []
    monkeypatch.setattr(
        migration.op, "create_table", lambda name, *args: created.append(name)
    )
    monkeypatch.setattr(migration.op, "create_index", lambda *args, **kwargs: None)
    monkeypatch.setattr(migration.op, "drop_index", lambda *args, **kwargs: None)
    monkeypatch.setattr(migration.op, "drop_table", dropped.append)
    migration.upgrade()
    migration.downgrade()
    assert created == ["saved_comparison", "saved_comparison_address_reference"]
    assert dropped == ["saved_comparison_address_reference", "saved_comparison"]
