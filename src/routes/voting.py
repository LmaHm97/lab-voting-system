from flask import Blueprint, request, jsonify
from src.models.voting import db, Week, Presentation, Vote
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
    vote = Vote(
        presentation_id=presentation_id,
        user_identifier=user_identifier
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

