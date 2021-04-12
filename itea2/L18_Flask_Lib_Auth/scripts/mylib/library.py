from .base_class_sql import Base

from .book import Book
from .reader import Reader

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

ERROR = -1
DONE = 0


class Library(dict):
    def __init__(self):
        super().__init__()

        self['books'] = {}
        self['readers'] = {}

        self.e = create_engine('postgresql://postgres:123@localhost:5432/postgres_orm')

        # create tables
        Base.metadata.create_all(self.e)

        # create session
        self.session = Session(bind=self.e)

        self.load_data_from_db()

    def load_data_from_db(self) -> None:
        """
        Функция для загрузки данных из БД в класс Library.
        Загружает список книг и читателей (self['books'], self['readers']).

        :return: None
        """
        for reader in self.session.query(Reader):
            self['readers'][reader.id] = reader

        for book in self.session.query(Book):
            self['books'][book.id] = book

    def get_all_book(self) -> list:
        """
        Выводит список всех книг, которые есть в библиотеке.

        :return: Список всех книг (type: list)
        """
        ret = list(map(lambda book: book.to_dict(), self['books'].values()))
        return sorted(ret, key=lambda book: book['id'])

    def get_available_books(self) -> list:
        """
        Выводит список книг, которые находятся в библиотеке.

        :return: Список всех книг (type: list)
        """
        ret = [book.to_dict() for book in self['books'].values() if book.reader_id is None]
        return sorted(ret, key=lambda book: book['id'])

    def get_reader_books(self, id_reader: int) -> list:
        """
        Выводит список книг, которые находятся у конкретного пользователя.

        :param id_reader: id конкретного пользователя
        :return: Список книг (type: list)
        """
        return sorted(self['readers'][id_reader].books, key=lambda book: book.id)

    def add_book(self, book: Book) -> (int, str):
        """
        Добавляет книгу в список и в БД.

        :param book: книга для добавления
        :return: код возврата и сообщение с результатом
        """
        self.session.add(book)
        self.session.commit()
        self['books'][book.id] = book

        return DONE, f'Книга "{book.title}" успешно добавлена в библиотеку.'

    def add_books(self, books: list) -> (int, str):
        """
        Добавляет список книг в Library и в БД.

        :param books: список книг
        :return: код возврата и сообщение с результатом
        """
        for book in books:
            self.session.add(book)

        self.session.commit()

        for book in books:
            self['books'][book.id] = book

        return DONE, f'Все книги успешно добавлены в библиотеку.'

    def delete_book(self, id_book: int) -> (int, str):
        """
        Удаляет книгу из списка Library и БД.

        :param id_book: книга для удаления
        :return: код возврата и сообщение с результатом
        """
        if id_book not in self['books'].keys():
            return ERROR, f'Книга с id {id_book} нет в библиотеке.'

        self.session.delete(self['books'][id_book])
        self.session.commit()
        _ = self['books'].pop(id_book, None)

        return DONE, f'Книга c id {id_book} удалена из библиотеки.'

    def delete_books(self, id_book_list: list) -> (int, str):
        """
        Удаляет спиок книг из списка Library и БД.
        Если хоть одной книги нет, операция отменяется.

        :param id_book_list: список с id книг, которые нужно удалить
        :return: код возврата и сообщение с результатом
        """
        for id_book in id_book_list:
            if id_book not in self['books'].keys():
                return ERROR, f'Книга с id {id_book} нет в библиотеке.'

        for id_book in id_book_list:
            self.session.delete(self['books'][id_book])

        self.session.commit()

        for id_book in id_book_list:
            _ = self['books'].pop(id_book, None)

        return DONE, f'Книги c id {id_book_list} удалены из библиотеки.'

    def add_reader(self, reader: Reader) -> (int, str):
        """
        Добавляет читателя (Reader) в Library и БД.

        :param reader: читатель для добавления
        :return: код возврата и сообщение с результатом
        """
        self.session.add(reader)
        self.session.commit()
        self['readers'][reader.id] = reader

        return DONE, f'Читатель "{reader}" успешно добавлен в библиотеку.'

    def get_reader_by_email(self, email: str):
        """
        Возвращает Reader из базы по email
        :param email: email reader
        :return: Reader or None
        """
        return self.session.query(Reader).filter(Reader.email == email).first()

    def give_books(self, id_reader: int, id_book_list: list):
        """
        Отдает книги (id_books) читателю (id_reader).
        Запись идет в БД.
        Если читателя нет - отмена операции.
        Если хоть одной книги нет в библиотеки или в наличии - отмена операции.

        :param id_reader: id читателя, которому отдают книги
        :param id_book_list: список id книг, которые отдают
        :return: код возврата и сообщение с результатом
        """
        if id_reader not in self['readers'].keys():
            return ERROR, f'Читателя с номером {id_reader} не зарегистрировано в библиотеке.'

        for id_book in id_book_list:
            if id_book not in self['books'].keys():
                return ERROR, f'Книги с номером {id_book} нет в библиотеке.'

            if self['books'][id_book].reader_id is not None:
                return ERROR, f'Книги с номером {id_book} нет в наличии.'

            self['books'][id_book].reader_id = self['readers'][id_reader].id

        self.session.commit()

        return DONE, None

    def return_books(self, id_reader: int, id_book_list: list):
        """
        Возврат книг (id_books) от читателя (id_reader) в библиотеку.
        Запись идет в БД.
        Если читателя нет - отмена операции.
        Если хоть одной книги нет в библиотеки или в наличии - отмена операции.

        :param id_reader: id читателя, который отдаёт книги
        :param id_book_list: список id книг, которые возвращает читатель
        :return: код возврата и сообщение с результатом
        """
        if id_reader not in self['readers'].keys():
            return ERROR, f'Читателя с номером {id_reader} не зарегистрировано в библиотеке.'

        for id_book in id_book_list:
            if id_book not in self['books'].keys():
                return ERROR, f'Книги с номером {id_book} нет в библиотеке.'

            if self['books'][id_book].reader_id is None:
                return ERROR, f'Книга с номером {id_book} находится в библиотеке.'

            self['books'][id_book].reader_id = None

        self.session.commit()

        return DONE, None
