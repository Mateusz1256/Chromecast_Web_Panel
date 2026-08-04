from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FloatField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, NumberRange


class LoginForm(FlaskForm):
    username = StringField("Nazwa użytkownika", validators=[DataRequired()])
    password = PasswordField("Hasło", validators=[DataRequired()])
    submit = SubmitField("Zaloguj")


class SettingsForm(FlaskForm):
    cast_ip = StringField("Adres IP urządzenia Cast", validators=[DataRequired()])
    nas_lan_ip = StringField("Adres IP NAS w sieci LAN", validators=[DataRequired()])
    app_port = IntegerField(
        "Port aplikacji",
        validators=[DataRequired(), NumberRange(min=1, max=65535)],
    )
    media_directory = StringField("Katalog multimediów", validators=[DataRequired()])
    max_upload_mb = IntegerField(
        "Maksymalny rozmiar pliku w MB",
        validators=[DataRequired(), NumberRange(min=1, max=2048)],
    )
    max_volume = FloatField(
        "Maksymalna głośność",
        validators=[DataRequired(), NumberRange(min=0.01, max=1)],
    )
    default_audio_volume = FloatField(
        "Domyślna głośność audio",
        validators=[DataRequired(), NumberRange(min=0, max=1)],
    )
    cast_timeout_seconds = FloatField(
        "Limit czasu Cast w sekundach",
        validators=[DataRequired(), NumberRange(min=1, max=60)],
    )
    status_refresh_seconds = FloatField(
        "Odświeżanie statusu w sekundach",
        validators=[DataRequired(), NumberRange(min=1, max=120)],
    )
    monitor_app_changes = BooleanField("Monitoruj zmianę aktywnej aplikacji")
    submit = SubmitField("Zapisz")
