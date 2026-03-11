# drop_items_table.py
from core.database import engine, Base

def drop_items_table():
    """Удаляет таблицу items из базы данных и из метаданных SQLAlchemy."""
    # Удаляем таблицу из БД
    with engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS items")
        conn.commit()
        print("✅ Таблица 'items' удалена из базы данных (если существовала).")

    # Удаляем запись о таблице из метаданных SQLAlchemy (чтобы избежать конфликта)
    if 'items' in Base.metadata.tables:
        del Base.metadata.tables['items']
        print("✅ Таблица 'items' удалена из метаданных SQLAlchemy.")

if __name__ == "__main__":
    drop_items_table()