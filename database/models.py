from __future__ import annotations # now the orded of annotations doesn't matter
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, SmallInteger, Date, Text, ForeignKey, Column, Table
from typing import List
import datetime
#SQLAlchemy моделі (Book, Author, Genre, Reader)
class Base(DeclarativeBase):
    pass

# Book and Author association table (many-to-many)
book_author = Table(
    "book_author",
    Base.metadata,
    Column("author_id", ForeignKey("author.id"), primary_key=True),
    Column("book_id", ForeignKey("book.id"), primary_key=True)
)

# Book and Genre association table (many-to-many)
book_genre = Table(
    "book_genre",
    Base.metadata,
    Column("book_id", ForeignKey("book.id"), primary_key=True),
    Column("genre_id", ForeignKey("genre.id"), primary_key=True)
)

class Author(Base):
    __tablename__ = "author"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    birth_year: Mapped[int] = mapped_column(SmallInteger)
    #Many to many with Book
    books: Mapped[List[Book]] = relationship(secondary=book_author, back_populates="authors")
    
class Book(Base):
    __tablename__ = "book"
    #Primary Key exists to uniquely identify the row itself
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    year: Mapped[int] = mapped_column(SmallInteger)
    #Unique Constraint exists to protect the integrity of the data in a specific column
    isbn: Mapped[str] = mapped_column(String(30), unique=True) #Example, 978-3-16-148410-0
    description: Mapped[str] = mapped_column(Text)
    authors: Mapped[List[Author]] = relationship(secondary=book_author, back_populates="books")
    genres: Mapped[List[Genre]] = relationship(secondary=book_genre, back_populates="books")
    loans: Mapped[List[Loan]] = relationship(back_populates="book")
         
    def __repr__(self):
        return f"{self.title} was published in {self.year}, it's isbn is {self.isbn}"
        
    
class Genre(Base):
    __tablename__ = "genre"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    books: Mapped[List[Book]] = relationship(secondary=book_genre, back_populates="genres")

class Reader(Base):
    __tablename__ = "reader"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(100), unique=True)#Example, 978-3-16-148410-0
    registered_at: Mapped[datetime.date] = mapped_column(Date)
    #Has one to many relationship with loan
    loans: Mapped[List[Loan]] = relationship(back_populates="reader")
    
class Loan(Base):
    __tablename__ = "loan"
    id: Mapped[int] = mapped_column(primary_key=True)
    loaned_at: Mapped[datetime.date] = mapped_column(Date) #Example, 978-3-16-148410-0
    returned_at: Mapped[datetime.date | None] = mapped_column(Date)
    #relationship many to one Book with Reader
    reader_id: Mapped[int] = mapped_column(ForeignKey("reader.id"))
    reader: Mapped[Reader] = relationship(back_populates="loans")
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"))
    book: Mapped[Book] = relationship(back_populates="loans")

"""
A one to many relationship places a foreign key on the child table referencing the parent.
relationship() is then specified on the parent, as referencing a collection of items represented by the child

Many to one places a foreign key in the parent table referencing the child. relationship()
is declared on the parent, where a new scalar-holding attribute will be created

One To One is essentially a One To Many relationship from a foreign key perspective, 
but indicates that there will only be one row at any time that refers to a particular parent row.

Many to Many adds an association table between two classes
The association table is nearly always given as a Core Table object or other Core selectable such as a 
Join object, and is indicated by the relationship.secondary argument to relationship(). 
Usually, the Table uses the MetaData object associated with the declarative base class,
so that the ForeignKey directives can locate the remote tables with which to link:
Setting Bi-Directional Many-to-many

For a bidirectional relationship, both sides of the relationship contain a collection.
Specify using relationship.back_populates, and for each relationship() specify the common association table
"""