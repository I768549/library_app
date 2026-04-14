from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, SmallInteger, Date, Text, ForeignKey
import datetime
#SQLAlchemy моделі (Book, Author, Genre, Reader)
class Base(DeclarativeBase):
    pass

class Book(Base):
    __tablename__ = "book"
    #Primary Key exists to uniquely identify the row itself
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    year: Mapped[int] = mapped_column(SmallInteger)
    #Unique Constraint exists to protect the integrity of the data in a specific column
    isbn: Mapped[str] = mapped_column(String(30), unique=True) #Example, 978-3-16-148410-0
    description: Mapped[str] = mapped_column(Text)
    
    def __repr__(self):
        return f"{self.title} was published in {self.year}, it's isbn is {self.isbn}"

class Author(Base):
    __tablename__ = "author"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    birth_year: Mapped[int] = mapped_column(SmallInteger)

class Genre(Base):
    __tablename__ = "genre"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)

class Reader(Base):
    __tablename__ = "reader"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(100), unique=True)#Example, 978-3-16-148410-0
    registered_at: Mapped[datetime.datetime] = mapped_column(Date)
    #Has one to many relationship with loan
    loan: Mapped[list["Loan"]] = relationship(back_populates="reader")
    
class Loan(Base):
    __tablename__ = "loan"
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[str] = mapped_column(String(255))
    loaned_at: Mapped[datetime.datetime] = mapped_column(Date) #Example, 978-3-16-148410-0
    returned_at: Mapped[datetime.datetime] = mapped_column(Date)
    #relationship many to one with Reader
    reader_id: Mapped[int] = mapped_column(ForeignKey("reader.id"))
    reader: Mapped["Reader"] = relationship(back_populates="loan")

"""
Notes: FK goes on the "many" side
back_populates on both sides — keeps both directions in sync. Use the attribute name, not the table name.
Mapped[list["Post"]] signals it's a collection. Mapped["User"] (no list) signals it's a single object.
Cascade — by default, SQLAlchemy doesn't cascade deletes. If you want deleting a user to kill their posts:
posts: Mapped[list["Post"]] = relationship(
    back_populates="author",
    cascade="all, delete-orphan"
)
That's basically it. FK on child, relationship() on both, back_populates to link them.
"""