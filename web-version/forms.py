# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired

class ConfigForm(FlaskForm):
    serial = StringField('Seriennummer:', validators=[DataRequired()])
    maximum_wr = IntegerField('WR max. Leistung:', validators=[DataRequired()])
    minimum_wr = IntegerField('WR min. Leistung:', validators=[DataRequired()])
    dtu_ip = StringField('DTU IP:', validators=[DataRequired()])
    dtu_nutzer = StringField('DTU Benutzer:', validators=[DataRequired()])
    dtu_passwort = StringField('DTU Passwort:', validators=[DataRequired()])
    shelly_ip = StringField('Shelly IP:', validators=[DataRequired()])
    manual_limit = IntegerField('Manuelles Limit (W):')
    submit = SubmitField('Speichern')
