from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class QuestForm(FlaskForm):
    ask = StringField('введите запрос', validators=[DataRequired()])
    submit = SubmitField('отправить')