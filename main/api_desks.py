from flask import Blueprint, jsonify, request, session
from functools import wraps
from .desks_store import get_tables, add_table, remove_table

bp = Blueprint('api_desks', __name__, url_prefix='/api')

def _is_admin():
    # Try session flag first (works if you set session['is_admin'] on login)
    if session.get('is_admin'):
        return True
    # Fallback to flask-login current_user if present and has is_admin attribute
    try:
        from flask_login import current_user
        return getattr(current_user, 'is_admin', False)
    except Exception:
        return False

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _is_admin():
            return jsonify({"error": "admin_required"}), 403
        return f(*args, **kwargs)
    return decorated

@bp.route('/desks', methods=['GET'])
def list_desks():
    return jsonify(get_tables()), 200

@bp.route('/desks', methods=['POST'])
@admin_required
def create_desk():
    payload = request.get_json() or {}
    if not payload.get('name'):
        return jsonify({"error": "name_required"}), 400
    new = add_table(payload)
    return jsonify(new), 201

@bp.route('/desks/<table_id>', methods=['DELETE'])
@admin_required
def delete_desk(table_id):
    ok = remove_table(table_id)
    if not ok:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"deleted": table_id}), 200
