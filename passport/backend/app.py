"""Futures Pulse Passport - Main Flask Application"""
from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import core modules
from core.db import init_db, engine
from core.auth import get_current_leader

# Import models to register them
from models import (
    Person, Track, TrackStop, Leader, Assignment,
    Stamp, Transfer, Activity, Note, RBACRole, EventLog
)

# Import routes
from routes import auth, leaders, people, inbox, push_queue, push, transfer, complete, stamps, tracks, reports, notes, passport

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-secret-key")

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000").split(",")
CORS(app, origins=cors_origins, supports_credentials=True)

# Initialize database
init_db()

# Register blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(leaders.bp)
app.register_blueprint(people.bp)
app.register_blueprint(inbox.bp)
app.register_blueprint(push_queue.bp)
app.register_blueprint(push.bp)
app.register_blueprint(transfer.bp)
app.register_blueprint(complete.bp)
app.register_blueprint(stamps.bp)
app.register_blueprint(tracks.bp)
app.register_blueprint(reports.bp)
app.register_blueprint(notes.bp)
app.register_blueprint(passport.bp)

@app.route('/')
def health():
    from flask import jsonify
    return jsonify({"status": "ok", "service": "Futures Pulse Passport"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

