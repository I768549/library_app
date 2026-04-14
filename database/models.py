from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, SmallInteger, Date
import datetime
#SQLAlchemy моделі (Book, Author, Genre, Reader)
class Base(DeclarativeBase):
    pass

class Book(Base):
    __tablename__ = "book"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    year: Mapped[int] = mapped_column(SmallInteger)
    isbn: Mapped[str] = mapped_column(String(30), primary_key=True)#Example, 978-3-16-148410-0
    description: Mapped[str] = mapped_column(String(1488))

class Author(Base):
    __tablename__ = "author"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[int] = mapped_column(String(50))
    birth_year: Mapped[int] = mapped_column(SmallInteger)

class Genre(Base):
    __tablename__ = "genre"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), primary_key=True)

class Reader(Base):
    __tablename__ = "reader"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(100), primary_key=True)#Example, 978-3-16-148410-0
    registered_at: Mapped[datetime.datetime] = mapped_column(Date)
    
class Loan(Base):
    __tablename__ = "loan"
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[str] = mapped_column(String(255))
    reader_id: Mapped[int] = mapped_column(SmallInteger)
    loaned_at: Mapped[str] = mapped_column(String(30), primary_key=True)#Example, 978-3-16-148410-0
    returned_at: Mapped[str] = mapped_column(String(1488))


    