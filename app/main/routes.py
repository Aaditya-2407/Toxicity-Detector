from flask import render_template, flash, redirect, url_for, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func
from app.extensions import db
from app.main import bp
from app.main.forms import CommentForm
from app.models import User, Comment
# Import the model with a new name to avoid conflicts
from app.toxic_bert.model import score_comment as score_comment_model

@bp.route('/', methods=['GET'])
@bp.route('/index', methods=['GET'])
@login_required
def index():
    form = CommentForm()
    comments = Comment.query.order_by(Comment.timestamp.desc()).all()
    return render_template('index.html', title='Home', form=form, comments=comments)

@bp.route('/leaderboard')
@login_required
def leaderboard():
    leaderboard_data = db.session.query(
        User.username,
        func.avg(Comment.toxicity_score).label('average_toxicity')
    ).join(Comment, User.id == Comment.user_id).group_by(User.username).order_by(
        func.avg(Comment.toxicity_score).asc()
    ).all()
    
    return render_template('leaderboard.html', title='Leaderboard', data=leaderboard_data)

# This route handles the "aesthetic" instant comment submission
@bp.route('/score-comment', methods=['POST'])
@login_required
def score_comment():
    form = CommentForm()
    if form.validate_on_submit():
        comment_text = form.comment.data
        toxicity = score_comment_model(comment_text) # Use the imported model
        
        comment = Comment(body=comment_text, author=current_user, toxicity_score=toxicity)
        db.session.add(comment)
        db.session.commit()
        
        # Send a JSON response back to the JavaScript
        return jsonify({
            'success': True,
            'comment': {
                'body': comment.body,
                'author': comment.author.username,
                'score': comment.toxicity_score,
                'timestamp': 'just now'
            }
        })
    return jsonify({'success': False, 'error': 'Invalid comment.'}), 400