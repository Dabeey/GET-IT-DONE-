from flask import Flask, render_template,Response, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy import inspect
from models import db, Task, User, Project, PriorityLevel, TaskStatus
from flask_login import current_user, login_required, LoginManager, UserMixin
from flask_login import login_user, logout_user
from flask import flash
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
import logging
import os
import secrets
import csv
import json

app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///get_it_done.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))

db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

class BaseForm(FlaskForm):
    pass    #Create an instance of the form class in every route that requires CSRF protection ie form = BaseForm()


def get_current_timestamp():
    return datetime.utcnow()


def get_enum_values(enum_class):
    """Extract values from a Python Enum class."""
    try:
        return [e.value for e in enum_class]
    except Exception as e:
        logging.error(f"Error getting enum values: {str(e)}")
        return []  # Fallback to an empty list
    

with app.app_context():
    db.create_all()  


################ EVERYTHING ERROR HANDLING #########################

if app.config['DEBUG']:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)

app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False') == 'True'


@app.errorhandler(500)
def internal_server_error(e):
    logging.error(f"Internal server error: {str(e)}")
    flash('An unexpected error occurred. Please try again later.', 'danger')
    return redirect(url_for('index'))



########################## EVERYTHING AUTHENTICATION #########################

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Define the User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate inputs
        if not email or not password:
            flash('Both email and password are required.', 'danger')
            return redirect(url_for('login'))

        # Check if the user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email. Please register first.', 'danger')
            return redirect(url_for('register'))

        # Verify the password
        if not user.check_password(password):  # Use hashed password comparison
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

        # Log the user in
        try:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            logging.error(f"Error during login: {str(e)}")
            flash('An error occurred during login. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if a message was passed via query parameters
    message = request.args.get('message')
    if message:
        flash(message, 'danger')

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate inputs
        if not username or not email or not password:
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))

        # Check if email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered! Please log in instead.', 'danger')
            return redirect(url_for('login'))

        try:
            # Create a new user
            new_user = User(username=username, email=email)
            new_user.set_password(password)  # Hash the password
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error during registration: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')

    return render_template('register.html')


@app.route('/')
@login_required
def index():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('index.html', projects=projects)



######################## EVERYTHING PROJECTS #########################

@app.route('/projects')
@login_required
def projects():
    projects = Project.query.filter_by(owner_id=current_user.id).order_by(Project.created_at.desc()).all()
    
    return render_template('projects.html', projects=projects)


@app.route('/add_project', methods=['GET','POST'])
@login_required
def add_project():
    form = BaseForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            project_name = request.form.get('project_name')
            project_description = request.form.get('project_description', '')
            project_deadline_str = request.form.get('project_deadline')

            if not project_name:
                flash('Project name is required', 'danger')
                return redirect(url_for('add_project'))

            try:
                # Convert string to datetime
                project_deadline = datetime.strptime(project_deadline_str, '%Y-%m-%d') if project_deadline_str else None
                
                new_project = Project(
                    name=project_name,
                    description=project_description,
                    deadline=project_deadline,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    owner_id=current_user.id
                )
                
                db.session.add(new_project)
                db.session.commit()
                flash('Project added successfully!', 'success')
                return redirect(url_for('projects'))
                
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD', 'danger')
                return redirect(url_for('add_project'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error adding project: {str(e)}")
                flash(f'An error occurred: {str(e)}', 'danger')
                return redirect(url_for('add_project'))
    
    return render_template('add_project.html', form=form)


@app.route('/project/<int:project_id>/tasks')
@login_required
def project_tasks(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id:
        flash("You don't have permission to view this project's tasks.", 'danger')
        return redirect(url_for('projects'))

    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.updated_at.desc()).all()
    return render_template('tasks.html', tasks=tasks, project=project)

@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id:
        flash("You don't have permission to edit this project.", 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        project.name = request.form.get('project_name')
        project.description = request.form.get('project_description')
        project.deadline = request.form.get('project_deadline')
        project.updated_at = get_current_timestamp()

        if not project.name:
            flash('Project name is required.', 'danger')
            return redirect(url_for('edit_project', project_id=project_id))

        try:
            db.session.commit()
            flash('Project updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating project: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('index'))

    return render_template('edit_project.html', project=project)



@app.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id:
        flash("You don't have permission to delete this project.", 'danger')
        return redirect(url_for('index'))

    try:
        db.session.delete(project)
        db.session.commit()
        flash('Project deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting project: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
    return redirect(url_for('index'))





############### EVERYTHING TASK ############################
@app.route('/tasks')
@login_required
def tasks():
    form = BaseForm()
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date.asc()).all()
    return render_template('tasks.html', tasks=tasks, form=form)


@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    form = BaseForm()
    projects = Project.query.filter_by(owner_id=current_user.id).all()

    # Get enum values for priorities and statuses
    priorities = list(PriorityLevel)
    statuses = list(TaskStatus)

    if request.method == 'POST' and form.validate_on_submit():
        task_title = request.form.get('title')
        task_description = request.form.get('description', '')
        task_due_date_str = request.form.get('due_date')
        task_priority = request.form.get('priority').title()
        task_status = request.form.get('status').title()
        project_id = request.form.get('project_id')

        # Debug logs
        logging.debug(f"Task Title: {task_title}")
        logging.debug(f"Task Description: {task_description}")
        logging.debug(f"Task Due Date: {task_due_date_str}")
        logging.debug(f"Task Priority: {task_priority}")
        logging.debug(f"Task Status: {task_status}")
        logging.debug(f"Project ID: {project_id}")

        # Normalize input
        task_priority = task_priority.title() if task_priority else None
        task_status = task_status.title() if task_status else None

        # Validate required fields
        if not task_title:
            flash('Task title is required.', 'danger')
            return render_template('add_task.html', form=form, projects=projects, priorities=priorities, statuses=statuses)

        if not task_due_date_str:
            flash('Due date is required.', 'danger')
            return render_template('add_task.html', form=form, projects=projects, priorities=priorities, statuses=statuses)

        if not project_id:
            flash('Project selection is required.', 'danger')
            return render_template('add_task.html', form=form, projects=projects, priorities=priorities, statuses=statuses)

        # Convert and validate due date
        try:
            task_due_date = datetime.strptime(task_due_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return render_template('add_task.html', form=form, projects=projects, priorities=priorities, statuses=statuses)

        # Validate project exists
        project = Project.query.get(project_id)
        if not project:
            flash('Selected project does not exist.', 'danger')
            return render_template('add_task.html', form=form, projects=projects, priorities=priorities, statuses=statuses)

        # Create and save task
        try:
            new_task = Task(
                title=task_title,
                description=task_description,
                due_date=task_due_date,
                priority=PriorityLevel(task_priority),  # Convert string to enum
                status=TaskStatus(task_status),        # Convert string to enum
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                user_id=current_user.id,
                project_id=project_id
            )
            db.session.add(new_task)
            db.session.commit()
            flash('Task created successfully!', 'success')
            return redirect(url_for('tasks'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating task: {str(e)}")
            flash('An error occurred while creating the task. Please try again.', 'danger')

    # Render the form for GET requests
    return render_template('add_task.html', form=form, projects=projects, priorities=priorities, statuses=statuses)


@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("You don't have permission to edit this task.", 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.due_date = request.form.get('due_date')
        task.priority = request.form.get('priority')
        task.status = request.form.get('status')
        task.updated_at = get_current_timestamp()

        if not task.title:
            flash('Task title is required.', 'danger')
            return redirect(url_for('edit_task', task_id=task_id))

        try:
            db.session.commit()
            flash('Task updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating task: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('index'))

    return render_template('edit_task.html', task=task)



@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("You don't have permission to delete this task.", 'danger')
        return redirect(url_for('index'))

    try:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting task: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
    return redirect(url_for('index'))



@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("You don't have permission to complete this task.", 'danger')
        return redirect(url_for('index'))

    try:
        task.status = 'Done'
        task.updated_at = get_current_timestamp()
        db.session.commit()
        flash('Task marked as complete!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error marking task as complete: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
    return redirect(url_for('index'))




@app.route('/task/<int:task_id>')
@login_required
def view_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("You don't have permission to view this task.", 'danger')
        return redirect(url_for('index'))

    return render_template('view_task.html', task=task)



############################## USER #################

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update user profile
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'danger')
    return render_template('profile.html', user=current_user)


@app.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('q')
    if not query:
        flash('Please enter a search term.', 'danger')
        return redirect(url_for('index'))

    tasks = Task.query.filter(Task.title.ilike(f'%{query}%')).all()
    projects = Project.query.filter(Project.name.ilike(f'%{query}%')).all()

    return render_template('search_results.html', tasks=tasks, projects=projects, query=query)


@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(owner_id=current_user.id).all()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, status='Done').count()
    pending_tasks = Task.query.filter_by(user_id=current_user.id, status='Pending').count()

    return render_template('dashboard.html', tasks=tasks, projects=projects, completed_tasks=completed_tasks, pending_tasks=pending_tasks)


@app.route('/export', methods=['GET'])
@login_required
def export_data():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    output = []
    for task in tasks:
        output.append({
            'Title': task.title,
            'Description': task.description,
            'Due Date': task.due_date,
            'Priority': task.priority,
            'Status': task.status,
        })

    return Response(
        json.dumps(output),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment;filename=tasks.json'}
    )


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Update user settings
        new_password = request.form.get('password')
        if new_password:
            current_user.set_password(new_password)
            try:
                db.session.commit()
                flash('Settings updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating your settings.', 'danger')
        else:
            flash('Password cannot be empty.', 'danger')
    return render_template('settings.html')


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)