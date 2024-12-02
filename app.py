from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import string
from forms import LoginForm, RegisterForm, BookingForm, ShowForm, ScheduleForm
from functools import wraps
import os
from werkzeug.utils import secure_filename
import time
import logging
from logging.handlers import RotatingFileHandler
from flask_caching import Cache
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///saksikan.db')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'posters')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Configure logging
if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/saksikan.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Saksikan startup')

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Show(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    production = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    poster_path = db.Column(db.String(200))
    location = db.Column(db.String(200))
    schedules = db.relationship('Schedule', backref='show', lazy=True, cascade='all, delete-orphan')

class Schedule(db.Model):
    __tablename__ = 'schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    bookings = db.relationship('Booking', backref='schedule', lazy=True, cascade='all, delete-orphan')

    def __init__(self, show_id, date, available_seats, price, is_active=True):
        self.show_id = show_id
        self.date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S') if isinstance(date, str) else date
        self.available_seats = available_seats
        self.price = price
        self.is_active = is_active

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    ticket_count = db.Column(db.Integer, nullable=False)
    booking_code = db.Column(db.String(20), unique=True, nullable=False)
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
# @cache.cached(timeout=300)  # Cache for 5 minutes
def index():
    page = request.args.get('page', 1, type=int)
    current_time = datetime.now()
    app.logger.info(f"Current time: {current_time}")
    
    # Query shows that have active schedules
    shows = Show.query.join(Schedule).filter(
        Schedule.is_active == True,
        Schedule.date >= current_time
    ).group_by(Show.id).paginate(
        page=page,
        per_page=9,
        error_out=False
    )
    
    # Log the number of shows found
    app.logger.info(f"Number of shows found: {shows.total}")
    
    return render_template('index.html', shows=shows)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Email atau password salah', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                   email=form.email.data)
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registrasi berhasil! Silakan login', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Email sudah digunakan', 'danger')
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/show/<int:show_id>')
def show_detail(show_id):
    show = Show.query.get_or_404(show_id)
    return render_template('show_detail.html', show=show, now=datetime.now())

def generate_booking_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@app.route('/book/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def book_ticket(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    form = BookingForm()
    
    if form.validate_on_submit():
        if form.ticket_count.data > schedule.available_seats:
            flash('Jumlah tiket tidak tersedia', 'danger')
            return redirect(url_for('book_ticket', schedule_id=schedule_id))
        
        booking_code = generate_booking_code()
        booking = Booking(
            user_id=current_user.id,
            schedule_id=schedule_id,
            ticket_count=form.ticket_count.data,
            booking_code=booking_code,
            payment_method=form.payment_method.data,
            payment_status='pending'
        )
        
        schedule.available_seats -= form.ticket_count.data
        
        try:
            db.session.add(booking)
            db.session.commit()
            flash('Pemesanan berhasil!', 'success')
            return redirect(url_for('payment', booking_id=booking.id))
        except IntegrityError:
            db.session.rollback()
            flash('Gagal memesan tiket', 'danger')
    
    return render_template('booking.html', schedule=schedule, form=form)

@app.route('/payment/<int:booking_id>')
@login_required
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        abort(403)
    
    total_price = booking.ticket_count * booking.schedule.price
    return render_template('payment.html', 
                         booking=booking,
                         total_price=total_price,
                         payment_method=booking.payment_method,
                         booking_code=booking.booking_code)

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    shows = Show.query.all()
    schedules = Schedule.query.all()
    users = User.query.all()
    return render_template('admin/dashboard.html', 
                         bookings=bookings, 
                         shows=shows,
                         schedules=schedules,
                         users=users)

@app.route('/admin/verify-booking/<booking_code>', methods=['POST'])
@login_required
def verify_booking(booking_code):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    booking = Booking.query.filter_by(booking_code=booking_code).first()
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found'}), 404
    
    booking.payment_status = 'verified'
    try:
        db.session.commit()
        return jsonify({'success': True})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Gagal memverifikasi booking'}), 500

@app.route('/my-bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/admin/manage-users')
@login_required
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=10)
    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin_status(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent self-modification
    if user.id == current_user.id:
        flash('Anda tidak dapat mengubah status admin Anda sendiri.', 'danger')
        return redirect(url_for('manage_users'))
    
    try:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'Status admin untuk {user.username} berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error toggling admin status: {str(e)}')
        flash('Terjadi kesalahan saat mengubah status admin.', 'danger')
    
    return redirect(url_for('manage_users'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent self-deletion
    if user.id == current_user.id:
        flash('Anda tidak dapat menghapus akun Anda sendiri.', 'danger')
        return redirect(url_for('manage_users'))
    
    try:
        # Delete all bookings associated with the user
        Booking.query.filter_by(user_id=user.id).delete()
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        flash(f'Pengguna {user.username} berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting user: {str(e)}')
        flash('Terjadi kesalahan saat menghapus pengguna.', 'danger')
    
    return redirect(url_for('manage_users'))

@app.route('/admin/shows')
@login_required
@admin_required
def manage_shows():
    page = request.args.get('page', 1, type=int)
    shows = Show.query.paginate(
        page=page,
        per_page=10,  # Show 10 items per page in admin view
        error_out=False
    )
    return render_template('admin/manage_shows.html', shows=shows)

@app.route('/admin/shows/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_show():
    form = ShowForm()
    if form.validate_on_submit():
        try:
            show = Show(
                title=form.title.data,
                production=form.production.data,
                description=form.description.data,
                location=form.location.data
            )
            
            if form.poster.data:
                show.poster_path = save_poster(form.poster.data)
            
            db.session.add(show)
            db.session.commit()
            cache.delete_memoized(index)  # Clear cached index page
            flash('Pertunjukan berhasil ditambahkan', 'success')
            return redirect(url_for('admin_dashboard'))
        except IntegrityError:
            db.session.rollback()
            flash('Gagal menambahkan pertunjukan', 'danger')
    
    return render_template('admin/show_form.html', form=form, show=None)

@app.route('/admin/shows/<int:show_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_show(show_id):
    show = Show.query.get_or_404(show_id)
    form = ShowForm(obj=show)
    
    if form.validate_on_submit():
        try:
            show.title = form.title.data
            show.production = form.production.data
            show.description = form.description.data
            show.location = form.location.data
            
            if form.poster.data:
                # Delete old poster
                delete_poster(show.poster_path)
                # Save new poster
                show.poster_path = save_poster(form.poster.data)
            
            db.session.commit()
            cache.delete_memoized(index)  # Clear cached index page
            flash('Pertunjukan berhasil diperbarui', 'success')
            return redirect(url_for('admin_dashboard'))
        except IntegrityError:
            db.session.rollback()
            flash('Gagal memperbarui pertunjukan', 'danger')
    
    return render_template('admin/show_form.html', form=form, show=show)

@app.route('/admin/shows/delete/<int:show_id>', methods=['POST'])
@login_required
@admin_required
def delete_show(show_id):
    show = Show.query.get_or_404(show_id)
    try:
        # Delete the poster file
        delete_poster(show.poster_path)
        # Delete the show and its related records
        db.session.delete(show)
        db.session.commit()
        cache.delete_memoized(index)  # Clear cached index page
        flash('Pertunjukan berhasil dihapus', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Gagal menghapus pertunjukan', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/shows/schedules')
@login_required
@admin_required
def list_shows_schedules():
    shows = Show.query.all()
    return render_template('admin/list_shows_schedules.html', shows=shows)

@app.route('/admin/shows/<int:show_id>/schedules')
@login_required
@admin_required
def manage_schedules(show_id):
    show = Show.query.get_or_404(show_id)
    schedules = Schedule.query.filter_by(show_id=show_id).order_by(Schedule.date).all()
    return render_template('admin/manage_schedules.html', show=show, schedules=schedules)

@app.route('/admin/shows/<int:show_id>/schedules/add', methods=['POST'])
@login_required
@admin_required
def add_schedule(show_id):
    show = Show.query.get_or_404(show_id)
    try:
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        datetime_str = f"{date_str} {time_str}"
        schedule_date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        
        schedule = Schedule(
            show_id=show_id,
            date=schedule_date,
            price=float(request.form.get('price')),
            available_seats=int(request.form.get('available_seats')),
            is_active=True if request.form.get('is_active') else False
        )
        
        db.session.add(schedule)
        db.session.commit()
        flash('Jadwal berhasil ditambahkan.', 'success')
    except ValueError as e:
        db.session.rollback()
        app.logger.error(f'Error adding schedule - Invalid input: {str(e)}')
        flash('Format input tidak valid. Pastikan semua field diisi dengan benar.', 'danger')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error adding schedule: {str(e)}')
        flash('Terjadi kesalahan saat menambahkan jadwal.', 'danger')
    
    return redirect(url_for('manage_schedules', show_id=show_id))

@app.route('/admin/shows/<int:show_id>/schedules/<int:schedule_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_schedule(show_id, schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    try:
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        datetime_str = f"{date_str} {time_str}"
        schedule.date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        
        schedule.price = float(request.form.get('price'))
        schedule.available_seats = int(request.form.get('available_seats'))
        schedule.is_active = True if request.form.get('is_active') else False
        
        db.session.commit()
        flash('Jadwal berhasil diperbarui.', 'success')
    except ValueError as e:
        db.session.rollback()
        app.logger.error(f'Error updating schedule - Invalid input: {str(e)}')
        flash('Format input tidak valid. Pastikan semua field diisi dengan benar.', 'danger')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error updating schedule: {str(e)}')
        flash('Terjadi kesalahan saat memperbarui jadwal.', 'danger')
    
    return redirect(url_for('manage_schedules', show_id=show_id))

@app.route('/admin/shows/<int:show_id>/schedules/<int:schedule_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_schedule(show_id, schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    try:
        db.session.delete(schedule)
        db.session.commit()
        flash('Jadwal berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting schedule: {str(e)}')
        flash('Terjadi kesalahan saat menghapus jadwal.', 'danger')
    
    return redirect(url_for('manage_schedules', show_id=show_id))

@app.route('/admin/manage-bookings')
@login_required
@admin_required
def manage_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/manage_bookings.html', bookings=bookings)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'Page not found: {request.url}')
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    app.logger.error(f'Forbidden access: {request.url}')
    return render_template('errors/403.html'), 403

# Template filters
@app.template_filter('format_price')
def format_price(value):
    return "{:,.0f}".format(value)

def save_poster(file):
    filename = secure_filename(file.filename)
    # Generate unique filename
    base, ext = os.path.splitext(filename)
    filename = f"{base}_{int(time.time())}{ext}"
    
    # Save file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Store relative path in database
    return os.path.join('posters', filename).replace('\\', '/')

def delete_poster(poster_path):
    if poster_path:
        poster_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(poster_path))
        if os.path.exists(poster_path):
            os.remove(poster_path)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
