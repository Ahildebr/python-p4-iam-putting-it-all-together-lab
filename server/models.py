# models.py

from sqlalchemy.orm import validates, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    _password_hash = Column(String, nullable=False)
    image_url = Column(String)
    bio = Column(Text)

    recipes = relationship('Recipe', backref='user')

    @hybrid_property
    def password_hash(self):
        raise AttributeError('password_hash is not a readable attribute')

    @password_hash.setter
    def password_hash(self, password):
        if not password:
            raise ValueError("Password cannot be empty.")  # ✅ Prevent NULL passwords
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    def authenticate(self, password):
        return self.verify_password(password)

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    instructions = Column(Text, nullable=False)
    minutes_to_complete = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))

    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if len(instructions) < 50:
            raise ValueError('Instructions must be at least 50 characters long')
        return instructions
