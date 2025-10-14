# serving_api.py
from flask import Blueprint, jsonify, request

serving_bp = Blueprint('serving', __name__, url_prefix='/api/serving')

@serving_bp.route('/opportunities', methods=['GET'])
def get_serving_opportunities():
    """Get all serving opportunities"""
    return jsonify([]), 200

@serving_bp.route('/opportunities', methods=['POST'])
def create_serving_opportunity():
    """Create a new serving opportunity"""
    return jsonify({'message': 'Serving opportunity created'}), 201

@serving_bp.route('/opportunities/<opportunity_id>', methods=['GET'])
def get_serving_opportunity(opportunity_id):
    """Get a specific serving opportunity"""
    return jsonify({'id': opportunity_id}), 200

@serving_bp.route('/opportunities/<opportunity_id>', methods=['PUT'])
def update_serving_opportunity(opportunity_id):
    """Update a serving opportunity"""
    return jsonify({'message': 'Serving opportunity updated'}), 200

@serving_bp.route('/opportunities/<opportunity_id>', methods=['DELETE'])
def delete_serving_opportunity(opportunity_id):
    """Delete a serving opportunity"""
    return jsonify({'message': 'Serving opportunity deleted'}), 200

@serving_bp.route('/teams', methods=['GET'])
def get_serving_teams():
    """Get all serving teams"""
    return jsonify([]), 200

