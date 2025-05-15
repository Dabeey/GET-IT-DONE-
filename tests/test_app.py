import unittest
from main import app, db
from models import Project, Task

class TestApp(unittest.TestCase):
    def setUp(self):
        # Set up a test client and a temporary database
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database for testing
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        # Clean up the database after each test
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_page(self):
        # Test if the index page loads successfully
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_add_project(self):
        # Test adding a project
        response = self.client.post('/add_project', data={
            'project_name': 'Test Project',
            'project_description': 'This is a test project.'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to index
        with app.app_context():
            project = Project.query.filter_by(name='Test Project').first()
            self.assertIsNotNone(project)
            self.assertEqual(project.description, 'This is a test project.')

    def test_add_task(self):
        # Test adding a task to a project
        with app.app_context():
            project = Project(name='Test Project', description='Test Description')
            db.session.add(project)
            db.session.commit()

        response = self.client.post('/add_task', data={
            'title': 'Test Task',
            'description': 'This is a test task.',
            'due_date': '2025-05-15',
            'priority': 'High',
            'status': 'Pending',
            'project_id': 1
        })
        self.assertEqual(response.status_code, 302)  # Redirect to index
        with app.app_context():
            task = Task.query.filter_by(title='Test Task').first()
            self.assertIsNotNone(task)
            self.assertEqual(task.description, 'This is a test task.')

if __name__ == '__main__':
    unittest.main()