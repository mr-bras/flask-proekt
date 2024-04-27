from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired


class QuestForm(FlaskForm):
    ask = StringField('введите запрос', validators=[DataRequired()])
    submit = SubmitField('отправить')