from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


ITEM_COLUMN_PATCHES = {
    "color": "ALTER TABLE items ADD COLUMN color VARCHAR(32) NULL",
    "brand": "ALTER TABLE items ADD COLUMN brand VARCHAR(64) NULL",
    "keywords": "ALTER TABLE items ADD COLUMN keywords TEXT NULL",
    "feature_text": "ALTER TABLE items ADD COLUMN feature_text TEXT NULL",
    "owner_deleted": "ALTER TABLE items ADD COLUMN owner_deleted BOOLEAN NOT NULL DEFAULT FALSE",
}

USER_COLUMN_PATCHES = {
    "is_superadmin": "ALTER TABLE users ADD COLUMN is_superadmin BOOLEAN NOT NULL DEFAULT FALSE",
}


def sync_item_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if "items" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("items")}
    missing_columns = [name for name in ITEM_COLUMN_PATCHES if name not in existing_columns]
    if not missing_columns:
        return

    with engine.begin() as connection:
        for column_name in missing_columns:
            connection.execute(text(ITEM_COLUMN_PATCHES[column_name]))


def sync_user_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    missing_columns = [name for name in USER_COLUMN_PATCHES if name not in existing_columns]

    with engine.begin() as connection:
        for column_name in missing_columns:
            connection.execute(text(USER_COLUMN_PATCHES[column_name]))

        superadmin_count = connection.execute(
            text("SELECT COUNT(*) FROM users WHERE is_superadmin = TRUE")
        ).scalar() or 0

        if superadmin_count == 0:
            candidate_id = connection.execute(
                text("SELECT id FROM users WHERE is_admin = TRUE ORDER BY id ASC LIMIT 1")
            ).scalar()
            if candidate_id is None:
                candidate_id = connection.execute(
                    text("SELECT id FROM users ORDER BY id ASC LIMIT 1")
                ).scalar()
            if candidate_id is not None:
                connection.execute(
                    text("UPDATE users SET is_superadmin = TRUE, is_admin = TRUE WHERE id = :user_id"),
                    {"user_id": candidate_id},
                )

