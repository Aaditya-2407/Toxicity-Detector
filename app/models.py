from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Composite weighted score [0, 1]
    toxicity_score = db.Column(db.Float)

    # Per-category raw sigmoid scores (nullable — legacy rows have NULL)
    score_toxic = db.Column(db.Float, nullable=True)
    score_severe_toxic = db.Column(db.Float, nullable=True)
    score_obscene = db.Column(db.Float, nullable=True)
    score_threat = db.Column(db.Float, nullable=True)
    score_insult = db.Column(db.Float, nullable=True)
    score_identity_hate = db.Column(db.Float, nullable=True)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
