"""
reviews.py — /api/reviews

avg_rating is now maintained by a PostgreSQL TRIGGER (trg_avg_rating).
The original Python-side aggregation has been removed — it was non-atomic
and would silently fail to update on DELETE or UPDATE of a review.
The trigger handles INSERT / UPDATE / DELETE automatically and within
the same transaction.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Review, Rental

reviews_bp = Blueprint('reviews', __name__, url_prefix='/api/reviews')


def err(msg, code=400): return jsonify({'success': False, 'message': msg}), code
def ok(data, msg='', code=200): return jsonify({'success': True, 'message': msg, 'data': data}), code


@reviews_bp.route('/', methods=['POST'])
@jwt_required()
def post_review():
    user_id = int(get_jwt_identity())
    body = request.get_json() or {}

    rental_id = body.get('rental_id')
    rating    = body.get('rating')
    comment   = body.get('comment_text')

    if not rental_id or not rating:
        return err('Missing rental_id or rating')

    # rating range is enforced by DB CHECK constraint (1–5),
    # but give a clear message here before hitting the DB
    if not (1 <= int(rating) <= 5):
        return err('Rating must be between 1 and 5')

    rental = Rental.query.get_or_404(rental_id)
    if rental.borrower_id != user_id:
        return err('Only the borrower can leave a review')

    if Review.query.filter_by(rental_id=rental_id).first():
        return err('Review already exists for this rental')

    review = Review(
        rental_id=rental_id,
        reviewer_id=user_id,
        reviewed_uid=rental.owner_id,
        rating=int(rating),
        comment_text=comment
    )
    db.session.add(review)
    db.session.commit()
    # avg_rating on the owner's User row is updated automatically by trg_avg_rating

    return ok({'review_id': review.review_id}, 'Review posted')
