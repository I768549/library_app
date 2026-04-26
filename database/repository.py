from .models import engine, Author, Genre, Loan, Book, Reader
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_, func, and_
import datetime

def get_all_books() -> list[dict]:
    with Session(engine) as session:
        stmt = select(Book).options(
            joinedload(Book.authors),
            joinedload(Book.genres),
        )
        books = session.execute(stmt).unique().scalars().all()        
        return [{
            "id": b.id,
            "title": b.title,
            "year": b.year,
            "isbn": b.isbn,
            "authors": ", ".join(f"{a.last_name} {a.first_name}" for a in b.authors),
            "genres": ", ".join(g.name for g in b.genres)                
        } for b in books]

def get_all_authors() -> list[dict]:
    with Session(engine) as session:
        stmt = select(Author).order_by(Author.last_name)
        authors = session.execute(stmt).scalars().all()
        return [
            {"id": a.id, "last_name": a.last_name, "first_name": a.first_name}
            for a in authors
        ]
def get_all_genres() -> list[dict]:
    with Session(engine) as session:
        stmt = select(Genre).order_by(Genre.name)
        genres = session.execute(stmt).scalars().all()
        return [
            {"id": g.id, "name": g.name}
            for g in genres
        ]
        
def add_book(title: str, year: int, isbn: str , description: str,
             genre_ids: list[int], author_ids: list[int]) -> int:
    with Session(engine) as session:
        
        book = Book(
            title = title,
            year = year,
            isbn = isbn,
            description = description
        )
        
        if author_ids:
            stmt = select(Author).where(Author.id.in_(author_ids))
            book.authors = list(session.execute(stmt).scalars().all())
            
        if genre_ids:
            stmt = select(Genre).where(Genre.id.in_(genre_ids))
            book.genres = list(session.execute(stmt).scalars().all())
            
        session.add(book)
        session.commit()    
    return book.id

# Для получения объекта по primary key есть удобный
# метод session.get(Class, id) — короче чем select с where.

def delete_book(book_id: int) -> None:
    with Session(engine) as session:
        # stmt = select(Book).where(Book.id == book_id)
        # book = session.execute(stmt).scalars().first()
        book = session.get(Book, book_id)        
        if book:
            session.delete(book)
            session.commit()
        else:
            raise ValueError(f"There is no such book with id: {book_id}")

def add_reader(full_name: str, email: str) -> int:
    with Session(engine) as session:
        reader = Reader(
            full_name = full_name,
            email = email
        )
        reader.registered_at = datetime.date.today()
        session.add(reader)
        session.commit()
    return reader.id

def get_all_readers() -> list[dict]:
    with Session(engine) as session:  
        stmt = (
            select(Reader, func.count(Loan.id))
            .outerjoin(Loan, and_(Reader.id == Loan.reader_id, Loan.returned_at.is_(None)))
            .order_by(Reader.full_name)
            .group_by(Reader.id)
        )
        result = session.execute(stmt).all()
        return [
            {
                "id": reader.id,
                "full_name": reader.full_name,
                "email": reader.email,
                "registered_at": reader.registered_at.isoformat(),
                "active loans": active_loans
            }
            for reader, active_loans in result
        ]
        
def delete_reader(reader_id: int) -> None:
    with Session(engine) as session:
        reader = session.get(Reader, reader_id)
        if reader is None:
            raise ValueError(f"There is no such reader with id: {reader_id}")

        active_count = session.scalar(
            select(func.count(Loan.id))
            .where(Loan.reader_id == reader_id, Loan.returned_at.is_(None))
        ) or 0
        if active_count > 0:
            raise ValueError("The reader has loans, must give the books back first")
        session.delete(reader)
        session.commit()

def get_active_loans() -> list[dict]:
    with Session(engine) as session:
        stmt = (
            select(Loan)
            .options(joinedload(Loan.book), joinedload(Loan.reader))
            .where(Loan.returned_at.is_(None))
            .order_by(Loan.loaned_at.desc())
        )
        loans = session.execute(stmt).scalars().all()
        return [
            {
                "id": loan.id,
                "loaned at": loan.loaned_at,
                "reader id": loan.reader.id,
                "reader name": loan.reader.full_name,
                "book id": loan.book.id,
                "book title": loan.book.title
            }
            for loan in loans
        ]
def create_loan(book_id: int, reader_id: int) -> int:
    with Session(engine) as session:
        book = session.get(Book, book_id)
        if book is None:
            raise ValueError(f"Book with id={book_id} is not found")
        reader = session.get(Reader, reader_id)
        if reader is None:
            raise ValueError(f"Reader with id={reader_id} is not found")

        already = session.scalar(
            select(func.count(Loan.id))
            .where(Loan.book_id == book_id, Loan.returned_at.is_(None))
        ) or 0
        if already > 0:
            raise ValueError("This book is loaned")

        loan = Loan(
            loaned_at=datetime.date.today(),
            book=book,
            book_id = book_id,
            reader_id = reader_id,
            reader=reader,
        )
        session.add(loan)
        session.commit()
        return loan.id
    
def return_book(loan_id: int) -> None:
    with Session(engine) as session:
        loan = session.get(Loan, loan_id)
        if loan is None:
            raise ValueError(f"There is no such loan with id {loan_id}")
        if loan.returned_at is not None:               # ← потом это, тут Pylance уже спокоен
            raise ValueError("Книга вже повернена")
        loan.returned_at = datetime.date.today()
        session.commit()
        
def seed_database() -> None:
    """Наповнює БД тестовими даними. Виконується лише якщо БД порожня."""
    with Session(engine) as session:
        if session.scalar(select(func.count(Author.id))):
            return

        # Автори (різні країни, епохи)
        shevchenko = Author(first_name="Тарас", last_name="Шевченко", birth_year=1814)
        ukrainka = Author(first_name="Леся", last_name="Українка", birth_year=1871)
        orwell = Author(first_name="George", last_name="Orwell", birth_year=1903)
        hemingway = Author(first_name="Ernest", last_name="Hemingway", birth_year=1899)
        tolkien = Author(first_name="J.R.R.", last_name="Tolkien", birth_year=1892)
        rowling = Author(first_name="J.K.", last_name="Rowling", birth_year=1965)
        king = Author(first_name="Stephen", last_name="King", birth_year=1947)
        murakami = Author(first_name="Haruki", last_name="Murakami", birth_year=1949)
        marquez = Author(first_name="Gabriel", last_name="García Márquez", birth_year=1927)
        kafka = Author(first_name="Franz", last_name="Kafka", birth_year=1883)
        austen = Author(first_name="Jane", last_name="Austen", birth_year=1775)
        christie = Author(first_name="Agatha", last_name="Christie", birth_year=1890)

        # Жанри
        poetry = Genre(name="Поезія")
        prose = Genre(name="Проза")
        drama = Genre(name="Драма")
        novel = Genre(name="Роман")
        fantasy = Genre(name="Фентезі")
        scifi = Genre(name="Наукова фантастика")
        horror = Genre(name="Жахи")
        detective = Genre(name="Детектив")
        dystopia = Genre(name="Антиутопія")
        classic = Genre(name="Класика")

        # Книги
        books = [
            Book(title="Кобзар", year=1840, isbn="9780000000001",
                 description="Збірка поезій українського генія",
                 authors=[shevchenko], genres=[poetry, classic]),
            Book(title="Лісова пісня", year=1911, isbn="9780000000002",
                 description="Драма-феєрія про Мавку",
                 authors=[ukrainka], genres=[drama, classic]),
            Book(title="1984", year=1949, isbn="9780000000007",
                 description="Тоталітарне суспільство майбутнього",
                 authors=[orwell], genres=[dystopia, novel]),
            Book(title="Колгосп тварин", year=1945, isbn="9780000000008",
                 description="Сатирична алегорія",
                 authors=[orwell], genres=[novel, dystopia]),
            Book(title="Старий і море", year=1952, isbn="9780000000009",
                 description="Притча про рибалку",
                 authors=[hemingway], genres=[prose, classic]),
            Book(title="Володар перснів", year=1954, isbn="9780000000010",
                 description="Епічна фентезі-сага",
                 authors=[tolkien], genres=[fantasy, novel]),
            Book(title="Гобіт", year=1937, isbn="9780000000011",
                 description="Пригоди Більбо Беггінса",
                 authors=[tolkien], genres=[fantasy]),
            Book(title="Гаррі Поттер і філософський камінь", year=1997, isbn="9780000000012",
                 description="Перша книга про юного чарівника",
                 authors=[rowling], genres=[fantasy, novel]),
            Book(title="Воно", year=1986, isbn="9780000000013",
                 description="Жах із міста Деррі",
                 authors=[king], genres=[horror, novel]),
            Book(title="Сяйво", year=1977, isbn="9780000000014",
                 description="Готель з привидами",
                 authors=[king], genres=[horror]),
            Book(title="Норвезький ліс", year=1987, isbn="9780000000015",
                 description="Меланхолійна історія кохання",
                 authors=[murakami], genres=[novel, prose]),
            Book(title="Кафка на пляжі", year=2002, isbn="9780000000016",
                 description="Магічний реалізм по-японськи",
                 authors=[murakami], genres=[novel]),
            Book(title="Сто років самотності", year=1967, isbn="9780000000017",
                 description="Історія родини Буендіа",
                 authors=[marquez], genres=[novel, classic]),
            Book(title="Перетворення", year=1915, isbn="9780000000018",
                 description="Грегор прокинувся комахою",
                 authors=[kafka], genres=[prose, classic]),
            Book(title="Гордість і упередження", year=1813, isbn="9780000000019",
                 description="Класичний англійський роман",
                 authors=[austen], genres=[novel, classic]),
            Book(title="Десять негренят", year=1939, isbn="9780000000020",
                 description="Детективна головоломка на острові",
                 authors=[christie], genres=[detective]),
            # Колаборація: Толкін + Орвелл (вигадана для демонстрації many-to-many)
            Book(title="Антологія класики XX століття", year=1990, isbn="9780000000021",
                 description="Збірка вибраних творів",
                 authors=[orwell, hemingway, tolkien],
                 genres=[classic, prose]),
        ]

        # Читачі
        readers = [
            Reader(full_name="Іван Петренко", email="ivan@test.ua",
                   registered_at=datetime.date(2024, 1, 15)),
            Reader(full_name="Олена Коваль", email="olena@test.ua",
                   registered_at=datetime.date(2024, 3, 22)),
            Reader(full_name="Андрій Мельник", email="andriy@test.ua",
                   registered_at=datetime.date(2024, 6, 1)),
            Reader(full_name="Марія Сидоренко", email="maria@test.ua",
                   registered_at=datetime.date(2025, 2, 10)),
        ]

        session.add_all([
            shevchenko, ukrainka, orwell, hemingway,
            tolkien, rowling, king, murakami, marquez, kafka, austen, christie,
        ])
        session.add_all([
            poetry, prose, drama, novel, fantasy, scifi, horror,
            detective, dystopia, classic,
        ])
        session.add_all(books)
        session.add_all(readers)
        session.flush()

        # Позики: 3 активні, 4 повернені
        loans = [
            # Активні
            Loan(book=books[2], reader=readers[0],     # 1984
                loaned_at=datetime.date(2025, 4, 10)),
            Loan(book=books[7], reader=readers[3],     # Гаррі Поттер
                loaned_at=datetime.date(2025, 4, 18)),
            Loan(book=books[10], reader=readers[1],    # Норвезький ліс
                loaned_at=datetime.date(2025, 4, 22)),
            # Повернені
            Loan(book=books[5], reader=readers[0],     # Володар перснів
                loaned_at=datetime.date(2025, 1, 5),
                returned_at=datetime.date(2025, 2, 1)),
            Loan(book=books[9], reader=readers[2],     # Сяйво
                loaned_at=datetime.date(2025, 2, 10),
                returned_at=datetime.date(2025, 3, 15)),
            Loan(book=books[15], reader=readers[1],    # Десять негренят
                loaned_at=datetime.date(2025, 3, 1),
                returned_at=datetime.date(2025, 3, 20)),
            Loan(book=books[12], reader=readers[3],    # Сто років самотності
                loaned_at=datetime.date(2024, 12, 1),
                returned_at=datetime.date(2025, 1, 10)),
        ]
        session.add_all(loans)  
        session.commit()