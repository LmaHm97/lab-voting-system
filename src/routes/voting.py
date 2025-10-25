from flask import Blueprint, request, jsonify
from src.models.voting import db, Week, Presentation, Vote, Rating, Comment
from sqlalchemy.exc import IntegrityError

voting_bp = Blueprint('voting', __name__, url_prefix='/api')

# Get all weeks with presentations
@voting_bp.route('/weeks', methods=['GET'])
def get_weeks():
    weeks = Week.query.all()
    weeks_dict = {}
    for week in weeks:
        weeks_dict[week.week_id] = {
            'presentations': [p.to_dict() for p in week.presentations]
        }
    return jsonify(weeks_dict)

# Create a new week
@voting_bp.route('/weeks', methods=['POST'])
def create_week():
    data = request.json
    week_id = data.get('week_id')
    
    if not week_id:
        return jsonify({'error': 'week_id is required'}), 400
    
    # Check if week already exists
    existing_week = Week.query.filter_by(week_id=week_id).first()
    if existing_week:
        return jsonify({'error': 'Week already exists'}), 400
    
    week = Week(week_id=week_id)
    db.session.add(week)
    db.session.commit()
    
    return jsonify(week.to_dict()), 201

# Add a presentation to a week
@voting_bp.route('/presentations', methods=['POST'])
def add_presentation():
    data = request.json
    week_id = data.get('week_id')
    title = data.get('title')
    presenter = data.get('presenter')
    
    if not all([week_id, title, presenter]):
        return jsonify({'error': 'week_id, title, and presenter are required'}), 400
    
    # Ensure week exists
    week = Week.query.filter_by(week_id=week_id).first()
    if not week:
        week = Week(week_id=week_id)
        db.session.add(week)
        db.session.commit()
    
    presentation = Presentation(
        week_id=week_id,
        title=title,
        presenter=presenter,
        votes=0
    )
    db.session.add(presentation)
    db.session.commit()
    
    return jsonify(presentation.to_dict()), 201

# Remove a presentation
@voting_bp.route('/presentations/<int:presentation_id>', methods=['DELETE'])
def remove_presentation(presentation_id):
    presentation = Presentation.query.get(presentation_id)
    if not presentation:
        return jsonify({'error': 'Presentation not found'}), 404
    
    db.session.delete(presentation)
    db.session.commit()
    
    return jsonify({'message': 'Presentation deleted'}), 200

# Vote on a presentation
@voting_bp.route('/presentations/<int:presentation_id>/vote', methods=['POST'])
def vote_presentation(presentation_id):
    data = request.json
    user_identifier = data.get('user_identifier')
    
    if not user_identifier:
        return jsonify({'error': 'user_identifier is required'}), 400
    
    presentation = Presentation.query.get(presentation_id)
    if not presentation:
        return jsonify({'error': 'Presentation not found'}), 404
    
    # Check if user has already voted
    existing_vote = Vote.query.filter_by(
        presentation_id=presentation_id,
        user_identifier=user_identifier
    ).first()
    
    if existing_vote:
        return jsonify({'error': 'Already voted'}), 400
    
    # Add vote
    username = data.get('username', 'Anonymous')
    vote = Vote(
        presentation_id=presentation_id,
        user_identifier=user_identifier,
        username=username
    )
    presentation.votes += 1
    
    db.session.add(vote)
    db.session.commit()
    
    return jsonify(presentation.to_dict()), 200

# Check if user has voted on a presentation
@voting_bp.route('/presentations/<int:presentation_id>/has-voted', methods=['POST'])
def has_voted(presentation_id):
    data = request.json
    user_identifier = data.get('user_identifier')
    
    if not user_identifier:
        return jsonify({'error': 'user_identifier is required'}), 400
    
    vote = Vote.query.filter_by(
        presentation_id=presentation_id,
        user_identifier=user_identifier
    ).first()
    
    return jsonify({'has_voted': vote is not None})

# Get all votes for a user
@voting_bp.route('/votes/<user_identifier>', methods=['GET'])
def get_user_votes(user_identifier):
    votes = Vote.query.filter_by(user_identifier=user_identifier).all()
    presentation_ids = [vote.presentation_id for vote in votes]
    return jsonify({'voted_presentations': presentation_ids})

# Reset votes for a week
@voting_bp.route('/weeks/<week_id>/reset-votes', methods=['POST'])
def reset_week_votes(week_id):
    presentations = Presentation.query.filter_by(week_id=week_id).all()
    
    for presentation in presentations:
        # Delete all votes for this presentation
        Vote.query.filter_by(presentation_id=presentation.id).delete()
        presentation.votes = 0
    
    db.session.commit()
    
    return jsonify({'message': 'Votes reset for week'}), 200


# ==================== RATING ENDPOINTS ====================

# Add or update rating for a presentation
@voting_bp.route('/presentations/<int:presentation_id>/rate', methods=['POST'])
def rate_presentation(presentation_id):
    data = request.json
    user_identifier = data.get('user_identifier')
    rating_value = data.get('rating')
    
    if not user_identifier or rating_value is None:
        return jsonify({'error': 'user_identifier and rating are required'}), 400
    
    if not isinstance(rating_value, int) or rating_value < 1 or rating_value > 5:
        return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
    
    presentation = Presentation.query.get(presentation_id)
    if not presentation:
        return jsonify({'error': 'Presentation not found'}), 404
    
    # Check if user has already rated
    existing_rating = Rating.query.filter_by(
        presentation_id=presentation_id,
        user_identifier=user_identifier
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_value
    else:
        # Add new rating
        rating = Rating(
            presentation_id=presentation_id,
            user_identifier=user_identifier,
            rating=rating_value
        )
        db.session.add(rating)
    
    db.session.commit()
    
    return jsonify(presentation.to_dict()), 200


# Get user's rating for a presentation
@voting_bp.route('/presentations/<int:presentation_id>/my-rating', methods=['POST'])
def get_my_rating(presentation_id):
    data = request.json
    user_identifier = data.get('user_identifier')
    
    if not user_identifier:
        return jsonify({'error': 'user_identifier is required'}), 400
    
    rating = Rating.query.filter_by(
        presentation_id=presentation_id,
        user_identifier=user_identifier
    ).first()
    
    if rating:
        return jsonify({'rating': rating.rating})
    else:
        return jsonify({'rating': None})


# ==================== COMMENT ENDPOINTS ====================

# Add a comment to a presentation
@voting_bp.route('/presentations/<int:presentation_id>/comments', methods=['POST'])
def add_comment(presentation_id):
    data = request.json
    user_identifier = data.get('user_identifier')
    username = data.get('username', 'Anonymous')
    comment_text = data.get('comment_text')
    
    if not user_identifier or not comment_text:
        return jsonify({'error': 'user_identifier and comment_text are required'}), 400
    
    if len(comment_text.strip()) == 0:
        return jsonify({'error': 'Comment cannot be empty'}), 400
    
    presentation = Presentation.query.get(presentation_id)
    if not presentation:
        return jsonify({'error': 'Presentation not found'}), 404
    
    comment = Comment(
        presentation_id=presentation_id,
        user_identifier=user_identifier,
        username=username,
        comment_text=comment_text.strip()
    )
    db.session.add(comment)
    db.session.commit()
    
    return jsonify(comment.to_dict()), 201


# Get all comments for a presentation
@voting_bp.route('/presentations/<int:presentation_id>/comments', methods=['GET'])
def get_comments(presentation_id):
    presentation = Presentation.query.get(presentation_id)
    if not presentation:
        return jsonify({'error': 'Presentation not found'}), 404
    
    comments = Comment.query.filter_by(presentation_id=presentation_id).order_by(Comment.created_at.desc()).all()
    return jsonify({'comments': [c.to_dict() for c in comments]})


# Delete a comment (user can delete their own comments)
@voting_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    data = request.json
    user_identifier = data.get('user_identifier')
    
    if not user_identifier:
        return jsonify({'error': 'user_identifier is required'}), 400
    
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    # Only allow user to delete their own comment
    if comment.user_identifier != user_identifier:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment deleted'}), 200




# Delete a week and all its presentations
@voting_bp.route('/weeks/<week_id>', methods=['DELETE'])
def delete_week(week_id):
    week = Week.query.filter_by(week_id=week_id).first()
    if not week:
        return jsonify({'error': 'Week not found'}), 404
    
    db.session.delete(week)
    db.session.commit()
    
    return jsonify({'message': 'Week deleted'}), 200


# Get votes for a presentation (with usernames)
@voting_bp.route('/presentations/<int:presentation_id>/votes', methods=['GET'])
def get_presentation_votes(presentation_id):
    votes = Vote.query.filter_by(presentation_id=presentation_id).order_by(Vote.voted_at.desc()).all()
    return jsonify({
        'votes': [vote.to_dict() for vote in votes]
    })
