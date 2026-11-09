from flask import render_template, flash, redirect, url_for, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func
from app.extensions import db
from app.main import bp
from app.main.forms import CommentForm
from app.models import User, Comment
from app.toxic_bert.model import score_comment as score_comment_model


def _build_comment_dict(comment):
    """Serialise a Comment row into the JSON shape the frontend expects."""
    has_breakdown = comment.score_toxic is not None
    return {
        "id": comment.id,
        "body": comment.body,
        "author": comment.author.username,
        "score": comment.toxicity_score,
        "timestamp": "just now",
        "scores": {
            "toxic":          comment.score_toxic,
            "severe_toxic":   comment.score_severe_toxic,
            "obscene":        comment.score_obscene,
            "threat":         comment.score_threat,
            "insult":         comment.score_insult,
            "identity_hate":  comment.score_identity_hate,
        } if has_breakdown else None,
    }


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
        func.avg(Comment.toxicity_score).label('average_toxicity'),
        func.count(Comment.id).label('comment_count'),
    ).join(Comment, User.id == Comment.user_id).group_by(User.username).order_by(
        func.avg(Comment.toxicity_score).asc()
    ).all()

    return render_template('leaderboard.html', title='Leaderboard', data=leaderboard_data)


@bp.route('/score-comment', methods=['POST'])
@login_required
def score_comment():
    """Submit a comment, score it, persist it, return JSON."""
    form = CommentForm()
    if form.validate_on_submit():
        comment_text = form.comment.data
        result = score_comment_model(comment_text)

        composite = result["composite"]
        sub = result["scores"]

        comment = Comment(
            body=comment_text,
            author=current_user,
            toxicity_score=composite,
            score_toxic=sub["toxic"],
            score_severe_toxic=sub["severe_toxic"],
            score_obscene=sub["obscene"],
            score_threat=sub["threat"],
            score_insult=sub["insult"],
            score_identity_hate=sub["identity_hate"],
        )
        db.session.add(comment)
        db.session.commit()

        return jsonify({"success": True, "comment": _build_comment_dict(comment)})

    return jsonify({"success": False, "error": "Invalid comment."}), 400


@bp.route('/preview-score', methods=['POST'])
@login_required
def preview_score():
    """Score text without persisting — used for the live preview strip."""
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    result = score_comment_model(text)
    return jsonify(result)
