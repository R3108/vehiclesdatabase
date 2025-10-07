from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Brand(db.Model):
    brand_id = db.Column(db.Integer, primary_key=True)
    brand_name = db.Column(db.String(50), nullable=False)

class Model(db.Model):
    model_id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.brand_id'), nullable=False)
    model_name = db.Column(db.String(50), nullable=False)
    brand = db.relationship('Brand', backref='models')

class Vehicle(db.Model):
    vin = db.Column(db.String(17), primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.model_id'), nullable=False)
    color = db.Column(db.String(30), nullable=False)
    engine = db.Column(db.String(50), nullable=False)
    transmission = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    model = db.relationship('Model', backref='vehicles')

class Sale(db.Model):
    sale_id = db.Column(db.Integer, primary_key=True)
    vin = db.Column(db.String(17), db.ForeignKey('vehicle.vin'), nullable=False)
    cust_id = db.Column(db.Integer, nullable=False)
    dealer_id = db.Column(db.Integer, nullable=False)
    sale_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sale_price = db.Column(db.Float, nullable=False)
    vehicle = db.relationship('Vehicle', backref='sales')

# Forms
class SaleForm(FlaskForm):
    vin = StringField('VIN', validators=[DataRequired(), Length(min=17, max=17)])
    model_id = SelectField('Model', coerce=int, validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired(), Length(max=30)])
    engine = StringField('Engine', validators=[DataRequired(), Length(max=50)])
    transmission = StringField('Transmission', validators=[DataRequired(), Length(max=20)])
    status = SelectField('Status', choices=[('Available', 'Available'), ('Sold', 'Sold')], validators=[DataRequired()])
    cust_id = StringField('Customer ID', validators=[DataRequired()])
    dealer_id = StringField('Dealer ID', validators=[DataRequired()])
    sale_price = FloatField('Sale Price', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Vehicle and Sale')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(message='Invalid email address')])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

# NEW Delete Form for confirmation
class DeleteForm(FlaskForm):
    submit = SubmitField('Yes, Delete')

# Create database tables
with app.app_context():
    db.create_all()

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    print(f"Loading user: {user_id}, Found: {user}")  # Debug
    return user

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vehicles')
@login_required
def view_all_vehicles():
    vehicles = Vehicle.query.all()
    return render_template('vehicles.html', vehicles=vehicles)

@app.route('/add_sale', methods=['GET', 'POST'])
@login_required
def add_sale():
    form = SaleForm()
    # Populate model choices
    models = Model.query.all()
    if not models:
        flash('No models available. Please add models to the database first.', 'danger')
        return redirect(url_for('index'))
    form.model_id.choices = [(model.model_id, f"{model.brand.brand_name} {model.model_name}") for model in models]
    
    if form.validate_on_submit():
        try:
            # Check if vehicle exists
            vehicle = Vehicle.query.get(form.vin.data)
            if not vehicle:
                # Create new vehicle
                vehicle = Vehicle(
                    vin=form.vin.data,
                    model_id=form.model_id.data,
                    color=form.color.data,
                    engine=form.engine.data,
                    transmission=form.transmission.data,
                    status=form.status.data
                )
                db.session.add(vehicle)
            else:
                # Update existing vehicle if needed
                vehicle.model_id = form.model_id.data
                vehicle.color = form.color.data
                vehicle.engine = form.engine.data
                vehicle.transmission = form.transmission.data
                vehicle.status = form.status.data

            # Record sale if status is Sold
            if form.status.data == 'Sold':
                if vehicle.status == 'Sold' and not vehicle:
                    flash('Vehicle is already sold.', 'danger')
                    return redirect(url_for('add_sale'))
                sale = Sale(
                    vin=form.vin.data,
                    cust_id=int(form.cust_id.data),
                    dealer_id=int(form.dealer_id.data),
                    sale_price=form.sale_price.data
                )
                db.session.add(sale)
            
            db.session.commit()
            flash('Vehicle and sale (if applicable) added successfully!', 'success')
            return redirect(url_for('index'))
        except ValueError:
            flash('Customer ID and Dealer ID must be valid integers.', 'danger')
            return redirect(url_for('add_sale'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('add_sale'))
    
    return render_template('add_sale.html', form=form)

@app.route('/top_brands')
@login_required
def top_brands():
    brands = db.session.query(
        Brand.brand_name,
        db.func.sum(Sale.sale_price).label('total_sales')
    ).join(Model, Brand.brand_id == Model.brand_id
    ).join(Vehicle, Model.model_id == Vehicle.model_id
    ).join(Sale, Vehicle.vin == Sale.vin
    ).group_by(Brand.brand_name
    ).order_by(db.desc('total_sales')
    ).limit(2).all()
    return render_template('top_brands.html', brands=brands)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print("User already authenticated, redirecting to index")  # Debug
        return redirect(url_for('index'))
    form = LoginForm()
    print(f"Form submitted: {form.is_submitted()}, Form data: {form.data}")  # Debug
    if form.validate_on_submit():
        print(f"Valid form submission, username: {form.username.data}")  # Debug
        user = User.query.filter_by(username=form.username.data).first()
        print(f"User query result: {user}")  # Debug
        if user and user.check_password(form.password.data):
            login_user(user)
            print(f"Login successful for user: {user.username}")  # Debug
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
            print("Login failed: Invalid username or password")  # Debug
    else:
        print(f"Form validation errors: {form.errors}")  # Debug
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# NEW Route: Delete vehicle and sale confirmation + deletion
@app.route('/delete_vehicle/<string:vin>', methods=['GET', 'POST'])
@login_required
def delete_vehicle(vin):
    vehicle = Vehicle.query.get_or_404(vin)
    sale = Sale.query.filter_by(vin=vin).first()  # Assuming one sale per vehicle

    form = DeleteForm()
    if form.validate_on_submit():
        try:
            # Delete sale record if exists
            if sale:
                db.session.delete(sale)
            # Delete vehicle
            db.session.delete(vehicle)
            db.session.commit()
            flash('Vehicle and sale deleted successfully.', 'success')
            return redirect(url_for('view_all_vehicles'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting vehicle: {str(e)}', 'danger')
            return redirect(url_for('view_all_vehicles'))

    return render_template('delete.html', vehicle=vehicle, sale=sale, form=form)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
