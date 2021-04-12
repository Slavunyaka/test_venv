from .base_class_sql import Base

from sqlalchemy import Column, Integer, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship


class Book(Base):
    __tablename__ = 'book'

    def __init__(self, title, author, years):
        self.title = title
        self.author = author
        self.years = years

        self.reader_id = None

    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    years = Column(Integer)

    reader_id = Column(Integer, ForeignKey('reader.id'))

    reader = relationship("Reader", backref="books")

    def to_dict(self):
        return dict(
            id=self.id,
            title=self.title,
            author=self.author,
            years=self.years
            # reader=f'{self.reader.name} {self.reader.surname}' if self.reader_id is not None else f'В наличии'
        )