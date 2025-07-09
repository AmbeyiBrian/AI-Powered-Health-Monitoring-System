"""
Authentication forms using Flask-WTF
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, FloatField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, ValidationError
from wtforms.widgets import TextArea


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    
    # Optional profile information
    age = IntegerField('Age (optional)', validators=[
        Optional(),
        NumberRange(min=1, max=120, message='Age must be between 1 and 120')
    ])
    height = FloatField('Height in cm (optional)', validators=[
        Optional(),
        NumberRange(min=50, max=300, message='Height must be between 50 and 300 cm')
    ])
    weight = FloatField('Weight in kg (optional)', validators=[
        Optional(),
        NumberRange(min=20, max=500, message='Weight must be between 20 and 500 kg')
    ])
    fitness_level = SelectField('Fitness Level', choices=[
        ('low', 'Low - Sedentary lifestyle'),
        ('moderate', 'Moderate - Regular light exercise'),
        ('high', 'High - Very active, regular intense exercise')
    ], default='moderate')
    
    timezone = SelectField('Timezone', choices=[
        ('Africa/Nairobi', 'Africa/Nairobi (EAT - East Africa Time)'),
        ('Africa/Cairo', 'Africa/Cairo (CAT - Central Africa Time)'),
        ('Africa/Lagos', 'Africa/Lagos (WAT - West Africa Time)'),
        ('Europe/London', 'Europe/London (GMT/BST)'),
        ('Europe/Paris', 'Europe/Paris (CET/CEST)'),
        ('US/Eastern', 'US/Eastern (EST/EDT)'),
        ('US/Central', 'US/Central (CST/CDT)'),
        ('US/Mountain', 'US/Mountain (MST/MDT)'),
        ('US/Pacific', 'US/Pacific (PST/PDT)'),
        ('Asia/Tokyo', 'Asia/Tokyo (JST)'),
        ('Asia/Dubai', 'Asia/Dubai (GST)'),
        ('Asia/Kolkata', 'Asia/Kolkata (IST)'),
        ('UTC', 'UTC (Coordinated Universal Time)')
    ], default='Africa/Nairobi')
    
    medical_conditions = TextAreaField('Medical Conditions (optional)', 
                                     widget=TextArea(),
                                     validators=[Optional()])
    
    def validate_username(self, username):
        """Check if username is unique"""
        from ..data.models import User
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different username.')
    
    def validate_email(self, email):
        """Check if email is unique"""
        from ..data.models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email or login.')
    
    submit = SubmitField('Register')


class ProfileForm(FlaskForm):
    """User profile update form"""
    name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    age = IntegerField('Age', validators=[
        Optional(),
        NumberRange(min=1, max=120, message='Age must be between 1 and 120')
    ])
    height = FloatField('Height (cm)', validators=[
        Optional(),
        NumberRange(min=50, max=300, message='Height must be between 50 and 300 cm')
    ])
    weight = FloatField('Weight (kg)', validators=[
        Optional(),
        NumberRange(min=20, max=500, message='Weight must be between 20 and 500 kg')
    ])
    fitness_level = SelectField('Fitness Level', choices=[
        ('low', 'Low - Sedentary lifestyle'),
        ('moderate', 'Moderate - Regular light exercise'),
        ('high', 'High - Very active, regular intense exercise')
    ])
    
    timezone = SelectField('Timezone', choices=[
        ('Africa/Nairobi', 'Africa/Nairobi (EAT - East Africa Time)'),
        ('Africa/Cairo', 'Africa/Cairo (CAT - Central Africa Time)'),
        ('Africa/Lagos', 'Africa/Lagos (WAT - West Africa Time)'),
        ('Europe/London', 'Europe/London (GMT/BST)'),
        ('Europe/Paris', 'Europe/Paris (CET/CEST)'),
        ('US/Eastern', 'US/Eastern (EST/EDT)'),
        ('US/Central', 'US/Central (CST/CDT)'),
        ('US/Mountain', 'US/Mountain (MST/MDT)'),
        ('US/Pacific', 'US/Pacific (PST/PDT)'),
        ('Asia/Tokyo', 'Asia/Tokyo (JST)'),
        ('Asia/Dubai', 'Asia/Dubai (GST)'),
        ('Asia/Kolkata', 'Asia/Kolkata (IST)'),
        ('UTC', 'UTC (Coordinated Universal Time)')
    ])
    
    medical_conditions = TextAreaField('Medical Conditions', 
                                     widget=TextArea(),
                                     validators=[Optional()])
    
    submit = SubmitField('Update Profile')


class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    new_password2 = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')


class DeviceRegistrationForm(FlaskForm):
    """Sensor device registration form"""
    device_name = StringField('Device Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Device name must be between 2 and 100 characters')
    ])
    device_type = SelectField('Device Type', choices=[
        ('smartwatch', 'Smart Watch'),
        ('fitness_tracker', 'Fitness Tracker'),
        ('medical_device', 'Medical Device'),
        ('smartphone', 'Smartphone App'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    manufacturer = StringField('Manufacturer (optional)', validators=[
        Optional(),
        Length(max=50)
    ])
    model = StringField('Model (optional)', validators=[
        Optional(),
        Length(max=50)
    ])
    
    # Data collection settings
    collection_interval = IntegerField('Data Collection Interval (seconds)', 
                                     default=60,
                                     validators=[
                                         NumberRange(min=10, max=3600, 
                                                   message='Interval must be between 10 seconds and 1 hour')
                                     ])
    
    collect_heart_rate = BooleanField('Collect Heart Rate Data', default=True)
    collect_blood_oxygen = BooleanField('Collect Blood Oxygen Data', default=True)
    collect_activity = BooleanField('Collect Activity Data', default=True)
    
    submit = SubmitField('Register Device')
