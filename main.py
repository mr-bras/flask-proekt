from flask import Flask, render_template, redirect, request, make_response, abort, jsonify
from data.users import User
from data.chats import Chats
from data.messages import Messages
from forms.user import RegisterForm
from forms.loginform import LoginForm
from flask_login import LoginManager
from flask_login import login_user, logout_user, login_required, current_user
from forms.jobs import QuestForm
from data import db_session
import gpt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


def main():
    db_session.global_init("db/chats.db")
    app.run()



@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        chats = db_sess.query(Chats).filter((Chats.user == current_user) & (Chats.is_archived != True))
    else:
        chats = []
    return render_template("index.html", chats=chats)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            position=form.position.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/new", methods=['GET', 'POST'])
def new_ask():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        chats = db_sess.query(Chats).filter((Chats.user == current_user) & (Chats.is_archived != True))
        print(1)
    else:
        chats = db_sess.query(Chats).filter(Chats.is_archived != True)
    form = QuestForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        chat = Chats()
        ask = form.ask.data
        chat.name = ask
        current_user.chats.append(chat)
        message1 = Messages()
        message1.role = 'user'
        message1.text = ask
        chat.messages.append(message1)
        message2 = Messages()
        message2.role = 'assistant'
        message2.text = gpt.ask_gpt([{'role': 'assistant', 'content': ask}])
        chat.messages.append(message2)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template("new_ask.html", form=form, chats=chats)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/archive')
def archive():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        chats = db_sess.query(Chats).filter((Chats.user == current_user) & (Chats.is_archived == True))
    else:
        chats = []
    return render_template('index.html', title='Главная', chats=chats)


@app.route('/chats/<int:id>', methods=['GET', 'POST'])
@login_required
def chat(id):
    form = QuestForm()
    history = []
    db_sess = db_session.create_session()
    messages = db_sess.query(Messages).filter(Messages.chats_id == id)
    for i in messages:
        history.append({'role': i.role, 'content': i.text})
    if current_user.is_authenticated:
        chats = db_sess.query(Chats).filter((Chats.user == current_user) & (Chats.is_archived != True))
    else:
        chats = db_sess.query(Chats).filter(Chats.is_archived != True)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        chat = db_sess.query(Chats).filter(Chats.id == id).first()
        ask = form.ask.data
        form.ask.data = ''
        message1 = Messages()
        message1.role = 'user'
        message1.text = ask
        chat.messages.append(message1)
        history.append({'role': 'user', 'content': ask})
        message2 = Messages()
        message2.role = 'assistant'
        res = gpt.ask_gpt(messages=history)
        message2.text = res
        history.append({'role': 'user', 'content': res})
        chat.messages.append(message2)
        db_sess.merge(current_user)
        db_sess.commit()

    return render_template('chats.html',
                           title='Редактирование новости',
                           form=form,
                           chat=messages,
                           chats=chats
                           )


@app.route('/archive/<int:id>', methods=['GET', 'POST'])
@login_required
def achivator(id):
    db_sess = db_session.create_session()
    chat = db_sess.query(Chats).filter(Chats.id == id).first()
    print(chat.is_archived)
    if chat:
        if chat.is_archived:
            chat.is_archived = False
        else:
            chat.is_archived = True
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


if __name__ == '__main__':
    main()
