"""
Authentication routes and views
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from ..auth.forms import LoginForm, RegistrationForm, ProfileForm, ChangePasswordForm, DeviceRegistrationForm
from ..data.models import User, SensorDevice, create_user, authenticate_user, register_sensor_device, db
import logging

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = authenticate_user(form.username.data, form.password.data)
        if user:
            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.name}!', 'success')
            
            # Redirect to the page user was trying to access
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('login_success')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                name=form.name.data,
                age=form.age.data,
                height=form.height.data,
                weight=form.weight.data,
                fitness_level=form.fitness_level.data,
                medical_conditions=form.medical_conditions.data,
                timezone=form.timezone.data
            )
            flash(f'Registration successful! Welcome, {user.name}!', 'success')
            login_user(user)
            return redirect(url_for('user_dashboard', user_id=user.user_id))
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    user_name = current_user.name
    logout_user()
    flash(f'Goodbye, {user_name}!', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    form = ProfileForm()
    password_form = ChangePasswordForm()
    
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.age = form.age.data
        current_user.height = form.height.data
        current_user.weight = form.weight.data
        current_user.fitness_level = form.fitness_level.data
        current_user.medical_conditions = form.medical_conditions.data
        current_user.timezone = form.timezone.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    # Pre-populate form with current user data
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.age.data = current_user.age
        form.height.data = current_user.height
        form.weight.data = current_user.weight
        form.fitness_level.data = current_user.fitness_level
        form.medical_conditions.data = current_user.medical_conditions
        form.timezone.data = current_user.timezone or 'Africa/Nairobi'
    
    return render_template('auth/profile.html', form=form, password_form=password_form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Current password is incorrect', 'error')
    
    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/devices', methods=['GET', 'POST'])
@login_required
def devices():
    """User devices page"""
    form = DeviceRegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Prepare enabled metrics
            enabled_metrics = []
            if hasattr(form, 'collect_heart_rate') and form.collect_heart_rate.data:
                enabled_metrics.append('heart_rate')
            if hasattr(form, 'collect_blood_oxygen') and form.collect_blood_oxygen.data:
                enabled_metrics.append('blood_oxygen')
            if hasattr(form, 'collect_activity') and form.collect_activity.data:
                enabled_metrics.append('activity')
            
            # If no checkboxes exist, enable all metrics by default
            if not enabled_metrics:
                enabled_metrics = ['heart_rate', 'blood_oxygen', 'activity']
            
            device = register_sensor_device(
                user_id=current_user.user_id,
                device_name=form.device_name.data,
                device_type=form.device_type.data,
                manufacturer=form.manufacturer.data or None,
                model=form.model.data or None,
                collection_interval=getattr(form, 'collection_interval', None) and form.collection_interval.data or 60,
                enabled_metrics=enabled_metrics
            )
            
            flash(f'Device "{device.device_name}" registered successfully!', 'success')
            flash(f'Device API Key: {device.api_key}', 'info')
            flash('Please save this API key - you will need it to configure your device.', 'warning')
            
            return redirect(url_for('auth.devices'))
        except Exception as e:
            logger.error(f"Device registration error: {str(e)}")
            flash('Device registration failed. Please try again.', 'error')
    
    user_devices = SensorDevice.query.filter_by(user_id=current_user.user_id).all()
    return render_template('auth/devices.html', devices=user_devices, form=form)


@auth_bp.route('/devices/register', methods=['GET', 'POST'])
@login_required
def register_device():
    """Register new sensor device"""
    form = DeviceRegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Prepare enabled metrics
            enabled_metrics = []
            if form.collect_heart_rate.data:
                enabled_metrics.append('heart_rate')
            if form.collect_blood_oxygen.data:
                enabled_metrics.append('blood_oxygen')
            if form.collect_activity.data:
                enabled_metrics.append('activity')
            
            device = register_sensor_device(
                user_id=current_user.user_id,
                device_name=form.device_name.data,
                device_type=form.device_type.data,
                manufacturer=form.manufacturer.data,
                model=form.model.data,
                collection_interval=form.collection_interval.data,
                enabled_metrics=enabled_metrics
            )
            
            flash(f'Device "{device.device_name}" registered successfully!', 'success')
            flash(f'Device API Key: {device.api_key}', 'info')
            flash('Please save this API key - you will need it to configure your device.', 'warning')
            
            return redirect(url_for('auth.devices'))
        except Exception as e:
            logger.error(f"Device registration error: {str(e)}")
            flash('Device registration failed. Please try again.', 'error')
    
    return render_template('auth/register_device.html', form=form)


@auth_bp.route('/devices/<device_id>/toggle')
@login_required
def toggle_device(device_id):
    """Toggle device active status"""
    device = SensorDevice.query.filter_by(
        device_id=device_id, 
        user_id=current_user.user_id
    ).first_or_404()
    
    device.is_active = not device.is_active
    db.session.commit()
    
    status = "activated" if device.is_active else "deactivated"
    flash(f'Device "{device.device_name}" {status}', 'success')
    
    return redirect(url_for('auth.devices'))


@auth_bp.route('/devices/<device_id>/delete', methods=['POST'])
@login_required
def delete_device(device_id):
    """Delete a device"""
    device = SensorDevice.query.filter_by(
        device_id=device_id, 
        user_id=current_user.user_id
    ).first_or_404()
    
    device_name = device.device_name
    db.session.delete(device)
    db.session.commit()
    
    flash(f'Device "{device_name}" deleted successfully', 'success')
    return redirect(url_for('auth.devices'))


# API endpoint for sensor data submission
@auth_bp.route('/api/sensor-data', methods=['POST'])
def sensor_data_api():
    """API endpoint for sensors to submit health data"""
    try:
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Verify device
        device = SensorDevice.query.filter_by(api_key=api_key, is_active=True).first()
        if not device:
            return jsonify({'error': 'Invalid or inactive API key'}), 401
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        # Import here to avoid circular imports
        from ..data.models import create_health_data_entry
        
        # Create health data entry
        health_data = create_health_data_entry(
            user_id=device.user_id,
            heart_rate=data.get('heart_rate'),
            blood_oxygen=data.get('blood_oxygen'),
            activity_level=data.get('activity_level', 'moderate'),
            timestamp=data.get('timestamp'),
            device_id=device.device_id
        )
        
        # Update device last sync
        device.update_last_sync()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Health data recorded',
            'data_id': health_data.id
        })
        
    except Exception as e:
        logger.error(f"Sensor API error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
