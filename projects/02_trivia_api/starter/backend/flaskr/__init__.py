import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import json

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    Set up CORS. Allow '*' for origins.
    Delete the sample route after completing the TODOs
    '''
    CORS(app)

    '''
    Use the after_request decorator to set Access-Control-Allow
    '''
    @app.after_request
    def handle_response(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    '''
    Create an endpoint to handle GET requests
    for all available categories.
    '''
    @app.route("/categories")
    def get_categories():
        categories = list(map(Category.format, Category.query.all()))
        result = {
            "success": True,
            "categories": categories
        }
        return jsonify(result)

    '''
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page
    and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    '''
    @app.route("/questions")
    def get_questions():
        page = int(request.args.get('page'))
        categories = list(map(Category.format, Category.query.all()))
        questions_query = Question.query.paginate(
            page, QUESTIONS_PER_PAGE, False)
        questions = list(map(Question.format, questions_query.items))
        if not questions:
            abort(404)
        result = {
            "success": True,
            "questions": questions,
            "total_questions": len(questions),
            "categories": categories,
            "current_category": None,
        }
        return jsonify(result)

    '''
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question,
    the question will be removed.
    This removal will persist in the database and when you refresh the page.
    '''
    @app.route("/questions/<question_id>", methods=['DELETE'])
    def delete_question(question_id):
        question_data = Question.query.get(question_id)
        if not question_data:
            abort(404)
        Question.delete(question_data)
        result = {
            "success": True,
        }
        return jsonify(result)

    '''
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question
    will appear at the end of the last page
    of the questions list in the "List" tab.
    '''
    @app.route("/questions", methods=['POST'])
    def add_question():
        if not request.data:
            abort(422)
        user_input = json.loads(request.data.decode('utf-8'))
        if 'question' not in user_input or 'answer' not in user_input \
                or 'difficulty' not in user_input \
                or 'category' not in user_input:
            abort(404)
        new_question = Question(
            question=user_input['question'],
            answer=user_input['answer'],
            difficulty=user_input['difficulty'],
            category=str(user_input['category'])
        )
        Question.insert(new_question)
        category_duplicate = Category.query.filter_by(
            type=str(user_input['category'])).first()
        if not category_duplicate:
            new_category = Category(type=str(user_input['category']))
            Category.insert(new_category)
        result = {
            "success": True,
        }
        return jsonify(result)

    '''
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''
    @app.route("/searchQuestions", methods=['POST'])
    def search_questions():
        if not request.data:
            abort(422)
        search_data = json.loads(request.data.decode('utf-8'))
        page = int(request.args.get('page', '1'))
        if 'searchTerm' in search_data:
            questions_query = Question.query.filter(
                Question.question.like('%'+search_data['searchTerm']+'%')
            ).paginate(page, QUESTIONS_PER_PAGE, False)
        questions = list(map(Question.format, questions_query.items))
        if not questions:
            abort(404)
        result = {
            "success": True,
            "questions": questions,
            "total_questions": len(questions),
            "current_category": None,
        }
        return jsonify(result)

    '''
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''
    @app.route("/categories/<int:category_id>/questions")
    def get_question_by_category(category_id):
        page = int(request.args.get('page', '1'))
        categories = list(map(Category.format, Category.query.all()))
        current_category = Category.format(Category.query.get(category_id))
        questions_query = Question.query.filter_by(
            category=str(category_id)).paginate(
            page, QUESTIONS_PER_PAGE, False)
        questions = list(map(Question.format, questions_query.items))
        if not questions:
            abort(404)
        result = {
            "success": True,
            "questions": questions,
            "total_questions": questions_query.total,
            "categories": categories,
            "current_category": current_category,
        }
        return jsonify(result)

    '''
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''
    @app.route("/quizzes", methods=['POST'])
    def get_question_for_quiz():
        if not request.data:
            abort(422)
        search_data = json.loads(request.data.decode('utf-8'))
        if ('quiz_category' not in search_data or
                'id' not in search_data['quiz_category'] or
                'previous_questions' not in search_data):
            abort(404)
        questions_query = Question.query.filter_by(
            category=str(search_data['quiz_category']['id'])
        ).filter(
            Question.id.notin_(search_data["previous_questions"])
        ).all()
        length_of_available_question = len(questions_query)
        result = {"success": True, "question": None}
        if length_of_available_question > 0:
            result = {
                "success": True,
                "question": Question.format(
                    questions_query[random.randrange(
                        0, length_of_available_question)]
                )
            }
        return jsonify(result)

    '''
    Create error handlers for all expected errors
    including 404 and 422.
    '''
    @app.errorhandler(404)
    def not_found(error):
        error_data = {
            "success": False,
            "error": 404,
            "message": "Resource not found"
        }
        return jsonify(error_data), 404

    @app.errorhandler(422)
    def unprocessable(error):
        error_data = {
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }
        return jsonify(error_data), 422

    return app
