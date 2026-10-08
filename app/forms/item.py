from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class ItemForm(FlaskForm):
    title = StringField(_l("Title"), validators=[DataRequired(), Length(max=200)])
    submit = SubmitField(_l("Add"))
