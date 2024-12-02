from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, EmailField, SubmitField, SelectField, IntegerField, TextAreaField, DateTimeLocalField, FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from datetime import datetime

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Masuk')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Konfirmasi Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Daftar')

class BookingForm(FlaskForm):
    ticket_count = IntegerField('Jumlah Tiket', 
                              validators=[DataRequired(), NumberRange(min=1, max=10)])
    payment_method = SelectField('Metode Pembayaran',
                               choices=[('gopay', 'GoPay'),
                                      ('ovo', 'OVO'),
                                      ('dana', 'DANA'),
                                      ('direct', 'Bayar Langsung')],
                               validators=[DataRequired()])
    submit = SubmitField('Konfirmasi Pemesanan')

class ShowForm(FlaskForm):
    title = StringField('Judul', validators=[DataRequired(), Length(min=2, max=200)])
    production = StringField('Produksi', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Deskripsi', validators=[DataRequired()])
    location = StringField('Lokasi', validators=[DataRequired(), Length(min=2, max=200)])
    poster = FileField('Poster', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Hanya gambar yang diperbolehkan!')])
    submit = SubmitField('Simpan')

class ScheduleForm(FlaskForm):
    date = DateTimeLocalField('Tanggal & Waktu', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    available_tickets = IntegerField('Jumlah Tiket', validators=[DataRequired(), NumberRange(min=1)])
    price = FloatField('Harga', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Simpan')
