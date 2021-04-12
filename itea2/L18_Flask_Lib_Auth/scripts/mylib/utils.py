from .book import Book


def read_list_books(filename):
    books = []

    with open(filename, encoding='utf-8') as f:
        for line in f:
            line = line.strip().split('$!$')

            books.append(Book(line[0], line[1], int(line[2])))

    return books
