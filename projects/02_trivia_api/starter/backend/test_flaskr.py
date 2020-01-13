import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = 'postgresql://postgres:123456@localhost:5432/' \
                             + self.database_name
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    Write at least one test for each test for successful operation
    and for expected errors.
    """
    def get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)
        self.assertEqual(200, res.status_code)
        self.assertTrue(data["success"])
        self.assertTrue(len(data["categories"]))

    def test_get_paginated_questions(self):
        res = self.client().get('/questions?page=1')
        data = json.loads(res.data)
        self.assertEqual(200, res.status_code)
        self.assertTrue(data["success"])
        self.assertTrue(data["total_questions"])
        self.assertTrue(len(data["categories"]))
        self.assertTrue(len(data["questions"]))

    def test_404_get_paginated_questions_beyond_valid_page(self):
        res = self.client().get('/questions?page=1000')
        data = json.loads(res.data)
        self.assertEqual(404, res.status_code)
        self.assertTrue(not data["success"])
        self.assertEqual("Resource not found", data["message"])

    def test_delete_question(self):
        res = self.client().delete('/questions/4')
        data = json.loads(res.data)
        self.assertEqual(200, res.status_code)
        self.assertTrue(data["success"])

    def test_404_delete_question(self):
        res = self.client().delete('/questions/1000')
        data = json.loads(res.data)
        self.assertEqual(404, res.status_code)
        self.assertTrue(not data["success"])
        self.assertEqual("Resource not found", data["message"])

    def test_post_new_question(self):
        post_data = {
            'question': 'my_question',
            'answer': 'my_answer',
            'difficulty': 1,
            'category': 'Science'
        }
        res = self.client().post('/questions', json=post_data)
        data = json.loads(res.data)
        self.assertEqual(200, res.status_code)
        self.assertTrue(data["success"])

    def test_404_post_new_question(self):
        post_data = {
            'question': 'my_question',
            'answer': 'my_answer',
            'difficulty': 1
        }
        res = self.client().post('/questions', json=post_data)
        data = json.loads(res.data)
        self.assertEqual(404, res.status_code)
        self.assertTrue(not data["success"])
        self.assertEqual("Resource not found", data["message"])

    def test_422_post_new_question(self):
        res = self.client().post('/questions')
        data = json.loads(res.data)
        self.assertEqual(422, res.status_code)
        self.assertTrue(not data["success"])
        self.assertEqual("unprocessable", data["message"])

    def test_post_paginated_search_questions(self):
        post_data = {
            'searchTerm': 'my_question',
        }
        res = self.client().post('/searchQuestions', json=post_data)
        data = json.loads(res.data)
        self.assertEqual(200, res.status_code)
        self.assertTrue(data["success"])
        self.assertTrue(data["total_questions"])
        self.assertTrue(len(data["questions"]))

    def test_404_post_paginated_search_questions_beyond_valid_page(self):
        post_data = {
            'searchTerm': 'my_question',
        }
        res = self.client().post('/searchQuestions?page=1000', json=post_data)
        data = json.loads(res.data)
        self.assertEqual(404, res.status_code)
        self.assertTrue(not data["success"])
        self.assertEqual("Resource not found", data["message"])

    def test_422_post_paginated_search_questions(self):
        res = self.client().post('/searchQuestions')
        data = json.loads(res.data)
        self.assertEqual(422, res.status_code)
        self.assertTrue(not data["success"])
        self.assertEqual("unprocessable", data["message"])

    def test_get_paginated_question_by_category(self):
        res = self.client().get('/categories/1/questions?page=1')
        data = json.loads(res.data)
        self.assertEqual(200, res.status_code)
        self.assertTrue(data["success"])
        self.assertTrue(data["total_questions"])
        self.assertTrue(len(data["categories"]))
        self.assertTrue(len(data["questions"]))

    def test_404_get_paginated_question_by_category_beyond_valid_page(self):
        res = self.client().get('/categories/1/questions?page=1000')
        data = json.loads(res.data)
        self.assertEqual(404, res.status_code)
        self.assertTrue(not data["success"])
        self.assertEqual("Resource not found", data["message"])

    def test_post_play_quiz(self):
        post_data = {
            'previous_questions': [],
            'quiz_category': {
                'type': 'Science',
                'id': 1
            }
        }
        res = self.client().post('/quizzes', json=post_data)
        data = json.loads(res.data)
        self.assertEqual(200, res.status_code)
        self.assertTrue(data["success"])
        self.assertTrue(data["question"])

    def test_404_post_play_quiz(self):
        post_data = {
            'previous_questions': [],
            'quiz_category': {
                'type': 'Science',
            }
        }
        res = self.client().post('/quizzes', json=post_data)
        data = json.loads(res.data)
        self.assertEqual(404, res.status_code)
        self.assertTrue(not data["success"])
        self.assertEqual("Resource not found", data["message"])

    def test_422_post_play_quiz(self):
        res = self.client().post('/quizzes')
        data = json.loads(res.data)
        self.assertEqual(422, res.status_code)
        self.assertTrue(not data["success"])
        self.assertEqual("unprocessable", data["message"])


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
