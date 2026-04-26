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

        # --- Автори ---
        # Українська література
        shevchenko = Author(first_name="Тарас", last_name="Шевченко", birth_year=1814)
        ukrainka = Author(first_name="Леся", last_name="Українка", birth_year=1871)

        # Художня література (оригінальні мови — англійська, японська, іспанська, німецька)
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

        # Філософія
        nietzsche = Author(first_name="Friedrich", last_name="Nietzsche", birth_year=1844)
        camus = Author(first_name="Albert", last_name="Camus", birth_year=1913)
        aurelius = Author(first_name="Marcus", last_name="Aurelius", birth_year=121)
        plato = Author(first_name="Plato", last_name="of Athens", birth_year=-427)
        suntzu = Author(first_name="Sun", last_name="Tzu", birth_year=-544)
        kant = Author(first_name="Immanuel", last_name="Kant", birth_year=1724)

        # Програмування
        hunt = Author(first_name="Andrew", last_name="Hunt", birth_year=1964)
        thomas = Author(first_name="David", last_name="Thomas", birth_year=1956)
        martin = Author(first_name="Robert C.", last_name="Martin", birth_year=1952)
        fowler = Author(first_name="Martin", last_name="Fowler", birth_year=1963)
        knuth = Author(first_name="Donald", last_name="Knuth", birth_year=1938)
        abelson = Author(first_name="Harold", last_name="Abelson", birth_year=1947)
        sussman = Author(first_name="Gerald J.", last_name="Sussman", birth_year=1947)
        gamma = Author(first_name="Erich", last_name="Gamma", birth_year=1961)
        helm = Author(first_name="Richard", last_name="Helm", birth_year=1960)
        johnson = Author(first_name="Ralph", last_name="Johnson", birth_year=1955)
        vlissides = Author(first_name="John", last_name="Vlissides", birth_year=1961)

        # --- Жанри ---
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
        philosophy = Genre(name="Філософія")
        essay = Genre(name="Есе")
        programming = Genre(name="Програмування")
        nonfiction = Genre(name="Нон-фікшн")

        # --- Книги ---
        books = [
            # Українські — в оригіналі
            Book(title="Кобзар", year=1840, isbn="9780000000001",
                 description="Збірка поезій Тараса Шевченка",
                 authors=[shevchenko], genres=[poetry, classic]),
            Book(title="Лісова пісня", year=1911, isbn="9780000000002",
                 description="Драма-феєрія про Мавку",
                 authors=[ukrainka], genres=[drama, classic]),

            # Іноземні — оригінальні назви
            Book(title="1984", year=1949, isbn="9780000000007",
                 description="A dystopian vision of a totalitarian future society",
                 authors=[orwell], genres=[dystopia, novel]),
            Book(title="Animal Farm", year=1945, isbn="9780000000008",
                 description="A satirical allegory about a farmyard revolution",
                 authors=[orwell], genres=[novel, dystopia]),
            Book(title="The Old Man and the Sea", year=1952, isbn="9780000000009",
                 description="A short novel about an aging Cuban fisherman",
                 authors=[hemingway], genres=[prose, classic]),
            Book(title="The Lord of the Rings", year=1954, isbn="9780000000010",
                 description="An epic high-fantasy trilogy set in Middle-earth",
                 authors=[tolkien], genres=[fantasy, novel]),
            Book(title="The Hobbit", year=1937, isbn="9780000000011",
                 description="Bilbo Baggins reluctantly joins a quest to reclaim a lost dwarven kingdom",
                 authors=[tolkien], genres=[fantasy]),
            Book(title="Harry Potter and the Philosopher's Stone", year=1997, isbn="9780000000012",
                 description="A young wizard discovers his heritage at Hogwarts",
                 authors=[rowling], genres=[fantasy, novel]),
            Book(title="It", year=1986, isbn="9780000000013",
                 description="A shape-shifting horror terrorizes the children of Derry, Maine",
                 authors=[king], genres=[horror, novel]),
            Book(title="The Shining", year=1977, isbn="9780000000014",
                 description="A family caretakes a remote, haunted hotel through winter",
                 authors=[king], genres=[horror]),
            Book(title="Norwegian Wood", year=1987, isbn="9780000000015",
                 description="A melancholy coming-of-age love story set in 1960s Tokyo",
                 authors=[murakami], genres=[novel, prose]),
            Book(title="Kafka on the Shore", year=2002, isbn="9780000000016",
                 description="Two parallel narratives weave through Japanese magical realism",
                 authors=[murakami], genres=[novel]),
            Book(title="One Hundred Years of Solitude", year=1967, isbn="9780000000017",
                 description="The multi-generational saga of the Buendía family in Macondo",
                 authors=[marquez], genres=[novel, classic]),
            Book(title="The Metamorphosis", year=1915, isbn="9780000000018",
                 description="Gregor Samsa wakes up transformed into a giant insect",
                 authors=[kafka], genres=[prose, classic]),
            Book(title="Pride and Prejudice", year=1813, isbn="9780000000019",
                 description="A classic English novel of manners and marriage",
                 authors=[austen], genres=[novel, classic]),
            Book(title="And Then There Were None", year=1939, isbn="9780000000020",
                 description="Ten strangers are lured to an isolated island and killed one by one",
                 authors=[christie], genres=[detective]),

            # Колаборація — many-to-many демо
            Book(title="20th Century Classics Anthology", year=1990, isbn="9780000000021",
                 description="A curated collection of seminal works from the 1900s",
                 authors=[orwell, hemingway, tolkien],
                 genres=[classic, prose]),

            # Філософія
            Book(title="Thus Spoke Zarathustra", year=1883, isbn="9780000000030",
                 description="A philosophical novel introducing the Übermensch and eternal recurrence",
                 authors=[nietzsche], genres=[philosophy, classic]),
            Book(title="Beyond Good and Evil", year=1886, isbn="9780000000031",
                 description="A critique of past philosophers and traditional morality",
                 authors=[nietzsche], genres=[philosophy, essay]),
            Book(title="The Myth of Sisyphus", year=1942, isbn="9780000000032",
                 description="An essay on absurdism and the meaning of life",
                 authors=[camus], genres=[philosophy, essay]),
            Book(title="The Stranger", year=1942, isbn="9780000000033",
                 description="A detached Algerian clerk drifts into a senseless killing",
                 authors=[camus], genres=[novel, philosophy, classic]),
            Book(title="Meditations", year=180, isbn="9780000000034",
                 description="Personal stoic reflections of a Roman emperor",
                 authors=[aurelius], genres=[philosophy, classic]),
            Book(title="The Republic", year=-375, isbn="9780000000035",
                 description="A Socratic dialogue on justice and the ideal state",
                 authors=[plato], genres=[philosophy, classic]),
            Book(title="The Art of War", year=-500, isbn="9780000000036",
                 description="An ancient Chinese treatise on military strategy",
                 authors=[suntzu], genres=[philosophy, essay, classic]),
            Book(title="Critique of Pure Reason", year=1781, isbn="9780000000037",
                 description="Kant's foundational inquiry into the limits of human knowledge",
                 authors=[kant], genres=[philosophy]),

            # Програмування
            Book(title="The Pragmatic Programmer", year=1999, isbn="9780000000040",
                 description="Practical advice on craftsmanship for software developers",
                 authors=[hunt, thomas], genres=[programming, nonfiction]),
            Book(title="Clean Code", year=2008, isbn="9780000000041",
                 description="A handbook of agile software craftsmanship by Uncle Bob",
                 authors=[martin], genres=[programming, nonfiction]),
            Book(title="Refactoring: Improving the Design of Existing Code", year=1999,
                 isbn="9780000000042",
                 description="Catalog of code smells and the refactorings that fix them",
                 authors=[fowler], genres=[programming, nonfiction]),
            Book(title="Design Patterns: Elements of Reusable Object-Oriented Software",
                 year=1994, isbn="9780000000043",
                 description="The original Gang of Four catalog of 23 OOP design patterns",
                 authors=[gamma, helm, johnson, vlissides],
                 genres=[programming, nonfiction, classic]),
            Book(title="Structure and Interpretation of Computer Programs", year=1985,
                 isbn="9780000000044",
                 description="The legendary MIT introductory text using Scheme — known as SICP",
                 authors=[abelson, sussman], genres=[programming, classic]),
            Book(title="The Art of Computer Programming, Vol. 1", year=1968,
                 isbn="9780000000045",
                 description="Knuth's foundational treatise on algorithms and analysis",
                 authors=[knuth], genres=[programming, classic, nonfiction]),
            Book(title="Clean Architecture", year=2017, isbn="9780000000046",
                 description="A craftsman's guide to software structure and design",
                 authors=[martin], genres=[programming, nonfiction]),
        ]

        # --- Читачі ---
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
            nietzsche, camus, aurelius, plato, suntzu, kant,
            hunt, thomas, martin, fowler, knuth, abelson, sussman,
            gamma, helm, johnson, vlissides,
        ])
        session.add_all([
            poetry, prose, drama, novel, fantasy, scifi, horror,
            detective, dystopia, classic, philosophy, essay,
            programming, nonfiction,
        ])
        session.add_all(books)
        session.add_all(readers)
        session.flush()

        # --- Позики: 3 активні, 4 повернені ---
        # Індекси відповідають порядку у books вище
        loans = [
            # Активні
            Loan(book=books[2], reader=readers[0],      # 1984
                 loaned_at=datetime.date(2025, 4, 10)),
            Loan(book=books[7], reader=readers[3],      # Harry Potter
                 loaned_at=datetime.date(2025, 4, 18)),
            Loan(book=books[10], reader=readers[1],     # Norwegian Wood
                 loaned_at=datetime.date(2025, 4, 22)),
            # Повернені
            Loan(book=books[5], reader=readers[0],      # Lord of the Rings
                 loaned_at=datetime.date(2025, 1, 5),
                 returned_at=datetime.date(2025, 2, 1)),
            Loan(book=books[9], reader=readers[2],      # The Shining
                 loaned_at=datetime.date(2025, 2, 10),
                 returned_at=datetime.date(2025, 3, 15)),
            Loan(book=books[15], reader=readers[1],     # And Then There Were None
                 loaned_at=datetime.date(2025, 3, 1),
                 returned_at=datetime.date(2025, 3, 20)),
            Loan(book=books[12], reader=readers[3],     # One Hundred Years of Solitude
                 loaned_at=datetime.date(2024, 12, 1),
                 returned_at=datetime.date(2025, 1, 10)),
        ]
        session.add_all(loans)
        session.commit()