from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class SettingsForm(FlaskForm):
    cast_ip = StringField("Cast IP", validators=[DataRequired()])
    nas_lan_ip = StringField("NAS LAN IP", validators=[DataRequired()])
    app_port = IntegerField(
        "Application port",
        validators=[DataRequired(), NumberRange(min=1, max=65535)],
    )
    media_directory = StringField("Media directory", validators=[DataRequired()])
    max_upload_mb = IntegerField(
        "Max upload MB",
        validators=[DataRequired(), NumberRange(min=1, max=2048)],
    )
    max_volume = FloatField(
        "Max volume",
        validators=[DataRequired(), NumberRange(min=0.01, max=1)],
    )
    default_audio_volume = FloatField(
        "Default audio volume",
        validators=[DataRequired(), NumberRange(min=0, max=1)],
    )
    cast_timeout_seconds = FloatField(
        "Cast timeout seconds",
        validators=[DataRequired(), NumberRange(min=1, max=60)],
    )
    status_refresh_seconds = FloatField(
        "Status refresh seconds",
        validators=[DataRequired(), NumberRange(min=1, max=120)],
    )
    submit = SubmitField("Save")
