from database.models import init_db
from database.repository import seed_database
from gui.app import LibraryApp


if __name__ == "__main__":
    init_db()
    seed_database()
    LibraryApp().run()
