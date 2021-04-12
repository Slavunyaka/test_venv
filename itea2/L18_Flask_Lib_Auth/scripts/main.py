from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, current_user, logout_user

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mylib.library import Library, ERROR, DONE
from mylib.book import Book
from mylib.reader import Reader
from mylib.utils import read_list_books

app = Flask(__name__,
            template_folder='../site/templates',
            static_folder='../site/static')
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'Hk4726AcVi82py5SrMnJFM824Ey3sXtp'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

e = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html'])
)

# create lib
lib = Library()

# Если книг в библе нет, то прочитаем файл books.txt
# и заполним нашу библиотеку
if not len(lib['books']):
    lib.add_books(read_list_books('mylib/books.txt'))

# # Если нет ни единого читателя, то создадим тестового
if not len(lib['readers']):
    lib.add_reader(Reader('Ivan', 'Petrov',
                          'ivan_ptrov@gmail.com',
                          'password',
                          1990))


@app.route('/')
@app.route('/index')
def index_page():
    return render_template('index.html')


@app.route('/books', methods=['GET'])
def api_get_all_books():
    return render_template('books.html', books=lib.get_all_book())


@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def api_add_book():
    if request.method == 'POST':
        title_book = request.form.get('title')
        author_book = request.form.get('author')
        year_book = request.form.get('year')

        if not (title_book and author_book and year_book):
            return render_template('add_book.html', message='Введены некорректные данные')

        if not year_book.isnumeric():
            return render_template('add_book.html', message='Введен некорректный год издания')

        _, message = lib.add_book(Book(title_book, author_book, int(year_book)))

        return render_template('add_book.html', message=message)

    return render_template('add_book.html')


@app.route('/take_book', methods=['GET', 'POST'])
@login_required
def api_take_book():
    if request.method == 'POST':
        id_books = [int(i) for i in request.form.keys() if i.isnumeric()]
        id_books = list(filter(lambda x: x in lib['books'], id_books))

        if len(id_books):
            _, message = lib.give_books(int(current_user.get_id()), id_books)
            return render_template('take_book.html',
                                   books=lib.get_available_books(),
                                   message=message)

    return render_template('take_book.html', books=lib.get_available_books())


@app.route('/delete_book', methods=['GET', 'POST'])
@login_required
def api_delete_book():
    if request.method == 'POST':
        id_books = [int(i) for i in request.form.keys() if i.isnumeric()]
        id_books = list(filter(lambda x: x in lib['books'], id_books))

        if len(id_books):
            _, message = lib.delete_books(id_books)
            return render_template('delete_book.html',
                                   books=lib.get_all_book(),
                                   message=message)

    return render_template('delete_book.html', books=lib.get_all_book())


@app.route('/return_book', methods=['GET', 'POST'])
@login_required
def api_return_book():
    if request.method == 'POST':
        id_books = [int(i) for i in request.form.keys() if i.isnumeric()]
        id_books = list(filter(lambda x: x in lib['books'], id_books))

        if len(id_books):
            _, message = lib.return_books(int(current_user.get_id()), id_books)
            return render_template('return_book.html',
                                   books=lib.get_reader_books(int(current_user.get_id())),
                                   message=message)

    return render_template('return_book.html', books=lib.get_reader_books(int(current_user.get_id())))


@login_manager.user_loader
def load_user(user_id):
    return lib['readers'][int(user_id)]


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index_page'))

    message = ''
    if request.method == 'POST':
        email = request.form.get('email')
        psw = request.form.get('psw')
        next_url = request.args.get('next', '')

        if email and psw:
            reader = lib.get_reader_by_email(email)
            if reader and reader.check_psw(psw):
                login_user(reader)
                if next_url:
                    return redirect(next_url)
                return redirect(url_for("index_page"))
            else:
                message = "Invalid username/password"

    return render_template('login.html', message=message)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index_page'))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for('index_page'))

    if request.method == 'POST':
        email = request.form.get('email')
        psw = request.form.get('psw')
        name = request.form.get('name')
        surname = request.form.get('surname')
        years = request.form.get('years')

        if not (email and psw and name and surname and years):
            return render_template('registration.html', message='Введены некорректные данные')

        if not years.isnumeric():
            return render_template('registration.html', message='Введен некорректный год рождения')

        if lib.get_reader_by_email(email) is not None:
            return render_template('registration.html', message='Пользователь с таким email уже зарегестрирован')

        code, message = lib.add_reader(Reader(name, surname, email, psw, years))

        if code == DONE:
            flash('Now you can login.')
            return redirect(url_for('login'))
        else:
            return render_template('registration.html', message=message)

    return render_template('registration.html')


if __name__ == "__main__":
    app.run()
