# webhooks.py
from flask import Blueprint, jsonify, request

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')

@webhooks_bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    return jsonify({'received': True}), 200

@webhooks_bp.route('/mailchimp', methods=['POST'])
def mailchimp_webhook():
    """Handle Mailchimp webhooks"""
    return jsonify({'received': True}), 200

@webhooks_bp.route('/planning-center', methods=['POST'])
def planning_center_webhook():
    """Handle Planning Center webhooks"""
    return jsonify({'received': True}), 200

@webhooks_bp.route('/test', methods=['GET', 'POST'])
def test_webhook():
    """Test webhook endpoint"""
    return jsonify({
        'message': 'Webhook test successful',
        'method': request.method,
        'data': request.get_json() if request.method == 'POST' else None
    }), 200

