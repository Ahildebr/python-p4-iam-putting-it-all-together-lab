# app.py

#!/usr/bin/env python3

from flask import request, session, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError, InvalidRequestError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        bio = data.get('bio')
        image_url = data.get('image_url')

        if not username or not password:
            return {'error': 'Username and password are required'}, 422

        try:
            user = User(username=username, bio=bio, image_url=image_url)
            user.password_hash = password  # Triggers the setter
            print(f"New User: {user.username}, Password Hash: {user._password_hash}")

            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id  

        except ValueError as e:  
            return {'error': str(e)}, 422

        except IntegrityError:
            db.session.rollback()
            return {'error': 'Username already exists'}, 422

        return {
            'id': user.id,
            'username': user.username,
            'bio': user.bio,
            'image_url': user.image_url
        }, 201

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        return {
            'id': user.id,
            'username': user.username,
            'bio': user.bio,
            'image_url': user.image_url
        }, 200  

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            session['user_id'] = user.id
            return {
                'id': user.id,
                'username': user.username,
                'bio': user.bio,
                'image_url': user.image_url
            }, 200  

        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        if 'user_id' in session:
            session.pop('user_id', None)
            return {}, 204

        return {'error': 'Unauthorized'}, 401


class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        recipes = Recipe.query.filter_by(user_id=user_id).all()
        return [
            {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'bio': user.bio,
                    'image_url': user.image_url
                }
            }
            for recipe in recipes
        ], 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        data = request.get_json()
        title = data.get('title')
        instructions = data.get('instructions')
        minutes_to_complete = data.get('minutes_to_complete') or 0

        if not title or not instructions:
            return {'error': 'Invalid recipe data'}, 422

        try:
            recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id,
            )
            db.session.add(recipe)
            db.session.commit()
        except (IntegrityError, ValueError, InvalidRequestError):
            db.session.rollback()
            return {'error': 'Invalid recipe data'}, 422

        return {
            'id': recipe.id,
            'title': recipe.title,
            'instructions': recipe.instructions,
            'minutes_to_complete': recipe.minutes_to_complete,
            'user': {
                'id': recipe.user.id,
                'username': recipe.user.username,
                'bio': recipe.user.bio,
                'image_url': recipe.user.image_url
            }
        }, 201

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=5555, debug=True)
