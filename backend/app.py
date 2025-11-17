# app.py

from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, flash, session, Response
from flask_cors import CORS
from flask_compress import Compress
from models import db, init_db, Person, EngagementProfile, BeaconZone, Event, EventCategory, create_person_with_engagement, ConnectGroup, ConnectGroupMeeting, ConnectGroupAttendance, ResourceCategory
from datetime import datetime, timezone, timedelta
import os
import re

try:
    import gspread
except Exception as e:
    print(f"[ERROR] Failed to import gspread: {e}")
    raise

try:
    import anthropic
except Exception as e:
    anthropic = None

try:
    from oauth2client.service_account import ServiceAccountCredentials
except Exception as e:
    print(f"[ERROR] Failed to import oauth2client.service_account: {e}")
    raise

import json
from typing import Dict, List, Optional, Any
import logging

try:
    from dotenv import load_dotenv
except Exception as e:
    print(f"[ERROR] Failed to import dotenv: {e}")
    raise

try:
    from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
except Exception as e:
    print(f"[ERROR] Failed to import Flask-Login: {e}")
    raise

try:
    from werkzeug.security import generate_password_hash, check_password_hash
except Exception as e:
    print(f"[ERROR] Failed to import werkzeug.security: {e}")
    raise

import requests
import uuid
from functools import wraps

try:
    from num2words import num2words
except ImportError:
    def num2words(n):
        return str(n)

# Default campus service time configuration
DEFAULT_CAMPUS_SERVICE_TIMES = {
    'Paradise': ['9:00 AM', '11:00 AM', '5:30 PM'],
    'South': ['9:00 AM', '11:00 AM'],
    'Salisbury': ['9:00 AM', '11:00 AM'],
    'Adelaide City': ['9:00 AM', '11:00 AM', '5:00 PM'],
    'Mount Barker': ['10:00 AM'],
    'Copper Coast': ['10:00 AM'],
    'Clare Valley': ['10:00 AM'],
    'Victor Harbor': ['10:00 AM'],
    'all_campuses': []  # Will be populated dynamically
}

def load_campus_config():
    """Load campus configuration from JSON file"""
    config_file = os.path.join(os.path.dirname(__file__), 'campus_config.json')
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                # Merge with default config, prioritizing loaded config
                merged_config = DEFAULT_CAMPUS_SERVICE_TIMES.copy()
                merged_config.update(loaded_config)
                return merged_config
        return DEFAULT_CAMPUS_SERVICE_TIMES.copy()
    except Exception as e:
        logger.error(f"Failed to load campus config: {e}")
        return DEFAULT_CAMPUS_SERVICE_TIMES.copy()

def save_campus_config(config: dict) -> bool:
    """Save campus configuration to JSON file"""
    config_file = os.path.join(os.path.dirname(__file__), 'campus_config.json')
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Campus configuration saved successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to save campus config: {e}")
        return False

# Load campus configuration at startup
CAMPUS_SERVICE_TIMES = load_campus_config()

def get_campus_service_times(campus: str) -> list:
    """Get service times for a specific campus from campuses.json"""
    campus_normalized = normalize_campus(campus)
    
    # Try to load from campuses.json first
    try:
        campuses_db = load_campuses_database()
        # Map normalized names to campus IDs
        campus_id_mapping = {
            'paradise': 'paradise',
            'south': 'south',
            'salisbury': 'salisbury',
            'adelaide city': 'adelaide_city',
            'mount barker': 'mount_barker',
            'copper coast': 'copper_coast',
            'clare valley': 'clare_valley',
            'victor harbor': 'victor_harbour'
        }
        
        campus_id = campus_id_mapping.get(campus_normalized, campus_normalized)
        campus_data = campuses_db.get('campuses', {}).get(campus_id, {})
        
        if campus_data and 'service_times' in campus_data:
            return campus_data['service_times']
    except Exception as e:
        logger.warning(f"Failed to load service times from campuses.json: {e}")
    
    # Fallback to hardcoded config
    campus_mapping = {
        'paradise': 'Paradise',
        'south': 'South',
        'salisbury': 'Salisbury',
        'adelaide city': 'Adelaide City',
        'mount barker': 'Mount Barker',
        'copper coast': 'Copper Coast',
        'clare valley': 'Clare Valley',
        'victor harbor': 'Victor Harbor'
    }
    
    config_key = campus_mapping.get(campus_normalized, campus)
    return CAMPUS_SERVICE_TIMES.get(config_key, ['10:00 AM'])

def get_all_service_times() -> dict:
    """Get all service times for all campuses"""
    return CAMPUS_SERVICE_TIMES.copy()

# Service time detection patterns for voice input
SERVICE_TIME_PATTERNS = {
    '9:00 AM': ['9am', '9 am', '9:00am', '9:00 am', 'nine am', 'nine o\'clock'],
    '10:00 AM': ['10am', '10 am', '10:00am', '10:00 am', 'ten am', 'ten o\'clock'],
    '11:00 AM': ['11am', '11 am', '11:00am', '11:00 am', 'eleven am', 'eleven o\'clock'],
    '5:00 PM': ['5pm', '5 pm', '5:00pm', '5:00 pm', 'five pm', 'five o\'clock', 'evening service']
}

# Weekend review detection phrases
WEEKEND_REVIEW_PHRASES = [
    'weekend review', 'weekend report', 'sunday review', 'sunday report',
    'how did the church go', 'how did futures church', 'how did the church do',
    'how did we go', 'church report', 'church review', 'futures church report',
    'futures church review', 'how did the church', 'how did futures', 'church summary',
    'church recap', 'church stats', 'futures church stats', 'futures church summary',
    'how did the church go this weekend', 'how did the church go this week',
    'how did futures church go', 'how did futures church go this weekend',
    'how did futures church go this week', 'how did the church go on sunday',
    'how did we go this weekend', 'how did we go this week', 'how did we go on sunday',
    'give me a weekend review', 'give me a church report', 'give me a church review',
    'give me a church summary', 'give me a church recap', 'give me a church stats',
    'give me a futures church report', 'give me a futures church review',
    'give me a futures church summary', 'give me a futures church recap',
    'give me a futures church stats', 'can i get a weekend review', 'can i get a church report',
    'can i get a church review', 'can i get a church summary', 'can i get a church recap',
    'can i get a church stats', 'can i get a futures church report', 'can i get a futures church review',
    'can i get a futures church summary', 'can i get a futures church recap',
    'can i get a futures church stats', 'church-wide report', 'church wide report',
    'church-wide review', 'church wide review', 'church-wide summary', 'church wide summary',
    'church-wide recap', 'church wide recap', 'church-wide stats', 'church wide stats',
]

# Pastor to review type mapping
PASTOR_MAPPING = {
    # Senior/Lead Pastors - get comprehensive all-campus reviews
    'ps ashley': 'all_campuses',
    'pastor ashley': 'all_campuses',
    'ashley': 'all_campuses',
    
    'ps josh': 'all_campuses',  # Lead Pastor - gets all campus data
    'pastor josh': 'all_campuses',
    'josh': 'all_campuses',
    
    'ps peter': 'paradise',
    'pastor peter': 'paradise',
    'peter': 'paradise',
    
    'ps david': 'adelaide_city',
    'pastor david': 'adelaide_city',
    'david': 'adelaide_city',
    
    'ps sarah': 'salisbury',
    'pastor sarah': 'salisbury',
    'sarah': 'salisbury',
    
    'ps mark': 'mount_barker',
    'pastor mark': 'mount_barker',
    'mark': 'mount_barker',
}

def detect_pastor_name(question: str) -> Optional[str]:
    """Detect pastor names in the question and return the campus they map to"""
    question_lower = question.lower()
    
    # Check for pastor names
    for pastor_name, campus in PASTOR_MAPPING.items():
        if pastor_name in question_lower:
            logger.info(f"[PASTOR_DETECTION] Found pastor '{pastor_name}' -> maps to '{campus}'")
            return campus
    
    return None

def detect_service_time(text: str) -> Optional[str]:
    """Detect service time mentioned in text"""
    text_lower = text.lower()
    
    for service_time, patterns in SERVICE_TIME_PATTERNS.items():
        for pattern in patterns:
            if pattern in text_lower:
                return service_time
    
    return None

def parse_service_attendance(text: str, campus: str) -> dict:
    """Parse service-specific attendance from text input"""
    service_times = get_campus_service_times(campus)
    service_attendance = {}
    
    # Try to extract attendance for each service time
    for service_time in service_times:
        patterns = SERVICE_TIME_PATTERNS.get(service_time, [])
        for pattern in patterns:
            # Look for patterns like "9am 150" or "150 at 9am"
            import re
            
            # Pattern: service time followed by number
            match = re.search(rf'{re.escape(pattern)}\s+(\d+)', text.lower())
            if match:
                service_attendance[service_time] = int(match.group(1))
                continue
                
            # Pattern: number followed by service time
            match = re.search(rf'(\d+)\s+(?:at\s+)?{re.escape(pattern)}', text.lower())
            if match:
                service_attendance[service_time] = int(match.group(1))
                continue
    
    return service_attendance

def load_local_data():
    """Load data from local JSON file as fallback when Google Sheets is not available"""
    try:
        # Try multiple possible locations for the data file
        data_locations = [
            'data/logged_stats.json',
            os.path.join(os.path.dirname(__file__), 'data/logged_stats.json'),
            'logged_stats.json',
            os.path.join(os.path.dirname(__file__), 'logged_stats.json')
        ]
        
        for data_path in data_locations:
            try:
                if os.path.exists(data_path):
                    with open(data_path, 'r') as f:
                        data = json.load(f)
                        logger.info(f"Loaded {len(data)} records from {data_path}")
                        return data
            except Exception as e:
                print(f"[DEBUG] Failed to load from {data_path}: {e}")
                continue
        
        logger.warning("No local data file found in any location")
        return []
    except Exception as e:
        logger.error(f"Failed to load local data: {e}")
        return []

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
print("[DEBUG] Finished Google Sheets Auth scope definition")

print("[DEBUG] Starting Google Sheets client initialization")
# Initialize Google Sheets client with robust fallback system
def initialize_google_sheets():
    """Initialize Google Sheets with fallback for both local and Railway deployment"""
    global sheet, client
    
    # Try multiple initialization methods
    initialization_methods = [
        ("Railway Environment Variable", initialize_from_railway),
        ("Local credentials.json", initialize_from_local_file),
        ("Local credentials.json in backend/", initialize_from_backend_file),
        ("Fallback to local data", initialize_fallback)
    ]
    
    for method_name, init_func in initialization_methods:
        try:
            print(f"[DEBUG] Trying {method_name}")
            result = init_func()
            if result:
                print(f"[DEBUG] Google Sheets initialized successfully via {method_name}")
                return True
        except Exception as e:
            print(f"[DEBUG] {method_name} failed: {e}")
            continue
    
    print("[WARNING] All Google Sheets initialization methods failed - using fallback")
    sheet = None
    return False

def initialize_from_railway():
    """Initialize from Railway environment variables"""
    global sheet, finance_sheet, client
    google_sheets_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    if not google_sheets_credentials:
        raise Exception("GOOGLE_SHEETS_CREDENTIALS not found")
    
    import json
    creds_dict = json.loads(google_sheets_credentials)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Stats")  # Default to "Stats" instead of "SHEETS"
    print(f"[DEBUG] Railway: Opening spreadsheet '{sheet_name}'")
    
    # Open the main Google Sheet file
    spreadsheet = client.open(sheet_name)
    print(f"[DEBUG] Railway: Spreadsheet opened successfully")
    print(f"[DEBUG] Railway: Available worksheets: {[ws.title for ws in spreadsheet.worksheets()]}")
    
    # Open the Stats worksheet
    sheet = spreadsheet.worksheet("Stats")  # Stats tab
    print(f"[DEBUG] Railway: Successfully opened 'Stats' worksheet")
    
    # Try to open the Tithe tab (try both "Tithe" and "tithe")
    try:
        finance_sheet = spreadsheet.worksheet("Tithe")
        print(f"[DEBUG] Railway: Successfully opened 'Tithe' worksheet")
    except Exception as e:
        try:
            finance_sheet = spreadsheet.worksheet("tithe")
            print(f"[DEBUG] Railway: Successfully opened 'tithe' worksheet")
        except Exception as e2:
            print(f"[WARNING] Railway: 'Tithe'/'tithe' worksheet not found - finance features will be disabled: {e}")
            finance_sheet = None
    
    print(f"[DEBUG] Railway: Google Sheets initialization complete")
    return True

def initialize_from_local_file():
    """Initialize from local credentials.json in current directory"""
    global sheet, finance_sheet, client
    if not os.path.exists("credentials.json"):
        raise Exception("credentials.json not found")
    
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    
    # Open the main Google Sheet file
    spreadsheet = client.open("Stats")
    sheet = spreadsheet.worksheet("Stats")  # Stats tab
    
    # Try to open the Tithe tab (try both "Tithe" and "tithe")
    try:
        finance_sheet = spreadsheet.worksheet("Tithe")
        print(f"[DEBUG] Local: Successfully opened 'Tithe' tab")
    except:
        try:
            finance_sheet = spreadsheet.worksheet("tithe")
            print(f"[DEBUG] Local: Successfully opened 'tithe' tab")
        except:
            print(f"[WARNING] Local: 'Tithe'/'tithe' tab not found - finance features will be disabled")
            finance_sheet = None
    
    return True

def initialize_from_backend_file():
    """Initialize from credentials.json in backend directory"""
    global sheet, finance_sheet, client
    backend_creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")
    if not os.path.exists(backend_creds_path):
        raise Exception("credentials.json not found in backend directory")
    
    creds = ServiceAccountCredentials.from_json_keyfile_name(backend_creds_path, scope)
    client = gspread.authorize(creds)
    
    # Open the main Google Sheet file
    spreadsheet = client.open("Stats")
    sheet = spreadsheet.worksheet("Stats")  # Stats tab
    
    # Try to open the Tithe tab (try both "Tithe" and "tithe")
    try:
        finance_sheet = spreadsheet.worksheet("Tithe")
        print(f"[DEBUG] Backend: Successfully opened 'Tithe' tab")
    except:
        try:
            finance_sheet = spreadsheet.worksheet("tithe")
            print(f"[DEBUG] Backend: Successfully opened 'tithe' tab")
        except:
            print(f"[WARNING] Backend: 'Tithe'/'tithe' tab not found - finance features will be disabled")
            finance_sheet = None
    
    return True

def initialize_fallback():
    """Fallback to local data when Google Sheets is not available"""
    global sheet, finance_sheet
    sheet = None
    finance_sheet = None
    print("[INFO] Using local data fallback - Google Sheets functionality disabled")
    return True

# Initialize Google Sheets
sheet = None  # Initialize as None first (Stats tab)
finance_sheet = None  # Initialize finance sheet for tithe entries
client = None  # Initialize client as None first

try:
    initialize_google_sheets()
except Exception as e:
    logger.error(f"Failed to initialize Google Sheets: {e}")
    print(f"[ERROR] Failed to initialize Google Sheets: {e}")
    sheet = None
    finance_sheet = None

# Simple rate limiter for Google Sheets API calls
import time
last_sheets_call = 0
SHEETS_RATE_LIMIT_SECONDS = 2  # Minimum 2 seconds between calls

# Cache for Google Sheets data - one cache per worksheet 
sheets_cache = {}  # Dictionary of caches keyed by worksheet title
cache_duration = 300  # 5 minutes - increased for better performance

def get_cached_sheets_data(cache_key):
    """Get cached data if fresh (under 2 min old)"""
    if cache_key in sheets_cache:
        cache_entry = sheets_cache[cache_key]
        if cache_entry['data'] and (time.time() - cache_entry['timestamp']) < cache_duration:
            print(f"[CACHE HIT] Using cached data for '{cache_key}' (age: {time.time() - cache_entry['timestamp']:.1f}s)")
            return cache_entry['data']
    return None

def clear_sheets_cache(worksheet_title=None):
    """Clear cache for a specific worksheet or all worksheets"""
    global sheets_cache
    if worksheet_title:
        # Clear cache for specific worksheet
        cache_key_pattern = f"{worksheet_title}_"
        keys_to_remove = [key for key in sheets_cache.keys() if key.startswith(cache_key_pattern)]
        for key in keys_to_remove:
            del sheets_cache[key]
        print(f"[CACHE] Cleared cache for '{worksheet_title}' worksheet")
    else:
        # Clear all cache
        sheets_cache = {}
        print(f"[CACHE] Cleared all cache")

def safe_sheets_request(func, *args, force_refresh=False, **kwargs):
    """Make a request to Google Sheets with rate limiting and caching"""
    global last_sheets_call
    
    # Generate cache key from function object (worksheet)
    try:
        worksheet_title = func.__self__.title
        cache_key = f"{worksheet_title}_{func.__name__}"
    except:
        cache_key = f"{func.__name__}_default"
    
    # Check cache first (unless force_refresh is True)
    if not force_refresh:
        cached = get_cached_sheets_data(cache_key)
        if cached:
            return cached
    
    # Rate limiting: ensure minimum time between calls
    current_time = time.time()
    time_since_last_call = current_time - last_sheets_call
    
    if time_since_last_call < SHEETS_RATE_LIMIT_SECONDS:
        sleep_time = SHEETS_RATE_LIMIT_SECONDS - time_since_last_call
        print(f"[RATE_LIMIT] Sleeping for {sleep_time:.2f} seconds to avoid Google Sheets rate limit")
        time.sleep(sleep_time)
    
    last_sheets_call = time.time()
    
    try:
        result = func(*args, **kwargs)
        # Cache the result with worksheet-specific key
        sheets_cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }
        print(f"[CACHE] Stored {len(result) if result else 0} rows for '{cache_key}'")
        return result
    except Exception as e:
        error_msg = str(e).lower()
        
        # Handle list index out of range (empty sheet or malformed structure)
        if 'list index out of range' in error_msg or 'index out of range' in error_msg:
            logger.warning(f"Detected 'list index out of range' error, attempting manual fetch from worksheet")
            try:
                worksheet = func.__self__
                all_values = worksheet.get_all_values()
                
                # If sheet is completely empty, return empty list
                if not all_values or len(all_values) == 0:
                    logger.info(f"Sheet '{worksheet.title}' is empty, returning empty list")
                    return []
                
                # If only headers exist (1 row), return empty list
                if len(all_values) < 2:
                    logger.info(f"Sheet '{worksheet.title}' has only headers, no data rows")
                    return []
                
                # Get headers and filter out empty ones
                headers = all_values[0] if all_values else []
                if not headers:
                    logger.warning(f"Sheet '{worksheet.title}' has no headers")
                    return []
                
                valid_headers = []
                valid_indices = []
                
                for i, header in enumerate(headers):
                    if header and str(header).strip():
                        valid_headers.append(str(header).strip())
                        valid_indices.append(i)
                
                if not valid_headers:
                    logger.warning(f"Sheet '{worksheet.title}' has no valid headers")
                    return []
                
                # Build records using only valid headers
                records = []
                for row_idx, row in enumerate(all_values[1:], start=2):
                    record = {}
                    for i, col_index in enumerate(valid_indices):
                        if col_index < len(row):
                            record[valid_headers[i]] = row[col_index]
                        else:
                            record[valid_headers[i]] = ""  # Fill with empty string if column missing
                    records.append(record)
                
                # Cache and return
                sheets_cache[cache_key] = {
                    'data': records,
                    'timestamp': time.time()
                }
                logger.info(f"[CACHE] Stored {len(records)} rows for '{cache_key}' (manual fetch due to index error)")
                return records
            except Exception as manual_error:
                logger.error(f"Manual fetch also failed: {manual_error}")
                # Return empty list instead of raising error for finance sheet
                if 'finance' in cache_key.lower() or 'tithe' in cache_key.lower():
                    logger.warning(f"Returning empty list for finance sheet due to error")
                    return []
                raise e
        
        # Handle empty header cells error specifically
        elif 'empty cell' in error_msg and 'header' in error_msg:
            logger.warning(f"Detected empty headers in sheet, attempting manual fetch")
            try:
                # Try to get data manually by fetching all values and building records
                worksheet = func.__self__
                all_values = worksheet.get_all_values()
                
                if len(all_values) < 2:
                    return []
                
                # Get headers and filter out empty ones
                headers = all_values[0]
                valid_headers = []
                valid_indices = []
                
                for i, header in enumerate(headers):
                    if header and header.strip():
                        valid_headers.append(header.strip())
                        valid_indices.append(i)
                
                # Build records using only valid headers
                records = []
                for row in all_values[1:]:
                    record = {}
                    for i, col_index in enumerate(valid_indices):
                        if col_index < len(row):
                            record[valid_headers[i]] = row[col_index]
                    records.append(record)
                
                # Cache and return
                sheets_cache[cache_key] = {
                    'data': records,
                    'timestamp': time.time()
                }
                print(f"[CACHE] Stored {len(records)} rows for '{cache_key}' (manual fetch)")
                return records
            except Exception as manual_error:
                logger.error(f"Manual fetch also failed: {manual_error}")
                raise e
        else:
            logger.error(f"Google Sheets API error: {e}")
            raise e
print("[DEBUG] Finished Google Sheets client initialization")

print("[DEBUG] Starting Claude setup")
# Claude setup
try:
    # Try to import anthropic
    try:
        from anthropic import Anthropic
        print("[DEBUG] Successfully imported anthropic.Anthropic")
        
        # Check version
        import anthropic
        print(f"[DEBUG] Anthropic version: {anthropic.__version__}")
        
    except ImportError as e:
        print(f"[ERROR] Failed to import anthropic: {e}")
        logger.error(f"Failed to import anthropic: {e}")
        claude = None
        raise e
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"[DEBUG] Found ANTHROPIC_API_KEY: {api_key[:10]}...")
        
        # Clear any proxy environment variables that might interfere
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for var in proxy_vars:
            if var in os.environ:
                print(f"[DEBUG] Clearing proxy environment variable: {var}")
                del os.environ[var]
        
        # Try multiple initialization methods for Railway compatibility
        claude = None
        initialization_methods = [
            ("Standard initialization", lambda: Anthropic(api_key=api_key)),
            ("With timeout", lambda: Anthropic(api_key=api_key, timeout=30.0)),
            ("With custom base URL", lambda: Anthropic(api_key=api_key, base_url="https://api.anthropic.com")),
            ("Minimal initialization", lambda: Anthropic(api_key=api_key)),
        ]
        
        for method_name, init_func in initialization_methods:
            try:
                print(f"[DEBUG] Trying {method_name}")
                claude = init_func()
                # Skip test call to avoid hanging during startup
                logger.info(f"Claude initialized successfully via {method_name}")
                print(f"[DEBUG] Claude initialized successfully via {method_name}")
                break
            except Exception as e:
                print(f"[DEBUG] {method_name} failed: {e}")
                logger.warning(f"Claude initialization method '{method_name}' failed: {e}")
                continue
        
        if claude is None:
            print("[WARNING] All Claude initialization methods failed")
            logger.warning("All Claude initialization methods failed")
            claude = None
        else:
            print("[DEBUG] Claude initialization completed successfully")
    else:
        logger.warning("ANTHROPIC_API_KEY not found in environment variables")
        print("[WARNING] ANTHROPIC_API_KEY not found in environment variables")
        claude = None
except Exception as e:
    logger.error(f"Failed to initialize Claude: {e}")
    print(f"[ERROR] Failed to initialize Claude: {e}")
    claude = None
print("[DEBUG] Finished Claude setup")

print("[DEBUG] Starting ElevenLabs setup")
# ElevenLabs setup
try:
    import requests
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default voice ID
    if elevenlabs_api_key:
        logger.info("ElevenLabs API key found")
        print("[DEBUG] ElevenLabs API key found")
    else:
        logger.warning("ELEVENLABS_API_KEY not found - will use browser TTS")
        print("[WARNING] ELEVENLABS_API_KEY not found - will use browser TTS")
except Exception as e:
    logger.error(f"Failed to initialize ElevenLabs: {e}")
    print(f"[ERROR] Failed to initialize ElevenLabs: {e}")
    elevenlabs_api_key = None
print("[DEBUG] Finished ElevenLabs setup")

print("[DEBUG] Starting memory storage setup")
# Memory storage for conversational history
conversation_memory_file = "data/conversation_memory.json"
print("[DEBUG] Finished memory storage setup")

# Restore missing memory functions

def parse_any_date(date_str):
    """Parse date from various formats commonly found in Google Sheets"""
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%-m/%-d/%Y'):
        try:
            return datetime.strptime(date_str, fmt)
        except Exception:
            continue
    raise ValueError(f"Unrecognized date format: {date_str}")

def safe_int(val: Any) -> int:
    """Safely convert a value to int, returning 0 on failure."""
    try:
        return int(str(val).replace(",", "").strip()) if str(val).strip() else 0
    except Exception:
        return 0

def get_row_timestamp(row: Any) -> datetime:
    """Extract and parse a timestamp from a row (dict or tuple). Returns datetime.min on failure."""
    import re
    from datetime import datetime
    ts = ''
    if isinstance(row, dict):
        # Prefer 'Date' column over 'Timestamp' for accurate date tracking
        ts = row.get('Date', '') or row.get('Timestamp', '')
    elif isinstance(row, (list, tuple)):
        # For list/tuple, column B (index 1) is Date, column A (index 0) is Timestamp
        ts = row[1] if len(row) > 1 else (row[0] if len(row) > 0 else '')
    
    if not ts:
        return datetime.min
    
    # Try multiple date formats
    date_formats = [
        '%Y-%m-%dT%H:%M:%S.%f',  # 2025-08-02T10:00:00.000000 (ISO with microseconds)
        '%Y-%m-%dT%H:%M:%S',     # 2025-08-02T10:00:00 (ISO without microseconds)
        '%Y-%m-%d %H:%M:%S',     # 2024-08-04 10:30:00
        '%Y-%m-%d',              # 2024-08-04
        '%m/%d/%Y',              # 10/13/2024
        '%m/%d/%Y %H:%M:%S',     # 10/13/2024 10:30:00
        '%d/%m/%Y',              # 13/10/2024
        '%d/%m/%Y %H:%M:%S',     # 13/10/2024 10:30:00
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(str(ts).strip(), fmt)
        except ValueError:
            continue
    
    # If all formats fail, try regex matching
    try:
        # Match YYYY-MM-DD format
        match = re.match(r'(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}:\d{2}))?', str(ts))
        if match:
            date_part = match.group(1)
            time_part = match.group(2) or '00:00:00'
            return datetime.strptime(f'{date_part} {time_part}', '%Y-%m-%d %H:%M:%S')
    except Exception:
        pass
    
    return datetime.min

def load_conversation_memory() -> Dict[str, Any]:
    """Load conversation memory from file"""
    try:
        if os.path.exists(conversation_memory_file):
            with open(conversation_memory_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load conversation memory: {e}")
    return {}

def save_conversation_memory(memory: Dict[str, Any]):
    """Save conversation memory to file"""
    try:
        os.makedirs(os.path.dirname(conversation_memory_file), exist_ok=True)
        with open(conversation_memory_file, 'w') as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save conversation memory: {e}")

print("[DEBUG] Creating Flask app instance")
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'futures-church-secret-key-2025')

# Configure session cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Configure SQLAlchemy database
# Strip whitespace from DATABASE_URL to handle Railway environment variable issues
database_url = os.environ.get('DATABASE_URL', 'sqlite:///futures_link.db')
if database_url:
    database_url = database_url.strip()  # Remove leading/trailing whitespace
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure direct database connection for new tables (regions, campuses_new)
# These are in church_voice.db, while SQLAlchemy uses futures_link.db
CHURCH_VOICE_DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'church_voice.db')

def get_db():
    """Get a direct sqlite3 connection to church_voice.db for new tables"""
    import sqlite3
    
    # On Railway, check if DATABASE_URL points to a database with users table
    database_url = os.getenv('DATABASE_URL', '').strip()
    if database_url and database_url.startswith('sqlite:///'):
        potential_path = database_url.replace('sqlite:///', '')
        if potential_path.startswith('/'):
            # Check if users table exists in this database
            try:
                test_conn = sqlite3.connect(potential_path)
                test_cursor = test_conn.cursor()
                test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if test_cursor.fetchone():
                    test_conn.close()
                    # Users table exists here, use this database
                    return sqlite3.connect(potential_path)
                test_conn.close()
            except:
                pass  # Fall back to default
    
    # Default to CHURCH_VOICE_DB_PATH
    return sqlite3.connect(CHURCH_VOICE_DB_PATH)

def run_migrations():
    """Run SQL migrations on startup"""
    import sqlite3
    try:
        # Determine which database to use for migrations
        # Check if DATABASE_URL points to a database we should use
        db_path = CHURCH_VOICE_DB_PATH
        database_url = os.getenv('DATABASE_URL', '').strip()
        if database_url and database_url.startswith('sqlite:///'):
            potential_path = database_url.replace('sqlite:///', '')
            if potential_path.startswith('/'):
                # On Railway, use the DATABASE_URL database
                db_path = potential_path
        
        # Ensure instance directory exists (for default path)
        if db_path == CHURCH_VOICE_DB_PATH:
            os.makedirs(os.path.dirname(CHURCH_VOICE_DB_PATH), exist_ok=True)
        else:
            # For absolute paths, ensure parent directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Get migrations directory
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        
        if not os.path.exists(migrations_dir):
            logger.warning(f"Migrations directory not found: {migrations_dir}")
            return
        
        # Get all SQL files in migrations directory
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
        
        if not migration_files:
            logger.info("No migration files found")
            return
        
        logger.info(f"Running migrations on database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create migrations tracking table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        
        # Get list of already applied migrations
        cursor.execute('SELECT filename FROM schema_migrations')
        applied_migrations = set(row[0] for row in cursor.fetchall())
        
        # Run pending migrations
        for migration_file in migration_files:
            if migration_file in applied_migrations:
                logger.info(f"Migration {migration_file} already applied, skipping")
                continue
            
            migration_path = os.path.join(migrations_dir, migration_file)
            logger.info(f"Running migration: {migration_file}")
            
            try:
                with open(migration_path, 'r') as f:
                    migration_sql = f.read()
                
                # Execute the migration
                # For ALTER TABLE ADD COLUMN, SQLite will fail if column exists
                # We'll catch that specific error and continue
                migration_succeeded = False
                try:
                    cursor.executescript(migration_sql)
                    conn.commit()
                    migration_succeeded = True
                except sqlite3.OperationalError as e:
                    error_msg = str(e).lower()
                    # If column already exists, that's okay - skip it
                    if 'duplicate column' in error_msg or 'already exists' in error_msg or 'duplicate column name' in error_msg:
                        logger.info(f"Migration {migration_file}: Column already exists, skipping")
                        conn.rollback()
                        migration_succeeded = True  # Consider it successful since column exists
                    else:
                        # Other operational errors should be raised
                        logger.error(f"Migration {migration_file} failed with OperationalError: {e}")
                        conn.rollback()
                        raise
                
                # Mark migration as applied (only if we got here without error)
                if migration_succeeded:
                    try:
                        cursor.execute('INSERT INTO schema_migrations (filename) VALUES (?)', (migration_file,))
                        conn.commit()
                        logger.info(f"Successfully applied migration: {migration_file}")
                    except sqlite3.IntegrityError:
                        # Migration already marked as applied
                        logger.info(f"Migration {migration_file} already marked as applied")
                        conn.rollback()
            except Exception as e:
                error_msg = str(e).lower()
                logger.error(f"Failed to apply migration {migration_file}: {e}")
                conn.rollback()
                # Don't raise for column already exists errors - just log and continue
                # Allow app to start even if migration fails (non-critical)
                if 'duplicate column' not in error_msg and 'already exists' not in error_msg and 'duplicate column name' not in error_msg:
                    logger.warning(f"Migration {migration_file} failed, but continuing startup...")
                    # Don't raise - allow app to start
        
        conn.close()
        logger.info("All migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
        # Don't raise - allow app to start even if migrations fail
        # This prevents the app from crashing on startup due to migration issues
        logger.warning("Continuing app startup despite migration errors...")

CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"], allow_headers=["Content-Type", "Authorization"])

# Enable response compression for better performance
Compress(app)

# Initialize database
init_db(app)

# Run migrations
run_migrations()

# Seed database with initial data
try:
    from seed_campuses import seed_campuses
    seed_campuses()
except Exception as e:
    logger.warning(f"Failed to seed campuses: {e}")

try:
    from seed_users import seed_users
    seed_users()
except Exception as e:
    logger.warning(f"Failed to seed users: {e}")

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'api_login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized API requests - return JSON instead of redirect"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Authentication required. Please sign in.'}), 401
    # For non-API routes, redirect to login
    return redirect(url_for('api_login'))

# User management functions
def load_users_database():
    """Load users from database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, password_hash, full_name, email, role, campus, active
            FROM users
            WHERE active = 1
        ''')
        
        users = {}
        for row in cursor.fetchall():
            username = row[1]
            users[username] = {
                'id': row[0],
                'username': row[1],
                'password_hash': row[2],
                'full_name': row[3] or username,
                'email': row[4] or '',
                'role': row[5],
                'campus': row[6] or '',
                'active': bool(row[7])
            }
        
        conn.close()
        
        if not users:
            print("[DEBUG] No users found in database")
            return {'users': {}}
        
        return {'users': users}
        
    except Exception as e:
        print(f"[DEBUG] Failed to load users from database: {e}")
        # If no database, create default users
        print("[DEBUG] No users.json found, creating default users")
        default_users = {
            "users": {
                "admin": {
                    "id": "admin",
                    "username": "admin",
                    "email": "admin@futureschurch.com",
                    "full_name": "Administrator",
                    "role": "admin",
                    "campus": "all_campuses",
                    "active": True,
                    "password_hash": "futures2025"
                }
            },
            "roles": {
                "admin": {
                    "name": "Administrator",
                    "permissions": {
                        "log_stats": "all",
                        "recall_stats": "all",
                        "dashboard_access": "all",
                        "query_access": "all",
                        "manage_users": True,
                        "system_settings": True,
                        "finance_access": True,
                        "cross_location_comparison": True
                    }
                }
            }
        }
        return default_users
    except Exception as e:
        logger.error(f"Failed to load users database: {e}")
        return {"users": {}, "roles": {}}
    
def save_users_database(data):
    """Save users to database (legacy function for compatibility)"""
    # This function is kept for compatibility but now saves to database
    # Individual user operations should use direct SQL instead
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        for username, user_data in data.get('users', {}).items():
            # Check if user exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing user
                cursor.execute('''
                    UPDATE users 
                    SET password_hash = ?, full_name = ?, email = ?, role = ?, campus = ?, active = ?
                    WHERE username = ?
                ''', (
                    user_data.get('password_hash', ''),
                    user_data.get('full_name', username),
                    user_data.get('email', ''),
                    user_data.get('role', 'campus_pastor'),
                    user_data.get('campus', ''),
                    1 if user_data.get('active', True) else 0,
                    username
                ))
            else:
                # Insert new user
                cursor.execute('''
                    INSERT INTO users (username, password_hash, full_name, email, role, campus, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    username,
                    user_data.get('password_hash', ''),
                    user_data.get('full_name', username),
                    user_data.get('email', ''),
                    user_data.get('role', 'campus_pastor'),
                    user_data.get('campus', ''),
                    1 if user_data.get('active', True) else 0
                ))
        
        conn.commit()
        conn.close()
        print(f"[DEBUG] Saved users to database")
        return True
    except Exception as e:
        logger.error(f"Failed to save users to database: {e}")
        print(f"[DEBUG] Failed to save users to database: {e}")
        return False

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.full_name = user_data['full_name']
        self.role = user_data['role']
        self.campus = user_data['campus']
        self.active = user_data['active']
        self.password_hash = user_data['password_hash']
        
    def is_authenticated(self):
        return True
        
    def is_active(self):
        return self.active
        
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.id)
        
    def check_password(self, password):
        """Check if the provided password is correct"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
        
    def has_permission(self, permission_type, campus=None):
        """Check if user has specific permission based on role"""
        # Define permissions for each role
        role_permissions = {
            'admin': {
                'log_stats': True,
                'recall_stats': True,
                'dashboard_access': True,
                'query_access': True,
                'finance_access': True,
                'manage_users': True,
                'manage_campuses': True,
                'view_all_campuses': True
            },
            'senior_leadership': {
                'log_stats': True,
                'recall_stats': True,
                'dashboard_access': True,
                'query_access': True,
                'finance_access': True,
                'manage_users': True,
                'manage_campuses': True,
                'view_all_campuses': True
            },
            'senior_leader': {
                'log_stats': True,
                'recall_stats': True,
                'dashboard_access': True,
                'query_access': True,
                'finance_access': True,
                'manage_users': True,
                'manage_campuses': True,
                'view_all_campuses': True
            },
            'senior_pastor': {
                'log_stats': True,
                'recall_stats': True,
                'dashboard_access': True,
                'query_access': True,
                'finance_access': True,
                'manage_users': True,
                'manage_campuses': True,
                'view_all_campuses': True
            },
            'lead_pastor': {
                'log_stats': True,
                'recall_stats': True,
                'dashboard_access': True,
                'query_access': True,
                'finance_access': True,
                'manage_users': True,
                'manage_campuses': True,
                'view_all_campuses': True
            },
            'finance': {
                'log_stats': False,
                'recall_stats': False,  # Cannot view dashboards
                'dashboard_access': False,  # No dashboard access
                'query_access': False,
                'finance_access': True,  # Can ONLY submit finance data
                'manage_users': False,
                'manage_campuses': False,
                'view_all_campuses': False
            },
            'campus_pastor': {
                'log_stats': True,  # Can log stats for their campus
                'recall_stats': 'own_campus',  # Can only see their own campus
                'dashboard_access': 'own_campus',
                'query_access': True,
                'finance_access': False,
                'manage_users': False,
                'manage_campuses': False,
                'view_all_campuses': False
            },
            'pastor': {
                'log_stats': True,  # Can log stats
                'recall_stats': 'own_campus',
                'dashboard_access': 'own_campus',
                'query_access': True,
                'finance_access': False,
                'manage_users': False,
                'manage_campuses': False,
                'view_all_campuses': False
            }
        }
        
        perms = role_permissions.get(self.role, {})
        perm_value = perms.get(permission_type, False)
        
        # Handle campus-specific permissions
        if permission_type == 'log_stats':
            if perm_value is True:
                return True
            elif perm_value == 'own_campus':
                return campus is None or campus == self.campus
            return False
            
        elif permission_type == 'recall_stats':
            if perm_value is True:
                return True
            elif perm_value == 'own_campus':
                return campus is None or campus == self.campus or self.campus == 'all_campuses'
            return False
            
        elif permission_type == 'dashboard_access':
            if perm_value is True:
                return True
            elif perm_value == 'own_campus':
                return campus is None or campus == self.campus or self.campus == 'all_campuses'
            return perm_value
            
        elif permission_type == 'query_access':
            return perm_value is True
            
        # For all other permissions, just return the boolean value
        else:
            return perm_value is True
        
    def get_accessible_campuses(self):
        """Get list of campuses this user can access for data recall"""
        if self.has_permission('recall_stats'):
            if self.campus == 'all_campuses':
                return ['all_campuses', 'paradise', 'adelaide_city', 'salisbury', 'south', 'mount_barker']
            else:
                return [self.campus]
        return []

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, password_hash, full_name, email, role, campus, active
            FROM users
            WHERE id = ? AND active = 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user_data = {
                'id': str(row[0]),  # Flask-Login expects string ID
                'username': row[1],
                'password_hash': row[2],
                'full_name': row[3] or row[1],
                'email': row[4] or '',
                'role': row[5],
                'campus': row[6] or '',
                'active': bool(row[7])
            }
            return User(user_data)
        return None
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
        return None

def authenticate_user(username, password):
    """Authenticate user and return User object if valid"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        # Use TRIM to handle any trailing spaces in database
        cursor.execute('''
            SELECT id, username, password_hash, full_name, email, role, campus, active
            FROM users
            WHERE TRIM(username) = ? AND active = 1
        ''', (username,))
        
        row = cursor.fetchone()
        
        if row:
            user_data = {
                'id': str(row[0]),
                'username': row[1],
                'password_hash': row[2],
                'full_name': row[3] or row[1],
                'email': row[4] or '',
                'role': row[5],
                'campus': row[6] or '',
                'active': bool(row[7])
            }
            
            user = User(user_data)
            if user.check_password(password):
                # Update last login
                cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                             (datetime.now(), row[0]))
                conn.commit()
                conn.close()
                return user
        
        conn.close()
        return None
    except Exception as e:
        logger.error(f"Authentication error for user {username}: {e}")
        return None

print("[DEBUG] User management functions and classes defined")

# Campus management functions
def load_campuses_database():
    """Load campuses from JSON file"""
    try:
        with open(os.path.join(os.path.dirname(__file__), 'campuses.json'), 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load campuses database: {e}")
        # Return basic fallback campuses
        return {
            "campuses": {
                "paradise": {"id": "paradise", "name": "Paradise Campus", "display_name": "Paradise", "active": True, "detection_patterns": ["paradise"]},
                "south": {"id": "south", "name": "South Campus", "display_name": "South", "active": True, "detection_patterns": ["south"]},
                "all_campuses": {"id": "all_campuses", "name": "All Campuses", "display_name": "All Campuses", "active": True, "special": True}
            },
            "metadata": {"version": "1.0"}
        }

def save_campuses_database(data):
    """Save campuses to JSON file"""
    try:
        # Update metadata
        data.setdefault('metadata', {})['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        active_count = sum(1 for campus in data.get('campuses', {}).values() if campus.get('active', False))
        data['metadata']['active_campuses'] = active_count
        data['metadata']['total_campuses'] = len(data.get('campuses', {}))
        
        with open(os.path.join(os.path.dirname(__file__), 'campuses.json'), 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save campuses database: {e}")
        return False

def get_active_campuses():
    """Get list of active campuses for dropdowns"""
    active_campuses = []
    
    try:
        # Try to load from database first
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.campus_id, c.name, c.display_name, c.region_id, r.code as region_code
            FROM campuses_new c
            LEFT JOIN regions r ON c.region_id = r.id
            WHERE c.active = 1
            ORDER BY c.display_name
        ''')
        
        for row in cursor.fetchall():
            active_campuses.append({
                'id': row[0],
                'name': row[2],  # display_name
                'full_name': row[1],  # name
                'region_id': row[3],  # region_id
                'region_code': row[4]  # region_code (AU, US, etc.)
            })
        
        conn.close()
        
        # Add "All Campuses" option at the top
        if active_campuses:
            active_campuses.insert(0, {
                'id': 'all_campuses',
                'name': 'All Campuses',
                'full_name': 'All Campuses',
                'region_id': None,
                'region_code': None
            })
        
    except Exception as e:
        logger.warning(f"Failed to load campuses from database, falling back to JSON: {e}")
        # Fallback to JSON file
        campuses_db = load_campuses_database()
        
        for campus_id, campus_data in campuses_db.get('campuses', {}).items():
            if campus_data.get('active', False):
                active_campuses.append({
                    'id': campus_id,
                    'name': campus_data.get('display_name', campus_data.get('name', campus_id)),
                    'full_name': campus_data.get('name', campus_id)
                })
        
        # Sort by name, but put "All Campuses" first if it exists
        active_campuses.sort(key=lambda x: (x['id'] != 'all_campuses', x['name']))
    
    return active_campuses

def get_campuses_for_user():
    """Get campuses accessible to current user based on their role"""
    try:
        if not hasattr(current_user, 'role'):
            return {'campuses': []}
            
        campuses_db = load_campuses_database()
        accessible_campuses = []
        
        # Finance team and admin roles can access all campuses
        if current_user.role in ['finance', 'admin', 'senior_leader']:
            for campus_id, campus_data in campuses_db.get('campuses', {}).items():
                if campus_data.get('active', False) and campus_id != 'all_campuses':
                    accessible_campuses.append({
                        'id': campus_id,
                        'name': campus_data.get('display_name', campus_data.get('name', campus_id)),
                        'full_name': campus_data.get('name', campus_id)
                    })
        elif current_user.role == 'campus_pastor':
            # Campus pastors only see their own campus
            user_campus = current_user.campus
            if user_campus in campuses_db.get('campuses', {}):
                campus_data = campuses_db['campuses'][user_campus]
                if campus_data.get('active', False):
                    accessible_campuses.append({
                        'id': user_campus,
                        'name': campus_data.get('display_name', campus_data.get('name', user_campus)),
                        'full_name': campus_data.get('name', user_campus)
                    })
        else:
            # Other roles get all campuses by default (except all_campuses)
            for campus_id, campus_data in campuses_db.get('campuses', {}).items():
                if campus_data.get('active', False) and campus_id != 'all_campuses':
                    accessible_campuses.append({
                        'id': campus_id,
                        'name': campus_data.get('display_name', campus_data.get('name', campus_id)),
                        'full_name': campus_data.get('name', campus_id)
                    })
        
        return {
            'campuses': sorted(accessible_campuses, key=lambda x: x['name'])
        }
    except Exception as e:
        logger.error(f"Error getting campuses for user: {e}")
        return {'campuses': []}

def get_campus_detection_patterns():
    """Get dynamic campus detection patterns from configuration with natural speech support"""
    campuses_db = load_campuses_database()
    patterns = {}
    
    for campus_id, campus_data in campuses_db.get('campuses', {}).items():
        if campus_data.get('active', False):
            detection_patterns = campus_data.get('detection_patterns', [campus_id])
            
            # Create flexible patterns that handle natural speech
            flexible_patterns = []
            for pattern in detection_patterns:
                # Add the base pattern
                flexible_patterns.append(rf'\b{re.escape(pattern)}\b')
                # Add common speech patterns
                flexible_patterns.append(rf'\bfor {re.escape(pattern)}\b')
                flexible_patterns.append(rf'\bat {re.escape(pattern)}\b')
                flexible_patterns.append(rf'\b{re.escape(pattern)} campus\b')
                flexible_patterns.append(rf'\bstats for {re.escape(pattern)}\b')
                flexible_patterns.append(rf'\blog stats for {re.escape(pattern)}\b')
                flexible_patterns.append(rf'\breporting for {re.escape(pattern)}\b')
            
            # Join patterns with OR regex
            pattern = '(?:' + '|'.join(flexible_patterns) + ')'
            patterns[campus_id] = pattern
    
    return patterns

print("[DEBUG] Campus management functions defined")

# Permission decorators
def require_permission(permission_type):
    """Decorator to check if user has specific permission"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(permission_type):
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('serve_index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin or senior leadership access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor']:
            flash('Administrator or Senior Leadership access required.', 'error')
            return redirect(url_for('serve_index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required_json(f):
    """Decorator to require admin access - returns JSON for API endpoints"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor']:
            return jsonify({'error': 'Administrator access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def can_recall_data(campus=None):
    """Check if current user can recall data for specified campus"""
    if not current_user.is_authenticated:
        return False
    return current_user.has_permission('recall_stats', campus)

def can_log_stats():
    """Check if current user can log stats"""
    if not current_user.is_authenticated:
        return False
    return current_user.has_permission('log_stats')

print("[DEBUG] Permission decorators defined")

# Enhanced regex patterns for parsing stats with better context awareness and natural speech support
# Voice recognition optimized patterns with common misheard words and variations
patterns = {
    # Main attendance - much more flexible with voice recognition variations
    "total_attendance": r"(\d+)\s+(?:people|attendance|total|had|got|there were|in attendance|attended|showed up|came|were there|total people|total attendance|people total|attendance total|peep|peeps|person|persons|folks|guys|everyone|everybody|crowd|gathering)",
    
    # New people breakdown - more natural variations with voice recognition
    "first_time_visitors": r"(\d+)\s+(?:first\s+time|first-time|first\s+timers?|new\s+people|newcomers?|ftv|first\s+time\s+visitors?|new\s+visitors?|first\s+time\s+guests?|first\s+time\s+guests?|first\s+time\s+people|new\s+comers?|new\s+comers?|first\s+timers?|first\s+time\s+visitors?)",
    "visitors": r"(\d+)\s+(?:visitors?|guests?|passing\s+through|tourists?|visiting|new\s+visitors?|visiting\s+people|visitors?|guests?|visiting\s+guests?|visiting\s+people)",
    "information_gathered": r"(\d+)\s+(?:info\s+gathered|information\s+gathered|details\s+gathered|details\s+collected|contact\s+info|info|cards\s+back|contact\s+cards|response\s+cards|visitor\s+cards|info\s+cards|information\s+cards|contact\s+information|contact\s+info|info\s+cards|contact\s+cards)",
    
    # Christian decisions breakdown - more natural speech with voice variations
    "first_time_christians": r"(\d+)\s+(?:first\s+time\s+(?:conversions?|decisions?|salvations?)|new\s+(?:conversions?|christians?)|(?:got\s+)?saved|baptisms?|ftc|people\s+got\s+saved|people\s+saved|salvations?|decisions?|conversions?|people\s+made\s+decisions?|people\s+accepted\s+christ|salvations?|decisions?|conversions?|saved|got\s+saved|made\s+decisions?|accepted\s+christ)",
    "rededications": r"(\d+)\s+(?:rededication|re-dedication|recommitment|re-commitment|renewed\s+(?:faith|commitment)|came\s+back|rededicated|re-dedicated|renewed|people\s+rededicated|people\s+renewed|rededications?|re-dedications?|recommitments?|renewed)",
    
    # Youth breakdown - more flexible with voice recognition
    "youth_attendance": r"(\d+)\s+(?:youth(?:\s+attendance|\s+group|\s+ministry)?|teens?|youth\s+people|youth\s+attended|youth\s+came|youth\s+showed\s+up|youth\s+group|youth\s+ministry|teens?|teenagers?|young\s+people)",
    "youth_salvations": r"(\d+)\s+(?:youth\s+(?:salvations?|decisions?|saved)|teen\s+(?:salvations?|decisions?)|youth\s+got\s+saved|youth\s+people\s+saved|youth\s+made\s+decisions?|youth\s+salvations?|youth\s+decisions?|youth\s+saved)",
    "youth_new_people": r"(\d+)\s+(?:youth\s+(?:new\s+people|visitors?|newcomers?)|teen\s+(?:new\s+people|visitors?)|new\s+youth|youth\s+newcomers?|youth\s+visitors?|new\s+youth|youth\s+new\s+people)",
    
    # Kids breakdown - more natural with voice recognition
    "kids_attendance": r"(\d+)\s+(?:kids\s+attendance|children\s+attendance|kids\s+total|kids|children|kids\s+attended|kids\s+came|kids\s+showed\s+up|kids\s+ministry|children\s+ministry|nursery|kid\s+ministry|children\s+attended)",
    "kids_leaders": r"(\d+)\s+(?:kids\s+leaders?|children\s+leaders?|kids\s+helpers?|kids\s+volunteers?|children\s+helpers?|kids\s+team|kids\s+leaders?|children\s+leaders?|kids\s+helpers?)",
    "new_kids": r"(\d+)\s+(?:new\s+kids|new\s+children|kids\s+visitors?|new\s+kids\s+came|new\s+children\s+came|new\s+kids|new\s+children|kids\s+visitors?)",
    "new_kids_salvations": r"(\d+)\s+(?:kids?\s+(?:salvations?|decisions?|saved)|children\s+(?:salvations?|decisions?)|kids\s+got\s+saved|children\s+got\s+saved|kids\s+made\s+decisions?|children\s+made\s+decisions?|kids\s+salvations?|children\s+salvations?)",
    
    # Ministry metrics - more flexible with voice recognition
    "connect_groups": r"(\d+)\s+(?:connect\s+groups?|small\s+groups?|connects?|life\s+groups?|active\s+groups?|people\s+in\s+connect\s+groups?|people\s+joined\s+connect\s+groups?|connect\s+groups?|small\s+groups?|life\s+groups?)",
    "dream_team": r"(\d+)\s+(?:dream\s+team|dt|team\s+members?|serving\s+team|people\s+on\s+dream\s+team|people\s+served|serving\s+people|volunteers?|on\s+dream\s+team|dream\s+team|volunteers?|team\s+members?)",
    
    # Special events - more natural with voice recognition
    "baptisms": r"(\d+)\s+(?:baptisms?|baptized|baptismal|water\s+baptism|people\s+baptized|people\s+got\s+baptized|baptisms?|baptized|baptismal)",
    "child_dedications": r"(\d+)\s+(?:child\s+dedications?|baby\s+dedications?|dedications?|dedicated|people\s+dedicated|children\s+dedicated|child\s+dedications?|baby\s+dedications?|dedications?)",
    
    # Information gathering - more flexible with voice recognition
    "information_gathered": r"(\d+)\s+(?:info\s+gathered|information\s+gathered|details\s+gathered|details\s+collected|contact\s+info|info|cards\s+back|contact\s+cards|response\s+cards|visitor\s+cards|info\s+cards|information\s+cards|contact\s+information|collected|gathered|info\s+gathered|information\s+gathered)",
    
    # Rededications - more flexible with voice recognition
    "rededications": r"(\d+)\s+(?:rededication|re-dedication|recommitment|re-commitment|renewed\s+(?:faith|commitment)|came\s+back|rededicated|re-dedicated|renewed|people\s+rededicated|people\s+renewed|rededications?|re-dedications?|recommitments?)",
    
    # New kids - more flexible with voice recognition
    "new_kids": r"(\d+)\s+(?:new\s+kids|new\s+children|kids\s+visitors?|new\s+kids\s+came|new\s+children\s+came|new\s+kids|new\s+children|kids\s+visitors?)",
    
    # Service time patterns - much more flexible with voice recognition
    "9:00_am": r"(\d+)\s+(?:9\s*am|9\s*:?\s*00\s*am|9\s*o'clock|nine\s*am|nine\s*o'clock|9\s*am\s*service|9\s*:?\s*00\s*service|nine\s*am\s*service|9\s*am|nine\s*am|9\s*o'clock)",
    "10:00_am": r"(\d+)\s+(?:10\s*am|10\s*:?\s*00\s*am|10\s*o'clock|ten\s*am|ten\s*o'clock|10\s*am\s*service|10\s*:?\s*00\s*service|ten\s*am\s*service|10\s*am|ten\s*am|10\s*o'clock)",
    "11:00_am": r"(\d+)\s+(?:11\s*am|11\s*:?\s*00\s*am|11\s*o'clock|eleven\s*am|eleven\s*o'clock|11\s*am\s*service|11\s*:?\s*00\s*service|eleven\s*am\s*service|11\s*am|eleven\s*am|11\s*o'clock)",
    "5:00_pm": r"(\d+)\s+(?:5\s*pm|5\s*:?\s*00\s*pm|5\s*o'clock|five\s*pm|five\s*o'clock|5\s*pm\s*service|5\s*:?\s*00\s*service|five\s*pm\s*service|5\s*pm|five\s*pm|5\s*o'clock)",
    
    # Financial - enhanced for voice recognition
    "tithe": r"(\d+(?:\.\d+)?)\s+(?:tithe|offering|giving|donations?|money|dollars?|bucks?|tithe|offering|giving|donations?|money|dollars?)",
    
    # Backward compatibility patterns with voice recognition
    "new_people": r"(\d+)\s+(?:new(?:\s+(?!time|people))|np)(?!\s+(?:visitors?|guests?))",
    "new_christians": r"(\d+)\s+(?:salvations?|decisions?|nc)(?!\s+(?:rededication|re-dedication))",
    "kids_total": r"(\d+)\s+(?:kids|children|kids\s+ministry|nursery)",
    "volunteers": r"(\d+)\s+(?:volunteers?|team\s+members?|servers?|volunteers?|team\s+members?)"
}

# Campus detection patterns (loaded dynamically)
def get_campus_patterns():
    """Get campus patterns dynamically from configuration"""
    return get_campus_detection_patterns()

def detect_campus(text: str) -> Optional[str]:
    """Detect campus from text using dynamic patterns from configuration with fuzzy matching for voice recognition"""
    text_lower = text.lower()
    
    # Get dynamic campus patterns
    campus_patterns = get_campus_patterns()
    
    # Check each campus pattern with exact matching first
    for campus_id, pattern in campus_patterns.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            return campus_id
    
    # Enhanced fuzzy matching for voice recognition with common misspellings and variations
    fuzzy_campus_patterns = {
        'south': [
            r'\bsouth\b', r'\bsowth\b', r'\bsow\b', r'\bsowf\b', r'\bsowth campus\b',
            r'\bsouth campus\b', r'\bsow campus\b', r'\bsowf campus\b', r'\bsouthside\b',
            r'\bsouth side\b', r'\bsouthern\b', r'\bsouth campus\b', r'\bsouth location\b',
            r'\bsouth church\b', r'\bsouth location\b', r'\bsouth site\b'
        ],
        'salisbury': [
            r'\bsalisbury\b', r'\bsalsbury\b', r'\bsalsbery\b', r'\bsalisbery\b',
            r'\bsalisbury campus\b', r'\bsalsbury campus\b', r'\bsalsbery campus\b',
            r'\bsalisbery campus\b', r'\bsalisbury location\b', r'\bsalisbury church\b',
            r'\bsalisbury site\b', r'\bsalsbury location\b', r'\bsalsbury church\b'
        ],
        'paradise': [
            r'\bparadise\b', r'\bparadice\b', r'\bparidise\b', r'\bparidice\b',
            r'\bparadise campus\b', r'\bparadice campus\b', r'\bparidise campus\b',
            r'\bparidice campus\b', r'\bparadise location\b', r'\bparadise church\b',
            r'\bparadise site\b', r'\bparadice location\b', r'\bparadice church\b'
        ],
        'adelaide_city': [
            r'\badelaide\b', r'\badelaide city\b', r'\badelaide city campus\b',
            r'\badelaide campus\b', r'\badelaide city campus\b', r'\badelaide location\b',
            r'\badelaide church\b', r'\badelaide site\b', r'\badelaide city location\b',
            r'\badelaide city church\b', r'\badelaide city site\b'
        ]
    }
    
    # Check fuzzy patterns for each campus
    for campus_id, patterns in fuzzy_campus_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.info(f"Fuzzy campus match: '{text}' -> {campus_id}")
                # Map campus IDs to actual Google Sheets campus names
                campus_mapping = {
                    'south': 'South',
                    'salisbury': 'Salisbury', 
                    'paradise': 'Paradise',
                    'adelaide_city': 'Adelaide City'
                }
                return campus_mapping.get(campus_id, campus_id)
    
    # Check for partial matches (for voice recognition errors)
    partial_matches = {
        'south': ['sow', 'sowth', 'sowf', 'south'],
        'salisbury': ['sals', 'salis', 'salsbury', 'salisbury'],
        'paradise': ['parad', 'paradis', 'paradice'],
        'adelaide_city': ['adela', 'adelaide']
    }
    
    for campus_id, partials in partial_matches.items():
        for partial in partials:
            if partial in text_lower:
                logger.info(f"Partial campus match: '{text}' -> {campus_id}")
                # Map campus IDs to actual Google Sheets campus names
                campus_mapping = {
                    'south': 'South',
                    'salisbury': 'Salisbury', 
                    'paradise': 'Paradise',
                    'adelaide_city': 'Adelaide City'
                }
                return campus_mapping.get(campus_id, campus_id)
    
    # If no specific campus is mentioned, check if this looks like a church-wide stat query
    church_wide_indicators = [
        'how many', 'what is', "what's", 'give me', 'tell me', 'what was', 'how much',
        'total', 'average', 'church', 'this weekend', 'this week', 'this month', 'this year',
        'all campuses', 'church wide', 'across all', 'every campus', 'all locations'
    ]
    
    has_church_wide_query = any(indicator in text_lower for indicator in church_wide_indicators)
    
    if has_church_wide_query:
        return "all_campuses"
    
    # If no campus mentioned but contains numbers (likely stat logging), 
    # we'll need to handle this in the calling function
    return None

def get_all_campuses_data(rows: list, start_date: datetime, end_date: datetime) -> list:
    """Get data from all campuses within the date range"""
    all_campus_data = []
    
    for row in rows:
        try:
            timestamp_str = row.get("Timestamp", "")
            if timestamp_str:
                # Handle different timestamp formats
                if "T" in timestamp_str:
                    row_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    row_date = parse_any_date(timestamp_str)
                # Check if row date is within the specified range
                if start_date <= row_date <= end_date:
                    all_campus_data.append(row)
            else:
                # If no timestamp, include the row (fallback)
                all_campus_data.append(row)
        except Exception as e:
            logger.warning(f"Could not parse timestamp for row: {e}")
            all_campus_data.append(row)
    
    return all_campus_data

def generate_cross_campus_insights(question: str, analysis_data: dict, filtered_rows: list) -> str:
    """Generate intelligent AI insights for cross-campus data"""
    if not claude:
        return "I'd be happy to analyze your church-wide data, but I need to connect to my AI assistant first."
    
    # Prepare data summary for Claude
    data_summary = f"""
Here's what I found for Futures Church ({analysis_data.get('date_range', 'recent data')}):

Church-wide numbers:
- {analysis_data.get('total_attendance', 0):,} total attendance
- {analysis_data.get('total_new_people', 0):,} new people
- {analysis_data.get('total_new_christians', 0):,} new christians
- {analysis_data.get('total_youth', 0):,} youth
- {analysis_data.get('total_kids', 0):,} kids
- {analysis_data.get('total_connect_groups', 0):,} connect groups

Weekly averages across all campuses:
- {analysis_data.get('averages', {}).get('attendance', 0):.1f} people per week
- {analysis_data.get('averages', {}).get('new_people', 0):.1f} new people per week
- {analysis_data.get('averages', {}).get('new_christians', 0):.1f} new christians per week
- {analysis_data.get('averages', {}).get('youth', 0):.1f} youth per week
- {analysis_data.get('averages', {}).get('kids', 0):.1f} kids per week
- {analysis_data.get('averages', {}).get('connect_groups', 0):.1f} connect groups per week
"""

    # Add recent data points for trend analysis
    if filtered_rows:
        recent_data = "Recent weeks across all campuses:\n"
        for i, row in enumerate(filtered_rows[-5:], 1):  # Last 5 entries
            if isinstance(row, dict):
                date = row.get('Date', row.get('Timestamp', 'Unknown'))
                campus = row.get('Campus', 'Unknown')
                attendance = row.get('Total Attendance', 0)
                new_people = row.get('New People', 0)
                new_christians = row.get('New Christians', 0)
                recent_data += f"{i}. {date} ({campus}): {attendance} people, {new_people} new, {new_christians} christians\n"
        data_summary += f"\n{recent_data}"

    # Create intelligent prompt for cross-campus analysis
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['trend', 'trends', 'pattern', 'growth', 'improve', 'attention', 'working']):
        prompt = f"""You're a friendly church growth expert. A leader from Futures Church is asking: "{question}"

{data_summary}

Give them warm, encouraging insights about their church-wide data. Focus on:
- What trends you see across all their campuses
- How the whole church is performing
- What areas are doing well or need attention across campuses
- Simple suggestions that could help the entire church

Be conversational and encouraging. Use their data to back up your insights. Keep it under 120 words and make it feel like a friendly conversation about their whole church."""
    
    elif any(word in question_lower for word in ['compare', 'vs', 'versus', 'against', 'difference']):
        prompt = f"""You're a helpful church data friend. A leader from Futures Church is asking: "{question}"

{data_summary}

Give them friendly analysis of their church-wide data. Focus on:
- How their overall numbers stack up
- What patterns you notice across campuses
- What the data tells us about their church-wide progress
- What might be influencing their results

Be encouraging and use their specific numbers. Keep it under 120 words and sound like you're chatting about their whole church."""
    
    else:
        prompt = f"""You're a helpful church assistant. A leader from Futures Church is asking: "{question}"

{data_summary}

Give them friendly, helpful insights about their church-wide data. Focus on:
- What they're really asking about
- What their church-wide data shows
- How this info can help their whole church
- What positive things you notice across all campuses

Be warm and specific. Use their data to give meaningful insights about Futures Church as a whole. Keep it under 120 words and sound conversational."""

    try:
        response = claude.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.content[0].text.strip() if hasattr(response.content[0], 'text') else str(response.content[0])
        return response_text
        
    except Exception as e:
        logger.error(f"Claude API error in generate_cross_campus_insights: {e}")
        return f"I'd be happy to analyze your church-wide data for Futures Church, but I'm having trouble connecting to my AI assistant right now. The data shows {analysis_data.get('total_attendance', 0)} total attendance across all campuses with an average of {analysis_data.get('averages', {}).get('attendance', 0):.1f} people per week."

def preprocess_voice_text(text: str) -> str:
    """Preprocess voice input text to improve recognition accuracy with enhanced noise handling"""
    # Convert to lowercase for consistent processing
    text = text.lower()
    
    # Enhanced voice recognition corrections with more comprehensive patterns
    voice_corrections = {
        # Numbers and common misheard words - expanded for better recognition
        'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
        'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
        'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14',
        'fifteen': '15', 'sixteen': '16', 'seventeen': '17', 'eighteen': '18',
        'nineteen': '19', 'twenty': '20', 'thirty': '30', 'forty': '40',
        'fifty': '50', 'sixty': '60', 'seventy': '70', 'eighty': '80',
        'ninety': '90', 'hundred': '100', 'thousand': '1000',
        
        # Common voice recognition errors - expanded list
        'peep': 'people', 'peeps': 'people', 'peeple': 'people', 'peepul': 'people',
        'peeple': 'people', 'peepul': 'people', 'peeple': 'people',
        'salvations': 'salvations', 'salvation': 'salvations', 'salvashuns': 'salvations',
        'decisions': 'decisions', 'decision': 'decisions', 'decishuns': 'decisions',
        'conversions': 'conversions', 'conversion': 'conversions', 'convershuns': 'conversions',
        'visitors': 'visitors', 'visitor': 'visitors', 'vizitors': 'visitors',
        'guests': 'guests', 'guest': 'guests', 'gests': 'guests',
        'kids': 'kids', 'kid': 'kids', 'kidds': 'kids',
        'children': 'children', 'child': 'children', 'chilldren': 'children',
        'youth': 'youth', 'teens': 'youth', 'teenagers': 'youth', 'yoot': 'youth',
        'volunteers': 'volunteers', 'volunteer': 'volunteers', 'voluntears': 'volunteers',
        'team members': 'volunteers', 'team member': 'volunteers', 'team membrs': 'volunteers',
        'dream team': 'dream team', 'dream team members': 'dream team', 'dream tem': 'dream team',
        
        # Campus name corrections - expanded for better recognition
        'sowth': 'south', 'sow': 'south', 'sowf': 'south', 'sowth': 'south',
        'salsbury': 'salisbury', 'salsbery': 'salisbury', 'salisbery': 'salisbury',
        'salsberry': 'salisbury', 'salisberry': 'salisbury', 'salsbery': 'salisbury',
        'paradice': 'paradise', 'paridise': 'paradise', 'paridice': 'paradise',
        'paradice': 'paradise', 'paridise': 'paradise', 'paridice': 'paradise',
        'adelaide city': 'adelaide city', 'adelaide': 'adelaide city', 'adelaid': 'adelaide city',
        
        # Query-specific corrections
        'how many': 'how many', 'how much': 'how much', 'what is': 'what is',
        'what was': 'what was', "what's": "what's", 'tell me': 'tell me',
        'give me': 'give me', 'show me': 'show me', 'can you': 'can you',
        'could you': 'could you', 'would you': 'would you',
        
        # Time-related corrections
        'last week': 'last week', 'this week': 'this week', 'last month': 'last month',
        'this month': 'this month', 'last year': 'last year', 'this year': 'this year',
        'quarter': 'quarter', 'q1': 'q1', 'q2': 'q2', 'q3': 'q3', 'q4': 'q4',
        
        # Stat-related corrections
        'attendance': 'attendance', 'attendence': 'attendance', 'attendence': 'attendance',
        'new people': 'new people', 'newpeeple': 'new people', 'newpeeple': 'new people',
        'first time': 'first time', 'firsttime': 'first time', 'firsttime': 'first time',
        'connect groups': 'connect groups', 'connectgroups': 'connect groups',
        'dream team': 'dream team', 'dreamteam': 'dream team', 'dreamtem': 'dream team',
        
        # Common speech patterns
        'um': '', 'uh': '', 'ah': '', 'er': '', 'like': '', 'you know': '',
        'i mean': '', 'sort of': '', 'kind of': '', 'basically': '', 'actually': '',
        
        # Filler words and hesitations
        'well': '', 'so': '', 'and': '', 'but': '', 'or': '', 'then': '',
        'now': '', 'here': '', 'there': '', 'this': '', 'that': '',
        
        # Common speech disfluencies
        'i think': '', 'i guess': '', 'i mean': '', 'you know': '', 'right': '',
        'okay': '', 'ok': '', 'yeah': '', 'yes': '', 'no': '', 'not': '',
        
        # Numbers in words to digits
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
        'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
        'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
        'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
        'eighty': '80', 'ninety': '90', 'hundred': '100', 'thousand': '1000'
    }
    
    # Apply corrections with word boundary matching for better accuracy
    for wrong, correct in voice_corrections.items():
        # Use word boundary matching to avoid partial word replacements
        pattern = r'\b' + re.escape(wrong) + r'\b'
        text = re.sub(pattern, correct, text, flags=re.IGNORECASE)
    
    # Clean up extra spaces and punctuation more aggressively
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
    text = re.sub(r'[^\w\s\d]', ' ', text)  # Remove punctuation but keep spaces
    text = re.sub(r'\s+', ' ', text)  # Clean up spaces again after punctuation removal
    text = text.strip()
    
    # Remove common speech artifacts
    text = re.sub(r'\b(um|uh|ah|er|like|you know|i mean|sort of|kind of|basically|actually)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)  # Clean up spaces again
    text = text.strip()
    
    # Normalize common phrases
    text = re.sub(r'\b(how many|how much)\b', 'how many', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(what is|what was|whats)\b', 'what is', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(tell me|give me|show me)\b', 'tell me', text, flags=re.IGNORECASE)
    
    # Final cleanup
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def extract_stats_with_context(text: str, campus: str) -> Dict[str, Any]:
    """Extract stats with enhanced context awareness and natural speech support"""
    # Preprocess voice input for better recognition
    processed_text = preprocess_voice_text(text)
    
    result = {
        "Campus": campus,
        "Timestamp": datetime.now(timezone.utc).isoformat(),
        "Raw_Text": text,
        "Processed_Text": processed_text
    }
    
    # Enhanced stat extraction with better context awareness
    # Use processed text for better voice recognition
    search_text = processed_text if processed_text else text
    
    for key, pattern in patterns.items():
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            # Convert to string for Google Sheets compatibility
            stat_name = key.replace("_", " ").title()
            
            # Handle special mappings for Google Sheets headers
            header_mapping = {
                "Total Attendance": "Total Attendance",
                "First Time Visitors": "First Time Visitors", 
                "Visitors": "Visitors",
                "Cards Back": "Cards Back",
                "First Time Christians": "First Time Christians",
                "Rededications": "Rededications",
                "Salvation Cards Returned": "Salvation Cards Returned",
                "Youth Attendance": "Youth Attendance",
                "Youth Salvations": "Youth Salvations", 
                "Youth New People": "Youth New People",
                "Kids Attendance": "Kids Attendance",
                "Kids Leaders": "Kids Leaders",
                "New Kids": "New Kids",
                "New Kids Salvations": "New Kids Salvations",
                "Connect Groups": "Connect Groups",
                "Dream Team": "Dream Team",
                "Baptisms": "Baptisms",
                "Child Dedications": "Child Dedications",
                "Tithe": "Tithe",
                # Service time mappings
                "9:00 Am": "9:00 AM",
                "10:00 Am": "10:00 AM", 
                "11:00 Am": "11:00 AM",
                "5:00 Pm": "5:00 PM"
            }
            
            final_stat_name = header_mapping.get(stat_name, stat_name)
            result[final_stat_name] = str(match.group(1))
            logger.info(f"Extracted {final_stat_name}: {match.group(1)}")
    
    return result

def extract_stats_with_smart_campus(text: str, default_campus: str = None) -> Dict[str, Any]:
    """Extract stats with smart campus detection - if no campus mentioned, use default or prompt"""
    # First try to detect campus from text
    detected_campus = detect_campus(text)
    
    if detected_campus:
        # Campus was mentioned in the text
        return extract_stats_with_context(text, detected_campus)
    else:
        # No campus mentioned - check if this looks like stat logging
        stat_patterns = [
            r'\d+\s+(?:people|attendance|total|had|got|there were)',
            r'\d+\s+(?:first\s+time|first-time|first\s+timers?|new\s+people|newcomers?)',
            r'\d+\s+(?:visitors?|guests?)',
            r'\d+\s+(?:salvations?|decisions?|got\s+saved|conversions?)',
            r'\d+\s+(?:youth|teens?)',
            r'\d+\s+(?:kids|children)',
            r'\d+\s+(?:connect\s+groups?|small\s+groups?)',
            r'\d+\s+(?:dream\s+team|volunteers?|team\s+members?)'
        ]
        
        has_stats = any(re.search(pattern, text.lower()) for pattern in stat_patterns)
        
        if has_stats:
            # This looks like stat logging but no campus mentioned
            if default_campus:
                logger.info(f"No campus mentioned but stats detected - using default campus: {default_campus}")
                return extract_stats_with_context(text, default_campus)
            else:
                # Return stats with a placeholder campus that will prompt user
                stats = extract_stats_with_context(text, "PENDING_CAMPUS")
                stats["requires_campus_selection"] = True
                return stats
        else:
            # No stats detected - return empty result
            return {
                "Campus": None,
                "Timestamp": datetime.now(timezone.utc).isoformat(),
                "Raw_Text": text,
                "requires_campus_selection": False
            }

def generate_encouragement_with_memory(text: str, campus: str, memory: Dict[str, Any]) -> List[str]:
    """Generate conversational responses using Claude with conversation memory"""
    if not claude:
        return ["Thanks for inputting those stats!", "Keep up the great work!"]
    
    # Build context from memory with better formatting
    campus_history = memory.get(campus, [])
    recent_stats = campus_history[-3:] if campus_history else []
    
    context = ""
    if recent_stats:
        context = f"\n\nRecent stats from {campus} campus:\n"
        for i, stat in enumerate(recent_stats, 1):
            raw_text = stat.get('Raw_Text', '')
            timestamp = stat.get('Timestamp', '')
            if timestamp:
                # Extract just the date part
                try:
                    date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%B %d")
                except:
                    date_str = "recently"
            else:
                date_str = "recently"
            context += f"{i}. {date_str}: {raw_text}\n"
    
    # Check if this contains actual numbers (indicating stat logging)
    text_lower = text.lower()
    contains_numbers = any(char.isdigit() for char in text)
    
    # Check for explicit query indicators
    is_query = any(word in text_lower for word in [
        'how many', 'what is', 'what was', 'what were', 'average', 'last week', 'this week', 'total', 'count', 'query', 'data', 'has had', 'had this year', 'had this month',
        'compare', 'comparison', 'vs', 'versus', 'between', 'year over year',
        'review', 'annual review', 'mid year review', 'mid-year review', 'report', 'summary', 'dashboard', 'snapshot', 'full report', 'overview', 'recap', 'stats summary', 'stat summary', 'stat report', 'stat overview', 'stat recap',
        'annual', 'mid year', 'mid-year', 'midyear'
    ]) or any(word in text_lower for word in ['q1', 'q2', 'q3', 'q4', 'quarter 1', 'quarter 2', 'quarter 3', 'quarter 4', 'first quarter', 'second quarter', 'third quarter', 'fourth quarter'])
    
    # Check if this is a request to log stats (no numbers yet)
    is_request = not contains_numbers and any(word in text_lower for word in ['log', 'record', 'enter', 'add', 'can i log', 'want to log', 'help me log', 'can we log'])
    
    # If it has numbers and is not explicitly a query, treat as stat logging
    is_stat_logging = contains_numbers and not is_query
    
    if is_query:
        prompt = f"""You are a helpful church AI assistant. A leader from the {campus} campus is asking for data:
"{text}"

{context}

Respond naturally as a helpful assistant. Tell them you'll look up that information for them right away! Be conversational and friendly. Keep it under 15 words. Examples:
- "I'll look that up for you right away!"
- "Let me check the data for {campus} campus."
- "I'll find that information for you."""
    elif is_request:
        prompt = f"""You are a friendly, helpful church AI assistant. A leader from the {campus} campus is asking:
"{text}"

{context}

Respond naturally as a helpful assistant. If they want to log stats, guide them conversationally. Be encouraging and friendly. Keep it under 20 words. 

Guide them to log new stats. Examples:
- "Perfect! I'm ready to record today's stats for {campus} campus. What were your numbers?"
- "Great! Let's log today's stats for {campus} campus. How many people attended?"
- "Absolutely! I'm here to help log stats for {campus} campus. What numbers do you have?"
- "Ready to log stats for {campus} campus! What numbers do you have today?"""
    elif is_stat_logging:
        # For actual stat logging with numbers, give confirmation responses
        return ["Thanks for inputting those stats for " + campus + " campus!", "Great numbers this week!"]
    else:
        prompt = f"""You are a church insights assistant. A leader from the {campus} campus submitted:
"{text}"

{context}

Generate EXACTLY 2 short insights (max 12 words each). Focus on different trends, patterns, or observations. Be encouraging but factual. Format as:
1. [First insight]
2. [Second insight]"""

    try:
        response = claude.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=80,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.content[0].text.strip() if hasattr(response.content[0], 'text') else str(response.content[0])
        
        if is_request:
            # For requests, return a single helpful response
            return [response_text]
        else:
            # Parse the response to extract exactly 2 insights
            lines = response_text.split('\n')
            insights = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('1.') and not line.startswith('2.'):
                    insights.append(line)
            
            # Ensure we have exactly 2 insights
            if len(insights) >= 2:
                return insights[:2]
            elif len(insights) == 1:
                return [insights[0], "Great progress this week!"]
            else:
                return ["Thanks for inputting those stats!", "Keep up the great work!"]
            
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        if is_request:
            return [f"Sure! I'd love to help input stats for {campus} campus. Just tell me the numbers!", "What were your attendance numbers today?"]
        else:
            return ["Thanks for inputting those stats!", "Keep up the great work!"]

def generate_audio_with_elevenlabs(text: str, filename: Optional[str] = None, voice_id: Optional[str] = None) -> Optional[str]:
    """Generate audio using ElevenLabs API with enhanced voice options and error handling"""
    if not elevenlabs_api_key:
        logger.warning("ElevenLabs API key not configured")
        return None
    
    try:
        # Use provided voice_id or default
        target_voice_id = voice_id or elevenlabs_voice_id
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{target_voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": elevenlabs_api_key
        }
        
        # Enhanced voice settings for better quality
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.6,  # Increased for more consistent voice
                "similarity_boost": 0.7,  # Increased for better voice quality
                "style": 0.3,  # Add some style variation
                "use_speaker_boost": True  # Enhance speaker clarity
            }
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Ensure temp_audio directory exists in backend folder
            temp_audio_dir = os.path.join(os.path.dirname(__file__), "temp_audio")
            os.makedirs(temp_audio_dir, exist_ok=True)
            
            if filename:
                # If filename provided, use it as-is
                audio_filename = filename  
                full_path = audio_filename
            else:
                # Generate filename with timestamp and voice info
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                voice_suffix = f"_v{target_voice_id}" if voice_id else ""
                audio_filename = f"response_{timestamp}{voice_suffix}.mp3"
                full_path = os.path.join(temp_audio_dir, audio_filename)
            
            with open(full_path, "wb") as f:
                f.write(response.content)
            logger.info(f"Generated audio file: {full_path} (voice: {target_voice_id})")
            
            # Return URL path for the audio file
            return f"/temp_audio/{audio_filename}"
        else:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        logger.error("ElevenLabs API request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"ElevenLabs API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to generate audio with ElevenLabs: {e}")
        return None

def detect_missing_stats(text: str, campus: str) -> List[str]:
    """Detect what stats might be missing and suggest follow-up questions"""
    extracted = extract_stats_with_context(text, campus)
    missing = []
    
    # Check for common missing stats
    if not any(key in extracted for key in ["Total Attendance", "Total attendance"]):
        missing.append("How many people attended today?")
    
    if not any(key in extracted for key in ["New People", "New people"]):
        missing.append("Were there any new visitors today?")
    
    if not any(key in extracted for key in ["Kids Total", "Kids total"]):
        missing.append("How many kids were in children's ministry?")
    
    if not any(key in extracted for key in ["Youth Attendance", "Youth attendance"]):
        missing.append("How many youth attended?")
    
    return missing

def parse_date_range(question: str) -> tuple:
    """Parse date range from question text"""
    question_lower = question.lower()
    current_year = datetime.now().year
    
    # Extract year from question (look for 4-digit years like 2024, 2023, etc.)
    import re
    year_match = re.search(r'\b(20\d{2})\b', question)
    target_year = int(year_match.group(1)) if year_match else current_year
    
    # YTD (Year to Date) detection
    if any(phrase in question_lower for phrase in ['ytd', 'year to date', 'this year', 'so far this year']):
        start_date = datetime(target_year, 1, 1)
        end_date = datetime.now() if target_year == current_year else datetime(target_year, 12, 31)
        logger.info(f"[QUERY] YTD detected: {start_date} to {end_date}")
        return start_date, end_date, f"year to date ({target_year})"
    
    # Month range detection
    months = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
        'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    
    # Look for "from X to Y" or "X to Y" patterns
    for month_name, month_num in months.items():
        if month_name in question_lower:
            # Check for "from X to Y" pattern
            if f"from {month_name}" in question_lower:
                for end_month_name, end_month_num in months.items():
                    if f"to {end_month_name}" in question_lower:
                        start_date = datetime(target_year, month_num, 1)
                        if end_month_num == 12:
                            end_date = datetime(target_year, end_month_num, 31)
                        else:
                            end_date = datetime(target_year, end_month_num + 1, 1) - timedelta(days=1)
                        return start_date, end_date, f"{month_name.title()} to {end_month_name.title()} {target_year}"
            
            # Check for "X to Y" pattern (without "from")
            for end_month_name, end_month_num in months.items():
                if f"{month_name} to {end_month_name}" in question_lower:
                    start_date = datetime(target_year, month_num, 1)
                    if end_month_num == 12:
                        end_date = datetime(target_year, end_month_num, 31)
                    else:
                        end_date = datetime(target_year, end_month_num + 1, 1) - timedelta(days=1)
                    return start_date, end_date, f"{month_name.title()} to {end_month_name.title()} {target_year}"
    
    # Single month detection
    for month_name, month_num in months.items():
        if month_name in question_lower:
            start_date = datetime(target_year, month_num, 1)
            if month_num == 12:
                end_date = datetime(target_year, month_num, 31)
            else:
                end_date = datetime(target_year, month_num + 1, 1) - timedelta(days=1)
            return start_date, end_date, f"{month_name.title()} {target_year}"
    
    # No date range found - default to recent data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Default to last 30 days
    return start_date, end_date, "recent data"

def detect_comparison_request(question: str) -> tuple:
    """Detect if this is a comparison request and extract years/periods to compare"""
    question_lower = question.lower()
    current_year = datetime.now().year
    import re
    
    # Look for comparison keywords - more precise list
    comparison_keywords = [
        'compare', 'comparison', 'vs', 'versus', 'against', 'side by side', 'year over year',
        'between', 'difference', 'compared to', 'compared with', 'relative to',
        'q1 vs', 'q2 vs', 'q3 vs', 'q4 vs', 'quarter 1 vs', 'quarter 2 vs', 'quarter 3 vs', 'quarter 4 vs',
        'first quarter vs', 'second quarter vs', 'third quarter vs', 'fourth quarter vs',
        'mid-year vs', 'mid year vs', 'midyear vs', 'year to year',
        'growth', 'trend', 'improvement', 'decline', 'increase', 'decrease', 'change',
        'how are we doing', 'how did we do', 'performance', 'results'
    ]
    
    # Check for explicit comparison indicators
    explicit_comparison_indicators = [
        'compare', 'comparison', 'vs', 'versus', 'against', 'side by side', 'year over year',
        'between', 'difference', 'compared to', 'compared with', 'relative to',
        'year to year', 'growth', 'trend', 'improvement', 'decline', 'increase', 'decrease', 'change'
    ]
    
    # Check for specific comparison patterns
    has_explicit_comparison = any(indicator in question_lower for indicator in explicit_comparison_indicators)
    
    # Check for YTD (Year to Date) comparison
    ytd_keywords = ['ytd', 'year to date', 'so far this year', 'this year to date']
    has_ytd_keyword = any(keyword in question_lower for keyword in ytd_keywords)
    
    # Check for "this year" which should NOT be a comparison, UNLESS it's explicitly a comparison
    if ('this year' in question_lower or 'current year' in question_lower) and not any(word in question_lower for word in ['compare', 'comparison', 'vs', 'versus', 'against', 'compared to', 'compared with', 'ytd', 'year to date']):
        return False, [], None, None
    
    # Check for "annual" or "yearly" only if they appear with comparison context
    annual_keywords = ['annual', 'yearly']
    has_annual_keyword = any(keyword in question_lower for keyword in annual_keywords)
    
    # Only treat as comparison if there's explicit comparison language OR annual/yearly with comparison context OR YTD comparison
    is_comparison = has_explicit_comparison or (has_annual_keyword and any(word in question_lower for word in ['compare', 'comparison', 'vs', 'versus', 'against', 'between', 'difference'])) or has_ytd_keyword
    logger.info(f"[COMPARE DEBUG] Question: '{question}' -> Lower: '{question_lower}'")
    logger.info(f"[COMPARE DEBUG] Comparison keywords found: {[kw for kw in comparison_keywords if kw in question_lower]}")
    logger.info(f"[COMPARE DEBUG] Is comparison: {is_comparison}")
    if not is_comparison:
        return False, [], None, None
    
    # Detect mid-year comparison
    if 'mid-year' in question_lower or 'mid year' in question_lower or 'midyear' in question_lower:
        years = re.findall(r'\b(20\d{2})\b', question)
        if len(years) >= 2:
            return True, [int(years[0]), int(years[1])], 'mid_year', None
        elif len(years) == 1:
            y = int(years[0])
            return True, [y-1, y], 'mid_year', None
        else:
            return True, [current_year-1, current_year], 'mid_year', None

    # Detect quarterly comparison (Q1, Q2, Q3, Q4) - improved detection
    quarter = None
    quarter_patterns = [
        (r'\bq1\b', 1), (r'\bq2\b', 2), (r'\bq3\b', 3), (r'\bq4\b', 4),
        (r'\bquarter 1\b', 1), (r'\bquarter 2\b', 2), (r'\bquarter 3\b', 3), (r'\bquarter 4\b', 4),
        (r'\bfirst quarter\b', 1), (r'\bsecond quarter\b', 2), (r'\bthird quarter\b', 3), (r'\bfourth quarter\b', 4)
    ]
    
    for pattern, q in quarter_patterns:
        if re.search(pattern, question_lower):
            quarter = q
            break
    
    if quarter:
        years = re.findall(r'\b(20\d{2})\b', question)
        if len(years) >= 2:
            return True, [int(years[0]), int(years[1])], 'quarterly', quarter
        elif len(years) == 1:
            y = int(years[0])
            return True, [y-1, y], 'quarterly', quarter
        else:
            return True, [current_year-1, current_year], 'quarterly', quarter

    # Detect monthly comparison
    months = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
        'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    
    # Check for monthly comparison patterns like "march vs april" or "monthly comparison"
    monthly_indicators = ['monthly comparison', 'monthly vs', 'month vs', 'month comparison']
    has_monthly_indicator = any(indicator in question_lower for indicator in monthly_indicators)
    
    # Also check for month names in comparison
    mentioned_months = []
    for month_name, month_num in months.items():
        if month_name in question_lower:
            mentioned_months.append(month_num)
    
    if has_monthly_indicator or len(mentioned_months) >= 1:
        # If we found month names, use the first one; otherwise use current month
        month = mentioned_months[0] if mentioned_months else datetime.now().month
        
        years = re.findall(r'\b(20\d{2})\b', question)
        if len(years) >= 2:
            return True, [int(years[0]), int(years[1])], 'monthly', month
        elif len(years) == 1:
            y = int(years[0])
            return True, [y-1, y], 'monthly', month
        else:
            return True, [current_year-1, current_year], 'monthly', month

    # Detect YTD comparison
    if has_ytd_keyword:
        years = re.findall(r'\b(20\d{2})\b', question)
        if len(years) >= 2:
            logger.info(f"[COMPARE DEBUG] YTD comparison detected with years: {years}")
            return True, [int(year) for year in years], 'ytd', None
        elif len(years) == 1:
            y = int(years[0])
            logger.info(f"[COMPARE DEBUG] YTD comparison detected with single year: {y}, comparing with {y-1}")
            return True, [y-1, y], 'ytd', None
        else:
            logger.info(f"[COMPARE DEBUG] YTD comparison detected with no years, using {current_year-1} and {current_year}")
            return True, [current_year-1, current_year], 'ytd', None

    # Default: annual comparison
    years = re.findall(r'\b(20\d{2})\b', question)
    if len(years) >= 2:
        return True, [int(year) for year in years], 'annual', None
    elif len(years) == 1:
        y = int(years[0])
        return True, [y-1, y], 'annual', None
    else:
        return True, [current_year-1, current_year], 'annual', None

def detect_cross_location_comparison(question: str) -> tuple:
    """Detect if this is a cross-location comparison request and extract campuses to compare"""
    question_lower = question.lower()
    
    # Check if user has permission for cross-location comparison
    if not hasattr(current_user, 'is_authenticated') or not current_user or not current_user.is_authenticated or not current_user.has_permission('cross_location_comparison'):
        return False, [], None, None
    
    # Look for cross-location comparison keywords
    cross_location_keywords = [
        'compare', 'vs', 'versus', 'against', 'between', 'difference',
        'south vs', 'barker vs', 'paradise vs', 'adelaide vs', 'salisbury vs',
        'south compared to', 'barker compared to', 'paradise compared to', 'adelaide compared to', 'salisbury compared to',
        'how many', 'did south have', 'did barker have', 'did paradise have', 'did adelaide have', 'did salisbury have',
        'south and', 'barker and', 'paradise and', 'adelaide and', 'salisbury and'
    ]
    
    # Check for explicit cross-location comparison indicators
    has_cross_location_indicator = any(indicator in question_lower for indicator in cross_location_keywords)
    
    if not has_cross_location_indicator:
        return False, [], None, None
    
    # Get all available campuses
    available_campuses = get_campuses_for_user()
    campus_names = [campus['id'] for campus in available_campuses.get('campuses', []) if campus['id'] != 'all_campuses']
    
    # Get campus detection patterns for better matching
    campus_patterns = get_campus_detection_patterns()
    
    # Detect mentioned campuses in the question
    mentioned_campuses = []
    for campus_id in campus_names:
        # Check if campus name appears in question
        if campus_id.lower() in question_lower:
            mentioned_campuses.append(campus_id)
        else:
            # Check campus detection patterns
            if campus_id in campus_patterns:
                pattern = campus_patterns[campus_id]
                if re.search(pattern, question_lower, re.IGNORECASE):
                    mentioned_campuses.append(campus_id)
    
    # Also check for common campus name variations
    campus_variations = {
        'mount_barker': ['barker', 'mt barker', 'mount barker'],
        'south': ['south'],
        'paradise': ['paradise'],
        'adelaide_city': ['adelaide', 'city', 'cbd'],
        'salisbury': ['salisbury']
    }
    
    for campus_id, variations in campus_variations.items():
        if campus_id in campus_names:  # Only check if campus is available to user
            for variation in variations:
                if variation.lower() in question_lower and campus_id not in mentioned_campuses:
                    mentioned_campuses.append(campus_id)
                    break
    
    # If no specific campuses mentioned, return False
    if len(mentioned_campuses) < 2:
        return False, [], None, None
    
    # Detect time period
    current_year = datetime.now().year
    years = re.findall(r'\b(20\d{2})\b', question)
    year = int(years[0]) if years else current_year
    
    # Detect specific stat being compared
    specific_stat = detect_specific_stat_in_comparison(question)
    
    logger.info(f"[CROSS_LOCATION] Detected cross-location comparison: campuses={mentioned_campuses}, year={year}, stat={specific_stat}")
    
    return True, mentioned_campuses, year, specific_stat

def handle_cross_location_comparison(question: str, campuses: list, year: int, specific_stat: str = None) -> dict:
    """Handle cross-location comparison requests between multiple campuses"""
    logger.info(f"[CROSS_LOCATION] handle_cross_location_comparison called with: question={question}, campuses={campuses}, year={year}, specific_stat={specific_stat}")
    
    try:
        # Get data for each campus
        campus_reports = []
        for campus in campuses:
            # Get data for the specific year
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            
            # Get rows data
            rows = []
            if sheet:
                try:
                    rows = safe_sheets_request(sheet.get_all_records)
                except Exception as e:
                    logger.error(f"Failed to get stats from Google Sheets: {e}")
                    rows = []
            
            # Filter rows for this campus and year
            filtered_rows = []
            campus_normalized = normalize_campus(campus)
            
            for row in rows:
                try:
                    if isinstance(row, dict):
                        row_campus = normalize_campus(row.get('Campus', ''))
                        if (row_campus == campus_normalized or 
                            campus_normalized in row_campus or 
                            row_campus in campus_normalized):
                            
                            row_date = get_row_timestamp(row)
                            if row_date != datetime.min and start_date <= row_date <= end_date:
                                filtered_rows.append(row)
                except Exception as e:
                    logger.warning(f"Could not process row: {e}")
                    continue
            
            # Calculate stats for this campus
            if filtered_rows:
                analysis_data = calculate_stats_from_filtered_rows(filtered_rows)
                
                # Create report for this campus
                campus_report = {
                    "campus": display_campus_name(campus),
                    "year": year,
                    "stats": analysis_data,
                    "entry_count": len(filtered_rows)
                }
                campus_reports.append(campus_report)
                
                # Debug logging
                logger.info(f"[CROSS_LOCATION] Campus {campus}: {len(filtered_rows)} rows, new_people={analysis_data.get('total_new_people', 0)}, new_christians={analysis_data.get('total_new_christians', 0)}")
            else:
                logger.warning(f"[CROSS_LOCATION] No data found for campus {campus} in year {year}")
        
        if not campus_reports:
            return {
                "error": "No data found for the specified campuses and year",
                "text": f"Sorry, I couldn't find data for {', '.join([display_campus_name(c) for c in campuses])} in {year}.",
                "popup": True
            }
        
        # Create comparison table
        comparison_data = []
        stat_mappings = [
            ("total_attendance", "Total Attendance"),
            ("total_first_time_visitors", "First Time Visitors"),
            ("total_new_people", "New People"),
            ("total_new_christians", "New Christians"),
            ("total_rededications", "Rededications"),
            ("total_youth_attendance", "Youth Attendance"),
            ("total_youth_salvations", "Youth Salvations"),
            ("total_youth_new_people", "Youth New People"),
            ("total_kids_attendance", "Kids Attendance"),
            ("total_kids_leaders", "Kids Leaders"),
            ("total_new_kids", "New Kids"),
            ("total_new_kids_salvations", "New Kids Salvations"),
            ("total_connect_groups", "Connect Groups"),
            ("total_dream_team", "Dream Team"),
            ("total_tithe", "Tithe"),
            ("total_baptisms", "Baptisms"),
            ("total_child_dedications", "Child Dedications"),
            ("total_information_gathered", "Cards Back")
        ]
        
        # If specific stat requested, only include that stat
        if specific_stat:
            stat_mappings = [(f"total_{specific_stat}", specific_stat.replace('_', ' ').title())]
        
        for stat_key, stat_label in stat_mappings:
            row_data = {"stat": stat_label}
            for report in campus_reports:
                # Use the original campus name as the key, not the display name
                campus_name = report["campus"]
                stat_value = report["stats"].get(stat_key, 0)
                # Use the original campus name from the campuses list
                original_campus = next((c for c in campuses if display_campus_name(c) == campus_name), campus_name)
                row_data[original_campus] = stat_value
            comparison_data.append(row_data)
        
        # Create summary text
        campus_names = [display_campus_name(c) for c in campuses]
        if specific_stat:
            summary = f"Comparison of {specific_stat.replace('_', ' ').title()} between {', '.join(campus_names)} in {year}"
        else:
            summary = f"Comparison of all stats between {', '.join(campus_names)} in {year}"
        
        # Create spoken summary
        spoken_summary = f"Here's your comparison between {', '.join(campus_names)} for {year}."
        
        return {
            "question": question,
            "comparison": True,
            "cross_location": True,
            "campuses": campuses,
            "year": year,
            "summary": summary,
            "data": comparison_data,
            "text": spoken_summary,
            "popup": True
        }
        
    except Exception as e:
        logger.error(f"[CROSS_LOCATION] Error in handle_cross_location_comparison: {e}")
        return {
            "error": "Failed to generate cross-location comparison",
            "text": "Sorry, I couldn't generate that cross-location comparison. Please try a different query.",
            "popup": True
        }

# Handler for mid-year and quarterly comparisons

def query_data_internal(data: Dict[str, Any]) -> Dict[str, Any]:
    """Internal function to query data - handles all types of stat queries with popup support"""
    question = str(data.get("question", "")).strip()
    if not question:
        return {"error": "Missing question"}

    # Extract campus from question using the same detection logic
    campus = detect_campus(question)
    question_lower = question.lower()
    
    # Smart campus defaulting based on user role when no campus is mentioned
    if not campus:
        if hasattr(current_user, 'is_authenticated') and current_user and current_user.is_authenticated:
            if current_user.role == 'campus_pastor':
                # Campus pastors get their assigned campus by default
                campus = getattr(current_user, 'campus', 'main')
                logger.info(f"[QUERY] No campus mentioned - using campus pastor's campus: {campus}")
            elif current_user.role in ['senior_pastor', 'lead_pastor', 'admin']:
                # Senior leadership gets all campuses by default
                campus = 'all_campuses'
                logger.info(f"[QUERY] No campus mentioned - using all campuses for senior leadership")
            else:
                # Other roles default to main or all_campuses
                campus = 'all_campuses'
                logger.info(f"[QUERY] No campus mentioned - defaulting to all campuses")
        else:
            campus = 'all_campuses'
    else:
        logger.info(f"[QUERY] Campus detected from question: {campus}")
    
    logger.info(f"[QUERY] Processing question: '{question}' | Final Campus: {campus}")
    
    # 1. CROSS-LOCATION COMPARISON REQUESTS - CHECK FIRST
    is_cross_location, campuses, year, specific_stat = detect_cross_location_comparison(question)
    if is_cross_location:
        logger.info(f"[QUERY] Detected cross-location comparison: campuses={campuses}, year={year}, stat={specific_stat}")
        
        result = handle_cross_location_comparison(question, campuses, year, specific_stat)
        
        # Ensure the response has the correct format for the frontend
        if result.get('comparison'):
            # Add popup flag for comparison results
            result['popup'] = True
            logger.info(f"[QUERY] Cross-location comparison result keys: {list(result.keys())}")
            return result
        else:
            logger.error(f"[QUERY] Cross-location comparison failed to return proper format")
            return {
                "error": "Failed to generate cross-location comparison",
                "text": "Sorry, I couldn't generate that cross-location comparison. Please try a different query.",
                "popup": True
            }

    # 2. COMPARISON REQUESTS (Year over year, quarterly, etc.)
    is_comparison, years, period_type, period_value = detect_comparison_request(question)
    if is_comparison:
        logger.info(f"[QUERY] Detected comparison: years={years}, period={period_type}, value={period_value}")
        campus = detect_campus(question) or campus or "main"
        
        # Add comprehensive logging
        logger.info(f"[QUERY] Processing comparison for campus: {campus}")
        logger.info(f"[QUERY] Question: '{question}'")
        logger.info(f"[QUERY] Period type: {period_type}, Period value: {period_value}")
        
        result = handle_period_comparison_request(question, campus, years, period_type, period_value)
        
        # Ensure the response has the correct format for the frontend
        if result.get('comparison'):
            # Add popup flag for comparison results
            result['popup'] = True
            logger.info(f"[QUERY] Comparison result keys: {list(result.keys())}")
            return result
        else:
            logger.error(f"[QUERY] Comparison failed to return proper format")
            return {
                "error": "Failed to generate comparison",
                "text": "Sorry, I couldn't generate that comparison. Please try a different query.",
                "popup": True
            }

    # 2. REVIEW INTENTS (Annual, Quarterly, Mid-Year Reviews)
    if is_review_intent(question):
        logger.info(f"[QUERY] Detected review intent")
        campus = detect_campus(question) or campus or "main"
        import re
        years = re.findall(r'\b(20\d{2})\b', question)
        if len(years) == 0:
            years = [datetime.now().year]
        elif len(years) == 1:
            years = [int(y) for y in years]
        else:
            years = [int(y) for y in years]
        # Check if this is a cross-campus request
        if campus == "all_campuses" or any(indicator in question_lower for indicator in ['all campuses', 'futures church', 'church wide', 'across all']):  
            # Detect specific review type for cross-campus
            review_type, period_value, year = detect_review_type(question)
            year = years[0] if years else year  # Use detected year or default
            
            # Map review types to cross-campus report types
            if review_type == "quarterly":
                cross_campus_report = generate_cross_campus_report('quarterly', f"Q{period_value} {year}")
                spoken_summary = f"Here's your Q{period_value} {year} quarterly review for All Campuses."
            elif review_type == "monthly":
                month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']
                month_name = month_names[period_value]
                cross_campus_report = generate_cross_campus_report('monthly', f"{month_name} {year}")
                spoken_summary = f"Here's your {month_name} {year} monthly review for All Campuses."
            elif review_type == "mid_year":
                cross_campus_report = generate_cross_campus_report('mid_year', f"Jan-Jun {year}")
                spoken_summary = f"Here's your {year} mid-year review for All Campuses."
            else:
                # Default to annual
                cross_campus_report = generate_cross_campus_report('annual', "")
                spoken_summary = f"Here's your annual review for All Campuses campus in {year}."
            
            stats = cross_campus_report.get('stats', {})
            
            # Create report format for popup
            report_data = [
                {"label": "Total Attendance", "total": stats.get('attendance', {}).get('total', 0), "average": stats.get('attendance', {}).get('average', 0), "count": cross_campus_report.get('entry_count', 0), "year": year},
                {"label": "New People", "total": stats.get('new_people', {}).get('total', 0), "average": stats.get('new_people', {}).get('average', 0), "count": cross_campus_report.get('entry_count', 0), "year": year},
                {"label": "New Christians", "total": stats.get('new_christians', {}).get('total', 0), "average": stats.get('new_christians', {}).get('average', 0), "count": cross_campus_report.get('entry_count', 0), "year": year},
                {"label": "Youth Attendance", "total": stats.get('youth', {}).get('total', 0), "average": stats.get('youth', {}).get('average', 0), "count": cross_campus_report.get('entry_count', 0), "year": year},
                {"label": "Kids Total", "total": stats.get('kids', {}).get('total', 0), "average": stats.get('kids', {}).get('average', 0), "count": cross_campus_report.get('entry_count', 0), "year": year},
                {"label": "Connect Groups", "total": stats.get('connect_groups', {}).get('total', 0), "average": stats.get('connect_groups', {}).get('average', 0), "count": cross_campus_report.get('entry_count', 0), "year": year},
                {"label": "Volunteers", "total": 0, "average": 0, "count": 0, "year": year}  # Volunteers not tracked in cross-campus yet
            ]
            
            return {
                "report": report_data,
                "text": spoken_summary,
                "popup": True,
                "stats": stats,
                "campus": "All Campuses",
                "year": year
            }
        else:
            # Single campus review - detect specific review type
            review_type, period_value, year = detect_review_type(question)
            year = years[0] if years else year  # Use detected year or default
            
            if review_type == "quarterly":
                report = generate_quarterly_report(campus, year, period_value)
            elif review_type == "monthly":
                report = generate_monthly_report(campus, year, period_value)
            elif review_type == "mid_year":
                report = generate_mid_year_report(campus, year)
            else:
                # Default to annual review
                report = generate_full_stat_report(campus, [year])
            
            report["popup"] = True  # Enable popup for reviews
            return report

    # 2. WEEKEND REVIEWS
    if any(phrase in question_lower for phrase in WEEKEND_REVIEW_PHRASES):
        logger.info(f"[QUERY] Detected weekend review")
        
        # First check for pastor names (priority over campus detection)
        pastor_campus = detect_pastor_name(question)
        if pastor_campus:
            campus = pastor_campus
            logger.info(f"[QUERY] Pastor detected - using campus: {campus}")
        else:
            campus = detect_campus(question)
            logger.info(f"[QUERY] No pastor detected - using campus detection: {campus}")
        if campus and campus != "all_campuses":
            # Campus-specific weekend review - use proper weekend date range
            today = datetime.now()
            # Find the most recent Sunday
            days_since_sunday = today.weekday() + 1  # Monday=0, so Sunday=6
            if days_since_sunday == 7:  # Today is Sunday
                days_since_sunday = 0
            most_recent_sunday = today - timedelta(days=days_since_sunday)
            
            # Weekend is Monday to Sunday (7 days ending on Sunday)
            start_date = most_recent_sunday - timedelta(days=6)  # Monday
            end_date = most_recent_sunday  # Sunday
            rows = []
            if sheet:
                try:
                    rows = safe_sheets_request(sheet.get_all_records)
                except Exception as e:
                    logger.error(f"Failed to get stats from Google Sheets: {e}")
                    rows = []
            if not rows:
                memory = load_conversation_memory()
                campus_history = memory.get("session_stats", {}).get(campus, [])
                rows = campus_history
            
            campus_normalized = normalize_campus(campus)
            filtered_rows = []
            for row in rows:
                row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
                if row_campus == campus_normalized or campus_normalized in row_campus:
                    # Use Date field instead of Timestamp for weekend reviews
                    date_str = row.get("Date", "")
                    if date_str:
                        try:
                            # Parse the Date field directly
                            row_date = datetime.strptime(date_str, "%Y-%m-%d")
                            if start_date <= row_date <= end_date:
                                filtered_rows.append(row)
                        except Exception:
                            continue
            
            logger.info(f"[WEEKEND_REVIEW] Found {len(rows)} total rows, {len(filtered_rows)} filtered rows for {campus} in last 7 days")
            analysis_data = calculate_stats_from_filtered_rows(filtered_rows)
            logger.info(f"[WEEKEND_REVIEW] Analysis data: {analysis_data}")
            
            # Check if we have any data
            has_data = (analysis_data.get('total_entries', 0) > 0 or 
                       any(analysis_data.get(key, 0) > 0 for key in ['total_attendance', 'total_new_people', 'total_new_christians', 'total_youth', 'total_kids', 'total_connect_groups']))
            
            if has_data:
                # Create detailed summary for display
                detailed_summary = (
                    f"{display_campus_name(campus)} Weekend Review\n"
                    f"Total Attendance: {analysis_data.get('total_attendance', 0):,}\n"
                    f"New People: {analysis_data.get('total_new_people', 0):,}\n"
                    f"New Christians: {analysis_data.get('total_new_christians', 0):,}\n"
                    f"Youth: {analysis_data.get('total_youth', 0):,}\n"
                    f"Kids: {analysis_data.get('total_kids', 0):,}\n"
                    f"Connect Groups: {analysis_data.get('total_connect_groups', 0):,}"
                )
                
                # Create spoken summary 
                spoken_summary = f"Here's your weekend review for {display_campus_name(campus)} campus."
            else:
                # No data found
                detailed_summary = (
                    f"{display_campus_name(campus)} Weekend Review\n"
                    f"No stats have been logged for {display_campus_name(campus)} campus in the last 7 days.\n"
                    f"This could mean:\n"
                    f"• Stats haven't been entered yet for this weekend\n"
                    f"• The campus name might not match our records\n"
                    f"• There was no service this weekend"
                )
                
                # Create spoken summary 
                spoken_summary = f"I couldn't find any weekend stats for {display_campus_name(campus)} campus in the last 7 days. You may need to enter the stats first or check if the campus name is correct."
            
            # Create comprehensive report with all available stats
            report = []
            stat_mappings = [
                ("total_attendance", "Total Attendance", "attendance"),
                ("total_first_time_visitors", "First Time Visitors", "first_time_visitors"),
                ("total_information_gathered", "Cards Back", "information_gathered"),
                ("total_new_christians", "New Christians", "new_christians"),
                ("total_rededications", "Rededications", "rededications"),
                ("total_youth_attendance", "Youth Attendance", "youth_attendance"),
                ("total_youth_salvations", "Youth Salvations", "youth_salvations"),
                ("total_youth_new_people", "Youth New People", "youth_new_people"),
                ("total_kids_attendance", "Kids Attendance", "kids_attendance"),
                ("total_kids_leaders", "Kids Leaders", "kids_leaders"),
                ("total_new_kids", "New Kids", "new_kids"),
                ("total_new_kids_salvations", "New Kids Salvations", "new_kids_salvations"),
                ("total_connect_groups", "Connect Groups", "connect_groups"),
                ("total_dream_team", "Dream Team", "dream_team"),
                ("total_tithe", "Tithe", "tithe"),
                ("total_baptisms", "Baptisms", "baptisms"),
                ("total_child_dedications", "Child Dedications", "child_dedications"),
                ("total_new_people", "New People", "new_people"),  # Keep for backward compatibility
            ]
            
            for stat_key, label, avg_key in stat_mappings:
                total = analysis_data.get(stat_key, 0)
                average = analysis_data.get("averages", {}).get(avg_key, 0)
                count = analysis_data.get("total_entries", 0)
                
                # Only include stats that have data or are important to show
                if total > 0 or label in ["Total Attendance", "New Christians", "Youth Attendance", "Kids Attendance", "Connect Groups", "Dream Team"]:
                    report.append({
                        "label": label,
                        "total": total,
                        "average": average,
                        "count": count,
                        "year": start_date.year
                    })
            return {
                "question": question,
                "campus": display_campus_name(campus),
                "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "summary": detailed_summary,
                "stats": analysis_data,
                "report": report,
                "text": spoken_summary,
                "popup": True
            }
        else:
            # Cross-campus weekend review
            logger.info(f"[WEEKEND_REVIEW] Processing cross-campus weekend review")
            report = generate_cross_campus_report('weekly', "")
            logger.info(f"[WEEKEND_REVIEW] Cross-campus report: {report}")
            stats = report.get('stats', {})
            
            # Create detailed summary for display
            detailed_summary = (
                f"Futures Church Weekend Review\n"
                f"Total Attendance: {stats.get('attendance', {}).get('total', 0):,}\n"
                f"Average Attendance: {stats.get('attendance', {}).get('average', 0):,.1f}\n"
                f"New People: {stats.get('new_people', {}).get('total', 0):,}\n"
                f"New Christians: {stats.get('new_christians', {}).get('total', 0):,}\n"
                f"Youth: {stats.get('youth', {}).get('total', 0):,}\n"
                f"Kids: {stats.get('kids', {}).get('total', 0):,}\n"
                f"Connect Groups: {stats.get('connect_groups', {}).get('total', 0):,}"
            )
            
            # Create spoken summary
            spoken_summary = f"Here's your weekend review for Futures Church across all campuses."
            return {
                "question": question,
                "campus": "Futures Church (All Campuses)",
                "date_range": report.get('date_range', ''),
                "summary": detailed_summary,
                "stats": stats,
                "report": report,
                "text": spoken_summary,
                "popup": True
            }

    # 3. CROSS-CAMPUS REVIEWS
    cross_campus_result = detect_cross_campus_review(question)
    if cross_campus_result:
        review_type, _ = cross_campus_result
        logger.info(f"[QUERY] Detected cross-campus review: {review_type}")
        report = generate_cross_campus_report(review_type, "")
        stats = report.get('stats', {})
        
        # Create comprehensive summary
        summary = f"Futures Church {review_type.title()} Report\n"
        summary += f"Total Attendance: {stats.get('attendance', {}).get('total', 0):,}\n"
        summary += f"Average Attendance: {stats.get('attendance', {}).get('average', 0):,.1f}\n"
        summary += f"New People: {stats.get('new_people', {}).get('total', 0):,}\n"
        summary += f"New Christians: {stats.get('new_christians', {}).get('total', 0):,}\n"
        summary += f"Youth: {stats.get('youth', {}).get('total', 0):,}\n"
        summary += f"Kids: {stats.get('kids', {}).get('total', 0):,}\n"
        summary += f"Connect Groups: {stats.get('connect_groups', {}).get('total', 0):,}"
        
        # Convert to report format for popup
        report_data = [
            {"label": "Total Attendance", "total": stats.get('attendance', {}).get('total', 0), "average": stats.get('attendance', {}).get('average', 0), "count": report.get('entry_count', 0), "year": datetime.now().year},
            {"label": "New People", "total": stats.get('new_people', {}).get('total', 0), "average": stats.get('new_people', {}).get('average', 0), "count": report.get('entry_count', 0), "year": datetime.now().year},
            {"label": "New Christians", "total": stats.get('new_christians', {}).get('total', 0), "average": stats.get('new_christians', {}).get('average', 0), "count": report.get('entry_count', 0), "year": datetime.now().year},
            {"label": "Youth", "total": stats.get('youth', {}).get('total', 0), "average": stats.get('youth', {}).get('average', 0), "count": report.get('entry_count', 0), "year": datetime.now().year},
            {"label": "Kids", "total": stats.get('kids', {}).get('total', 0), "average": stats.get('kids', {}).get('average', 0), "count": report.get('entry_count', 0), "year": datetime.now().year},
            {"label": "Connect Groups", "total": stats.get('connect_groups', {}).get('total', 0), "average": stats.get('connect_groups', {}).get('average', 0), "count": report.get('entry_count', 0), "year": datetime.now().year},
        ]
        
        return {
            "question": question,
            "campus": "Futures Church (All Campuses)",
            "date_range": report.get('date_range', ''),
            "summary": summary,
            "stats": stats,
            "report": report_data,
            "text": summary,
            "popup": True
        }

    # 5. SIMPLE STAT QUERIES (How many people, what was attendance, etc.)
    # First check for multiple stats (e.g., "np and nc")
    multiple_stats = detect_multiple_stats(question)
    simple_stat_result = detect_simple_stat_query(question)
    
    if multiple_stats:
        logger.info(f"[QUERY] Detected multiple stat query: {multiple_stats}")
        stat_types = multiple_stats
        keyword = "multiple stats"
    elif simple_stat_result:
        stat_type, keyword = simple_stat_result
        stat_types = [stat_type]  # Convert to list for consistency
        logger.info(f"[QUERY] Detected simple stat query: {stat_type} (keyword: {keyword})")
    else:
        stat_types = None
        keyword = None
    
    if stat_types:
        
        # Default campus if none detected
        if not campus or campus == "all_campuses":
            campus = "main"
        
        # Parse date range from question
        start_date, end_date, date_range_text = parse_date_range(question)
        
        # Get data - prioritize Google Sheets over local data
        rows = []
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
                logger.info(f"[QUERY] Using Google Sheets data: {len(rows)} rows")
            except Exception as e:
                logger.error(f"Failed to get stats from Google Sheets: {e}")
                rows = []
        
        if not rows:
            logger.info("[QUERY] Falling back to local data")
            rows = load_local_data()
            if not rows:
                memory = load_conversation_memory()
                campus_history = memory.get("session_stats", {}).get(campus, [])
                rows = campus_history
        
        # Handle cross-campus queries
        if campus == "all_campuses" or any(indicator in question_lower for indicator in ['all campuses', 'futures church', 'church wide', 'across all']):
            # Cross-campus simple stat query
            analysis_data = get_all_campuses_data(rows, start_date, end_date)
            campus_display = "Futures Church (All Campuses)"
            
            # Calculate cross-campus totals
            total_attendance = sum(safe_int(row.get('Total Attendance', 0)) for row in analysis_data)
            total_new_people = sum(safe_int(row.get('New People', 0)) for row in analysis_data)
            total_new_christians = sum(safe_int(row.get('New Christians', 0)) for row in analysis_data)
            total_youth = sum(safe_int(row.get('Youth Attendance', 0)) for row in analysis_data)
            total_kids = sum(safe_int(row.get('Kids Total', 0)) for row in analysis_data)
            total_connect_groups = sum(safe_int(row.get('Connect Groups', 0)) for row in analysis_data)
            
            # Calculate averages
            valid_entries = len([row for row in analysis_data if safe_int(row.get('Total Attendance', 0)) > 0])
            avg_attendance = total_attendance / valid_entries if valid_entries > 0 else 0
            avg_new_people = total_new_people / valid_entries if valid_entries > 0 else 0
            avg_new_christians = total_new_christians / valid_entries if valid_entries > 0 else 0
            avg_youth = total_youth / valid_entries if valid_entries > 0 else 0
            avg_kids = total_kids / valid_entries if valid_entries > 0 else 0
            avg_connect_groups = total_connect_groups / valid_entries if valid_entries > 0 else 0
            
            cross_campus_data = {
                'total_attendance': total_attendance,
                'total_new_people': total_new_people,
                'total_new_christians': total_new_christians,
                'total_youth': total_youth,
                'total_kids': total_kids,
                'total_connect_groups': total_connect_groups,
                'averages': {
                    'attendance': avg_attendance,
                    'new_people': avg_new_people,
                    'new_christians': avg_new_christians,
                    'youth': avg_youth,
                    'kids': avg_kids,
                    'connect_groups': avg_connect_groups
                }
            }
            
            answer = generate_simple_stat_answer(stat_types[0], cross_campus_data, campus_display, f" {date_range_text}")
            
            # Create targeted report data for popup - only show the requested stat(s)
            report_data = create_targeted_report_data(stat_types, cross_campus_data, start_date.year, valid_entries)
            
            return {
                "question": question,
                "campus": campus_display,
                "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "answer": answer,
                "text": answer,
                "stats": cross_campus_data,
                "report": report_data,
                "popup": True
            }
        else:
            # Single campus simple stat query
            campus_normalized = normalize_campus(campus)
            filtered_rows = []
            logger.info(f"[QUERY] Looking for campus: '{campus}' (normalized: '{campus_normalized}')")
            
            for row in rows:
                row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
                original_campus = row.get("Campus") or row.get("campus") or ""
                logger.info(f"[QUERY] Row campus: '{original_campus}' (normalized: '{row_campus}')")
                
                # Enhanced campus matching with better case-insensitive handling
                campus_match = False
                
                # Direct normalization comparison
                if row_campus == campus_normalized:
                    campus_match = True
                
                # Case-insensitive comparison of original names
                elif original_campus.lower() == campus.lower():
                    campus_match = True
                
                # Partial matching for voice recognition
                elif campus_normalized in row_campus or row_campus in campus_normalized:
                    campus_match = True
                
                # Handle special cases like "south" vs "South"
                elif campus_normalized == "south" and row_campus == "south":
                    campus_match = True
                elif campus_normalized == "salisbury" and row_campus == "salisbury":
                    campus_match = True
                elif campus_normalized == "paradise" and row_campus == "paradise":
                    campus_match = True
                elif campus_normalized == "adelaide city" and row_campus == "adelaide city":
                    campus_match = True
                
                if campus_match:
                    row_date = get_row_timestamp(row)
                    if row_date != datetime.min and start_date <= row_date <= end_date:
                        filtered_rows.append(row)
            
            logger.info(f"[QUERY] Found {len(filtered_rows)} rows for campus '{campus}'")
            if filtered_rows:
                logger.info(f"[QUERY] Sample row: {filtered_rows[0]}")
            
            analysis_data = calculate_stats_for_year_range(filtered_rows, campus, start_date.year, end_date.year if end_date.year != start_date.year else None)
            
            # Calculate cross-campus averages for comparison
            if sheet:
                try:
                    all_rows = safe_sheets_request(sheet.get_all_records)
                    all_filtered_rows = []
                    for row in all_rows:
                        row_date = get_row_timestamp(row)
                        if row_date != datetime.min and start_date <= row_date <= end_date:
                            all_filtered_rows.append(row)
                    
                    # Calculate averages across all campuses
                    if all_filtered_rows:
                        total_weeks = len(all_filtered_rows)
                        cross_campus_totals = {
                            'attendance': sum(safe_int(row.get('Attendance', 0)) for row in all_filtered_rows),
                            'new_people': sum(safe_int(row.get('New People', 0)) for row in all_filtered_rows),
                            'new_christians': sum(safe_int(row.get('New Christians', 0)) for row in all_filtered_rows),
                            'youth': sum(safe_int(row.get('Youth', 0)) for row in all_filtered_rows),
                            'kids': sum(safe_int(row.get('Kids', 0)) for row in all_filtered_rows),
                            'connect_groups': sum(safe_int(row.get('Connect Groups', 0)) for row in all_filtered_rows),
                            'dream_team': sum(safe_int(row.get('Dream Team', 0)) for row in all_filtered_rows)
                        }
                        
                        analysis_data['cross_campus_averages'] = {
                            stat_type: total / total_weeks if total_weeks > 0 else 0
                            for stat_type, total in cross_campus_totals.items()
                        }
                except Exception as e:
                    logger.error(f"Failed to calculate cross-campus averages: {e}")
                    analysis_data['cross_campus_averages'] = {}
            
            answer = generate_simple_stat_answer(stat_types[0], analysis_data, display_campus_name(campus), f" {date_range_text}")
            
            # Create targeted report data for popup - only show the requested stat(s)
            report_data = create_targeted_report_data(stat_types, analysis_data, start_date.year, analysis_data.get("total_entries", 0))
            
            return {
                "question": question,
                "campus": display_campus_name(campus),
                "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "answer": answer,
                "text": answer,
                "stats": analysis_data,
                "report": report_data,
                "popup": True
            }

    # 6. GENERAL/BIG PICTURE QUERIES
    general_patterns = [
        'summary', 'all numbers', 'big picture', 'overview', 'all stats', 'full stats',
        'church numbers', 'show me everything', 'what are our numbers', 'church stats'
    ]
    
    if any(pattern in question_lower for pattern in general_patterns):
        logger.info(f"[QUERY] Detected general/big picture query")
        
        # Default to current year if no specific period mentioned
        if not campus or campus == "all_campuses":
            campus = "main"
        
        start_date, end_date, date_range_text = parse_date_range(question)
        
        # Get data and calculate comprehensive stats
        rows = []
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
                logger.info(f"[QUERY] Retrieved {len(rows)} rows from Google Sheets")
                if rows:
                    logger.info(f"[QUERY] Sample row keys: {list(rows[0].keys())}")
            except Exception as e:
                logger.error(f"Failed to get stats from Google Sheets: {e}")
                rows = []
        if not rows:
            memory = load_conversation_memory()
            campus_history = memory.get("session_stats", {}).get(campus, [])
            rows = campus_history
        
        # Filter by campus and date
        campus_normalized = normalize_campus(campus)
        logger.info(f"[QUERY] Looking for campus: '{campus}' (normalized: '{campus_normalized}')")
        filtered_rows = []
        for row in rows:
            row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
            original_campus = row.get("Campus") or row.get("campus") or ""
            logger.info(f"[QUERY] Row campus: '{original_campus}' (normalized: '{row_campus}')")
            
            # More flexible campus matching
            if (row_campus == campus_normalized or 
                campus_normalized in row_campus or 
                row_campus in campus_normalized or
                campus_normalized.replace(" ", "") in row_campus.replace(" ", "") or
                row_campus.replace(" ", "") in campus_normalized.replace(" ", "")):
                timestamp_str = row.get("Timestamp", "")
                if timestamp_str:
                    try:
                        if "T" in timestamp_str:
                            row_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            row_date = parse_any_date(timestamp_str)
                        if start_date <= row_date <= end_date:
                            filtered_rows.append(row)
                    except Exception:
                        continue
        
        analysis_data = calculate_stats_for_year_range(filtered_rows, campus, start_date.year, end_date.year if end_date.year != start_date.year else None)
        
        # Create comprehensive summary
        campus_display = display_campus_name(campus)
        summary = f"{campus_display} Church Stats ({date_range_text})\n\n"
        summary += f"📊 Attendance: {analysis_data.get('total_attendance', 0):,} total (avg: {analysis_data.get('averages', {}).get('attendance', 0):.1f})\n"
        summary += f"👥 New People: {analysis_data.get('total_new_people', 0):,} total (avg: {analysis_data.get('averages', {}).get('new_people', 0):.1f})\n"
        summary += f"✝️ New Christians: {analysis_data.get('total_new_christians', 0):,} total (avg: {analysis_data.get('averages', {}).get('new_christians', 0):.1f})\n"
        summary += f"🎯 Youth: {analysis_data.get('total_youth', 0):,} total (avg: {analysis_data.get('averages', {}).get('youth', 0):.1f})\n"
        summary += f"👶 Kids: {analysis_data.get('total_kids', 0):,} total (avg: {analysis_data.get('averages', {}).get('kids', 0):.1f})\n"
        summary += f"🤝 Connect Groups: {analysis_data.get('total_connect_groups', 0):,} total (avg: {analysis_data.get('averages', {}).get('connect_groups', 0):.1f})\n"
        summary += f"🌟 Dream Team: {analysis_data.get('total_dream_team', 0):,} total (avg: {analysis_data.get('averages', {}).get('dream_team', 0):.1f})"
        
        # Create report data for popup
        report_data = [
            {"label": "Total Attendance", "total": analysis_data.get("total_attendance", 0), "average": analysis_data.get("averages", {}).get("attendance", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "New People", "total": analysis_data.get("total_new_people", 0), "average": analysis_data.get("averages", {}).get("new_people", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "New Christians", "total": analysis_data.get("total_new_christians", 0), "average": analysis_data.get("averages", {}).get("new_christians", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "Youth", "total": analysis_data.get("total_youth", 0), "average": analysis_data.get("averages", {}).get("youth", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "Kids", "total": analysis_data.get("total_kids", 0), "average": analysis_data.get("averages", {}).get("kids", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "Connect Groups", "total": analysis_data.get("total_connect_groups", 0), "average": analysis_data.get("averages", {}).get("connect_groups", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "Dream Team", "total": analysis_data.get("total_dream_team", 0), "average": analysis_data.get("averages", {}).get("dream_team", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
        ]
        
        return {
            "question": question,
            "campus": campus_display,
            "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "answer": summary,
            "text": summary,
            "stats": analysis_data,
            "report": report_data,
            "popup": True
        }

    # 7. AI INSIGHTS for complex questions
    if any(word in question_lower for word in ['trend', 'trends', 'pattern', 'growth', 'improve', 'attention', 'working', 'analysis', 'insight', 'why', 'how are we', 'what areas']):
        logger.info(f"[QUERY] Detected AI insights query")
        
        if not campus or campus == "all_campuses":
            campus = "main"
        
        start_date, end_date, date_range_text = parse_date_range(question)
        
        # Get and filter data
        rows = []
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
            except Exception as e:
                logger.error(f"Failed to get stats from Google Sheets: {e}")
                rows = []
        if not rows:
            memory = load_conversation_memory()
            campus_history = memory.get("session_stats", {}).get(campus, [])
            rows = campus_history
        
        campus_normalized = normalize_campus(campus)
        filtered_rows = []
        for row in rows:
            row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
            if row_campus == campus_normalized or campus_normalized in row_campus:
                timestamp_str = row.get("Timestamp", "")
                if timestamp_str:
                    try:
                        if "T" in timestamp_str:
                            row_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            row_date = parse_any_date(timestamp_str)
                        if start_date <= row_date <= end_date:
                            filtered_rows.append(row)
                    except Exception:
                        continue
        
        analysis_data = calculate_stats_for_year_range(filtered_rows, campus, start_date.year, end_date.year if end_date.year != start_date.year else None)
        ai_insights = generate_ai_insights(question, campus, analysis_data, filtered_rows)
        
        # Create report data for popup
        report_data = [
            {"label": "Total Attendance", "total": analysis_data.get("total_attendance", 0), "average": analysis_data.get("averages", {}).get("attendance", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "New People", "total": analysis_data.get("total_new_people", 0), "average": analysis_data.get("averages", {}).get("new_people", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "New Christians", "total": analysis_data.get("total_new_christians", 0), "average": analysis_data.get("averages", {}).get("new_christians", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "Youth", "total": analysis_data.get("total_youth", 0), "average": analysis_data.get("averages", {}).get("youth", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "Kids", "total": analysis_data.get("total_kids", 0), "average": analysis_data.get("averages", {}).get("kids", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "Connect Groups", "total": analysis_data.get("total_connect_groups", 0), "average": analysis_data.get("averages", {}).get("connect_groups", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
            {"label": "Dream Team", "total": analysis_data.get("total_dream_team", 0), "average": analysis_data.get("averages", {}).get("dream_team", 0), "count": analysis_data.get("total_entries", 0), "year": start_date.year},
        ]
        
        return {
            "question": question,
            "campus": display_campus_name(campus),
            "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "answer": ai_insights,
            "text": ai_insights,
            "insights": [ai_insights],
            "stats": analysis_data,
            "report": report_data,
            "popup": True
        }

    # 8. FALLBACK: Default response for unrecognized queries
    logger.info(f"[QUERY] No specific pattern matched, using fallback")
    return {
        "error": f"I'm not sure how to answer '{question}'. Try asking for specific stats like 'How many people attended this month?' or 'Show me the annual report for South campus'."
    }

def generate_ai_insights(question: str, campus: str, analysis_data: dict, filtered_rows: list) -> str:
    """Generate intelligent AI insights using Claude based on the data and question"""
    if not claude:
        return "I'd be happy to analyze your data, but I need to connect to my AI assistant first."
    
    # Prepare data summary for Claude
    data_summary = f"""
Here's what I found for {display_campus_name(campus)} campus ({analysis_data.get('date_range', 'recent data')}):

Their numbers:
- {analysis_data.get('total_attendance', 0):,} total attendance
- {analysis_data.get('total_new_people', 0):,} new people
- {analysis_data.get('total_new_christians', 0):,} new christians
- {analysis_data.get('total_youth', 0):,} youth
- {analysis_data.get('total_kids', 0):,} kids
- {analysis_data.get('total_connect_groups', 0):,} connect groups

Weekly averages:
- {analysis_data.get('averages', {}).get('attendance', 0):.1f} people per week
- {analysis_data.get('averages', {}).get('new_people', 0):.1f} new people per week
- {analysis_data.get('averages', {}).get('new_christians', 0):.1f} new christians per week
- {analysis_data.get('averages', {}).get('youth', 0):.1f} youth per week
- {analysis_data.get('averages', {}).get('kids', 0):.1f} kids per week
- {analysis_data.get('averages', {}).get('connect_groups', 0):.1f} connect groups per week
"""

    # Add recent data points for trend analysis
    if filtered_rows:
        recent_data = "Recent weeks:\n"
        for i, row in enumerate(filtered_rows[-5:], 1):  # Last 5 entries
            if isinstance(row, dict):
                date = row.get('Date', row.get('Timestamp', 'Unknown'))
                attendance = row.get('Total Attendance', 0)
                new_people = row.get('New People', 0)
                new_christians = row.get('New Christians', 0)
                recent_data += f"{i}. {date}: {attendance} people, {new_people} new, {new_christians} christians\n"
        data_summary += f"\n{recent_data}"

    # Create intelligent prompt based on question type
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['trend', 'trends', 'pattern', 'growth', 'improve', 'attention', 'working', 'analysis', 'insight', 'why', 'how are we', 'what areas']):
        prompt = f"""You're a friendly church growth expert. A leader from {display_campus_name(campus)} campus is asking: "{question}"

{data_summary}

Give them warm, encouraging insights about their data. Focus on:
- What trends you see in their numbers
- How their campus is performing overall
- What areas are doing well or need attention
- Simple suggestions that could help

Be conversational and encouraging. Use their data to back up your insights. Keep it under 120 words and make it feel like a friendly conversation."""
    
    elif any(word in question_lower for word in ['compare', 'vs', 'versus', 'against', 'difference']):
        prompt = f"""You're a helpful church data friend. A leader from {display_campus_name(campus)} campus is asking: "{question}"

{data_summary}

Give them friendly analysis of their data. Focus on:
- How their numbers stack up
- What patterns you notice
- What the data tells us about their progress
- What might be influencing their results

Be encouraging and use their specific numbers. Keep it under 120 words and sound like you're chatting with a friend."""
    
    elif any(word in question_lower for word in ['how', 'what', 'why', 'analysis', 'insight']):
        prompt = f"""You're a helpful church assistant. A leader from {display_campus_name(campus)} campus is asking: "{question}"

{data_summary}

Give them friendly, helpful insights. Focus on:
- What they're really asking about
- What their data shows
- How this info can help them
- What positive things you notice

Be warm and specific. Use their data to give meaningful insights. Keep it under 120 words and sound conversational."""
    
    else:
        prompt = f"""You're a helpful church assistant. A leader from {display_campus_name(campus)} campus is asking: "{question}"

{data_summary}

Give them friendly, helpful insights. Focus on:
- What they're really asking about
- What their data shows
- How this info can help them
- What positive things you notice

Be warm and specific. Use their data to give meaningful insights. Keep it under 120 words and sound conversational."""

    try:
        response = claude.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.content[0].text.strip() if hasattr(response.content[0], 'text') else str(response.content[0])
        return response_text
        
    except Exception as e:
        logger.error(f"Claude API error in generate_ai_insights: {e}")
        return f"I'd be happy to analyze your data for {display_campus_name(campus)} campus, but I'm having trouble connecting to my AI assistant right now. The data shows {analysis_data.get('total_attendance', 0)} total attendance with an average of {analysis_data.get('averages', {}).get('attendance', 0):.1f} people per week."

def detect_review_type(question: str) -> tuple:
    """Detect the type of review requested and extract relevant parameters"""
    import re
    q = question.lower()
    
    # Quarterly review detection (Q1, Q2, Q3, Q4)
    quarterly_patterns = [
        r'\bq1\b', r'\bq2\b', r'\bq3\b', r'\bq4\b',
        r'\bquarter 1\b', r'\bquarter 2\b', r'\bquarter 3\b', r'\bquarter 4\b',
        r'\bfirst quarter\b', r'\bsecond quarter\b', r'\bthird quarter\b', r'\bfourth quarter\b',
        r'\bq1 review\b', r'\bq2 review\b', r'\bq3 review\b', r'\bq4 review\b',
        r'\bquarterly review\b', r'\bquarter review\b'
    ]
    
    for pattern in quarterly_patterns:
        if re.search(pattern, q):
            # Extract quarter number
            if 'q1' in q or 'quarter 1' in q or 'first quarter' in q:
                quarter = 1
            elif 'q2' in q or 'quarter 2' in q or 'second quarter' in q:
                quarter = 2
            elif 'q3' in q or 'quarter 3' in q or 'third quarter' in q:
                quarter = 3
            elif 'q4' in q or 'quarter 4' in q or 'fourth quarter' in q:
                quarter = 4
            else:
                quarter = 1  # Default to Q1
            
            # Extract year
            import re
            years = re.findall(r'\b(20\d{2})\b', question)
            year = int(years[0]) if years else datetime.now().year
            
            return "quarterly", quarter, year
    
    # Monthly review detection
    monthly_patterns = [
        r'\bmonthly review\b', r'\bmonth review\b', r'\bmonthly report\b', r'\bmonth report\b',
        r'\bmonthly summary\b', r'\bmonth summary\b', r'\bmonthly stats\b', r'\bmonth stats\b',
        r'\bmonthly statistics\b', r'\bmonth statistics\b', r'\bmonthly numbers\b', r'\bmonth numbers\b',
        r'\bmonthly data\b', r'\bmonth data\b', r'\bmonthly recap\b', r'\bmonth recap\b',
        r'\bmonthly overview\b', r'\bmonth overview\b', r'\bmonthly dashboard\b', r'\bmonth dashboard\b',
        r'\bjanuary review\b', r'\bfebruary review\b', r'\bmarch review\b', r'\bapril review\b',
        r'\bmay review\b', r'\bjune review\b', r'\bjuly review\b', r'\baugust review\b',
        r'\bseptember review\b', r'\boctober review\b', r'\bnovember review\b', r'\bdecember review\b',
        r'\bjanuary report\b', r'\bfebruary report\b', r'\bmarch report\b', r'\bapril report\b',
        r'\bmay report\b', r'\bjune report\b', r'\bjuly report\b', r'\baugust report\b',
        r'\bseptember report\b', r'\boctober report\b', r'\bnovember report\b', r'\bdecember report\b'
    ]
    
    for pattern in monthly_patterns:
        if re.search(pattern, q):
            # Extract month number
            months = {
                'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
                'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
                'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
                'november': 11, 'nov': 11, 'december': 12, 'dec': 12
            }
            
            month = None
            for month_name, month_num in months.items():
                if month_name in q or month_name[:3] in q:
                    month = month_num
                    break
            
            # If no specific month found, default to the most recent complete month (previous month)
            if month is None:
                current_date = datetime.now()
                if current_date.month == 1:
                    month = 12  # December of previous year
                else:
                    month = current_date.month - 1
                
            # Extract year
            years = re.findall(r'\b(20\d{2})\b', question)
            if years:
                year = int(years[0])
            else:
                current_date = datetime.now()
                # If we defaulted to December and we're in January, use previous year
                if month == 12 and current_date.month == 1:
                    year = current_date.year - 1
                else:
                    year = current_date.year
            
            return "monthly", month, year

    # Mid-year review detection
    mid_year_patterns = [
        r'\bmid.?year\b', r'\bmidyear\b', r'\bmid.?year review\b', r'\bmidyear review\b',
        r'\bmid.?year report\b', r'\bmidyear report\b', r'\bmid.?year summary\b', r'\bmidyear summary\b',
        r'\bmid.?year stats\b', r'\bmidyear stats\b', r'\bmid.?year statistics\b', r'\bmidyear statistics\b',
        r'\bmid.?year numbers\b', r'\bmidyear numbers\b', r'\bmid.?year data\b', r'\bmidyear data\b',
        r'\bmid.?year recap\b', r'\bmidyear recap\b', r'\bmid.?year overview\b', r'\bmidyear overview\b',
        r'\bmid.?year dashboard\b', r'\bmidyear dashboard\b', r'\bmid.?year snapshot\b', r'\bmidyear snapshot\b',
        r'\bmid.?year full report\b', r'\bmidyear full report\b', r'\bmid.?year full review\b', r'\bmidyear full review\b',
        r'\bmid.?year full summary\b', r'\bmidyear full summary\b', r'\bmid.?year stat report\b', r'\bmidyear stat report\b',
        r'\bmid.?year stat summary\b', r'\bmidyear stat summary\b', r'\bmid.?year stat overview\b', r'\bmidyear stat overview\b',
        r'\bmid.?year stat recap\b', r'\bmidyear stat recap\b', r'\bmid.?year stats summary\b', r'\bmidyear stats summary\b',
        r'\bmid.?year stats overview\b', r'\bmidyear stats overview\b', r'\bmid.?year stats recap\b', r'\bmidyear stats recap\b'
    ]
    
    for pattern in mid_year_patterns:
        if re.search(pattern, q):
            # Extract year
            import re
            years = re.findall(r'\b(20\d{2})\b', question)
            year = int(years[0]) if years else datetime.now().year
            
            return "mid_year", None, year
    
    # Annual review detection (default)
    annual_patterns = [
        'review', 'annual review', 'anual review', 'report', 'summary', 'dashboard', 'snapshot', 'full report', 'overview', 'recap',
        'stats summary', 'stat summary', 'stat report', 'stat overview', 'stat recap',
        'year in review', 'yearly review', 'yearly report', 'year-end review', 'end of year report', 'end of year review',
        'give me a review', 'give me an annual review', 'can i get a review', 'can i get an annual review', 'show me a review', 'show me an annual review',
        'show me the annual report', 'show me the report', 'show me the summary', 'show me the dashboard', 'show me the stats summary',
        'generate a report', 'generate an annual report', 'generate a summary', 'generate an annual summary',
        'full stats', 'all stats', 'all statistics', 'all numbers', 'all data', 'all metrics',
        'recap of the year', 'recap for the year', 'recap', 'stat recap', 'stats recap',
        'big picture', 'big picture stats', 'big picture summary', 'big picture report',
        'comprehensive report', 'comprehensive review', 'comprehensive summary',
        'church report', 'church review', 'church summary',
        'annual stats', 'annual statistics', 'annual numbers', 'annual data',
        'give me a summary', 'can i get a summary', 'show me a summary',
        'give me a dashboard', 'can i get a dashboard', 'show me a dashboard',
        'give me a snapshot', 'can i get a snapshot', 'show me a snapshot',
        'give me an overview', 'can i get an overview', 'show me an overview',
        'give me a full report', 'can i get a full report', 'show me a full report',
        'give me a full review', 'can i get a full review', 'show me a full review',
        'give me a full summary', 'can i get a full summary', 'show me a full summary',
        'give me a stat report', 'can i get a stat report', 'show me a stat report',
        'give me a stat summary', 'can i get a stat summary', 'show me a stat summary',
        'give me a stat overview', 'can i get a stat overview', 'show me a stat overview',
        'give me a stat recap', 'can i get a stat recap', 'show me a stat recap',
        'give me a stats summary', 'can i get a stats summary', 'show me a stats summary',
        'give me a stats overview', 'can i get a stats overview', 'show me a stats overview',
        'give me a stats recap', 'can i get a stats recap', 'show me a stats recap',
        'give me an annual stats', 'can i get annual stats', 'show me annual stats',
        'give me an annual statistics', 'can i get annual statistics', 'show me annual statistics',
        'give me an annual numbers', 'can i get annual numbers', 'show me annual numbers',
        'give me an annual data', 'can i get annual data', 'show me annual data',
        'give me an annual summary', 'can i get annual summary', 'show me annual summary',
        'give me an annual report', 'can i get annual report', 'show me annual report',
        'give me an annual review', 'can i get annual review', 'show me annual review',
        'give me an anual review', 'can i get an anual review', 'show me an anual review',
        'give me an anual report', 'can i get an anual report', 'show me an anual report',
        'give me an anual summary', 'can i get an anual summary', 'show me an anual summary',
        'give me an anual stats', 'can i get an anual stats', 'show me an anual stats',
        'give me an anual statistics', 'can i get an anual statistics', 'show me an anual statistics',
        'give me an anual numbers', 'can i get an anual numbers', 'show me an anual numbers',
        'give me an anual data', 'can i get an anual data', 'show me an anual data'
    ]
    
    for pattern in annual_patterns:
        if pattern in q:
            # Extract year
            import re
            years = re.findall(r'\b(20\d{2})\b', question)
            year = int(years[0]) if years else datetime.now().year
            
            return "annual", None, year
    
    return None, None, None

def is_review_intent(question: str) -> bool:
    """Check if the question is asking for a review (but not a comparison or weekend review)"""
    # First check if this is a comparison request - if so, it's not a review intent
    is_comparison, _, _, _ = detect_comparison_request(question)
    if is_comparison:
        return False
    
    # Check if this is a weekend review - if so, it's not a general review intent
    question_lower = question.lower()
    if any(phrase in question_lower for phrase in WEEKEND_REVIEW_PHRASES):
        return False
    
    # Then check for review intent
    review_type, _, _ = detect_review_type(question)
    return review_type is not None

def generate_quarterly_report(campus: str, year: int, quarter: int) -> dict:
    """Generate a quarterly report for a specific quarter and year"""
    # Define quarter date ranges
    quarter_ranges = {
        1: (datetime(year, 1, 1), datetime(year, 3, 31)),
        2: (datetime(year, 4, 1), datetime(year, 6, 30)),
        3: (datetime(year, 7, 1), datetime(year, 9, 30)),
        4: (datetime(year, 10, 1), datetime(year, 12, 31))
    }
    
    start_date, end_date = quarter_ranges[quarter]
    
    # Get rows data
    rows = []
    if sheet:
        try:
            rows = safe_sheets_request(sheet.get_all_records)
        except Exception as e:
            logger.error(f"Failed to get stats from Google Sheets: {e}")
            rows = []
    
    if not rows:
        memory = load_conversation_memory()
        campus_history = memory.get("session_stats", {}).get(campus, [])
        if not campus_history:
            campus_capitalized = campus.title()
            campus_history = memory.get("session_stats", {}).get(campus_capitalized, [])
            if campus_history:
                campus = campus_capitalized
        rows = campus_history
    
    # Filter rows by campus and date range
    filtered_rows = []
    campus_normalized = normalize_campus(campus)
    
    for row in rows:
        row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
        if row_campus == campus_normalized or campus_normalized in row_campus:
            timestamp_str = row.get("Timestamp", "")
            if timestamp_str:
                try:
                    if "T" in timestamp_str:
                        row_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        row_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    if start_date <= row_date <= end_date:
                        filtered_rows.append(row)
                except Exception:
                    continue
    
    # Calculate stats for the quarter
    total_attendance = 0
    total_new_people = 0
    total_new_christians = 0
    total_youth = 0
    total_kids = 0
    total_connect_groups = 0
    entry_count = 0
    
    # Track values for average calculation
    attendance_values = []
    new_people_values = []
    new_christians_values = []
    youth_values = []
    kids_values = []
    connect_groups_values = []
    
    for entry in filtered_rows:
        if isinstance(entry, dict):
            def safe_int_stat(val):
                try:
                    if val is None or val == '':
                        return 0
                    return int(str(val).replace(',', '').strip())
                except Exception:
                    return 0
            attendance_val = safe_int_stat(entry.get('Total Attendance'))
            new_people_val = safe_int_stat(entry.get('New People'))
            new_christians_val = safe_int_stat(entry.get('New Christians'))
            youth_val = safe_int_stat(entry.get('Youth Attendance'))
            kids_val = safe_int_stat(entry.get('Kids Total'))
            connect_groups_val = safe_int_stat(entry.get('Connect Groups'))
            
            # Only count entries with at least one stat
            if any([attendance_val, new_people_val, new_christians_val, youth_val, kids_val, connect_groups_val]):
                entry_count += 1
            
            # Add to totals
            total_attendance += attendance_val
            total_new_people += new_people_val
            total_new_christians += new_christians_val
            total_youth += youth_val
            total_kids += kids_val
            total_connect_groups += connect_groups_val
            
            # Add to lists for averages (only if > 0)
            if attendance_val > 0:
                attendance_values.append(attendance_val)
            if new_people_val > 0:
                new_people_values.append(new_people_val)
            if new_christians_val > 0:
                new_christians_values.append(new_christians_val)
            if youth_val > 0:
                youth_values.append(youth_val)
            if kids_val > 0:
                kids_values.append(kids_val)
            if connect_groups_val > 0:
                connect_groups_values.append(connect_groups_val)
    
    # Calculate averages
    avg_attendance = sum(attendance_values) / len(attendance_values) if attendance_values else 0
    avg_new_people = sum(new_people_values) / len(new_people_values) if new_people_values else 0
    avg_new_christians = sum(new_christians_values) / len(new_christians_values) if new_christians_values else 0
    avg_youth = sum(youth_values) / len(youth_values) if youth_values else 0
    avg_kids = sum(kids_values) / len(kids_values) if kids_values else 0
    avg_connect_groups = sum(connect_groups_values) / len(connect_groups_values) if connect_groups_values else 0
    
    # Create results in the same format as annual report
    results = []
    stat_types = [
        ('attendance', 'Total Attendance', 'attendance'),
        ('new_people', 'New People', 'new_people'),
        ('new_christians', 'New Christians', 'new_christians'),
        ('youth', 'Youth Attendance', 'youth'),
        ('kids', 'Kids Total', 'kids'),
        ('connect_groups', 'Connect Groups', 'connect_groups'),
    ]
    
    for stat_type, stat_label, avg_key in stat_types:
        if stat_type == 'attendance':
            total = total_attendance
            avg = avg_attendance
        elif stat_type == 'new_people':
            total = total_new_people
            avg = avg_new_people
        elif stat_type == 'new_christians':
            total = total_new_christians
            avg = avg_new_christians
        elif stat_type == 'youth':
            total = total_youth
            avg = avg_youth
        elif stat_type == 'kids':
            total = total_kids
            avg = avg_kids
        elif stat_type == 'connect_groups':
            total = total_connect_groups
            avg = avg_connect_groups
        else:
            total = 0
            avg = 0
        
        results.append({
            "stat": stat_type,
            "label": stat_label,
            "year": year,
            "quarter": quarter,
            "campus": display_campus_name(campus),
            "total": total,
            "average": round(avg, 1),
            "count": entry_count
        })
    
    # Generate spoken summary
    quarter_names = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
    spoken_summary = f"Here's your {quarter_names[quarter]} {year} report for {display_campus_name(campus)} campus."
    
    return {
        "report": results,
        "text": spoken_summary,
        "review_type": "quarterly",
        "quarter": quarter,
        "year": year
    }

def generate_monthly_report(campus: str, year: int, month: int) -> dict:
    """Generate a monthly report for a specific month and year"""
    # Calculate month date range
    if month == 12:
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, 31)
    else:
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Get rows data
    rows = []
    if sheet:
        try:
            rows = safe_sheets_request(sheet.get_all_records)
        except Exception as e:
            logger.error(f"Failed to get stats from Google Sheets: {e}")
            rows = []
    
    if not rows:
        memory = load_conversation_memory()
        campus_history = memory.get("session_stats", {}).get(campus, [])
        if not campus_history:
            campus_capitalized = campus.title()
            campus_history = memory.get("session_stats", {}).get(campus_capitalized, [])
            if campus_history:
                campus = campus_capitalized
        rows = campus_history
    
    # Filter rows by campus and date range
    filtered_rows = []
    campus_normalized = normalize_campus(campus)
    
    for row in rows:
        row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
        if row_campus == campus_normalized or campus_normalized in row_campus:
            timestamp_str = row.get("Timestamp", "")
            if timestamp_str:
                try:
                    if "T" in timestamp_str:
                        row_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        row_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    if start_date <= row_date <= end_date:
                        filtered_rows.append(row)
                except Exception:
                    filtered_rows.append(row)
            else:
                filtered_rows.append(row)
    
    # Initialize all stat totals
    totals = {
        'total_attendance': 0,
        'first_time_visitors': 0,
        'visitors': 0,
        'information_gathered': 0,
        'first_time_christians': 0,
        'rededications': 0,
        'youth_attendance': 0,
        'youth_salvations': 0,
        'youth_new_people': 0,
        'kids_attendance': 0,
        'kids_leaders': 0,
        'new_kids': 0,
        'new_kids_salvations': 0,
        'connect_groups': 0,
        'dream_team': 0
    }
    
    # Initialize value lists for averages
    values = {key: [] for key in totals.keys()}
    
    entry_count = 0
    
    for entry in filtered_rows:
        if isinstance(entry, dict):
            def safe_int_stat(val):
                try:
                    if val is None or val == '':
                        return 0
                    return int(str(val).replace(',', '').strip())
                except Exception:
                    return 0
            
            # Extract all stats
            stats = {
                'total_attendance': safe_int_stat(entry.get('Total Attendance')),
                'first_time_visitors': safe_int_stat(entry.get('First Time Visitors')),
                'visitors': safe_int_stat(entry.get('Visitors')),
                'information_gathered': safe_int_stat(entry.get('Cards Back')),
                'first_time_christians': safe_int_stat(entry.get('First Time Christians')),
                'rededications': safe_int_stat(entry.get('Rededications')),
                'youth_attendance': safe_int_stat(entry.get('Youth Attendance')),
                'youth_salvations': safe_int_stat(entry.get('Youth Salvations')),
                'youth_new_people': safe_int_stat(entry.get('Youth New People')),
                'kids_attendance': safe_int_stat(entry.get('Kids Attendance') or entry.get('Kids Total')),
                'kids_leaders': safe_int_stat(entry.get('Kids Leaders')),
                'new_kids': safe_int_stat(entry.get('New Kids')),
                'new_kids_salvations': safe_int_stat(entry.get('New Kids Salvations')),
                'connect_groups': safe_int_stat(entry.get('Connect Groups')),
                'dream_team': safe_int_stat(entry.get('Dream Team'))
            }
            
            # Only count entries with at least one stat
            if any(stats.values()):
                entry_count += 1
            
            # Add to totals and value lists
            for key, value in stats.items():
                totals[key] += value
                if value > 0:
                                         values[key].append(value)
    
    # Calculate averages
    averages = {}
    for key in totals.keys():
        averages[key] = sum(values[key]) / len(values[key]) if values[key] else 0
    
    # Create comprehensive results with ALL stat headers
    results = []
    stat_definitions = [
        ('total_attendance', 'Total Attendance'),
        ('first_time_visitors', 'First Time Visitors'),
        ('visitors', 'Visitors'),
        ('new_people', 'New People'),  # Calculated field
        ('information_gathered', 'Cards Back'),
        ('first_time_christians', 'First Time Christians'),
        ('rededications', 'Rededications'),
        ('new_christians', 'New Christians'),  # Calculated field
        ('youth_attendance', 'Youth Attendance'),
        ('youth_salvations', 'Youth Salvations'),
        ('youth_new_people', 'Youth New People'),
        ('kids_attendance', 'Kids Total'),
        ('kids_leaders', 'Kids Leaders'),
        ('new_kids', 'New Kids'),
        ('new_kids_salvations', 'New Kids Salvations'),
        ('connect_groups', 'Connect Groups'),
        ('dream_team', 'Volunteers')  # Dream Team = Volunteers
    ]
    
    month_names = [
        '', 'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    
    for stat_key, stat_label in stat_definitions:
        # Handle calculated fields
        if stat_key == 'new_people':
            total = totals['first_time_visitors'] + totals['visitors']
            avg = (averages['first_time_visitors'] + averages['visitors']) if (averages['first_time_visitors'] > 0 or averages['visitors'] > 0) else 0
        elif stat_key == 'new_christians':
            total = totals['first_time_christians'] + totals['rededications']
            avg = (averages['first_time_christians'] + averages['rededications']) if (averages['first_time_christians'] > 0 or averages['rededications'] > 0) else 0
        else:
            total = totals.get(stat_key, 0)
            avg = averages.get(stat_key, 0)
        
        results.append({
            "stat": stat_key,
            "label": stat_label,
            "year": year,
            "month": month,
            "period": "monthly",
            "campus": display_campus_name(campus),
            "total": total,
            "average": round(avg, 1),
            "count": entry_count
        })
    
    # Add service breakdown if campus has multiple services
    service_breakdown = calculate_service_breakdown(filtered_rows, campus)
    service_breakdown_text = format_service_breakdown_for_display(service_breakdown, campus)
    
    # Generate spoken summary with service breakdown if available
    month_name = month_names[month]
    spoken_summary = f"Here's your {month_name} {year} monthly review for {display_campus_name(campus)}."
    
    # Add service breakdown to spoken summary if multiple services
    if service_breakdown and len(service_breakdown) > 1:
        total_by_services = sum(data['total'] for data in service_breakdown.values())
        if total_by_services > 0:
            breakdown_parts = []
            for service_time, data in service_breakdown.items():
                if data['total'] > 0:
                    breakdown_parts.append(f"{service_time}: {data['total']:,}")
            if breakdown_parts:
                spoken_summary += f" Service breakdown: {', '.join(breakdown_parts)}."
    
    return {
        "report": results,
        "text": spoken_summary,
        "review_type": "monthly",
        "month": month,
        "year": year,
        "service_breakdown": service_breakdown,
        "service_breakdown_text": service_breakdown_text
    }

def generate_mid_year_report(campus: str, year: int) -> dict:
    """Generate a mid-year report (January to June)"""
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 6, 30)
    
    # Get rows data
    rows = []
    if sheet:
        try:
            rows = safe_sheets_request(sheet.get_all_records)
        except Exception as e:
            logger.error(f"Failed to get stats from Google Sheets: {e}")
            rows = []
    
    if not rows:
        memory = load_conversation_memory()
        campus_history = memory.get("session_stats", {}).get(campus, [])
        if not campus_history:
            campus_capitalized = campus.title()
            campus_history = memory.get("session_stats", {}).get(campus_capitalized, [])
            if campus_history:
                campus = campus_capitalized
        rows = campus_history
    
    # Filter rows by campus and date range
    filtered_rows = []
    campus_normalized = normalize_campus(campus)
    
    for row in rows:
        row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
        if row_campus == campus_normalized or campus_normalized in row_campus:
            timestamp_str = row.get("Timestamp", "")
            if timestamp_str:
                try:
                    if "T" in timestamp_str:
                        row_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        row_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    if start_date <= row_date <= end_date:
                        filtered_rows.append(row)
                except Exception:
                    continue
    
    # Calculate stats for the mid-year period
    total_attendance = 0
    total_new_people = 0
    total_new_christians = 0
    total_youth = 0
    total_kids = 0
    total_connect_groups = 0
    entry_count = 0
    
    # Track values for average calculation
    attendance_values = []
    new_people_values = []
    new_christians_values = []
    youth_values = []
    kids_values = []
    connect_groups_values = []
    
    for entry in filtered_rows:
        if isinstance(entry, dict):
            def safe_int_stat(val):
                try:
                    if val is None or val == '':
                        return 0
                    return int(str(val).replace(',', '').strip())
                except Exception:
                    return 0
            attendance_val = safe_int_stat(entry.get('Total Attendance'))
            new_people_val = safe_int_stat(entry.get('New People'))
            new_christians_val = safe_int_stat(entry.get('New Christians'))
            youth_val = safe_int_stat(entry.get('Youth Attendance'))
            kids_val = safe_int_stat(entry.get('Kids Total'))
            connect_groups_val = safe_int_stat(entry.get('Connect Groups'))
            
            # Only count entries with at least one stat
            if any([attendance_val, new_people_val, new_christians_val, youth_val, kids_val, connect_groups_val]):
                entry_count += 1
            
            # Add to totals
            total_attendance += attendance_val
            total_new_people += new_people_val
            total_new_christians += new_christians_val
            total_youth += youth_val
            total_kids += kids_val
            total_connect_groups += connect_groups_val
            
            # Add to lists for averages (only if > 0)
            if attendance_val > 0:
                attendance_values.append(attendance_val)
            if new_people_val > 0:
                new_people_values.append(new_people_val)
            if new_christians_val > 0:
                new_christians_values.append(new_christians_val)
            if youth_val > 0:
                youth_values.append(youth_val)
            if kids_val > 0:
                kids_values.append(kids_val)
            if connect_groups_val > 0:
                connect_groups_values.append(connect_groups_val)
    
    # Calculate averages
    avg_attendance = sum(attendance_values) / len(attendance_values) if attendance_values else 0
    avg_new_people = sum(new_people_values) / len(new_people_values) if new_people_values else 0
    avg_new_christians = sum(new_christians_values) / len(new_christians_values) if new_christians_values else 0
    avg_youth = sum(youth_values) / len(youth_values) if youth_values else 0
    avg_kids = sum(kids_values) / len(kids_values) if kids_values else 0
    avg_connect_groups = sum(connect_groups_values) / len(connect_groups_values) if connect_groups_values else 0
    
    # Create results in the same format as annual report
    results = []
    stat_types = [
        ('attendance', 'Total Attendance', 'attendance'),
        ('new_people', 'New People', 'new_people'),
        ('new_christians', 'New Christians', 'new_christians'),
        ('youth', 'Youth Attendance', 'youth'),
        ('kids', 'Kids Total', 'kids'),
        ('connect_groups', 'Connect Groups', 'connect_groups'),
    ]
    
    for stat_type, stat_label, avg_key in stat_types:
        if stat_type == 'attendance':
            total = total_attendance
            avg = avg_attendance
        elif stat_type == 'new_people':
            total = total_new_people
            avg = avg_new_people
        elif stat_type == 'new_christians':
            total = total_new_christians
            avg = avg_new_christians
        elif stat_type == 'youth':
            total = total_youth
            avg = avg_youth
        elif stat_type == 'kids':
            total = total_kids
            avg = avg_kids
        elif stat_type == 'connect_groups':
            total = total_connect_groups
            avg = avg_connect_groups
        else:
            total = 0
            avg = 0
        
        results.append({
            "stat": stat_type,
            "label": stat_label,
            "year": year,
            "period": "mid_year",
            "campus": display_campus_name(campus),
            "total": total,
            "average": round(avg, 1),
            "count": entry_count
        })
    
    # Generate spoken summary
    spoken_summary = f"Here's your mid-year {year} report for {display_campus_name(campus)} campus."
    
    return {
        "report": results,
        "text": spoken_summary,
        "review_type": "mid_year",
        "year": year
    }

def generate_full_stat_report(campus: str, years: list) -> dict:
    # List of all stat types to include - comprehensive list
    stat_types = [
        ('attendance', 'Total Attendance', 'attendance'),
        ('first_time_visitors', 'First Time Visitors', 'first_time_visitors'),
        ('information_gathered', 'Cards Back', 'information_gathered'),
        ('new_christians', 'New Christians', 'new_christians'),
        ('rededications', 'Rededications', 'rededications'),
        ('youth_attendance', 'Youth Attendance', 'youth_attendance'),
        ('youth_salvations', 'Youth Salvations', 'youth_salvations'),
        ('youth_new_people', 'Youth New People', 'youth_new_people'),
        ('kids_attendance', 'Kids Attendance', 'kids_attendance'),
        ('kids_leaders', 'Kids Leaders', 'kids_leaders'),
        ('new_kids', 'New Kids', 'new_kids'),
        ('new_kids_salvations', 'New Kids Salvations', 'new_kids_salvations'),
        ('connect_groups', 'Connect Groups', 'connect_groups'),
        ('dream_team', 'Dream Team', 'dream_team'),
        ('tithe', 'Tithe', 'tithe'),
        ('baptisms', 'Baptisms', 'baptisms'),
        ('child_dedications', 'Child Dedications', 'child_dedications'),
        ('new_people', 'New People', 'new_people'),  # Keep for backward compatibility
    ]
    results = []
    for year in years:
        rows = []
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
            except Exception as e:
                logger.error(f"Failed to get stats from Google Sheets: {e}")
                rows = []
        if not rows:
            memory = load_conversation_memory()
            campus_history = memory.get("session_stats", {}).get(campus, [])
            if not campus_history:
                campus_capitalized = campus.title()
                campus_history = memory.get("session_stats", {}).get(campus_capitalized, [])
                if campus_history:
                    campus = campus_capitalized
            rows = campus_history
        year_stats = calculate_stats_for_year_range(rows, campus, year)
        for stat_type, stat_label, avg_key in stat_types:
            # Get total and average from the calculated stats
            total = year_stats.get(f'total_{stat_type}', 0)
            avg = year_stats.get('averages', {}).get(stat_type, 0)
            count = year_stats.get('total_entries', 0)
            
            results.append({
                "stat": stat_type,
                "label": stat_label,
                "year": year,
                "campus": display_campus_name(campus),
                "total": total,
                "average": round(avg, 1),
                "count": count
            })
    # Generate a spoken summary that matches the report data
    spoken_summary = generate_spoken_report_summary(results, campus, years)
    return {
        "report": results,
        "text": spoken_summary
    }

def generate_spoken_report_summary(results: list, campus: str, years: list) -> str:
    """Generate a simple, friendly response for annual/mid-year reviews"""
    campus_display = display_campus_name(campus)
    if not results:
        return f"No data found for {campus_display} campus."
    
    # Default to "annual review" unless it's clearly mid-year
    current_year = datetime.now().year
    current_month = datetime.now().month
    is_mid_year = any(year == current_year for year in years) and current_month <= 6  # Only call it mid-year if we're in first half
    
    if len(years) == 1:
        year_str = str(years[0])
        if is_mid_year:
            return f"Here's your mid-year review for {campus_display} campus in {year_str}."
        else:
            return f"Here's your annual review for {campus_display} campus in {year_str}."
    else:
        years_str = ", ".join(str(year) for year in sorted(years))
        return f"Here's your annual review for {campus_display} campus covering {years_str}."
    # After generating the summary string, replace large numbers with their word equivalents
    import re
    def replace_large_numbers(text):
        def repl(match):
            n = int(match.group(0).replace(',', ''))
            if n >= 1000:
                return num2words(n, to='number').replace('-', ' ')
            return match.group(0)
        return re.sub(r'\b\d{1,3}(?:,\d{3})+|\b\d{4,}\b', repl, text)
    summary = ... # existing summary generation logic
    summary = replace_large_numbers(summary)
    return summary

def detect_specific_stat_in_comparison(question: str) -> Optional[str]:
    """Detect which specific stat is being compared in the question"""
    question_lower = question.lower()
    
    # Map of stat keywords to stat types
    stat_keywords = {
        'attendance': ['attendance', 'total attendance', 'total', 'people'],
        'new_people': ['new people', 'newpeople', 'np', 'new', 'visitors'],
        'new_christians': ['new christians', 'christians', 'souls', 'salvations', 'conversions'],
        'youth': ['youth', 'youth attendance', 'teens', 'teenagers'],
        'kids': ['kids', 'children', 'kids total', 'children total'],
        'connect_groups': ['connect groups', 'connectgroups', 'groups', 'small groups', 'cell groups'],
        'dream_team': ['volunteers', 'dream team', 'serving', 'team']
    }
    
    # Check for specific stat mentions
    for stat_type, keywords in stat_keywords.items():
        for keyword in keywords:
            if keyword in question_lower:
                logger.info(f"[COMPARE] Detected specific stat: {stat_type} (keyword: {keyword})")
                return stat_type
    
    # If no specific stat detected, return None (will show all stats)
    logger.info(f"[COMPARE] No specific stat detected, will show all stats")
    return None

def generate_single_year_report(campus: str, year: int) -> dict:
    """Generate a report for a single year for comparison purposes"""
    # List of all stat types to include - comprehensive list
    stat_types = [
        ('attendance', 'Total Attendance', 'attendance'),
        ('first_time_visitors', 'First Time Visitors', 'first_time_visitors'),
        ('information_gathered', 'Cards Back', 'information_gathered'),
        ('new_christians', 'New Christians', 'new_christians'),
        ('rededications', 'Rededications', 'rededications'),
        ('youth_attendance', 'Youth Attendance', 'youth_attendance'),
        ('youth_salvations', 'Youth Salvations', 'youth_salvations'),
        ('youth_new_people', 'Youth New People', 'youth_new_people'),
        ('kids_attendance', 'Kids Attendance', 'kids_attendance'),
        ('kids_leaders', 'Kids Leaders', 'kids_leaders'),
        ('new_kids', 'New Kids', 'new_kids'),
        ('new_kids_salvations', 'New Kids Salvations', 'new_kids_salvations'),
        ('connect_groups', 'Connect Groups', 'connect_groups'),
        ('dream_team', 'Dream Team', 'dream_team'),
        ('tithe', 'Tithe', 'tithe'),
        ('baptisms', 'Baptisms', 'baptisms'),
        ('child_dedications', 'Child Dedications', 'child_dedications'),
        ('new_people', 'New People', 'new_people'),  # Keep for backward compatibility
    ]
    results = []
    rows = []
    if sheet:
        try:
            rows = safe_sheets_request(sheet.get_all_records)
        except Exception as e:
            logger.error(f"Failed to get stats from Google Sheets: {e}")
            rows = []
    if not rows:
        memory = load_conversation_memory()
        campus_history = memory.get("session_stats", {}).get(campus, [])
        if not campus_history:
            campus_capitalized = campus.title()
            campus_history = memory.get("session_stats", {}).get(campus_capitalized, [])
            if campus_history:
                campus = campus_capitalized
        rows = campus_history
    
    year_stats = calculate_stats_for_year_range(rows, campus, year)
    for stat_type, stat_label, avg_key in stat_types:
        # Get total and average from the calculated stats
        total = year_stats.get(f'total_{stat_type}', 0)
        avg = year_stats.get('averages', {}).get(stat_type, 0)
        count = year_stats.get('total_entries', 0)
        
        results.append({
            "stat": stat_type,
            "label": stat_label,
            "year": year,
            "campus": display_campus_name(campus),
            "total": total,
            "average": round(avg, 1),
            "count": count
        })
    
    return {
        "report": results,
        "text": f"Report for {display_campus_name(campus)} campus in {year}"
    }

def generate_targeted_comparison_report(campus: str, year: int, period_type: str, period_value: Optional[int], specific_stat: str) -> dict:
    """Generate a targeted report with only the specific stat for comparison"""
    # Generate the full report first
    if period_type == 'mid_year':
        full_report = generate_mid_year_report(campus, year)
    elif period_type == 'quarterly' and period_value:
        full_report = generate_quarterly_report(campus, year, period_value)
    elif period_type == 'monthly' and period_value:
        full_report = generate_monthly_report(campus, year, period_value)
    elif period_type == 'ytd':
        # Generate YTD report using the same logic as in handle_period_comparison_request
        current_date = datetime.now()
        start_date = datetime(year, 1, 1)
        
        # For YTD comparison, we want to compare the same period:
        # - Current year: Jan 1 to current date
        # - Past year: Jan 1 to the same day/month as current date
        if year == current_date.year:
            end_date = current_date
        else:
            # For past years, use the same day/month as current date
            try:
                end_date = datetime(year, current_date.month, current_date.day)
            except ValueError:
                # Get the last day of the month
                if current_date.month == 12:
                    end_date = datetime(year, 12, 31)
                else:
                    end_date = datetime(year, current_date.month + 1, 1) - timedelta(days=1)
        
        logger.info(f"[YTD DEBUG] Processing YTD for year {year}")
        logger.info(f"[YTD DEBUG] Start date: {start_date}, End date: {end_date}")
        logger.info(f"[YTD DEBUG] Current date: {current_date}")
        logger.info(f"[YTD DEBUG] Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"[YTD DEBUG] Period type: {period_type}")
        logger.info(f"[YTD DEBUG] Campus: {campus}")
        
        # Get all rows and filter by date range
        if sheet:
            rows = safe_sheets_request(sheet.get_all_records)
            logger.info(f"[YTD DEBUG] Retrieved {len(rows)} rows from Google Sheets")
        else:
            rows = []
            logger.info(f"[YTD DEBUG] No sheet available, using empty rows")
        
        # Filter rows for YTD period
        filtered_rows = []
        for row in rows:
            row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
            campus_normalized = normalize_campus(campus)
            
            # More flexible campus matching
            campus_match = (row_campus == campus_normalized or
                          campus_normalized in row_campus or
                          row_campus in campus_normalized or
                          campus_normalized.replace(" ", "") in row_campus.replace(" ", "") or
                          row_campus.replace(" ", "") in campus_normalized.replace(" ", ""))
            
            if campus_match:
                row_date = get_row_timestamp(row)
                if row_date != datetime.min and start_date <= row_date <= end_date:
                    filtered_rows.append(row)
                    logger.info(f"[YTD DEBUG] Included row: {row.get('Date', 'unknown')} - {row.get('Campus', 'unknown')} - Attendance: {row.get('Total Attendance', 0)}")
                else:
                    logger.info(f"[YTD DEBUG] Excluded row: {row.get('Date', 'unknown')} - {row.get('Campus', 'unknown')} - Date: {row_date} (not in range {start_date} to {end_date})")
        
        logger.info(f"[YTD DEBUG] Found {len(filtered_rows)} rows matching campus '{campus}' and date range")
        
        # Calculate stats for YTD period
        stats = calculate_stats_from_filtered_rows(filtered_rows)
        stats["year"] = year
        
        logger.info(f"[YTD DEBUG] Calculated YTD stats: {stats}")
        
        # Format as report
        full_report = {
            "report": [],
            "text": f"YTD Report for {display_campus_name(campus)} campus in {year}",
            "year": year,
            "campus": campus
        }
        
        # Convert stats to report format
        stat_types = [
            ('attendance', 'Total Attendance'),
            ('new_people', 'New People'),
            ('new_christians', 'New Christians'),
            ('youth_attendance', 'Youth Attendance'),
            ('kids_attendance', 'Kids Attendance'),
            ('connect_groups', 'Connect Groups'),
            ('dream_team', 'Dream Team')
        ]
        
        for stat_key, stat_label in stat_types:
            total = stats.get(f'total_{stat_key}', 0)
            avg = stats.get('averages', {}).get(stat_key, 0)
            count = stats.get('total_entries', 0)
            
            full_report["report"].append({
                "stat": stat_key,
                "label": stat_label,
                "year": year,
                "campus": display_campus_name(campus),
                "total": total,
                "average": round(avg, 1),
                "count": count
            })
    else:
        full_report = generate_single_year_report(campus, year)
    
    # Filter to only include the specific stat
    filtered_report = []
    for stat_entry in full_report.get('report', []):
        if stat_entry.get('stat') == specific_stat:
            filtered_report.append(stat_entry)
            break
    
    # Return the report with only the specific stat
    result = full_report.copy()
    result['report'] = filtered_report
    return result

def handle_period_comparison_request(question: str, campus: str, years: list, period_type: str, period_value: Optional[int] = None) -> dict:
    logger.info(f"[COMPARE] handle_period_comparison_request called with: question={question}, campus={campus}, years={years}, period_type={period_type}, period_value={period_value}")
    # period_type: 'mid_year' or 'quarterly'
    # period_value: quarter number if quarterly, None if mid_year
    
    # Detect which specific stat is being compared
    specific_stat = detect_specific_stat_in_comparison(question)
    logger.info(f"[COMPARE] Specific stat detected: {specific_stat}")
    
    try:
        reports = []
        for year in years:
            if specific_stat:
                # Generate targeted report with only the specific stat
                report = generate_targeted_comparison_report(campus, year, period_type, period_value, specific_stat)
            else:
                # Generate full report with all stats
                if period_type == 'mid_year':
                    report = generate_mid_year_report(campus, year)
                elif period_type == 'quarterly' and period_value:
                    report = generate_quarterly_report(campus, year, period_value)
                elif period_type == 'monthly' and period_value:
                    report = generate_monthly_report(campus, year, period_value)
                elif period_type == 'ytd':
                    # For YTD comparison, we need to compare the same period in both years
                    current_date = datetime.now()
                    start_date = datetime(year, 1, 1)
                    
                    # For YTD comparison, we want to compare the same period:
                    # - Current year: Jan 1 to current date
                    # - Past year: Jan 1 to the same day/month as current date
                    if year == current_date.year:
                        end_date = current_date
                    else:
                        # For past years, use the same day/month as current date
                        try:
                            end_date = datetime(year, current_date.month, current_date.day)
                        except ValueError:
                            # Get the last day of the month
                            if current_date.month == 12:
                                end_date = datetime(year, 12, 31)
                            else:
                                end_date = datetime(year, current_date.month + 1, 1) - timedelta(days=1)
                    
                    logger.info(f"[YTD DEBUG] Processing YTD for year {year}")
                    logger.info(f"[YTD DEBUG] Start date: {start_date}, End date: {end_date}")
                    logger.info(f"[YTD DEBUG] Current date: {current_date}")
                    logger.info(f"[YTD DEBUG] Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                    logger.info(f"[YTD DEBUG] Period type: {period_type}")
                    logger.info(f"[YTD DEBUG] Campus: {campus}")
                    
                    # Get all rows and filter by date range
                    if sheet:
                        rows = safe_sheets_request(sheet.get_all_records)
                        logger.info(f"[YTD DEBUG] Retrieved {len(rows)} rows from Google Sheets")
                    else:
                        rows = []
                        logger.info(f"[YTD DEBUG] No sheet available, using empty rows")
                    
                    # Filter rows for YTD period
                    filtered_rows = []
                    for row in rows:
                        row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
                        campus_normalized = normalize_campus(campus)
                        
                        # More flexible campus matching
                        campus_match = (row_campus == campus_normalized or
                                      campus_normalized in row_campus or
                                      row_campus in campus_normalized or
                                      campus_normalized.replace(" ", "") in row_campus.replace(" ", "") or
                                      row_campus.replace(" ", "") in campus_normalized.replace(" ", ""))
                        
                        if campus_match:
                            row_date = get_row_timestamp(row)
                            if row_date != datetime.min and start_date <= row_date <= end_date:
                                filtered_rows.append(row)
                                logger.info(f"[YTD DEBUG] Included row: {row.get('Date', 'unknown')} - {row.get('Campus', 'unknown')} - Attendance: {row.get('Total Attendance', 0)}")
                            else:
                                logger.info(f"[YTD DEBUG] Excluded row: {row.get('Date', 'unknown')} - {row.get('Campus', 'unknown')} - Date: {row_date} (not in range {start_date} to {end_date})")
                    
                    logger.info(f"[YTD DEBUG] Found {len(filtered_rows)} rows matching campus '{campus}' and date range")
                    
                    # Calculate stats for YTD period
                    stats = calculate_stats_from_filtered_rows(filtered_rows)
                    stats["year"] = year
                    
                    logger.info(f"[YTD DEBUG] Calculated YTD stats: {stats}")
                    
                    # Format as report
                    report = {
                        "report": [],
                        "text": f"YTD Report for {display_campus_name(campus)} campus in {year}",
                        "year": year,
                        "campus": campus
                    }
                    
                    # Convert stats to report format
                    stat_types = [
                        ('attendance', 'Total Attendance'),
                        ('new_people', 'New People'),
                        ('new_christians', 'New Christians'),
                        ('youth_attendance', 'Youth Attendance'),
                        ('kids_attendance', 'Kids Attendance'),
                        ('connect_groups', 'Connect Groups'),
                        ('dream_team', 'Dream Team')
                    ]
                    
                    for stat_key, stat_label in stat_types:
                        total = stats.get(f'total_{stat_key}', 0)
                        avg = stats.get('averages', {}).get(stat_key, 0)
                        count = stats.get('total_entries', 0)
                        
                        report["report"].append({
                            "stat": stat_key,
                            "label": stat_label,
                            "year": year,
                            "campus": display_campus_name(campus),
                            "total": total,
                            "average": round(avg, 1),
                            "count": count
                        })
                else:
                    report = generate_single_year_report(campus, year)
            reports.append(report)
        
        logger.info(f"[COMPARE] Generated {len(reports)} reports")
        
        # Compose comparison summary
        if specific_stat:
            stat_labels = {
                'attendance': 'Attendance',
                'new_people': 'New People', 
                'new_christians': 'New Christians',
                'youth': 'Youth',
                'kids': 'Kids',
                'connect_groups': 'Connect Groups',
                'dream_team': 'Volunteers'
            }
            stat_name = stat_labels.get(specific_stat, specific_stat)
            summary = f"Comparison of {stat_name} for {years[0]} and {years[1]} at {display_campus_name(campus)} campus."
        else:
            if period_type == 'ytd':
                summary = f"YTD (Year to Date) comparison for {years[0]} and {years[1]} at {display_campus_name(campus)} campus."
            else:
                summary = f"Comparison of {period_type.replace('_',' ')} "
                if period_type == 'quarterly' and period_value:
                    summary += f"Q{period_value} "
                summary += f"for {years[0]} and {years[1]} at {display_campus_name(campus)} campus."

        # PATCH: Ensure both reports have all stat keys
        stat_keys = ['attendance', 'new_people', 'new_christians', 'youth', 'kids', 'connect_groups']
        stat_labels = {
            'attendance': 'Attendance',
            'new_people': 'New People',
            'new_christians': 'New Christians',
            'youth': 'Youth',
            'kids': 'Kids',
            'connect_groups': 'Connect Groups'
        }
        
        def fill_missing_stats(report, year):
            stats_dict = {stat['stat']: stat for stat in report.get('report', [])}
            filled = []
            
            # If specific stat requested, only include that stat
            if specific_stat:
                stat = stats_dict.get(specific_stat, {
                    'stat': specific_stat,
                    'label': stat_labels.get(specific_stat, specific_stat.title()),
                    'year': year,
                    'total': 0,
                    'average': 0,
                    'count': 0,
                    'campus': campus,
                    'quarter': period_value if period_type == 'quarterly' else None
                })
                filled.append(stat)
            else:
                # Include all stats
                for key in stat_keys:
                    stat = stats_dict.get(key, {
                        'stat': key,
                        'label': stat_labels[key],
                        'year': year,
                        'total': 0,
                        'average': 0,
                        'count': 0,
                        'campus': campus,
                        'quarter': period_value if period_type == 'quarterly' else None
                    })
                    filled.append(stat)
            return filled
        
        # Fill missing stats for both reports (only if not specific stat)
        if not specific_stat:
            for i, year in enumerate(years):
                reports[i]['report'] = fill_missing_stats(reports[i], year)
        
        # Calculate percent changes
        percent_changes = {}
        if specific_stat:
            # Only calculate for the specific stat
            if len(reports[0]['report']) > 0 and len(reports[1]['report']) > 0:
                v1 = reports[0]['report'][0]['total']
                v2 = reports[1]['report'][0]['total']
                if v1 == 0 and v2 == 0:
                    pct = 0.0
                elif v1 == 0:
                    pct = 100.0
                else:
                    pct = ((v2 - v1) / abs(v1)) * 100.0
                percent_changes[specific_stat] = pct
        else:
            # Calculate for all stats
            for idx, key in enumerate(stat_keys):
                if idx < len(reports[0]['report']) and idx < len(reports[1]['report']):
                    v1 = reports[0]['report'][idx]['total']
                    v2 = reports[1]['report'][idx]['total']
                    if v1 == 0 and v2 == 0:
                        pct = 0.0
                    elif v1 == 0:
                        pct = 100.0
                    else:
                        pct = ((v2 - v1) / abs(v1)) * 100.0
                    percent_changes[key] = pct
        
        logger.info(f"[COMPARE] Calculated percent changes: {percent_changes}")
        
        # Compose and return the full comparison object
        result = {
            'comparison': True,
            'reports': reports,
            'percent_changes': percent_changes,
            'text': summary,
            'campus': campus,
            'insights': [summary],
            'years': years,
            'period_type': period_type,
            'period_value': period_value,
            'specific_stat': specific_stat
        }
        
        logger.info(f"[COMPARE] Returning comparison result with keys: {list(result.keys())}")
        logger.info(f"[COMPARE] Reports length: {len(result['reports'])}")
        logger.info(f"[COMPARE] Percent changes keys: {list(result['percent_changes'].keys())}")
        
        return result
        
    except Exception as e:
        logger.error(f"[COMPARE] Error in handle_period_comparison_request: {e}")
        # Return a fallback response
        return {
            'comparison': True,
            'reports': [],
            'percent_changes': {},
            'text': f"Error generating comparison for {campus} campus",
            'campus': campus,
            'insights': [f"Could not generate comparison: {str(e)}"],
            'years': years,
            'period_type': period_type,
            'period_value': period_value,
            'specific_stat': specific_stat
        }

def calculate_stats_from_filtered_rows(filtered_rows: List[dict]) -> dict:
    """Calculate stats from already filtered rows without additional filtering"""
    # Initialize all stat totals
    stats = {
        'attendance': 0,
        'first_time_visitors': 0,
        'information_gathered': 0,
        'new_christians': 0,
        'rededications': 0,
        'youth_attendance': 0,
        'youth_salvations': 0,
        'youth_new_people': 0,
        'kids_attendance': 0,
        'kids_leaders': 0,
        'new_kids': 0,
        'new_kids_salvations': 0,
        'connect_groups': 0,
        'dream_team': 0,
        'tithe': 0,
        'baptisms': 0,
        'child_dedications': 0,
        'new_people': 0  # Keep for backward compatibility
    }
    
    # Track values for average calculation
    averages = {}
    entry_count = 0
    
    for entry in filtered_rows:
        if isinstance(entry, dict):
            def safe_int_stat(val):
                try:
                    if val is None or val == '':
                        return 0
                    return int(str(val).replace(',', '').strip())
                except Exception:
                    return 0
            
            # Extract all available stats with flexible field name matching
            def get_stat_value(field_names):
                """Get stat value from multiple possible field names"""
                for field_name in field_names:
                    value = entry.get(field_name)
                    if value is not None and value != '':
                        return safe_int_stat(value)
                return 0
            
            stat_values = {
                'attendance': get_stat_value(['Total Attendance', 'attendance']),
                'first_time_visitors': get_stat_value(['First Time Visitors', 'ft_visitors']),
                'visitors': get_stat_value(['Visitors', 'visitors']),
                'information_gathered': get_stat_value(['Cards Back', 'info_collected']),
                'first_time_christians': get_stat_value(['First Time Christians', 'salvations']),
                'rededications': get_stat_value(['Rededications', 'rededications']),
                'youth_attendance': get_stat_value(['Youth Attendance', 'youth']),
                'youth_salvations': get_stat_value(['Youth Salvations', 'youth_salvations']),
                'youth_new_people': get_stat_value(['Youth New People', 'youth_new']),
                'kids_attendance': get_stat_value(['Kids Attendance', 'Kids Total', 'kids']),
                'kids_leaders': get_stat_value(['Kids Leaders', 'kids_leaders']),
                'new_kids': get_stat_value(['New Kids', 'new_kids']),
                'new_kids_salvations': get_stat_value(['New Kids Salvations', 'new_kids_salvations']),
                'connect_groups': get_stat_value(['Connect Groups', 'groups']),
                'dream_team': get_stat_value(['Dream Team', 'team', 'Volunteers', 'volunteers']),
                'tithe': get_stat_value(['Tithe']),
                'baptisms': get_stat_value(['Baptisms']),
                'child_dedications': get_stat_value(['Child Dedications'])
            }
            
            # Calculate new people as First Time Visitors + Visitors
            new_people_total = stat_values['first_time_visitors'] + stat_values['visitors']
            stat_values['new_people'] = new_people_total
            
            # Calculate new christians as First Time Christians + Rededications
            new_christians_total = stat_values['first_time_christians'] + stat_values['rededications']
            stat_values['new_christians'] = new_christians_total
            
            # Only count entries with at least one stat
            if any(stat_values.values()):
                entry_count += 1
            
            # Add to totals
            for stat_name, value in stat_values.items():
                stats[f'total_{stat_name}'] = stats.get(f'total_{stat_name}', 0) + value
                
                # Track for averages (only if > 0)
                if value > 0:
                    if stat_name not in averages:
                        averages[stat_name] = []
                    averages[stat_name].append(value)
    
    # Calculate averages
    avg_stats = {}
    for stat_name, values in averages.items():
        if values:
            avg_stats[stat_name] = round(sum(values) / len(values), 1)
        else:
            avg_stats[stat_name] = 0
    
    return {
        "total_entries": entry_count,
        **stats,
        "averages": avg_stats
    }

def calculate_service_breakdown(filtered_rows: List[dict], campus: str) -> dict:
    """Calculate attendance breakdown by service times for a campus using actual Google Sheets columns"""
    print(f"\n[DEBUG SERVICE BREAKDOWN] ========== Starting for campus: {campus} ==========")
    print(f"[DEBUG SERVICE BREAKDOWN] Processing {len(filtered_rows)} rows")
    for idx, row in enumerate(filtered_rows):  # Show ALL rows now
        print(f"[DEBUG ROW {idx+1}] Date: {row.get('Date')}, Campus: {row.get('Campus')}, 9AM: {row.get('9:00 AM')}, 10AM: {row.get('10:00 AM')}, 11AM: {row.get('11:00 AM')}, 5PM: {row.get('5:00 PM')}, 5:30PM: {row.get('5:30 PM')}")
    service_times = get_campus_service_times(campus)
    print(f"[DEBUG SERVICE BREAKDOWN] Service times for {campus}: {service_times}")
    service_breakdown = {}
    kids_service_breakdown = {}
    
    # Map service times to actual Google Sheets column names
    SERVICE_COLUMN_MAPPING = {
        '9:00 AM': '9:00 AM',
        '10:00 AM': '10:00 AM', 
        '11:00 AM': '11:00 AM',
        '5:00 PM': '5:00 PM',
        '5:30 PM': '5:30 PM'
    }
    
    # Map kids service times to Google Sheets columns
    KIDS_COLUMN_MAPPING = {
        '9:00 AM': 'Kids 9:00 AM',
        '10:00 AM': 'Kids 10:00 AM', 
        '11:00 AM': 'Kids 11:00 AM',
        '5:00 PM': 'Kids 5:00 PM',
        '5:30 PM': 'Kids 5:30 PM'
    }
    
    # Initialize service breakdown structure
    for service_time in service_times:
        service_breakdown[service_time] = {
            'total': 0,
            'count': 0,
            'average': 0.0,
            'entries': []
        }
        kids_service_breakdown[service_time] = {
            'total': 0,
            'count': 0,
            'average': 0.0,
            'entries': []
        }
    
    # Process each row to extract service-specific data
    for entry in filtered_rows:
        if isinstance(entry, dict):
            total_attendance = 0
            try:
                total_attendance = int(str(entry.get('Total Attendance', 0)).replace(',', '').strip())
            except:
                total_attendance = 0
            
            # Extract service-specific attendance from actual Google Sheets columns
            service_specific_data = {}
            kids_specific_data = {}
            service_total = 0
            
            for service_time in service_times:
                # Adult attendance
                column_name = SERVICE_COLUMN_MAPPING.get(service_time, service_time)
                if column_name in entry:
                    try:
                        attendance = int(str(entry[column_name]).replace(',', '').strip())
                        if attendance > 0:
                            service_specific_data[service_time] = attendance
                            service_total += attendance
                    except:
                        pass
                
                # Kids attendance
                kids_column_name = KIDS_COLUMN_MAPPING.get(service_time)
                if kids_column_name and kids_column_name in entry:
                    try:
                        kids_attendance = int(str(entry[kids_column_name]).replace(',', '').strip())
                        if kids_attendance > 0:
                            kids_specific_data[service_time] = kids_attendance
                    except:
                        pass
            
            # If we have service-specific data from Google Sheets columns, use it
            if service_specific_data:
                for service_time, attendance in service_specific_data.items():
                    if service_time in service_breakdown:
                        service_breakdown[service_time]['total'] += attendance
                        service_breakdown[service_time]['count'] += 1
                        service_breakdown[service_time]['entries'].append(attendance)
            
            # Process kids data
            if kids_specific_data:
                for service_time, kids_attendance in kids_specific_data.items():
                    if service_time in kids_service_breakdown:
                        kids_service_breakdown[service_time]['total'] += kids_attendance
                        kids_service_breakdown[service_time]['count'] += 1
                        kids_service_breakdown[service_time]['entries'].append(kids_attendance)
            
            # If no service-specific data but we have total attendance, distribute proportionally
            elif total_attendance > 0 and len(service_times) > 0:
                # Use default distribution based on typical service patterns
                # This can be customized per campus in the future
                default_ratios = {
                    '9:00 AM': 0.35,   # 35% typically at 9am
                    '10:00 AM': 1.0,   # 100% for single service campuses
                    '11:00 AM': 0.65,  # 65% typically at 11am  
                    '5:00 PM': 0.15    # 15% typically at evening service
                }
                
                if len(service_times) == 1:
                    # Single service campus - all attendance goes to that service
                    service_time = service_times[0]
                    attendance = total_attendance
                    service_breakdown[service_time]['total'] += attendance
                    service_breakdown[service_time]['count'] += 1
                    service_breakdown[service_time]['entries'].append(attendance)
                else:
                    # Multiple services - distribute based on ratios
                    remaining_attendance = total_attendance
                    
                    for i, service_time in enumerate(service_times):
                        if i == len(service_times) - 1:
                            # Last service gets remainder
                            attendance = remaining_attendance
                        else:
                            ratio = default_ratios.get(service_time, 1.0 / len(service_times))
                            attendance = int(total_attendance * ratio)
                            remaining_attendance -= attendance
                        
                        if attendance > 0:
                            service_breakdown[service_time]['total'] += attendance
                            service_breakdown[service_time]['count'] += 1
                            service_breakdown[service_time]['entries'].append(attendance)
    
    # Calculate averages for adult attendance
    for service_time in service_breakdown:
        if service_breakdown[service_time]['count'] > 0:
            service_breakdown[service_time]['average'] = round(
                service_breakdown[service_time]['total'] / service_breakdown[service_time]['count'], 1
            )
    
    # Calculate averages for kids attendance
    for service_time in kids_service_breakdown:
        if kids_service_breakdown[service_time]['count'] > 0:
            kids_service_breakdown[service_time]['average'] = round(
                kids_service_breakdown[service_time]['total'] / kids_service_breakdown[service_time]['count'], 1
            )
    
    print(f"[DEBUG SERVICE BREAKDOWN] Final results for {campus}:")
    for service_time, data in service_breakdown.items():
        print(f"  {service_time}: total={data['total']}, count={data['count']}, avg={data['average']}")
    print(f"[DEBUG SERVICE BREAKDOWN] ========== End for campus: {campus} ==========\n")
    
    return {
        'adult': service_breakdown,
        'kids': kids_service_breakdown
    }

def enhance_attendance_with_service_breakdown(stats: dict, filtered_rows: List[dict], campus: str) -> dict:
    """Enhance attendance stats with service time breakdown"""
    breakdown_data = calculate_service_breakdown(filtered_rows, campus)
    
    # Add both adult and kids service breakdown to the stats
    stats['service_breakdown'] = breakdown_data['adult']
    stats['kids_service_breakdown'] = breakdown_data['kids']
    
    # Add summary information
    total_services = sum(data['total'] for data in breakdown_data['adult'].values())
    stats['total_attendance_by_services'] = total_services
    
    # If the service breakdown total doesn't match the original total attendance,
    # use the original (it might be more accurate)
    if 'total_attendance' in stats and stats['total_attendance'] != total_services:
        stats['attendance_note'] = f"Service breakdown total ({total_services}) differs from reported total ({stats.get('total_attendance', 0)})"
    
    return stats

def format_service_breakdown_for_display(service_breakdown: dict, campus: str) -> str:
    """Format service breakdown for display in reports"""
    if not service_breakdown:
        return ""
    
    campus_name = display_campus_name(campus)
    breakdown_text = f"\n\n{campus_name} Service Breakdown:\n"
    
    total_all_services = 0
    for service_time, data in service_breakdown.items():
        total = data['total']
        average = data['average']
        count = data['count']
        
        breakdown_text += f"  • {service_time}: {total:,} total"
        if count > 1:
            breakdown_text += f" (avg: {average:.1f} over {count} services)"
        breakdown_text += "\n"
        
        total_all_services += total
    
    breakdown_text += f"  Total across all services: {total_all_services:,}"
    
    return breakdown_text

def extract_stats_with_service_context(text: str, campus: str) -> Dict[str, Any]:
    """Enhanced stats extraction that recognizes service-specific attendance"""
    # Start with the existing extraction
    stats = extract_stats_with_context(text, campus)
    
    # Try to parse service-specific attendance
    service_attendance = parse_service_attendance(text, campus)
    
    if service_attendance:
        # If we found service-specific data, add it to the stats
        stats['service_breakdown'] = service_attendance
        
        # Calculate total attendance from services
        total_from_services = sum(service_attendance.values())
        
        # If no total attendance was found, use the service total
        if not stats.get('Total Attendance') and total_from_services > 0:
            stats['Total Attendance'] = total_from_services
        
        # Add individual service columns for storage
        for service_time, attendance in service_attendance.items():
            column_name = f"{service_time.replace(':', '').replace(' ', '_').lower()}_attendance"
            stats[column_name] = attendance
    
    return stats

def calculate_stats_for_year_range(rows: List[dict], campus: str, start_year: int, end_year: Optional[int] = None) -> dict:
    """Calculate stats for a specific year range"""
    if end_year is None:
        end_year = start_year
    
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31, 23, 59, 59)
    
    # Normalize campus name for comparison
    campus_normalized = normalize_campus(campus)
    filtered_rows = []
    unique_campuses = set()
    
    logger.info(f"[YEAR_RANGE] Filtering for {campus} ({campus_normalized}) from {start_year} to {end_year}")
    logger.info(f"[YEAR_RANGE] Date range: {start_date} to {end_date}")
    
    for row in rows:
        row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
        unique_campuses.add(row_campus)
        
        # More flexible campus matching
        campus_match = (row_campus == campus_normalized or
                       campus_normalized in row_campus or
                       row_campus in campus_normalized or
                       campus_normalized.replace(" ", "") in row_campus.replace(" ", "") or
                       row_campus.replace(" ", "") in campus_normalized.replace(" ", ""))
        
        if campus_match:
            # Use the improved get_row_timestamp function
            row_date = get_row_timestamp(row)
            
            if row_date != datetime.min and start_date <= row_date <= end_date:
                filtered_rows.append(row)
                logger.info(f"[YEAR_RANGE] INCLUDED: {row.get('Date', 'No Date')} - {row.get('Campus', 'No Campus')} - {row_date}")
            else:
                logger.info(f"[YEAR_RANGE] EXCLUDED: {row.get('Date', 'No Date')} - {row.get('Campus', 'No Campus')} - {row_date}")
    
    logger.info(f"[YEAR_RANGE] Found {len(filtered_rows)} rows for {campus} in {start_year}-{end_year}")
    logger.info(f"[YEAR_RANGE] Unique campuses in data: {sorted(unique_campuses)}")
    
    # Use the comprehensive calculate_stats_from_filtered_rows function
    stats = calculate_stats_from_filtered_rows(filtered_rows)
    stats["year"] = start_year
    return stats

def extract_stat_from_row(entry, stat_type):
    # If entry is a dict, use flexible field name matching
    if isinstance(entry, dict):
        stat_fields = {
            'attendance': ["Total Attendance", "Attendance", "attendance", "total_attendance"],
            'new_people': ["New People", "NewPeople", "new_people", "First Time Visitors", "Visitors"],
            'new_christians': ["New Christians", "Souls", "new_christians", "First Time Christians", "Rededications"],
            'youth': ["Youth Attendance", "Youth", "youth_attendance"],
            'kids': ["Kids Total", "Kids", "kids_total"],
            'connect_groups': ["Connect Groups", "ConnectGroups", "connect_groups"],
            'dream_team': ["Volunteers", "volunteers", "Dream Team", "dream_team"]
        }
        for field in stat_fields.get(stat_type, []):
            val = entry.get(field)
            if val not in (None, ""):
                try:
                    return int(str(val).replace(",", "").strip())
                except Exception:
                    continue
        return 0
    # If entry is a list or tuple, use positional mapping
    elif isinstance(entry, (list, tuple)):
        # Detect format: if 3rd column is a date, it's standard; if 2nd column is campus, it's link-logged
        def is_date(val):
            try:
                if not val or not isinstance(val, str):
                    return False
                parts = val.split("-")
                return len(parts) >= 3 and len(parts[0]) == 4
            except Exception:
                return False
        # Standard: [Timestamp, Date, Campus, ...]
        if len(entry) >= 12 and is_date(entry[1]):
            mapping = {
                'attendance': 3,
                'new_people': 4,
                'new_christians': 5,
                'youth': 6,
                'kids': 9,
                'connect_groups': 11,
                'dream_team': None  # Not present
            }
        # Link-logged: [Timestamp, Campus, Attendance, ...]
        elif len(entry) >= 8 and not is_date(entry[1]):
            mapping = {
                'attendance': 2,
                'new_people': 3,
                'new_christians': 4,
                'youth': 5,
                'kids': 6,
                'connect_groups': 7,
                'dream_team': None  # Not present
            }
        else:
            return 0
        idx = mapping.get(stat_type)
        if idx is not None and idx < len(entry):
            val = entry[idx]
            if val not in (None, ""):
                try:
                    return int(str(val).replace(",", "").strip())
                except Exception:
                    return 0
        return 0
    return 0

def get_weekly_campus_comparison_data():
    """Get weekly comparison data across all campuses for senior leaders/admins (always last 7 days)"""
    try:
        if not sheet:
            return []
        
        # Get all records
        rows = safe_sheets_request(sheet.get_all_records)
        if not rows:
            return []
        
        # Always use last 7 days for weekly comparison
        now = datetime.now()
        start_date = now - timedelta(days=7)
        end_date = now
        
        # Get active campuses (excluding 'all_campuses' special entry)
        campuses_db = load_campuses_database()
        active_campuses = []
        for campus_id, campus_info in campuses_db.get('campuses', {}).items():
            if campus_info.get('active', False) and not campus_info.get('special', False):
                active_campuses.append({
                    'id': campus_id,
                    'name': campus_info.get('display_name', campus_id),
                    'full_name': campus_info.get('name', campus_id)
                })
        
        comparison_data = []
        
        for campus_info in active_campuses:
            campus_id = campus_info['id']
            campus_name = campus_info['name']
            
            # Filter rows for this campus
            campus_normalized = normalize_campus(campus_id)
            campus_rows = []
            for row in rows:
                row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
                if row_campus == campus_normalized or campus_normalized in row_campus:
                    timestamp_str = row.get("Timestamp", "")
                    if timestamp_str:
                        try:
                            if "T" in timestamp_str:
                                row_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            else:
                                row_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            
                            if start_date <= row_date <= end_date:
                                campus_rows.append(row)
                        except Exception:
                            continue
            
            # Calculate campus stats
            total_attendance = 0
            total_new_people = 0
            total_new_christians = 0
            total_dream_team = 0
            entry_count = 0
            
            for row in campus_rows:
                total_attendance += safe_int(row.get('Total Attendance', 0))
                total_new_people += safe_int(row.get('New People', 0))
                total_new_christians += safe_int(row.get('New Christians', 0))
                total_dream_team += safe_int(row.get('Dream Team', 0))
                entry_count += 1
            
            # Calculate Dream Team percentage (dream team as % of attendance)
            dream_team_percentage = (total_dream_team / total_attendance * 100) if total_attendance > 0 else 0
            
            # Determine status based on performance
            status = determine_campus_status(total_attendance, total_new_people, total_new_christians, dream_team_percentage, entry_count)
            
            comparison_data.append({
                'campus': campus_name,
                'attendance': total_attendance,
                'new_people': total_new_people,
                'salvations': total_new_christians,
                'dream_team_percent': round(dream_team_percentage, 1),
                'status': status,
                'entries': entry_count
            })
        
        # Sort by attendance (highest first)
        comparison_data.sort(key=lambda x: x['attendance'], reverse=True)
        
        return comparison_data
        
    except Exception as e:
        logger.error(f"Campus comparison data error: {e}")
        return []

def determine_campus_status(attendance, new_people, salvations, dream_team_percent, entries):
    """Determine campus status based on performance metrics"""
    if entries == 0:
        return "No Data"
    
    # Calculate performance score (out of 100)
    score = 0
    
    # Attendance factor (30% of score)
    if attendance >= 400:
        score += 30
    elif attendance >= 200:
        score += 20
    elif attendance >= 100:
        score += 15
    else:
        score += 5
    
    # New People factor (25% of score)
    avg_new_people = new_people / entries if entries > 0 else 0
    if avg_new_people >= 8:
        score += 25
    elif avg_new_people >= 5:
        score += 20
    elif avg_new_people >= 2:
        score += 15
    else:
        score += 5
    
    # Salvations factor (25% of score)
    avg_salvations = salvations / entries if entries > 0 else 0
    if avg_salvations >= 3:
        score += 25
    elif avg_salvations >= 1:
        score += 20
    elif avg_salvations >= 0.5:
        score += 15
    else:
        score += 5
    
    # Dream Team factor (20% of score)
    if dream_team_percent >= 30:
        score += 20
    elif dream_team_percent >= 25:
        score += 15
    elif dream_team_percent >= 20:
        score += 10
    else:
        score += 5
    
    # Determine status based on total score
    if score >= 85:
        return "Excellent"
    elif score >= 65:
        return "Good"
    elif score >= 45:
        return "Fair"
    else:
        return "Needs Attention"

# Insights function removed - will be rebuilt from scratch

def calculate_date_range(date_filter, custom_start_date, custom_end_date, now):
    """Calculate start and end dates based on filter type"""
    print(f"[DEBUG] calculate_date_range called with: date_filter={date_filter}, custom_start_date={custom_start_date}, custom_end_date={custom_end_date}")
    try:
        if date_filter == 'last_7_days':
            start_date = now - timedelta(days=7)
            end_date = now
        elif date_filter == 'last_30_days':
            start_date = now - timedelta(days=30)
            end_date = now
        elif date_filter == 'last_90_days':
            start_date = now - timedelta(days=90)
            end_date = now
        elif date_filter == 'last_6_months':
            start_date = now - timedelta(days=180)  # Approximately 6 months
            end_date = now
        elif date_filter == 'last_12_months':
            start_date = now - timedelta(days=365)  # 12 months
            end_date = now
        elif date_filter == 'ytd':
            # Year to date
            start_date = datetime(now.year, 1, 1)
            end_date = now
        elif date_filter == 'year_to_date':
            # Year to date (alternative name)
            start_date = datetime(now.year, 1, 1)
            end_date = now
        elif date_filter == 'this_year':
            # This year (January 1 to December 31)
            start_date = datetime(now.year, 1, 1)
            end_date = datetime(now.year, 12, 31, 23, 59, 59)
            print(f"[DEBUG] this_year case: start_date={start_date}, end_date={end_date}")
        elif date_filter == 'last_year':
            # Previous full year
            start_date = datetime(now.year - 1, 1, 1)
            end_date = datetime(now.year - 1, 12, 31, 23, 59, 59)
        elif date_filter == 'custom' and custom_start_date and custom_end_date:
            # Custom date range
            start_date = datetime.strptime(custom_start_date, '%Y-%m-%d')
            end_date = datetime.strptime(custom_end_date, '%Y-%m-%d')
            # Set end date to end of day
            end_date = end_date.replace(hour=23, minute=59, second=59)
        else:
            # Default to last 30 days
            start_date = now - timedelta(days=30)
            end_date = now
        
        return start_date, end_date
    except Exception as e:
        logger.error(f"Date range calculation error: {e}")
        # Default fallback
        return now - timedelta(days=30), now

def get_monthly_tithe_from_finance_tab(campus, start_date, end_date):
    """Get monthly tithe totals from the Tithe tab for charts"""
    try:
        if not finance_sheet:
            return {}
        
        rows = safe_sheets_request(finance_sheet.get_all_records)
        monthly_tithe = {}
        
        # Convert datetime to date if necessary
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        
        for row in rows:
            try:
                date_str = row.get('Date', '')
                if not date_str:
                    continue
                
                # Parse date
                if isinstance(date_str, str):
                    row_date = None
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            row_date = datetime.strptime(date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                    if not row_date:
                        continue
                else:
                    continue
                
                # Check if in date range
                if not (start_date <= row_date <= end_date):
                    continue
                
                # Check campus match (skip filtering for roll-up views)
                if campus not in ['all_campuses', 'australia']:
                    row_campus = str(row.get('Campus', '')).strip().lower().replace(' ', '_')
                    campus_normalized = campus.lower().replace(' ', '_')
                    if row_campus != campus_normalized:
                        continue
                
                # Get month key and accumulate tithe
                month_key = row_date.strftime('%Y-%m')
                if month_key not in monthly_tithe:
                    monthly_tithe[month_key] = 0
                
                total = float(row.get('Total', 0) or 0)
                monthly_tithe[month_key] += total
            except Exception as e:
                continue
        
        return monthly_tithe
    except Exception as e:
        logger.error(f"Error fetching monthly tithe from Tithe tab: {str(e)}")
        return {}

def get_tithe_breakdown(campus, start_date, end_date):
    """Get tithe breakdown from the Tithe tab for a specific campus and date range"""
    try:
        if not finance_sheet:
            return {'general': 0, 'trust': 0, 'online': 0, 'text': 0, 'total': 0}
        
        rows = safe_sheets_request(finance_sheet.get_all_records)
        breakdown = {'general': 0, 'trust': 0, 'online': 0, 'text': 0, 'total': 0, 'count': 0}
        
        # Convert datetime to date if necessary
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        
        for row in rows:
            try:
                date_str = row.get('Date', '')
                if not date_str:
                    continue
                
                # Parse date
                if isinstance(date_str, str):
                    row_date = None
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            row_date = datetime.strptime(date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                    if not row_date:
                        continue
                else:
                    continue
                
                # Check if in date range
                if not (start_date <= row_date <= end_date):
                    continue
                
                # Check campus match (skip filtering for roll-up views)
                if campus not in ['all_campuses', 'australia']:
                    row_campus = str(row.get('Campus', '')).strip().lower().replace(' ', '_')
                    campus_normalized = campus.lower().replace(' ', '_')
                    if row_campus != campus_normalized:
                        continue
                
                # Accumulate breakdown (column names match Google Sheets exactly)
                breakdown['general'] += float(row.get('General', 0) or 0)
                breakdown['trust'] += float(row.get('Trust', 0) or 0)
                breakdown['online'] += float(row.get('Online Giving', 0) or 0)
                breakdown['text'] += float(row.get('Text', 0) or 0)
                breakdown['total'] += float(row.get('Total', 0) or 0)
                breakdown['count'] += 1
            except Exception as e:
                continue
        
        # Calculate averages
        if breakdown['count'] > 0:
            for key in ['general', 'trust', 'online', 'text', 'total']:
                breakdown[key] = round(breakdown[key] / breakdown['count'], 2)
        
        return breakdown
    except Exception as e:
        logger.error(f"Error fetching tithe breakdown: {str(e)}")
        return {'general': 0, 'trust': 0, 'online': 0, 'text': 0, 'total': 0}

def get_dashboard_data(campus, date_filter='last_12_months', custom_start_date='', custom_end_date='', show_previous_year=False):
    """
    Get dashboard data - SIMPLE CLEAN VERSION
    Reads from Google Sheets:
    - Column B: Date (service date)
    - Column D: Total Attendance
    - Column I: First Time Christians
    - Column J: Rededications  
    - Column K: First Time Visitors
    - Column L: Visitors
    """
    try:
        # Try to get data from Google Sheets first, fallback to local data
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
                if rows is None:  # Rate limited or failed
                    rows = load_local_data()
                    data_source = "Local Data (Google Sheets rate limited)"
                else:
                    data_source = "Google Sheets"
            except Exception as e:
                logger.warning(f"Google Sheets failed, using local data: {e}")
                rows = load_local_data()
                data_source = "Local Data (Google Sheets failed)"
        else:
            rows = load_local_data()
            data_source = "Local Data (Google Sheets not available)"
        
        if not rows:
            return {"stats": {}, "recent_entries": [], "trends": {}, "data_source": data_source}
        
        # Calculate date range first to avoid redundant computation
        now = datetime.now()
        start_date, end_date = calculate_date_range(date_filter, custom_start_date, custom_end_date, now)
        
        # Pre-normalize campus for single-pass filtering
        campus_normalized = None
        skip_campus_filter = campus in ['all_campuses', 'australia']
        if not skip_campus_filter:
            campus_normalized = normalize_campus(campus)
        
        # Pre-compile date parsing (most common format first for speed)
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
        
        # Combine campus and date filtering into single pass for performance
        filtered_rows = []
        for row in rows:
            # Campus filtering (if needed)
            if not skip_campus_filter:
                row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
                campus_match = (row_campus == campus_normalized or
                               campus_normalized in row_campus or
                               row_campus in campus_normalized or
                               campus_normalized.replace(" ", "") in row_campus.replace(" ", "") or
                               row_campus.replace(" ", "") in campus_normalized.replace(" ", ""))
                if not campus_match:
                    continue
            
            # Date filtering (combined with campus check)
            date_str = row.get("Date", "")
            if not date_str or not isinstance(date_str, str):
                continue
            
            # Optimized date parsing - try most common format first
            row_date = None
            for fmt in date_formats:
                try:
                    row_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            
            # Check if date is valid and within range
            if row_date and start_date <= row_date <= end_date:
                filtered_rows.append(row)
        
        # Ensure we have data to process
        if not filtered_rows:
            return {"stats": {}, "recent_entries": [], "trends": {}, "data_source": data_source}
        
        period_stats = {
            # Main attendance
            'total_attendance': 0,
            
            # Campus database
            'total_people': 0,
            
                    # Service time totals removed
            
            # New people breakdown
            'first_time_visitors': 0,
            'visitors': 0,
            'information_gathered': 0,
            'new_people': 0,  # Calculated: first_time + visitors
            
            # Christian decisions breakdown
            'first_time_christians': 0,
            'rededications': 0,
            'new_christians': 0,  # Calculated: first_time + rededications
            
            # Youth breakdown
            'youth_attendance': 0,
            'youth_salvations': 0,
            'youth_new_people': 0,
            
            # Kids breakdown
            'kids_attendance': 0,
            'kids_leaders': 0,
            'new_kids': 0,
            'new_kids_salvations': 0,
            'salvation_cards_returned': 0,
            
            # Ministry metrics
            'connect_groups': 0,
            'dream_team': 0,
            
            # Financial data
            'tithe': 0,
            
            # Special events
            'baptisms': 0,
            'child_dedications': 0,
            
            # System tracking
            'entry_count': 0,
            
            # Backward compatibility
            'kids_total': 0,  # Will map to kids_attendance
            'volunteers': 0  # Will map to dream_team
        }
        
        recent_entries = []
        monthly_trends = {}
        
        processed_count = 0
        valid_timestamps = 0
        
        # Helper function to get stat value with flexible field names
        def get_stat_value(row, field_names):
            for field in field_names:
                value = row.get(field)
                if value is not None and value != '' and str(value).strip() != '':
                    # Handle numeric values and convert to int
                    try:
                        return safe_int(value)
                    except (ValueError, TypeError):
                        continue
            return 0
        
        # Helper function to calculate total attendance from service times
        def calculate_total_attendance(row):
            """Calculate total attendance by summing all service time columns"""
            service_times = ['9:00 AM', '10:00 AM', '11:00 AM', '5:00 PM', '5:30 PM']
            total = 0
            for service_time in service_times:
                value = row.get(service_time, '')
                if value is not None and value != '' and str(value).strip() != '':
                    try:
                        total += safe_int(value)
                    except (ValueError, TypeError):
                        continue
            return total
        
        # Helper function to calculate total kids attendance from service times
        def calculate_kids_attendance(row):
            """Calculate total kids attendance by summing all kids service time columns"""
            kids_service_times = ['Kids 9:00 AM', 'Kids 10:00 AM', 'Kids 11:00 AM', 'Kids 5:00 PM', 'Kids 5:30 PM']
            total = 0
            for service_time in kids_service_times:
                value = row.get(service_time, '')
                if value is not None and value != '' and str(value).strip() != '':
                    try:
                        total += safe_int(value)
                    except (ValueError, TypeError):
                        continue
            return total
        
        # Initialize monthly trends tracking
        monthly_trends = {}
        
        for row in filtered_rows:
            processed_count += 1
            try:
                # Get date from row (already filtered, so should be valid)
                row_date = get_row_timestamp(row)
                if row_date and row_date != datetime.min:
                    valid_timestamps += 1
                    
                    # Add to recent entries for display
                    if len(recent_entries) < 10:
                        # Calculate New People and New Christians for recent entries
                        first_time_visitors = get_stat_value(row, ['First Time Visitors', 'first_time_visitors'])
                        visitors = get_stat_value(row, ['Visitors', 'visitors'])
                        new_people = first_time_visitors + visitors
                        
                        first_time_christians = get_stat_value(row, ['First Time Christians', 'first_time_christians'])
                        rededications = get_stat_value(row, ['Rededications', 'rededications'])
                        new_christians = first_time_christians + rededications
                        
                        recent_entries.append({
                            'date': row_date.strftime('%Y-%m-%d'),
                            'campus': row.get('Campus', 'Unknown'),
                            'attendance': calculate_total_attendance(row),
                            'new_people': new_people,
                            'new_christians': new_christians
                        })
                    
                    # Calculate monthly trends
                    month_key = row_date.strftime('%Y-%m')
                    if month_key not in monthly_trends:
                        monthly_trends[month_key] = {
                            'attendance': 0,
                            'count': 0,
                            'new_people': 0,
                            'new_christians': 0,
                            'tithe': 0
                        }
                    
                    attendance = calculate_total_attendance(row)
                    
                    # Calculate New People from First Time Visitors + Visitors
                    first_time_visitors = get_stat_value(row, ['First Time Visitors', 'first_time_visitors'])
                    visitors = get_stat_value(row, ['Visitors', 'visitors'])
                    new_people = first_time_visitors + visitors
                    
                    # Calculate New Christians from First Time Christians + Rededications
                    first_time_christians = get_stat_value(row, ['First Time Christians', 'first_time_christians'])
                    rededications = get_stat_value(row, ['Rededications', 'rededications'])
                    new_christians = first_time_christians + rededications
                    
                    monthly_trends[month_key]['attendance'] += attendance
                    monthly_trends[month_key]['count'] += 1
                    monthly_trends[month_key]['new_people'] += new_people
                    monthly_trends[month_key]['new_christians'] += new_christians
                    
                    # Add tithe data to monthly trends
                    tithe_value = row.get('Tithe', '')
                    if tithe_value and str(tithe_value).strip() != '':
                        try:
                            tithe_clean = str(tithe_value).replace('$', '').replace(',', '').strip()
                            if tithe_clean:
                                monthly_trends[month_key]['tithe'] += float(tithe_clean)
                        except (ValueError, TypeError):
                            pass
                    
                    # Main attendance
                    period_stats['total_attendance'] += attendance
                    
                    # Campus database size
                    total_people = get_stat_value(row, ['Total People in Campus', 'total_people_in_campus'])
                    period_stats['total_people'] = max(period_stats['total_people'], total_people)  # Use max value (most recent)
                    
                                         # Service time processing removed
                    
                    # New people breakdown
                    first_time = get_stat_value(row, ['First Time Visitors', 'first_time_visitors'])
                    visitors = get_stat_value(row, ['Visitors', 'visitors'])
                    period_stats['first_time_visitors'] += first_time
                    period_stats['visitors'] += visitors
                    info_gathered_value = get_stat_value(row, ['Cards Back', 'information_gathered'])
                    if row.get('Campus') == 'Adelaide City' and row.get('Date') == '2025-10-05':
                        print(f"[DEBUG] Adelaide City 2025-10-05 - Raw row data: {row}")
                        print(f"[DEBUG] Cards Back value: {info_gathered_value}")
                        print(f"[DEBUG] Row keys: {list(row.keys())}")
                    period_stats['information_gathered'] += info_gathered_value
                    
                    # Debug: Track total information_gathered for Adelaide City
                    if row.get('Campus') == 'Adelaide City':
                        print(f"[DEBUG] Adelaide City running total - information_gathered: {period_stats['information_gathered']}, entry_count: {period_stats['entry_count']}")
                    
                    # Christian decisions breakdown
                    first_time_christians = get_stat_value(row, ['First Time Christians', 'first_time_christians'])
                    rededications = get_stat_value(row, ['Rededications', 'rededications'])
                    
                    # Debug: Check First Time Christians value for Adelaide City
                    if row.get('Campus') == 'Adelaide City' and row.get('Date') == '2025-10-05':
                        raw_value = row.get('First Time Christians', 'NOT_FOUND')
                        print(f"[DEBUG] Adelaide City 2025-10-05 - Raw First Time Christians: {raw_value} (type: {type(raw_value)})")
                        print(f"[DEBUG] Adelaide City 2025-10-05 - After get_stat_value: {first_time_christians}")
                        print(f"[DEBUG] Adelaide City 2025-10-05 - After safe_int: {safe_int(raw_value) if raw_value != 'NOT_FOUND' else 'N/A'}")
                    
                    period_stats['first_time_christians'] += first_time_christians
                    period_stats['rededications'] += rededications
                        
                    # Youth breakdown
                    period_stats['youth_attendance'] += get_stat_value(row, ['Youth Attendance', 'youth_attendance'])
                    period_stats['youth_salvations'] += get_stat_value(row, ['Youth Salvations', 'youth_salvations'])
                    period_stats['youth_new_people'] += get_stat_value(row, ['Youth New People', 'youth_new_people'])
                    
                    # Kids breakdown
                    period_stats['kids_attendance'] += calculate_kids_attendance(row)
                    period_stats['kids_leaders'] += get_stat_value(row, ['Kids Leaders', 'kids_leaders'])
                    period_stats['new_kids'] += get_stat_value(row, ['New Kids', 'new_kids'])
                    period_stats['new_kids_salvations'] += get_stat_value(row, ['New Kids Salvations', 'new_kids_salvations'])
                    
                    # Salvation Cards Returned
                    period_stats['salvation_cards_returned'] += get_stat_value(row, ['Salvation Cards Returned', 'salvation_cards_returned'])
                    
                    # Ministry metrics
                    period_stats['connect_groups'] += get_stat_value(row, ['Connect Groups', 'connect_groups'])
                    period_stats['dream_team'] += get_stat_value(row, ['Dream Team', 'dream_team', 'Volunteers', 'volunteers'])
                    
                    # Financial data - handle empty strings and convert to number
                    tithe_value = row.get('Tithe', '')
                    if tithe_value and str(tithe_value).strip() != '':
                        try:
                            # Remove any currency symbols and commas, then convert to float
                            tithe_clean = str(tithe_value).replace('$', '').replace(',', '').strip()
                            if tithe_clean:
                                period_stats['tithe'] += float(tithe_clean)
                        except (ValueError, TypeError):
                            pass
                    
                    # Additional metrics that might be missing
                    # Baptisms and child dedications
                    baptisms = int(row.get('Baptisms', 0) or 0)
                    child_dedications = int(row.get('Child Dedications', 0) or 0)
                    period_stats['baptisms'] += baptisms
                    period_stats['child_dedications'] += child_dedications
                    
                    # System tracking
                    period_stats['entry_count'] += 1
                    
                    # Backward compatibility
                    period_stats['kids_total'] = period_stats['kids_attendance']
                    period_stats['volunteers'] = period_stats['dream_team']
                    
            except Exception as e:
                print(f"[DEBUG] Error processing row: {e}")
                continue
        
        # Calculate derived stats
        period_stats['new_people'] = period_stats['first_time_visitors'] + period_stats['visitors']
        period_stats['new_christians'] = period_stats['first_time_christians'] + period_stats['rededications']
        
        # Total people comes from Google Sheet only - no hardcoded defaults
        
        # Calculate tithe YTD totals from Tithe tab (not Stats tab)
        # YTD = Year-To-Date (January 1 to current date of current year)
        now = datetime.now()
        ytd_start = datetime(now.year, 1, 1)
        ytd_end = now
        
        # Get YTD tithe from Tithe tab
        tithe_ytd_breakdown = get_tithe_breakdown(campus, ytd_start, ytd_end)
        period_stats['tithe_ytd'] = tithe_ytd_breakdown.get('total', 0)
        print(f"[DEBUG TITHE YTD] YTD total from Tithe tab: ${period_stats['tithe_ytd']:,.2f}")
        
        # Initialize previous_year_averages if not defined yet
        if 'previous_year_averages' not in locals():
            previous_year_averages = {}
        period_stats['tithe_previous_year'] = sum(prev_data.get('total_tithe', 0) for prev_data in previous_year_averages.values())
        
        # Build YTD monthly data for charts (January through current month of current year)
        # This is separate from filtered_rows and always shows full YTD
        ytd_monthly_trends = {}
        
        print(f"[DEBUG YTD] Building YTD data from {ytd_start.strftime('%Y-%m-%d')} to {ytd_end.strftime('%Y-%m-%d')}")
        print(f"[DEBUG YTD] Total rows to process: {len(rows)}")
        
        ytd_rows_processed = 0
        ytd_rows_matched_campus = 0
        ytd_rows_matched_date = 0
        
        for row in rows:
            try:
                row_date = get_row_timestamp(row)
                if not row_date or row_date == datetime.min:
                    continue
                
                ytd_rows_processed += 1
                
                # Only process YTD data (Jan 1 to now of current year)
                if not (ytd_start <= row_date <= ytd_end):
                    continue
                
                ytd_rows_matched_date += 1
                
                # Filter by campus if needed (skip filtering for roll-up views)
                if campus not in ['all_campuses', 'australia']:
                    row_campus = normalize_campus(row.get('Campus', ''))
                    campus_normalized = normalize_campus(campus)
                    if row_campus != campus_normalized:
                        continue
                
                ytd_rows_matched_campus += 1
                
                # Calculate YTD monthly trends for charts
                month_key = row_date.strftime('%Y-%m')
                if month_key not in ytd_monthly_trends:
                    ytd_monthly_trends[month_key] = {
                        'attendance': 0,
                        'count': 0,
                        'new_people': 0,
                        'new_christians': 0,
                        'tithe': 0,
                        'youth_attendance': 0,
                        'kids_attendance': 0
                    }
                
                attendance = calculate_total_attendance(row)
                first_time_visitors = get_stat_value(row, ['First Time Visitors', 'first_time_visitors'])
                visitors = get_stat_value(row, ['Visitors', 'visitors'])
                new_people = first_time_visitors + visitors
                first_time_christians = get_stat_value(row, ['First Time Christians', 'first_time_christians'])
                rededications = get_stat_value(row, ['Rededications', 'rededications'])
                new_christians = first_time_christians + rededications
                youth_attendance = get_stat_value(row, ['Youth Attendance', 'youth_attendance'])
                kids_attendance = calculate_kids_attendance(row)
                
                ytd_monthly_trends[month_key]['attendance'] += attendance
                ytd_monthly_trends[month_key]['count'] += 1
                ytd_monthly_trends[month_key]['new_people'] += new_people
                ytd_monthly_trends[month_key]['new_christians'] += new_christians
                ytd_monthly_trends[month_key]['youth_attendance'] += youth_attendance
                ytd_monthly_trends[month_key]['kids_attendance'] += kids_attendance
                
                tithe_value = row.get('Tithe', '')
                if tithe_value and str(tithe_value).strip() != '':
                    try:
                        tithe_clean = str(tithe_value).replace('$', '').replace(',', '').strip()
                        if tithe_clean:
                            ytd_monthly_trends[month_key]['tithe'] += float(tithe_clean)
                    except (ValueError, TypeError):
                        pass
                        
            except Exception as e:
                continue
        
        print(f"[DEBUG YTD] Rows processed: {ytd_rows_processed}, matched date: {ytd_rows_matched_date}, matched campus: {ytd_rows_matched_campus}")
        print(f"[DEBUG YTD] YTD monthly trends found: {list(ytd_monthly_trends.keys())}")
        
        # Fetch monthly tithe data from Tithe tab (not Stats tab)
        monthly_tithe_from_finance = get_monthly_tithe_from_finance_tab(campus, ytd_start, ytd_end)
        print(f"[DEBUG TITHE] Monthly tithe from Tithe tab: {monthly_tithe_from_finance}")
        
        # Calculate monthly averages from YTD data (for charts)
        monthly_averages = {}
        
        # Use YTD data for chart monthly averages
        # Calculate averages per WEEK, not per entry
        for month_key, month_data in ytd_monthly_trends.items():
            if month_data['count'] > 0:
                # Use actual service count for more accurate averages
                services_count = month_data['count']
                
                # Get tithe from Tithe tab instead of Stats tab
                tithe_from_finance_tab = monthly_tithe_from_finance.get(month_key, 0)
                
                monthly_averages[month_key] = {
                    'avg_attendance': round(month_data['attendance'] / services_count, 1),
                    'total_attendance': month_data['attendance'],
                    'services_count': services_count,
                    'avg_new_people': round(month_data['new_people'] / services_count, 1),
                    'total_new_people': month_data['new_people'],
                    'avg_new_christians': round(month_data['new_christians'] / services_count, 1),
                    'total_new_christians': month_data['new_christians'],
                    'avg_youth_attendance': round(month_data['youth_attendance'] / services_count, 1),
                    'total_youth_attendance': month_data['youth_attendance'],
                    'avg_kids_attendance': round(month_data['kids_attendance'] / services_count, 1),
                    'total_kids_attendance': month_data['kids_attendance'],
                    'total_tithe': tithe_from_finance_tab  # Use Tithe tab data, not Stats tab
                }
        
        # Then, add missing months with zero data to ensure complete range
        if start_date and end_date:
            current_date = start_date.replace(day=1)
            end_month = end_date.replace(day=1)
            
            while current_date <= end_month:
                month_key = current_date.strftime('%Y-%m')
                if month_key not in monthly_averages:
                    monthly_averages[month_key] = {
                        'avg_attendance': 0,
                        'total_attendance': 0,
                        'services_count': 0,
                        'avg_new_people': 0,
                        'total_new_people': 0,
                        'avg_youth_attendance': 0,
                        'total_youth_attendance': 0,
                        'avg_kids_attendance': 0,
                        'total_kids_attendance': 0,
                        'avg_new_christians': 0,
                        'total_new_christians': 0
                    }
                
                # Move to next month
                current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        print(f"[DEBUG] Total attendance calculated: {period_stats['total_attendance']}")
        print(f"[DEBUG] Total people in campus: {period_stats['total_people']}")
        print(f"[DEBUG] Total new people calculated: {period_stats['new_people']}")
        print(f"[DEBUG] Total new christians calculated: {period_stats['new_christians']}")
        print(f"[DEBUG] Monthly averages: {monthly_averages}")
        
        # Prepare chart data with monthly averages
        # Chart data will be generated later with complete month range
        
        # Calculate averages for all metrics
        # Calculate number of weeks in the date range for proper averaging
        date_range_days = (end_date - start_date).days
        num_weeks = max(1, date_range_days / 7)  # At least 1 week
        
        if period_stats['entry_count'] > 0:
            # Main metrics - average per SERVICE for attendance (for monthly/period reports)
            period_stats['avg_attendance'] = period_stats['total_attendance'] / period_stats['entry_count']
            period_stats['avg_total_people'] = period_stats['total_people']  # This is a single value per campus, not averaged
            
            # New people breakdown - use entry_count (these are totals, not averages)
            period_stats['avg_first_time_visitors'] = period_stats['first_time_visitors'] / period_stats['entry_count']
            period_stats['avg_visitors'] = period_stats['visitors'] / period_stats['entry_count']
            period_stats['avg_information_gathered'] = period_stats['information_gathered'] / period_stats['entry_count']
            period_stats['avg_new_people'] = period_stats['new_people'] / period_stats['entry_count']
            
            # Christian decisions breakdown - use entry_count (these are totals, not averages)
            period_stats['avg_first_time_christians'] = period_stats['first_time_christians'] / period_stats['entry_count']
            period_stats['avg_rededications'] = period_stats['rededications'] / period_stats['entry_count']
            period_stats['avg_new_christians'] = period_stats['new_christians'] / period_stats['entry_count']
            
            # Youth breakdown - average per SERVICE for attendance
            period_stats['avg_youth_attendance'] = period_stats['youth_attendance'] / period_stats['entry_count']
            period_stats['avg_youth_salvations'] = period_stats['youth_salvations'] / period_stats['entry_count']
            period_stats['avg_youth_new_people'] = period_stats['youth_new_people'] / period_stats['entry_count']
            
            # Kids breakdown - average per SERVICE for attendance
            period_stats['avg_kids_attendance'] = period_stats['kids_attendance'] / period_stats['entry_count']
            period_stats['avg_kids_leaders'] = period_stats['kids_leaders'] / period_stats['entry_count']
            period_stats['avg_new_kids'] = period_stats['new_kids'] / period_stats['entry_count']
            period_stats['avg_new_kids_salvations'] = period_stats['new_kids_salvations'] / period_stats['entry_count']
            
            # Ministry metrics - average per SERVICE
            period_stats['avg_connect_groups'] = period_stats['connect_groups'] / period_stats['entry_count']
            period_stats['avg_dream_team'] = period_stats['dream_team'] / period_stats['entry_count']
            
            # Financial data - average per SERVICE
            period_stats['avg_tithe'] = period_stats['tithe'] / period_stats['entry_count']
            
            # Special events - use entry_count
            period_stats['avg_baptisms'] = period_stats['baptisms'] / period_stats['entry_count']
            period_stats['avg_child_dedications'] = period_stats['child_dedications'] / period_stats['entry_count']
            
                    # Service time averages removed
            
            # Backward compatibility
            period_stats['avg_kids_total'] = period_stats['kids_total'] / period_stats['entry_count']
            period_stats['avg_volunteers'] = period_stats['volunteers'] / period_stats['entry_count']
        else:
            # Zero out all averages if no entries
            period_stats['avg_attendance'] = 0
            period_stats['avg_total_people'] = 0
            period_stats['avg_first_time_visitors'] = 0
            period_stats['avg_visitors'] = 0
            period_stats['avg_information_gathered'] = 0
            period_stats['avg_new_people'] = 0
            period_stats['avg_first_time_christians'] = 0
            period_stats['avg_rededications'] = 0
            period_stats['avg_new_christians'] = 0
            period_stats['avg_youth_attendance'] = 0
            period_stats['avg_youth_salvations'] = 0
            period_stats['avg_youth_new_people'] = 0
            period_stats['avg_kids_attendance'] = 0
            period_stats['avg_kids_leaders'] = 0
            period_stats['avg_new_kids'] = 0
            period_stats['avg_new_kids_salvations'] = 0
            period_stats['avg_connect_groups'] = 0
            period_stats['avg_dream_team'] = 0
            period_stats['avg_tithe'] = 0
            period_stats['avg_baptisms'] = 0
            period_stats['avg_child_dedications'] = 0
            period_stats['avg_service_9am'] = 0
            period_stats['avg_service_10am'] = 0
            period_stats['avg_service_11am'] = 0
            period_stats['avg_service_5pm'] = 0
            period_stats['avg_kids_total'] = 0
            period_stats['avg_volunteers'] = 0
        
        # Sort trends by month (show more months for longer date ranges)
        trend_months = min(12, max(6, int((end_date - start_date).days / 30)))  # Adaptive trend period
        sorted_trends = dict(sorted(monthly_trends.items())[-trend_months:])
        
        # Prepare dashboard data for insights generation
        dashboard_data_for_insights = {
            'stats': period_stats,
            'trends': sorted_trends,
            'campus': campus
        }
        
        # Calculate service breakdown for campuses with multiple services
        service_breakdown = {}
        kids_service_breakdown = {}
        if campus != 'all_campuses':
            breakdown_data = calculate_service_breakdown(filtered_rows, campus)
            service_breakdown = breakdown_data.get('adult', {})
            kids_service_breakdown = breakdown_data.get('kids', {})
        
        # Generate chart data - only show months with actual data
        chart_data = {
            'labels': [],
            'attendance': [],
            'new_people': [],
            'new_christians': [],
            'youth': [],
            'kids': [],
            'tithe_ytd': [],
            'tithe_previous_year': [],
            'attendance_previous_year': [],
            'tithe_labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        }
        
        # Add previous year data (always calculate when available)
        previous_year_data = {
            'attendance': [],
            'new_people': [],
            'new_christians': [],
            'tithe': []
        }
        
        # Calculate previous year averages (always calculate when available)
        previous_year_averages = {}
        
        # Calculate date range for previous year (same months, but previous year)
        prev_start_date = start_date.replace(year=start_date.year - 1)
        prev_end_date = end_date.replace(year=end_date.year - 1)
        
        print(f"[DEBUG PREV YEAR] Calculating previous year data for range: {prev_start_date.strftime('%Y-%m-%d')} to {prev_end_date.strftime('%Y-%m-%d')}")
        print(f"[DEBUG PREV YEAR] Campus filter: '{campus}'")
        print(f"[DEBUG PREV YEAR] Total rows available: {len(rows)}")
        
        # Filter rows for previous year
        prev_filtered_rows = []
        for row in rows:
            try:
                date_str = row.get("Date", "")
                if not date_str:
                    continue
                
                if isinstance(date_str, str):
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            row_date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        continue
                else:
                    continue
                
                # Check if row is within previous year date range
                if prev_start_date <= row_date <= prev_end_date:
                    prev_filtered_rows.append(row)
                    
            except Exception:
                continue
        
        print(f"[DEBUG PREV YEAR] Found {len(prev_filtered_rows)} rows for previous year")
        print(f"[DEBUG PREV YEAR] Looking for campus: {campus} (normalized: {normalize_campus(campus)})")
        if len(prev_filtered_rows) > 0:
            print(f"[DEBUG PREV YEAR] Sample row: {prev_filtered_rows[0]}")
        
        # Debug: Show unique campuses in previous year data
        prev_year_campuses = set()
        for row in prev_filtered_rows:
            row_campus = row.get('Campus', '')
            if row_campus:
                prev_year_campuses.add(f"{row_campus} -> {normalize_campus(row_campus)}")
        print(f"[DEBUG PREV YEAR] Unique campuses found: {prev_year_campuses}")
        
        # Calculate monthly trends for previous year
        prev_monthly_trends = {}
        prev_rows_matched_campus = 0
        for row in prev_filtered_rows:
            try:
                row_date = None
                date_str = row.get("Date", "")
                if isinstance(date_str, str):
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            row_date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                
                if not row_date:
                    continue
                
                # Filter by campus if not all_campuses
                if campus not in ['all_campuses', 'australia']:
                    row_campus = normalize_campus(row.get('Campus', ''))
                    campus_normalized = normalize_campus(campus)
                    if row_campus != campus_normalized:
                        continue
                
                prev_rows_matched_campus += 1
                
                # Calculate monthly trends
                month_key = row_date.strftime('%Y-%m')
                if month_key not in prev_monthly_trends:
                    prev_monthly_trends[month_key] = {
                        'attendance': 0,
                        'count': 0,
                        'new_people': 0,
                        'new_christians': 0,
                        'tithe': 0
                    }
                
                # Calculate attendance by summing service time columns
                service_times = ['9:00 AM', '10:00 AM', '11:00 AM', '5:00 PM', '5:30 PM']
                attendance = 0
                for service_time in service_times:
                    value = row.get(service_time, '')
                    if value is not None and value != '' and str(value).strip() != '':
                        try:
                            attendance += int(str(value).replace(',', '').strip())
                        except (ValueError, TypeError):
                            continue
                
                first_time_visitors = get_stat_value(row, ['First Time Visitors', 'first_time_visitors'])
                visitors = get_stat_value(row, ['Visitors', 'visitors'])
                new_people = first_time_visitors + visitors
                first_time_christians = get_stat_value(row, ['First Time Christians', 'first_time_christians'])
                rededications = get_stat_value(row, ['Rededications', 'rededications'])
                new_christians = first_time_christians + rededications
                
                prev_monthly_trends[month_key]['attendance'] += attendance
                prev_monthly_trends[month_key]['count'] += 1
                prev_monthly_trends[month_key]['new_people'] += new_people
                prev_monthly_trends[month_key]['new_christians'] += new_christians
                
                # Add tithe data to previous year trends
                tithe_value = row.get('Tithe', '')
                if tithe_value and str(tithe_value).strip() != '':
                    try:
                        tithe_clean = str(tithe_value).replace('$', '').replace(',', '').strip()
                        if tithe_clean:
                            prev_monthly_trends[month_key]['tithe'] += float(tithe_clean)
                    except (ValueError, TypeError):
                        pass
                
            except Exception as e:
                continue
        
        print(f"[DEBUG PREV YEAR] Rows matched campus filter: {prev_rows_matched_campus}")
        print(f"[DEBUG PREV YEAR] Monthly trends found: {list(prev_monthly_trends.keys())}")
        
        # Calculate previous year monthly averages - include ALL months
        for month_key, month_data in prev_monthly_trends.items():
            if month_data['count'] > 0:
                previous_year_averages[month_key] = {
                    'avg_attendance': round(month_data['attendance'] / month_data['count'], 1),
                    'avg_new_people': round(month_data['new_people'] / month_data['count'], 1),
                    'avg_new_christians': round(month_data['new_christians'] / month_data['count'], 1),
                    'total_tithe': month_data['tithe']
                }
        
        # Add missing months with zero data to ensure complete range
        prev_current_date = prev_start_date.replace(day=1)
        prev_end_month = prev_end_date.replace(day=1)
        
        while prev_current_date <= prev_end_month:
            prev_month_key = prev_current_date.strftime('%Y-%m')
            if prev_month_key not in previous_year_averages:
                previous_year_averages[prev_month_key] = {
                    'avg_attendance': 0,
                    'avg_new_people': 0,
                    'avg_new_christians': 0,
                    'total_tithe': 0
                }
            
            # Move to next month
            prev_current_date = (prev_current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        print(f"[DEBUG PREV YEAR] Rows matched campus filter: {prev_rows_matched_campus}")
        print(f"[DEBUG PREV YEAR] Previous year monthly trends: {list(prev_monthly_trends.keys())}")
        print(f"[DEBUG PREV YEAR] Previous year averages: {previous_year_averages}")
        
        # Get current month to exclude from charts
        current_month = datetime.now().strftime('%Y-%m')
        
        # Always show YTD (Year-To-Date) for charts - January to current month
        print(f"[DEBUG] Chart generation - monthly_averages: {monthly_averages}")
        print(f"[DEBUG] Chart generation - current_month: {current_month}")
        
        # For charts, always show YTD (Jan through current month), not just the filtered date range
        now = datetime.now()
        ytd_start = datetime(now.year, 1, 1)  # January 1st of current year
        ytd_end = now.replace(day=1)  # Current month
        
        if ytd_start and ytd_end:
            current_date = ytd_start.replace(day=1)  # Start from January
            end_month = ytd_end.replace(day=1)  # End at current month
            
            while current_date <= end_month:
                month_key = current_date.strftime('%Y-%m')
                
                # Format month label (e.g., "2025-01" -> "Jan 2025")
                month_name = current_date.strftime('%b %Y')
                chart_data['labels'].append(month_name)
                
                # Get data for this month from averages, or use zeros if no data
                month_data = monthly_averages.get(month_key, {})
                
                attendance_val = month_data.get('avg_attendance', 0)
                new_people_val = month_data.get('avg_new_people', 0)
                new_christians_val = month_data.get('avg_new_christians', 0)
                youth_val = month_data.get('avg_youth_attendance', 0)
                kids_val = month_data.get('avg_kids_attendance', 0)
                tithe_val = month_data.get('total_tithe', 0)
                
                # For current month, show average based on number of actual entries
                # 1 entry: show actual data
                # 2 entries: divide total by 2
                # 3 entries: divide total by 3, etc.
                if month_key == current_month and month_data.get('services_count', 0) > 0:
                    # Get the number of actual services/entries we have for this month
                    num_entries = month_data.get('services_count', 0)
                    
                    # For 2+ entries, calculate average by dividing sum by number of entries
                    if num_entries >= 2:
                        # Use total values and divide by number of actual entries
                        total_attendance = month_data.get('total_attendance', 0)
                        total_new_people = month_data.get('total_new_people', 0)
                        total_new_christians = month_data.get('total_new_christians', 0)
                        total_youth = month_data.get('total_youth_attendance', 0)
                        total_kids = month_data.get('total_kids_attendance', 0)
                        
                        # Divide by number of actual entries to get average
                        attendance_val = total_attendance / num_entries if total_attendance > 0 else attendance_val
                        new_people_val = total_new_people / num_entries if total_new_people > 0 else new_people_val
                        new_christians_val = total_new_christians / num_entries if total_new_christians > 0 else new_christians_val
                        youth_val = total_youth / num_entries if total_youth > 0 else youth_val
                        kids_val = total_kids / num_entries if total_kids > 0 else kids_val
                        tithe_val = tithe_val / num_entries if tithe_val > 0 else tithe_val
                        
                        print(f"[DEBUG] Current month {month_key}: {num_entries} entries - showing average (total÷{num_entries})")
                    else:
                        print(f"[DEBUG] Current month {month_key}: {num_entries} entry - showing actual data")
                
                chart_data['attendance'].append(attendance_val)
                chart_data['new_people'].append(new_people_val)
                chart_data['new_christians'].append(new_christians_val)
                chart_data['youth'].append(youth_val)
                chart_data['kids'].append(kids_val)
                chart_data['tithe_ytd'].append(tithe_val)
                
                # Add previous year data (always add when available)
                # Find corresponding month in previous year
                prev_month_key = f"{current_date.year - 1}-{current_date.strftime('%m')}"
                prev_data = previous_year_averages.get(prev_month_key, {})
                
                previous_year_data['attendance'].append(prev_data.get('avg_attendance', 0))
                previous_year_data['new_people'].append(prev_data.get('avg_new_people', 0))
                previous_year_data['new_christians'].append(prev_data.get('avg_new_christians', 0))
                previous_year_data['tithe'].append(prev_data.get('total_tithe', 0))
                chart_data['tithe_previous_year'].append(prev_data.get('total_tithe', 0))
                chart_data['attendance_previous_year'].append(prev_data.get('avg_attendance', 0))
                
                print(f"[DEBUG] Added to chart: {month_name} - attendance: {attendance_val}, new_people: {new_people_val}, new_christians: {new_christians_val}")
                
                # Move to next month
                current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)

        
        # Always include previous year data if it has content
        final_previous_year_data = None
        if previous_year_data and any(previous_year_data.values()):
            final_previous_year_data = previous_year_data
            print(f"[DEBUG] Returning previous year data: {final_previous_year_data}")
        else:
            print(f"[DEBUG] No previous year data to return: {previous_year_data}")
            
        # Force populate previous year data arrays if they're empty but we have averages
        if (final_previous_year_data is None and 
            previous_year_averages and 
            len(previous_year_averages) > 0):
            
            print(f"[DEBUG] Force populating previous year data arrays from averages")
            final_previous_year_data = {
                'attendance': [],
                'new_people': [],
                'new_christians': []
            }
            
            # Populate arrays with the calculated averages
            for month_key in sorted(prev_monthly_trends.keys()):
                month_data = prev_monthly_trends[month_key]
                if month_data['count'] > 0:
                    final_previous_year_data['attendance'].append(month_data['attendance'])
                    final_previous_year_data['new_people'].append(month_data['new_people'])
                    final_previous_year_data['new_christians'].append(month_data['new_christians'])
            
            print(f"[DEBUG] Force populated previous year data: {final_previous_year_data}")
        
        # Get tithe breakdown from Tithe tab
        tithe_breakdown = get_tithe_breakdown(campus, start_date, end_date)
        
        return {
            'stats': period_stats,
            'recent_entries': recent_entries[:10],
            'trends': {
                'monthly_averages': monthly_averages,
                'monthly_trends': monthly_trends
            },
            'chart_data': chart_data,
            'previous_year_data': final_previous_year_data,  # Always return previous year data when available
            'campus': campus,
            'service_breakdown': service_breakdown,  # Adult service times
            'kids_service_breakdown': kids_service_breakdown,  # Kids service times
            'tithe_breakdown': tithe_breakdown,  # Include tithe breakdown from Tithe tab
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
                'filter_type': date_filter
            },
            'function_called': 'FIRST_FUNCTION_WITH_AVERAGES'
        }
        
    except Exception as e:
        logger.error(f"Dashboard data error: {e}")
        return {"error": str(e)}



# Removed duplicate get_dashboard_data_v2 function to fix conflicts
# def get_dashboard_data_v2(campus, date_filter='last_12_months', custom_start_date='', custom_end_date=''):
#     """Get dashboard data with date filtering - V2 with averages"""
#     try:
#         print("[DEBUG] SECOND get_dashboard_data function called - THIS IS THE OLD ONE")
        # # Get data from Google Sheets
        # rows = []
        # logger.info(f"[SHEETS DEBUG] Starting data retrieval for campus: {campus}")
        # logger.info(f"[SHEETS DEBUG] Sheet object exists: {sheet is not None}")
        # 
        # if sheet:
        #     try:
        #         logger.info(f"[SHEETS DEBUG] Attempting to get all records from Google Sheets")
        #         rows = safe_sheets_request(sheet.get_all_records)
        #         logger.info(f"[SHEETS DEBUG] Successfully retrieved {len(rows)} rows from Google Sheets")
        #         if rows:
        #             logger.info(f"[SHEETS DEBUG] First row keys: {list(rows[0].keys())}")
        #             logger.info(f"[SHEETS DEBUG] Sample first row: {rows[0]}")
        #         else:
        #             logger.warning(f"[SHEETS DEBUG] Google Sheets returned empty data")
        #     except Exception as e:
        #         logger.error(f"[SHEETS DEBUG] Failed to get stats from Google Sheets: {e}")
        #         logger.error(f"[SHEETS DEBUG] Exception type: {type(e).__name__}")
        #         rows = []
        # 
        # if not rows:
        #     logger.warning(f"[SHEETS DEBUG] No rows from Google Sheets, falling back to conversation memory for campus: {campus}")
        #     # Fallback to conversation memory
        #     memory = load_conversation_memory()
        #     campus_history = memory.get("session_stats", {}).get(campus, [])
        #         logger.info(f"[SHEETS DEBUG] Conversation memory has {len(campus_history)} rows for campus: {campus}")
        #     if campus_history:
        #         logger.info(f"[SHEETS DEBUG] Memory row keys: {list(campus_history[0].keys())}")
        #     rows = campus_history
        
        # # Calculate date range based on filter
        # end_date = datetime.now()
        # if date_filter == 'last_7_days':
        #     start_date = end_date - timedelta(days=7)
        # elif date_filter == 'last_30_days':
        #     start_date = end_date - timedelta(days=30)
        # elif date_filter == 'last_90_days':
        #     start_date = end_date - timedelta(days=90)
        # elif date_filter == 'this_year':
        #     start_date = datetime(end_date.year, 1, 1)
        # elif date_filter == 'last_12_months':
        #     start_date = end_date - timedelta(days=365)  # 12 months
        # elif custom_start_date and custom_end_date:
        #     start_date = datetime.strptime(custom_start_date, '%Y-%m-%d')
        #     end_date = datetime.strptime(custom_end_date, '%Y-%m-%d')
        # else:
        #     start_date = end_date - timedelta(days=30)  # Default to 30 days
        # 
        # # Filter rows by campus and date range
        # filtered_rows = []
        # campus_normalized = normalize_campus(campus) if campus != 'all_campuses' else None
        # logger.info(f"[FILTER DEBUG] Total rows before filtering: {len(rows)}")
        # logger.info(f"[FILTER DEBUG] Campus: {campus}, Normalized: {campus_normalized}")
        # logger.info(f"[FILTER DEBUG] Date filter: {date_filter}, Start: {start_date}, End: {end_date}")
        # 
        # campus_match_count = 0
        # date_match_count = 0
        # 
        # for i, row in enumerate(rows):
        #     try:
        #         # Check campus filter
        #         if campus_normalized:
        #             row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
        #             campus_matches = (row_campus == campus_normalized or campus_normalized in row_campus)
        #             if not campus_matches:
        #             if i < 5:  # Log first few mismatches for debugging
        #                 logger.debug(f"[FILTER DEBUG] Row {i} campus mismatch: '{row_campus}' vs '{campus_normalized}'")
        #             continue
        #         campus_match_count += 1
        #         
        #         # Check date filter - use Date column instead of Timestamp
        #         date_str = row.get("Date", "")
        #         if not date_str:
        #             date_str = row.get("Timestamp", "")
        #         
        #         if date_str:
        #             try:
        #                 # Parse date using the same logic as query functions
        #                 row_date = get_row_timestamp(row)
        #                 
        #                 # Check if row is within date range
        #                 if row_date != datetime.min and start_date <= row_date <= end_date:
        #                     filtered_rows.append(row)
        #                     date_match_count += 1
        #                 else:
        #                     if i < 5:  # Log first few date mismatches for debugging
        #                         logger.debug(f"[FILTER DEBUG] Row {i} date mismatch: {row_date} not in range {start_date} to {end_date}")
        #             except Exception as e:
        #                 logger.warning(f"[FILTER DEBUG] Could not parse date '{date_str}' from row {i}: {e}")
        #         else:
        #             # No date column, include the row
        #             filtered_rows.append(row)
        #             date_match_count += 1
        # except Exception as e:
        #     logger.warning(f"[FILTER DEBUG] Error processing row {i}: {e}")
        #     continue
        
        logger.info(f"[FILTER DEBUG] Campus matches: {campus_match_count}, Date matches: {date_match_count}")
        logger.info(f"[FILTER DEBUG] Final filtered rows: {len(filtered_rows)}")
        
        print(f"[DEBUG] Filtered rows after date filtering: {len(filtered_rows)}")
        
        # Calculate stats using correct Google Sheets headers
        print(f"[DEBUG] Sample row keys: {list(filtered_rows[0].keys()) if filtered_rows else 'No rows'}")
        print(f"[DEBUG] Sample row: {filtered_rows[0] if filtered_rows else 'No rows'}")
        total_attendance = sum(safe_int(row.get('Total Attendance', 0)) for row in filtered_rows)
        print(f"[DEBUG] Total attendance calculated: {total_attendance}")
        
        # New People = First Time Visitors + Visitors  
        total_new_people = sum(
            safe_int(row.get('First Time Visitors', 0)) + safe_int(row.get('Visitors', 0)) 
            for row in filtered_rows
        )
        
        # New Christians = First Time Christians + Rededications
        total_new_christians = sum(
            safe_int(row.get('First Time Christians', 0)) + safe_int(row.get('Rededications', 0))
            for row in filtered_rows
        )
        
        total_youth = sum(safe_int(row.get('Youth Attendance', 0)) for row in filtered_rows)
        total_kids = sum(safe_int(row.get('Kids Attendance', 0)) for row in filtered_rows)
        total_connect_groups = sum(safe_int(row.get('Connect Groups', 0)) for row in filtered_rows)
        total_dream_team = sum(safe_int(row.get('Dream Team', 0)) for row in filtered_rows)
        # Debug tithe calculation - more robust with currency handling
        def parse_tithe_value(val):
            """Parse tithe value, handling currency formatting"""
            if not val:
                return 0
            try:
                # Remove dollar signs, commas, and spaces, then convert to float
                cleaned = str(val).replace('$', '').replace(',', '').replace(' ', '').strip()
                if cleaned:
                    return int(float(cleaned))
                return 0
            except Exception:
                return 0
        
        tithe_values = []
        tithe_debug_info = []
        for i, row in enumerate(filtered_rows):
            tithe_raw = row.get('Tithe', 0)
            tithe_converted = parse_tithe_value(tithe_raw)
            tithe_debug_info.append(f"Row {i}: raw='{tithe_raw}', converted={tithe_converted}")
            if tithe_converted > 0:
                tithe_values.append(tithe_converted)
                logger.debug(f"[TITHE DEBUG] Row {i} tithe: '{tithe_raw}' -> {tithe_converted}")
        
        total_tithe = sum(tithe_values)
        logger.debug(f"[TITHE DEBUG] Total tithe values found: {len(tithe_values)}, Total: ${total_tithe}")
        logger.debug(f"[TITHE DEBUG] First 5 tithe debug entries: {tithe_debug_info[:5]}")
        
        # Calculate averages
        valid_entries = len([row for row in filtered_rows if calculate_total_attendance(row) > 0])
        avg_attendance = total_attendance / valid_entries if valid_entries > 0 else 0
        avg_new_people = total_new_people / valid_entries if valid_entries > 0 else 0
        avg_new_christians = total_new_christians / valid_entries if valid_entries > 0 else 0
        avg_youth = total_youth / valid_entries if valid_entries > 0 else 0
        avg_kids = total_kids / valid_entries if valid_entries > 0 else 0
        avg_connect_groups = total_connect_groups / valid_entries if valid_entries > 0 else 0
        avg_dream_team = total_dream_team / valid_entries if valid_entries > 0 else 0
        
        # Prepare chart data for YTD trends (monthly aggregation)
        chart_data = {}
        
        # Group data by month for trend analysis
        monthly_data = {}
        for row in filtered_rows:
            try:
                # Use Date field instead of Timestamp for more accurate date filtering
                date_str = row.get("Date", "")
                if not date_str:
                    # Fallback to Timestamp if Date is not available
                    date_str = row.get("Timestamp", "")
                
                if date_str:
                    if "T" in date_str:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        date_obj = parse_any_date(date_str)
                    
                    month_key = date_obj.strftime('%Y-%m')
                    if month_key not in monthly_data:
                        monthly_data[month_key] = {
                            'attendance': [],
                            'new_people': [],
                            'new_christians': [],
                            'month_name': date_obj.strftime('%b %Y')
                        }
                    
                    monthly_data[month_key]['attendance'].append(safe_int(row.get('Total Attendance', 0)))
                    monthly_data[month_key]['new_people'].append(
                        safe_int(row.get('First Time Visitors', 0)) + safe_int(row.get('Visitors', 0))
                    )
                    monthly_data[month_key]['new_christians'].append(
                        safe_int(row.get('First Time Christians', 0)) + safe_int(row.get('Rededications', 0))
                    )
            except Exception:
                continue
        
        # Convert to chart format with complete month range
        attendance_labels = []
        attendance_values = []
        new_people_values = []
        new_christians_values = []
        
        # Create complete month range from start_date to end_date
        if start_date and end_date:
            current_date = start_date.replace(day=1)  # Start from first day of month
            end_month = end_date.replace(day=1)  # End at first day of month
            
            # Get current month to exclude from charts
            current_month = datetime.now().strftime('%Y-%m')
            
            while current_date <= end_month:
                month_key = current_date.strftime('%Y-%m')
                
                # Skip current month
                if month_key == current_month:
                    current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
                    continue
                
                month_name = current_date.strftime('%b %Y')
                attendance_labels.append(month_name)
                
                # Get data for this month from monthly_data, or use zeros if no data
                data = monthly_data.get(month_key, {'attendance': [], 'new_people': [], 'new_christians': []})
                
                # Calculate averages instead of totals
                attendance_count = len(data['attendance'])
                new_people_count = len(data['new_people'])
                new_christians_count = len(data['new_christians'])
                
                avg_attendance = sum(data['attendance']) / attendance_count if attendance_count > 0 else 0
                avg_new_people = sum(data['new_people']) / new_people_count if new_people_count > 0 else 0
                avg_new_christians = sum(data['new_christians']) / new_christians_count if new_christians_count > 0 else 0
                
                attendance_values.append(round(avg_attendance, 1))
                new_people_values.append(round(avg_new_people, 1))
                new_christians_values.append(round(avg_new_christians, 1))
                
                # Move to next month
                current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        chart_data = {
            'labels': attendance_labels,
            'attendance': attendance_values,
            'new_people': new_people_values,
            'new_christians': new_christians_values
        }
        
        # Calculate detailed breakdown stats for modals using correct headers
        total_first_time_visitors = sum(safe_int(row.get('First Time Visitors', 0)) for row in filtered_rows)
        total_visitors = sum(safe_int(row.get('Visitors', 0)) for row in filtered_rows)
        total_first_time_christians = sum(safe_int(row.get('First Time Christians', 0)) for row in filtered_rows)
        total_rededications = sum(safe_int(row.get('Rededications', 0)) for row in filtered_rows)
        total_youth_attendance = sum(safe_int(row.get('Youth Attendance', 0)) for row in filtered_rows)
        total_youth_salvations = sum(safe_int(row.get('Youth Salvations', 0)) for row in filtered_rows)
        total_youth_new_people = sum(safe_int(row.get('Youth New People', 0)) for row in filtered_rows)
        total_kids_attendance = sum(safe_int(row.get('Kids Attendance', 0)) for row in filtered_rows)
        total_kids_leaders = sum(safe_int(row.get('Kids Leaders', 0)) for row in filtered_rows)
        total_new_kids = sum(safe_int(row.get('New Kids', 0)) for row in filtered_rows)
        total_new_kids_salvations = sum(safe_int(row.get('New Kids Salvations', 0)) for row in filtered_rows)

        # Calculate service time breakdown for attendance
        service_breakdown = {}
        if campus != 'all_campuses':
            service_breakdown = calculate_service_breakdown(filtered_rows, campus)
        else:
            # For all campuses, show individual service time totals
            service_times = ['9:00 AM', '10:00 AM', '11:00 AM', '5:00 PM']
            for service_time in service_times:
                total = sum(safe_int(row.get(service_time, 0)) for row in filtered_rows)
                if total > 0:
                    service_breakdown[service_time] = {
                        'total': total,
                        'count': len([row for row in filtered_rows if safe_int(row.get(service_time, 0)) > 0]),
                        'average': total / len([row for row in filtered_rows if safe_int(row.get(service_time, 0)) > 0]) if len([row for row in filtered_rows if safe_int(row.get(service_time, 0)) > 0]) > 0 else 0,
                        'entries': [safe_int(row.get(service_time, 0)) for row in filtered_rows if safe_int(row.get(service_time, 0)) > 0]
                    }

        return {
            'stats': {
                'total_attendance': total_attendance,
                'total_new_people': total_new_people,
                'total_new_christians': total_new_christians,
                'total_youth': total_youth,
                'total_kids': total_kids,
                'total_connect_groups': total_connect_groups,
                'total_dream_team': total_dream_team,
                'total_tithe': total_tithe,
                'avg_attendance': avg_attendance,
                'avg_new_people': avg_new_people,
                'avg_new_christians': avg_new_christians,
                'avg_youth': avg_youth,
                'avg_kids': avg_kids,
                'avg_connect_groups': avg_connect_groups,
                'avg_dream_team': avg_dream_team,
                # Breakdown stats for modals
                'first_time_visitors': total_first_time_visitors,
                'visitors': total_visitors,
                'first_time_christians': total_first_time_christians,
                'rededications': total_rededications,
                'youth_attendance': total_youth_attendance,
                'youth_salvations': total_youth_salvations,
                'youth_new_people': total_youth_new_people,
                'kids_attendance': total_kids_attendance,
                'kids_leaders': total_kids_leaders,
                'new_kids': total_new_kids,
                'new_kids_salvations': total_new_kids_salvations
            },
            'service_breakdown': service_breakdown,
            'chart_data': chart_data,
            'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'function_called': 'SECOND_FUNCTION_WITH_TOTALS'
        }
    
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return {
            'error': f'Error loading dashboard data: {str(e)}',
            'stats': {},
            'chart_data': {'attendance_labels': [], 'attendance_values': []}
        }

def get_campus_comparison_data(campus_filter=None):
    """Get comparison data across campuses for leadership insights"""
    try:
        if not sheet:
            return []
        
        # sheet is already a worksheet object, not a spreadsheet
        data = safe_sheets_request(sheet.get_all_records)
        
        if not data:
            return []
        
        # Get data for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # If campus_filter is provided, only analyze that campus
        if campus_filter:
            campuses = [campus_filter.lower()]
        else:
            campuses = ['paradise', 'south', 'adelaide_city', 'salisbury', 'clare_valley', 
                       'mount_barker', 'victor_harbour', 'copper_coast']
        
        campus_stats = []
        
        for campus in campuses:
            # Filter data for this campus and date range
            campus_data = []
            for row in data:
                try:
                    date_str = row.get('Date', '')
                    if not date_str:
                        continue
                    
                    # Try multiple date formats
                    row_date = None
                    date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                    
                    for date_format in date_formats:
                        try:
                            row_date = datetime.strptime(date_str, date_format)
                            break
                        except ValueError:
                            continue
                    
                    if row_date and start_date <= row_date <= end_date and row.get('Campus', '').lower() == campus.lower():
                        campus_data.append(row)
                except (ValueError, TypeError):
                    continue
            
            if campus_data:
                # Calculate basic stats for this campus using correct headers
                total_attendance = sum(safe_int(row.get('Total Attendance', 0)) for row in campus_data)
                
                # New People = First Time Visitors + Visitors  
                total_new_people = sum(
                    safe_int(row.get('First Time Visitors', 0)) + safe_int(row.get('Visitors', 0))
                    for row in campus_data
                )
                
                # New Christians = First Time Christians + Rededications
                total_new_christians = sum(
                    safe_int(row.get('First Time Christians', 0)) + safe_int(row.get('Rededications', 0))
                    for row in campus_data
                )
                
                total_youth = sum(safe_int(row.get('Youth Attendance', 0)) for row in campus_data)
                total_kids = sum(safe_int(row.get('Kids Attendance', 0)) for row in campus_data)
                
                avg_attendance = total_attendance / len(campus_data) if campus_data else 0
                avg_new_people = total_new_people / len(campus_data) if campus_data else 0
                avg_new_christians = total_new_christians / len(campus_data) if campus_data else 0
                
                # Calculate growth rates compared to previous period
                prev_start = start_date - timedelta(days=30)
                prev_data = []
                for row in data:
                    try:
                        date_str = row.get('Date', '')
                        if not date_str:
                            continue
                        
                        # Try multiple date formats
                        row_date = None
                        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                        
                        for date_format in date_formats:
                            try:
                                row_date = datetime.strptime(date_str, date_format)
                                break
                            except ValueError:
                                continue
                        
                        if row_date and prev_start <= row_date < start_date and row.get('Campus', '').lower() == campus.lower():
                            prev_data.append(row)
                    except (ValueError, TypeError):
                        continue
                
                # Calculate growth percentages
                attendance_growth = 0
                new_people_growth = 0
                new_christians_growth = 0
                
                if prev_data:
                    prev_avg_attendance = sum(safe_int(row.get('Total Attendance', 0)) for row in prev_data) / len(prev_data)
                    
                    # Calculate previous period averages with correct headers
                    prev_total_new_people = sum(
                        safe_int(row.get('First Time Visitors', 0)) + safe_int(row.get('Visitors', 0))
                        for row in prev_data
                    )
                    prev_avg_new_people = prev_total_new_people / len(prev_data)
                    
                    prev_total_new_christians = sum(
                        safe_int(row.get('First Time Christians', 0)) + safe_int(row.get('Rededications', 0))
                        for row in prev_data
                    )
                    prev_avg_new_christians = prev_total_new_christians / len(prev_data)
                    
                    if prev_avg_attendance > 0:
                        attendance_growth = ((avg_attendance - prev_avg_attendance) / prev_avg_attendance) * 100
                    
                    if prev_avg_new_people > 0:
                        new_people_growth = ((avg_new_people - prev_avg_new_people) / prev_avg_new_people) * 100
                    
                    if prev_avg_new_christians > 0:
                        new_christians_growth = ((avg_new_christians - prev_avg_new_christians) / prev_avg_new_christians) * 100
                
                campus_stats.append({
                    'campus': campus,
                    'display_name': campus.replace('_', ' ').title(),
                    'attendance': round(avg_attendance, 1),
                    'new_people': round(avg_new_people, 1),
                    'new_christians': round(avg_new_christians, 1),
                    'youth': round(total_youth / len(campus_data), 1) if campus_data else 0,
                    'kids': round(total_kids / len(campus_data), 1) if campus_data else 0,
                    'attendance_growth': round(attendance_growth, 1),
                    'new_people_growth': round(new_people_growth, 1),
                    'new_christians_growth': round(new_christians_growth, 1),
                    'total_records': len(campus_data),
                    'conversion_rate': round((avg_new_christians / max(avg_new_people, 1)) * 100, 1)
                })
        
        return sorted(campus_stats, key=lambda x: x['attendance'], reverse=True)
        
    except Exception as e:
        logger.error(f"Campus comparison data error: {e}")
        return []

def generate_campus_insights(campus_data, campus_filter=None):
    """Generate AI-powered insights from campus data"""
    try:
        if not campus_data:
            return ["No campus data available for insights generation."]
        
        insights = []
        
        # If this is campus-specific data (single campus)
        if campus_filter and len(campus_data) == 1:
            campus = campus_data[0]
            
            # Campus-specific insights
            insights.append(f"📊 {campus['display_name']} current performance: {campus['attendance']} average attendance, {campus['new_people']} new people per week")
            
            # Growth insights
            if campus['attendance_growth'] > 10:
                insights.append(f"🚀 Excellent growth! Your attendance is up {campus['attendance_growth']}% from last month")
            elif campus['attendance_growth'] > 0:
                insights.append(f"📈 Positive growth: {campus['attendance_growth']}% attendance increase from last month")
            elif campus['attendance_growth'] < -10:
                insights.append(f"⚠️ Attendance declined {abs(campus['attendance_growth'])}% - consider community outreach initiatives")
            else:
                insights.append(f"📊 Attendance stable with {campus['attendance_growth']}% change from last month")
            
            # Conversion insights
            if campus['conversion_rate'] > 25:
                insights.append(f"🎯 Outstanding conversion rate! {campus['conversion_rate']}% of new people are becoming Christians")
            elif campus['conversion_rate'] > 15:
                insights.append(f"✅ Good conversion rate: {campus['conversion_rate']}% of new people becoming Christians")
            else:
                insights.append(f"💡 Focus opportunity: {campus['conversion_rate']}% conversion rate - consider follow-up strategies")
            
            # Youth and kids
            if campus['youth'] > 25:
                insights.append(f"👥 Strong youth program with {campus['youth']} average attendance")
            elif campus['youth'] > 0:
                insights.append(f"👥 Youth engagement: {campus['youth']} average - room for growth")
            
            if campus['kids'] > 20:
                insights.append(f"👶 Thriving kids ministry with {campus['kids']} average attendance")
            elif campus['kids'] > 0:
                insights.append(f"👶 Kids ministry: {campus['kids']} average - potential for expansion")
            
            # Encouragement
            insights.append(f"💪 Keep up the great work! {campus['display_name']} is making a real impact in the community")
            
        else:
            # Multi-campus insights (for senior leadership/admin)
            
            # Top performing campus
            if campus_data:
                top_campus = campus_data[0]
                insights.append(f"🏆 {top_campus['display_name']} leads in attendance with {top_campus['attendance']} average weekly attendance")
            
            # Growth analysis
            growth_leaders = [campus for campus in campus_data if campus['attendance_growth'] > 10]
            if growth_leaders:
                campus_names = [campus['display_name'] for campus in growth_leaders[:3]]
                insights.append(f"📈 Strong growth at {', '.join(campus_names)} - attendance up 10%+ from last month")
            
            declining_campuses = [campus for campus in campus_data if campus['attendance_growth'] < -10]
            if declining_campuses:
                campus_names = [campus['display_name'] for campus in declining_campuses[:2]]
                insights.append(f"⚠️ {', '.join(campus_names)} showing declining attendance - may need attention")
            
            # New people conversion insights
            high_conversion = [campus for campus in campus_data if campus['conversion_rate'] > 20]
            if high_conversion:
                campus_names = [campus['display_name'] for campus in high_conversion[:2]]
                insights.append(f"🎯 Excellent conversion rates at {', '.join(campus_names)} - over 20% of new people becoming Christians")
            
            # Youth and kids analysis
            youth_leaders = sorted([campus for campus in campus_data if campus['youth'] > 0], key=lambda x: x['youth'], reverse=True)[:2]
            if youth_leaders:
                campus_names = [f"{campus['display_name']} ({campus['youth']})" for campus in youth_leaders]
                insights.append(f"👥 Youth engagement leaders: {', '.join(campus_names)}")
            
            # Overall network performance
            total_attendance = sum(campus['attendance'] * campus['total_records'] for campus in campus_data)
            total_records = sum(campus['total_records'] for campus in campus_data)
            network_avg = total_attendance / max(total_records, 1)
            
            total_new_people = sum(campus['new_people'] * campus['total_records'] for campus in campus_data)
            total_new_christians = sum(campus['new_christians'] * campus['total_records'] for campus in campus_data)
            network_conversion = (total_new_christians / max(total_new_people, 1)) * 100
            
            insights.append(f"🌟 Network average: {network_avg:.1f} attendance, {network_conversion:.1f}% conversion rate across all campuses")
            
            # Opportunities
            underperforming = [campus for campus in campus_data if campus['attendance'] < network_avg * 0.7]
            if underperforming:
                campus_names = [campus['display_name'] for campus in underperforming[:2]]
                insights.append(f"💡 Growth opportunities at {', '.join(campus_names)} - below network average")
        
        return insights[:6]  # Limit to 6 insights
        
    except Exception as e:
        logger.error(f"Insights generation error: {e}")
        return ["Unable to generate insights at this time. Please try again later."]

def get_weekly_campus_comparison_data():
    """Get campus comparison data for the current week"""
    try:
        # Get data from Google Sheets
        rows = []
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
            except Exception as e:
                logger.error(f"Failed to get stats from Google Sheets: {e}")
                rows = []
        
        if not rows:
            return []
        
        # Get current week's data (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Group by campus
        campus_data = {}
        for row in rows:
            try:
                # Check if row is within current week
                timestamp_str = row.get("Timestamp", "")
                if timestamp_str:
                    if "T" in timestamp_str:
                        row_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        row_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    
                    if start_date <= row_date <= end_date:
                        campus = row.get("Campus", "").lower()
                        if campus not in campus_data:
                            campus_data[campus] = {
                                'campus': campus,
                                'attendance': 0,
                                'new_people': 0,
                                'new_christians': 0
                            }
                        
                        campus_data[campus]['attendance'] += safe_int(row.get('Total Attendance', 0))
                        campus_data[campus]['new_people'] += safe_int(row.get('New People', 0))
                        campus_data[campus]['new_christians'] += safe_int(row.get('New Christians', 0))
            except Exception:
                continue
        
        # Convert to list and sort by attendance
        comparison_list = list(campus_data.values())
        comparison_list.sort(key=lambda x: x['attendance'], reverse=True)
        
        return comparison_list
    
    except Exception as e:
        logger.error(f"Error getting campus comparison data: {e}")
        return []

# @app.route('/dashboard')
# @login_required
# def dashboard():
#     """Dashboard with analytics and statistics - React app handles this now"""
#     # This route is now handled by React Router
#     pass

# @app.route('/finance')
# @login_required
# def finance_dashboard():
#     """Finance team tithe logging interface - React app handles this now"""
#     # This route is now handled by React Router
#     pass

def get_existing_tithe_data(selected_date):
    """Get existing tithe data for the selected date from the Tithe tab"""
    try:
        if not finance_sheet:
            return {}
        
        # Get all rows from the Tithe tab
        rows = safe_sheets_request(finance_sheet.get_all_records)
        existing_data = {}
        
        # Parse the selected date
        target_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        
        for row in rows:
            date_str = row.get("Date", "")
            if date_str:
                try:
                    # Parse the date from the row
                    if "T" in date_str:
                        row_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                    else:
                        row_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    
                    # If dates match, collect tithe data
                    if row_date == target_date:
                        campus = row.get('Campus', '')
                        general = row.get('General', 0)
                        trust = row.get('Trust', 0)
                        online = row.get('Online Giving', 0)
                        text = row.get('Text', 0)
                        total = row.get('Total', 0)
                        if campus:
                            existing_data[campus.lower()] = {
                                'general': safe_int(general) if general else 0,
                                'trust': safe_int(trust) if trust else 0,
                                'online': safe_int(online) if online else 0,
                                'text': safe_int(text) if text else 0,
                                'total': safe_int(total) if total else 0,
                                'row_index': rows.index(row) + 2  # +2 because sheets are 1-indexed and have header
                            }
                except Exception as e:
                    logger.warning(f"Error parsing date {date_str}: {e}")
                    continue
        
        return existing_data
        
    except Exception as e:
        logger.error(f"Error getting existing tithe data: {str(e)}")
        return {}

@app.route('/finance/submit', methods=['POST'])
@login_required
def submit_tithe_data():
    """Submit tithe data for multiple campuses"""
    try:
        # Only users with finance access can access this
        if not current_user.has_permission('finance_access'):
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        selected_date = data.get('date')
        tithe_data = data.get('tithe_data', {})
        
        if not selected_date or not tithe_data:
            return jsonify({'error': 'Missing date or tithe data'}), 400
        
        results = []
        
        # Process each campus's tithe data
        for campus_id, amount in tithe_data.items():
            if amount and float(amount) > 0:
                result = update_tithe_for_campus(campus_id, selected_date, float(amount))
                results.append({
                    'campus': campus_id,
                    'amount': amount,
                    'success': result['success'],
                    'message': result['message']
                })
        
        return jsonify({
            'success': True,
            'message': f'Tithe data submitted for {len(results)} campuses',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error submitting tithe data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/finance/status')
@login_required
def check_finance_status():
    """Check if finance sheet is connected"""
    try:
        return jsonify({
            'success': True,
            'finance_sheet_connected': finance_sheet is not None,
            'finance_sheet_title': finance_sheet.title if finance_sheet else None
        })
    except Exception as e:
        logger.error(f"Error checking finance status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/finance/existing')
@login_required
def get_existing_finance_data():
    """Get existing finance data for a specific date"""
    try:
        # Only users with finance access can access this
        if not current_user.has_permission('finance_access'):
            return jsonify({'success': False, 'error': 'Access denied. Finance access required.'}), 403
        
        date_str = request.args.get('date')
        if not date_str:
            return jsonify({'success': False, 'error': 'Date parameter is required'}), 400
        
        # Get existing tithe data for the date
        existing_data = get_existing_tithe_data(date_str)
        
        return jsonify({
            'success': True,
            'existing_data': existing_data
        })
        
    except Exception as e:
        logger.error(f"Error getting existing finance data: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred while loading finance data'}), 500

@app.route('/api/finance/submit', methods=['POST'])
@login_required
def submit_finance_data():
    """Submit tithe data for multiple campuses"""
    try:
        # Check if finance sheet is available
        if not finance_sheet:
            logger.error("Finance sheet is not available - check Google Sheets connection")
            return jsonify({'success': False, 'error': 'Finance sheet not available. Please contact administrator.'}), 500
        
        # Only users with finance access can access this
        if not current_user.has_permission('finance_access'):
            return jsonify({'success': False, 'error': 'Access denied. Finance access required.'}), 403
        
        data = request.get_json()
        selected_date = data.get('date')
        tithe_data = data.get('tithe_data', {})
        
        logger.info(f"Finance submit request - Date: {selected_date}, Campus count: {len(tithe_data)}")
        
        if not selected_date:
            return jsonify({'success': False, 'error': 'Date is required'}), 400
        
        if not tithe_data:
            return jsonify({'success': False, 'error': 'Tithe data is required for at least one campus'}), 400
        
        results = []
        success_count = 0
        
        # Process each campus's tithe data
        for campus_id, campus_data in tithe_data.items():
            if campus_data:
                # campus_data is now a dict with {general, trust, online, text}
                general = float(campus_data.get('general', 0))
                trust = float(campus_data.get('trust', 0))
                online = float(campus_data.get('online', 0))
                text = float(campus_data.get('text', 0))
                total = general + trust + online + text
                
                if total > 0:
                    breakdown = {
                        'general': general,
                        'trust': trust,
                        'online': online,
                        'text': text,
                        'total': total
                    }
                    result = update_tithe_for_campus(campus_id, selected_date, breakdown)
                    results.append({
                        'campus': campus_id,
                        'total': total,
                        'breakdown': breakdown,
                        'success': result.get('success', False),
                        'message': result.get('message', '')
                    })
                    if result.get('success'):
                        success_count += 1
        
        if success_count > 0:
            return jsonify({
                'success': True,
                'message': f'Tithe data submitted for {success_count} campus(es)',
                'results': results
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to submit tithe data for any campus',
                'results': results
            }), 500
            
    except Exception as e:
        logger.error(f"Error submitting finance data: {str(e)}")
        return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'}), 500

def update_tithe_for_campus(campus_id, date_str, tithe_amount):
    """Update or add tithe data for a specific campus and date to the Tithe tab"""
    try:
        if not finance_sheet:
            logger.error("Finance sheet is None when trying to update tithe")
            return {'success': False, 'message': 'Finance sheet (Tithe tab) not available'}
        
        # Get all rows from the Tithe tab
        try:
            rows = safe_sheets_request(finance_sheet.get_all_records)
            # Ensure rows is a list (handle None case)
            if rows is None:
                rows = []
        except Exception as e:
            logger.error(f"Error getting records from finance sheet: {str(e)}")
            # Return empty list instead of failing - we can still append new rows
            rows = []
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Look for existing row for this campus and date
        # Normalize the incoming campus_id for comparison
        normalized_campus_id = normalize_campus(campus_id)
        existing_row_index = None
        latest_timestamp = None
        
        # Only search existing rows if we have any
        for i, row in enumerate(rows):
            date_str_row = row.get("Date", "")
            campus_name = row.get('Campus', '')
            timestamp_str = row.get('Timestamp', '')
            if date_str_row and campus_name:
                try:
                    if "T" in date_str_row:
                        row_date = datetime.fromisoformat(date_str_row.replace('Z', '+00:00')).date()
                    else:
                        row_date = datetime.strptime(date_str_row, "%Y-%m-%d").date()
                    
                    # Normalize both campus names for comparison
                    normalized_row_campus = normalize_campus(campus_name)
                    
                    if row_date == target_date and normalized_row_campus == normalized_campus_id:
                        # If there are multiple matches, use the most recent one (by timestamp)
                        if timestamp_str:
                            try:
                                if "T" in timestamp_str:
                                    row_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                else:
                                    row_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                
                                if latest_timestamp is None or row_timestamp > latest_timestamp:
                                    latest_timestamp = row_timestamp
                                    existing_row_index = i + 2  # +2 for 1-indexed and header
                            except:
                                # If timestamp parsing fails, just use this row if we haven't found one yet
                                if existing_row_index is None:
                                    existing_row_index = i + 2
                        else:
                            # No timestamp, use first match if we haven't found one
                            if existing_row_index is None:
                                existing_row_index = i + 2
                except Exception as e:
                    logger.warning(f"Error matching row {i}: {e}")
                    continue
        
        if existing_row_index:
            logger.info(f"Found existing row {existing_row_index} for {campus_id} on {date_str} (updating instead of creating new)")
        
        # tithe_amount is now a dict with breakdown: {general, trust, online, text, total}
        general = tithe_amount.get('general', 0) if isinstance(tithe_amount, dict) else 0
        trust = tithe_amount.get('trust', 0) if isinstance(tithe_amount, dict) else 0
        online = tithe_amount.get('online', 0) if isinstance(tithe_amount, dict) else 0
        text = tithe_amount.get('text', 0) if isinstance(tithe_amount, dict) else 0
        total = tithe_amount.get('total', 0) if isinstance(tithe_amount, dict) else tithe_amount
        
        if existing_row_index:
            # Update existing row - update all tithe breakdown columns (D-H)
            # D=General, E=Trust, F=Online Giving, G=Text, H=Total
            try:
                finance_sheet.update(f'D{existing_row_index}:H{existing_row_index}', [[general, trust, online, text, total]])
                logger.info(f"Updated tithe for {campus_id} on {date_str}: ${total} (G:{general}, T:{trust}, O:{online}, Tx:{text})")
                return {'success': True, 'message': f'Updated existing entry for {campus_id}'}
            except Exception as e:
                logger.error(f"Error updating row in finance sheet: {str(e)}")
                return {'success': False, 'message': f'Error updating entry: {str(e)}'}
        else:
            # Create new row in Tithe tab with breakdown
            # Tithe tab columns: A=Timestamp, B=Date, C=Campus, D=General, E=Trust, F=Online Giving, G=Text, H=Total
            # Use Adelaide timezone for timestamp
            from zoneinfo import ZoneInfo
            adelaide_tz = ZoneInfo('Australia/Adelaide')
            now_adelaide = datetime.now(adelaide_tz)
            
            # First, ensure headers exist (in case sheet was just created)
            try:
                headers = finance_sheet.row_values(1)  # Get first row (headers)
                expected_headers = ['Timestamp', 'Date', 'Campus', 'General', 'Trust', 'Online Giving', 'Text', 'Total']
                if len(headers) < len(expected_headers):
                    # Add missing headers
                    finance_sheet.update('A1:H1', [expected_headers])
                    logger.info(f"Updated Tithe sheet headers")
            except Exception as e:
                logger.warning(f"Could not check/update headers: {e}")
            
            new_row = [
                now_adelaide.strftime('%Y-%m-%d %H:%M:%S'),  # A: Timestamp
                date_str,                    # B: Date
                campus_id.replace('_', ' ').title(),  # C: Campus
                general,                     # D: General
                trust,                       # E: Trust
                online,                      # F: Online Giving
                text,                        # G: Text
                total                        # H: Total
            ]
            
            try:
                finance_sheet.append_row(new_row, value_input_option='USER_ENTERED')
                logger.info(f"Created new tithe entry for {campus_id} on {date_str}: ${total} (G:{general}, T:{trust}, O:{online}, Tx:{text})")
                return {'success': True, 'message': f'Created new entry for {campus_id}'}
            except Exception as e:
                logger.error(f"Error appending row to finance sheet: {str(e)}")
                return {'success': False, 'message': f'Error creating entry: {str(e)}'}
            
    except Exception as e:
        logger.error(f"Error updating tithe for {campus_id}: {str(e)}")
        return {'success': False, 'message': str(e)}

@app.route('/')
def serve_index():
    """Main application page - serve React app for all users"""
    print(f"[DEBUG] Root route accessed - User authenticated: {current_user.is_authenticated}")
    
    # Always serve the React app - let React handle authentication
    print("[DEBUG] Serving React app")
    return send_from_directory('static', 'index.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """API login endpoint for React frontend"""
    if request.is_json:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
    else:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
    
    if not username or not password:
        return jsonify({"error": "Please enter both username and password."}), 400
    
    user = authenticate_user(username, password)
    if user:
        login_user(user, remember=True)
        # Log successful login
        log_security_event(user.id, 'login_success', 'User logged in successfully')
        return jsonify({"success": True, "redirect": "/"})
    else:
        # Log failed login attempt
        log_security_event('unknown', 'login_failed', f'Failed login attempt for username: {username}')
        return jsonify({"error": "Invalid username or password."}), 401

# Security Settings Endpoints
@app.route('/api/security/change_password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('currentPassword', '').strip()
        new_password = data.get('newPassword', '').strip()
        confirm_password = data.get('confirmPassword', '').strip()
        
        if not current_password or not new_password or not confirm_password:
            return jsonify({"error": "All fields are required"}), 400
        
        if new_password != confirm_password:
            return jsonify({"error": "New passwords do not match"}), 400
        
        if len(new_password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Update password in users.json
        users_data = load_users()
        if current_user.id in users_data['users']:
            users_data['users'][current_user.id]['password_hash'] = generate_password_hash(new_password)
            save_users(users_data)
            
            # Log security event
            log_security_event(current_user.id, 'password_change', 'Password changed successfully')
            
            return jsonify({"message": "Password changed successfully"}), 200
        else:
            return jsonify({"error": "User not found"}), 404
            
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/security/account_info', methods=['GET'])
@login_required
def get_account_info():
    """Get current user account information"""
    try:
        users_data = load_users()
        user_data = users_data['users'].get(current_user.id, {})
        
        # Remove sensitive information
        account_info = {
            'id': user_data.get('id'),
            'username': user_data.get('username'),
            'email': user_data.get('email'),
            'full_name': user_data.get('full_name'),
            'role': user_data.get('role'),
            'campus': user_data.get('campus'),
            'active': user_data.get('active'),
            'created_date': user_data.get('created_date'),
            'last_login': user_data.get('last_login'),
            'role_name': users_data['roles'].get(user_data.get('role', ''), {}).get('name', 'Unknown'),
            'role_description': users_data['roles'].get(user_data.get('role', ''), {}).get('description', '')
        }
        
        return jsonify(account_info), 200
        
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/security/sessions', methods=['GET'])
@login_required
def get_active_sessions():
    """Get active sessions for current user (simplified - in production would track actual sessions)"""
    try:
        # For now, return basic session info
        # In production, this would track actual session tokens
        session_info = {
            'current_session': {
                'id': f"session_{current_user.id}_{int(datetime.now().timestamp())}",
                'created': datetime.now().isoformat(),
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            },
            'total_sessions': 1  # Simplified for demo
        }
        
        return jsonify(session_info), 200
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/security/logout_all', methods=['POST'])
@login_required
def logout_all_sessions():
    """Logout from all sessions (simplified implementation)"""
    try:
        # In production, this would invalidate all session tokens
        # For now, just log the event
        log_security_event(current_user.id, 'logout_all', 'User logged out from all sessions')
        
        return jsonify({"message": "Logged out from all sessions"}), 200
        
    except Exception as e:
        logger.error(f"Error logging out all sessions: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/security/activity_log', methods=['GET'])
@login_required
def get_activity_log():
    """Get user activity log"""
    try:
        # Load security logs
        security_logs = load_security_logs()
        user_logs = security_logs.get(current_user.id, [])
        
        # Return last 50 entries
        recent_logs = user_logs[-50:] if user_logs else []
        
        return jsonify({
            'logs': recent_logs,
            'total_entries': len(user_logs)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting activity log: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/security/two_factor', methods=['GET', 'POST'])
@login_required
def two_factor_settings():
    """Two-factor authentication settings (placeholder for future implementation)"""
    try:
        if request.method == 'GET':
            # Return current 2FA status
            return jsonify({
                'enabled': False,
                'method': 'none',
                'message': 'Two-factor authentication is not yet implemented'
            }), 200
        else:
            # POST request to enable/disable 2FA
            data = request.get_json()
            action = data.get('action', '')
            
            if action == 'enable':
                return jsonify({
                    'message': 'Two-factor authentication is not yet implemented',
                    'enabled': False
                }), 200
            elif action == 'disable':
                return jsonify({
                    'message': 'Two-factor authentication is not yet implemented',
                    'enabled': False
                }), 200
            else:
                return jsonify({"error": "Invalid action"}), 400
                
    except Exception as e:
        logger.error(f"Error with 2FA settings: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Admin-only security endpoints
@app.route('/api/security/admin/users', methods=['GET'])
@login_required
def get_all_users():
    """Get all users (admin only)"""
    try:
        if not current_user.has_permission('manage_users'):
            return jsonify({"error": "Access denied"}), 403
        
        # Get users from database instead of JSON file
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, email, full_name, role, campus, active, created_at, last_login
            FROM users
            ORDER BY full_name
        ''')
        
        users_list = []
        users_data = load_users()  # Still need this for role names
        
        for row in cursor.fetchall():
            user_id, username, email, full_name, role, campus, active, created_at, last_login = row
            
            # Format last login for display
            last_login_display = "Never"
            if last_login:
                try:
                    # Convert to readable format
                    if isinstance(last_login, str):
                        last_login_dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                    else:
                        last_login_dt = last_login
                    last_login_display = last_login_dt.strftime('%Y-%m-%d %H:%M')
                except:
                    last_login_display = "Unknown"
            
            user_info = {
                'id': str(user_id),
                'username': username,
                'email': email or 'N/A',
                'full_name': full_name or username,
                'role': role,
                'campus': campus or '',
                'active': bool(active),
                'created_date': created_at.strftime('%Y-%m-%d') if created_at else 'Unknown',
                'last_login': last_login_display,
                'role_name': users_data['roles'].get(role, {}).get('name', 'Unknown')
            }
            users_list.append(user_info)
        
        conn.close()
        return jsonify({'users': users_list}), 200
        
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/security/admin/user/<user_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_user(user_id):
    """Manage user (admin only)"""
    try:
        if not current_user.has_permission('manage_users'):
            return jsonify({"error": "Access denied"}), 403
        
        # Check if user exists in database first
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        user_exists = cursor.fetchone()
        conn.close()
        
        if not user_exists:
            return jsonify({"error": "User not found"}), 404
        
        users_data = load_users()
        
        if request.method == 'PUT':
            # Update user
            data = request.get_json()
            
            # Update database
            conn = get_db()
            cursor = conn.cursor()
            
            # Build update query dynamically
            update_fields = []
            update_values = []
            
            if 'active' in data:
                update_fields.append('active = ?')
                update_values.append(data['active'])
            if 'role' in data:
                update_fields.append('role = ?')
                update_values.append(data['role'])
            if 'campus' in data:
                update_fields.append('campus = ?')
                update_values.append(data['campus'])
                
                # Auto-assign role based on campus
                if data['campus'] and data['campus'] != 'all_campuses':
                    # If assigned to specific campus, make them campus_pastor
                    if 'role' not in data or data.get('role') == 'admin':
                        update_fields.append('role = ?')
                        update_values.append('campus_pastor')
                elif data['campus'] == 'all_campuses':
                    # If assigned to all campuses, make them senior_leader (unless they're admin)
                    if 'role' not in data or data.get('role') == 'campus_pastor':
                        update_fields.append('role = ?')
                        update_values.append('senior_leader')
            if 'email' in data:
                update_fields.append('email = ?')
                update_values.append(data['email'])
            if 'full_name' in data:
                update_fields.append('full_name = ?')
                update_values.append(data['full_name'])
            
            if update_fields:
                update_values.append(user_id)
                cursor.execute(f'''
                    UPDATE users 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', update_values)
                conn.commit()
            
            conn.close()
            
            # Also update JSON file for backward compatibility (if user exists there)
            if user_id in users_data['users']:
                user_data = users_data['users'][user_id]
                if 'active' in data:
                    user_data['active'] = data['active']
                if 'role' in data:
                    user_data['role'] = data['role']
                if 'campus' in data:
                    user_data['campus'] = data['campus']
                if 'email' in data:
                    user_data['email'] = data['email']
                if 'full_name' in data:
                    user_data['full_name'] = data['full_name']
                
                save_users(users_data)
            
            log_security_event(current_user.id, 'user_updated', f'Updated user {user_id}')
            
            return jsonify({"message": "User updated successfully"}), 200
            
        elif request.method == 'DELETE':
            # Deactivate user (don't actually delete)
            users_data['users'][user_id]['active'] = False
            save_users(users_data)
            log_security_event(current_user.id, 'user_deactivated', f'Deactivated user {user_id}')
            
            return jsonify({"message": "User deactivated successfully"}), 200
            
    except Exception as e:
        logger.error(f"Error managing user: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/security/admin/logs', methods=['GET'])
@login_required
def get_security_logs():
    """Get all security logs (admin only)"""
    try:
        if not current_user.has_permission('manage_users'):
            return jsonify({"error": "Access denied"}), 403
        
        security_logs = load_security_logs()
        
        # Return all logs (in production, this would be paginated)
        all_logs = []
        for user_id, logs in security_logs.items():
            for log in logs:
                log['user_id'] = user_id
                all_logs.append(log)
        
        # Sort by timestamp (newest first)
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'logs': all_logs[:100],  # Limit to 100 most recent
            'total_entries': len(all_logs)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting security logs: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Security utility functions
def log_security_event(user_id, event_type, description):
    """Log security events"""
    try:
        security_logs = load_security_logs()
        
        if user_id not in security_logs:
            security_logs[user_id] = []
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'description': description,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        security_logs[user_id].append(log_entry)
        
        # Keep only last 1000 entries per user
        if len(security_logs[user_id]) > 1000:
            security_logs[user_id] = security_logs[user_id][-1000:]
        
        save_security_logs(security_logs)
        
    except Exception as e:
        logger.error(f"Error logging security event: {e}")

def load_security_logs():
    """Load security logs from file"""
    try:
        log_file = os.path.join('data', 'security_logs.json')
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading security logs: {e}")
        return {}

def save_security_logs(logs):
    """Save security logs to file"""
    try:
        log_file = os.path.join('data', 'security_logs.json')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving security logs: {e}")

def load_users():
    """Load users from users.json"""
    try:
        users_file = os.path.join('users.json')
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                return json.load(f)
        return {"users": {}, "roles": {}, "metadata": {}}
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return {"users": {}, "roles": {}, "metadata": {}}

def save_users(data):
    """Save users to users.json"""
    try:
        users_file = os.path.join('users.json')
        with open(users_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user and clear session"""
    try:
        # Get user ID before logout
        user_id = None
        if hasattr(current_user, 'id') and current_user.is_authenticated:
            user_id = current_user.id
        elif 'user_id' in session:
            user_id = session.get('user_id')
        
        # Remove Flask-Login user session data
        if '_user_id' in session:
            session.pop('_user_id', None)
        if 'user_id' in session:
            session.pop('user_id', None)
        if '_fresh' in session:
            session.pop('_fresh', None)
            
        # Call Flask-Login logout
        logout_user()
        
        # Force clear the entire session
        for key in list(session.keys()):
            session.pop(key, None)
        
        # Modify session to force save
        session.modified = True
        
        logger.info(f"User {user_id} logged out successfully")
        
        # Return response with clear cookie headers
        response = jsonify({"success": True, "message": "Logged out successfully"})
        response.set_cookie('session', '', expires=0, samesite='Lax', path='/')
        response.set_cookie('remember_token', '', expires=0, path='/')
        
        return response
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        # Even if there's an error, try to clear everything
        for key in list(session.keys()):
            session.pop(key, None)
        session.modified = True
        response = jsonify({"success": True, "message": "Logged out"})
        response.set_cookie('session', '', expires=0, path='/')
        return response

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files from static directory"""
    if app.static_folder:
        return send_from_directory(app.static_folder, filename)
    return jsonify({"error": "Static folder not configured"}), 404

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve React assets from static/assets directory"""
    if app.static_folder:
        return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)
    return jsonify({"error": "Static folder not configured"}), 404

@app.route('/temp_audio/<path:filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    # Use absolute path to temp_audio directory in backend folder
    temp_audio_dir = os.path.join(os.path.dirname(__file__), "temp_audio")
    return send_from_directory(temp_audio_dir, filename)

# @app.route('/query')
# @login_required
# def serve_query():
#     """Query page with voice interface - React app handles this now"""
#     # This route is now handled by React Router
#     pass

@app.route('/api/health')
def health_check():
    """Simple health check endpoint - must respond quickly"""
    try:
        # Simple health check - don't check external services to avoid timeouts
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/api/debug/auth')
def debug_auth():
    """Debug authentication status"""
    return jsonify({
        "is_authenticated": current_user.is_authenticated,
        "user_id": current_user.get_id() if current_user.is_authenticated else None,
        "username": current_user.username if current_user.is_authenticated else None,
        "role": current_user.role if current_user.is_authenticated else None
    })

@app.route('/api/debug/sheets')
def debug_sheets():
    """Debug Google Sheets connection"""
    try:
        google_sheets_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        sheet_name = os.getenv("GOOGLE_SHEET_NAME", "SHEETS")
        
        if not google_sheets_credentials:
            return jsonify({
                "error": "GOOGLE_SHEETS_CREDENTIALS not found in environment variables"
            })
        
        import json
        creds_dict = json.loads(google_sheets_credentials)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Try to list available spreadsheets
        try:
            available_sheets = client.openall()
            sheet_titles = [s.title for s in available_sheets]
            
            # Try to access the specific sheet
            try:
                target_sheet = client.open(sheet_name)
                sheet_data = target_sheet.sheet1.get_all_records()
                sample_row = sheet_data[0] if sheet_data else {}
                return jsonify({
                    "success": True,
                    "sheet_name": sheet_name,
                    "available_sheets": sheet_titles,
                    "row_count": len(sheet_data),
                    "sample_row": sample_row,
                    "service_account_email": creds_dict.get("client_email", "unknown")
                })
            except Exception as sheet_error:
                return jsonify({
                    "error": f"Could not access sheet '{sheet_name}': {str(sheet_error)}",
                    "available_sheets": sheet_titles,
                    "service_account_email": creds_dict.get("client_email", "unknown")
                })
                
        except Exception as list_error:
            return jsonify({
                "error": f"Could not list sheets: {str(list_error)}",
                "service_account_email": creds_dict.get("client_email", "unknown")
            })
            
    except Exception as e:
        return jsonify({
            "error": f"Failed to initialize Google Sheets: {str(e)}"
        })

@app.route('/api/debug/data')
def debug_data():
    """Debug local data loading"""
    try:
        data = load_local_data()
        return jsonify({
            "status": "success",
            "data_count": len(data) if data else 0,
            "sample_data": data[:2] if data else [],
            "data_locations_tried": ["backend/data/logged_stats.json", "data/logged_stats.json", "/app/backend/data/logged_stats.json"]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        })

@app.route('/api/debug/claude')
def debug_claude():
    """Debug Claude connection"""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        api_key_present = bool(api_key)
        
        # Try to create a new client directly in this endpoint
        test_client = None
        test_error = None
        
        try:
            from anthropic import Anthropic
            # Try without any extra arguments to avoid proxy issues
            test_client = Anthropic(api_key=api_key)
            # Test with a simple API call
            test_response = test_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            test_success = True
        except Exception as e:
            test_error = str(e)
            test_success = False
        
        if claude is None:
            return jsonify({
                "status": "error",
                "message": "Claude not initialized during startup",
                "claude": None,
                "api_key_present": api_key_present,
                "api_key_preview": api_key[:10] + "..." if api_key else None,
                "test_client_creation": test_success,
                "test_error": test_error,
                "anthropic_import_success": "anthropic imported successfully"
            })
        
        # Try to make a simple test call
        try:
            # This is a minimal test - just check if the client can be created
            return jsonify({
                "status": "success",
                "message": "Claude connected",
                "claude": "initialized",
                "api_key_present": api_key_present,
                "api_key_preview": api_key[:10] + "..." if api_key else None,
                "test_client_creation": test_success,
                "test_error": test_error
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Claude test failed: {e}",
                "claude": None,
                "api_key_present": api_key_present,
                "api_key_preview": api_key[:10] + "..." if api_key else None,
                "test_client_creation": test_success,
                "test_error": test_error
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Debug error: {e}",
            "claude": None,
            "api_key_present": bool(os.getenv("ANTHROPIC_API_KEY"))
        })

@app.route('/api/session')
def session_info():
    if current_user.is_authenticated:
        # Check if user needs Google Drive auth (admin users only)
        needs_drive_auth = False
        if current_user.role in ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor']:
            # Check if Google Drive is authenticated
            drive_authenticated = session.get('google_drive_authenticated', False)
            # Check if token is still valid
            token_expiry = session.get('google_drive_token_expiry', 0)
            token_valid = token_expiry > datetime.now(timezone.utc).timestamp()
            
            # Admin users need Drive auth if not authenticated or token expired
            needs_drive_auth = not (drive_authenticated and token_valid)
        
        return jsonify({
            "authenticated": True,
            "user": current_user.username,
            "role": current_user.role,
            "campus": current_user.campus,
            "full_name": current_user.full_name,
            "needs_drive_auth": needs_drive_auth,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    else:
        return jsonify({
            "authenticated": False,
            "user": None,
            "role": None,
            "campus": None,
            "full_name": None,
            "needs_drive_auth": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

@app.route('/api/stats')
@login_required
def get_stats():
    # Check if user has recall permissions
    if not current_user.has_permission('recall_stats'):
        return jsonify({"error": "You do not have permission to recall statistics data"}), 403
    
    print(f"[DEBUG] get_stats called - campus_filter: {request.args.get('campus', '')}")
    
    try:
        campus_filter = request.args.get('campus', '').strip()
        
        # For campus pastors, restrict to their campus only
        if current_user.role == 'campus_pastor':
            if campus_filter and campus_filter != current_user.campus:
                return jsonify({
                    "error": f"You can only access data for {safe_campus_name(current_user.campus)[1]} campus"
                }), 403
            # Force campus filter to user's campus
            campus_filter = current_user.campus
        
        # Try to get data from Google Sheets first, fallback to local data
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
                data_source = "Google Sheets"
            except Exception as e:
                logger.warning(f"Google Sheets failed, using local data: {e}")
                rows = load_local_data()
                data_source = "Local Data (Google Sheets failed)"
        else:
            rows = load_local_data()
            data_source = "Local Data (Google Sheets not available)"
        logger.info(f"Retrieved {len(rows)} total rows from {data_source}")
        # Load any link-logged rows from memory (if you store them)
        # If you have a function to get link-logged rows, add them to rows here
        # rows += get_link_logged_rows()
        if not rows:
            logger.warning("No rows found in Google Sheets")
            return jsonify({"stats": [], "encouragements": []})
        # Filter by campus if specified
        if campus_filter:
            # Helper for sorting rows by timestamp (available to both branches)
            def get_row_timestamp(row):
                import re
                from datetime import datetime
                ts = ''
                if isinstance(row, dict):
                    ts = row.get('Timestamp', '') or row.get('Date', '')
                elif isinstance(row, (list, tuple)):
                    ts = row[0] if len(row) > 0 else ''
                try:
                    match = re.match(r'(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}:\d{2}))?', ts)
                    if match:
                        date_part = match.group(1)
                        time_part = match.group(2) or '00:00:00'
                        return datetime.strptime(f'{date_part} {time_part}', '%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass
                return datetime.min
            filtered_rows = []
            for row in rows:
                row_campus = str(row.get('Campus', '')).strip().lower()
                if row_campus == campus_filter.lower():
                    # Support both column name formats
                    total_attendance = row.get('Total Attendance', '') or row.get('Total People in Campus', '')
                    if total_attendance and str(total_attendance).strip():
                        filtered_rows.append(row)
            filtered_rows.sort(key=get_row_timestamp, reverse=True)
            most_recent = filtered_rows[0] if filtered_rows else {}
            
            # Helper function to get value with fallback column names
            def get_stat(primary, fallback=None):
                if isinstance(most_recent, dict):
                    val = most_recent.get(primary, 0)
                    if not val and fallback:
                        val = most_recent.get(fallback, 0)
                    return val
                return 0
            
            stats_for_frontend = {
                'Total Attendance': get_stat('Total Attendance', 'Total People in Campus'),
                'total_attendance': get_stat('Total Attendance', 'Total People in Campus'),
                'New People': get_stat('New People', 'First Time Visitors'),
                'new_people': get_stat('New People', 'First Time Visitors'),
                'New Christians': get_stat('New Christians', 'First Time Christians'),
                'new_christians': get_stat('New Christians', 'First Time Christians'),
                'Youth Attendance': get_stat('Youth Attendance'),
                'youth_attendance': get_stat('Youth Attendance'),
                'Kids Total': get_stat('Kids Total'),
                'kids_total': get_stat('Kids Total'),
                'Connect Groups': get_stat('Connect Groups'),
                'connect_groups': get_stat('Connect Groups')
            }
            encouragements = []
            encouragement = most_recent.get("Encouragement", "") if isinstance(most_recent, dict) else ''
            if encouragement:
                if " | " in encouragement:
                    encouragements.extend(encouragement.split(" | "))
                else:
                    encouragements.append(encouragement)
            logger.info(f"Returning stats for {campus_filter}: {stats_for_frontend}")
            return jsonify({
                "stats": stats_for_frontend,
                "encouragements": encouragements
            })
        else:
            # No campus filter - return the 5 most recent rows overall
            valid_rows = [row for row in rows if (row.get('Total Attendance', '') if isinstance(row, dict) else False) and str(row.get('Total Attendance', '') if isinstance(row, dict) else '').strip()]
            valid_rows.sort(key=get_row_timestamp, reverse=True)
            recent_stats = valid_rows[:5] if valid_rows else []
            stats_for_frontend = []
            for row in recent_stats:
                stats_for_frontend.append({
                    'Total Attendance': row.get('Total Attendance', 0) if isinstance(row, dict) else 0,
                    'total_attendance': row.get('Total Attendance', 0) if isinstance(row, dict) else 0,
                    'New People': row.get('New People', 0) if isinstance(row, dict) else 0,
                    'new_people': row.get('New People', 0) if isinstance(row, dict) else 0,
                    'New Christians': row.get('New Christians', 0) if isinstance(row, dict) else 0,
                    'new_christians': row.get('New Christians', 0) if isinstance(row, dict) else 0,
                    'Youth Attendance': row.get('Youth Attendance', 0) if isinstance(row, dict) else 0,
                    'youth_attendance': row.get('Youth Attendance', 0) if isinstance(row, dict) else 0,
                    'Kids Total': row.get('Kids Total', 0) if isinstance(row, dict) else 0,
                    'kids_total': row.get('Kids Total', 0) if isinstance(row, dict) else 0,
                    'Connect Groups': row.get('Connect Groups', 0) if isinstance(row, dict) else 0,
                    'connect_groups': row.get('Connect Groups', 0) if isinstance(row, dict) else 0
                })
            encouragements = []
            for row in recent_stats:
                encouragement = row.get("Encouragement", "") if isinstance(row, dict) else ''
                if encouragement:
                    if " | " in encouragement:
                        encouragements.extend(encouragement.split(" | "))
                    else:
                        encouragements.append(encouragement)
            logger.info(f"Returning {len(recent_stats)} stats overall (no campus filter)")
            return jsonify({
                "stats": stats_for_frontend,
                "encouragements": encouragements
            })
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return jsonify({"error": "Failed to retrieve stats"}), 500

# Add a decorator to log endpoint and request data
from functools import wraps

def log_endpoint(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            data = request.get_json(silent=True)
        except Exception:
            data = None
        logger.info(f"[API LOG] Endpoint: {request.path} | Method: {request.method} | Data: {data}")
        return f(*args, **kwargs)
    return decorated_function

# Apply the decorator to all API endpoints
@app.route('/api/process_voice', methods=['POST'])
@log_endpoint
@login_required
def process_voice():
    if not request.is_json:
        return jsonify({"error": "Expected JSON request"}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body"}), 400

    text = str(data.get("text", "")).strip()
    campus = str(data.get("campus", "")).strip()
    input_type = str(data.get("input_type", "text")).strip()  # 'voice' or 'text'

    if not text:
        return jsonify({"error": "Missing text"}), 400

    # Always detect campus from text first, then fall back to provided campus
    detected_campus = detect_campus(text)
    if detected_campus:  # If we detected a specific campus
        campus = detected_campus
        logger.info(f"Detected campus from text: {campus}")
    elif campus and campus.lower() not in ['none', 'null', '']:
        logger.info(f"Using provided campus: {campus}")
    else:
        # Smart campus defaulting based on user role when no campus is mentioned
        if current_user.is_authenticated:
            if current_user.role == 'campus_pastor':
                # Campus pastors get their assigned campus by default
                campus = getattr(current_user, 'campus', None)
                if campus:
                    logger.info(f"No campus mentioned - using campus pastor's campus: {campus}")
                else:
                    campus = None  # No assigned campus - will prompt user
            elif current_user.role in ['senior_pastor', 'lead_pastor', 'admin']:
                # Senior leadership gets all campuses by default for queries
                # For stat logging, they'll still need to specify
                campus = None  # Will be handled differently for queries vs logging
                logger.info(f"No campus mentioned - senior leadership (will default to all_campuses for queries)")
            else:
                campus = None  # No campus detected - will prompt user
        else:
            campus = None  # No campus detected - will prompt user
    
    logger.info(f"Final campus: {campus}")
    
    # Enhanced query detection with better natural language understanding
    import re
    text_lower = text.lower()
    
    # Query intent patterns (questions, requests for information)
    query_patterns = [
        r'\b(?:what|how|when|where|why|which|who)\b',
        r'\b(?:tell me|show me|give me|can you|could you|would you)\b',
        r'\b(?:what is|what was|what are|what were)\b',
        r'\b(?:how many|how much|how often|how long)\b',
        r'\b(?:average|total|sum|count|number)\b',
        r'\b(?:compare|comparison|versus|vs)\b',
        r'\b(?:trend|trends|pattern|growth|change)\b',
        r'\b(?:report|summary|overview|recap|review)\b',
        r'\b(?:this week|this month|this year|last week|last month|last year)\b',
        r'\b(?:quarterly|monthly|annual|yearly)\b',
        r'\b(?:best|worst|highest|lowest|top|bottom)\b',
        r'\b(?:percentage|percent|%)\b',
        r'\b(?:increase|decrease|up|down|better|worse)\b'
    ]
    
    # Stat logging patterns (specific numbers being reported)
    stat_patterns = [
        r'\d+\s+(?:people|attendance|total|had|got|there were)',
        r'\d+\s+(?:first\s+time|first-time|first\s+timers?|new\s+people|newcomers?)',
        r'\d+\s+(?:visitors?|guests?)',
        r'\d+\s+(?:info\s+gathered|information\s+gathered|details\s+gathered|cards\s+back|contact\s+cards|info\s+cards|information\s+cards)',
        r'\d+\s+(?:salvations?|decisions?|got\s+saved|conversions?)',
        r'\d+\s+(?:rededication|re-dedication|rededications?)',
        r'\d+\s+(?:youth|teens?)',
        r'\d+\s+(?:kids|children)',
        r'\d+\s+(?:connect\s+groups?|small\s+groups?|groups?)',
        r'\d+\s+(?:dream\s+team|volunteers?|team\s+members?|on\s+dream\s+team)',
        r'\d+\s+(?:baptisms?|baptized|baptismal)',
        r'\d+\s+(?:child\s+dedications?|baby\s+dedications?|dedications?)',
        r'\d+\s+(?:new\s+kids|new\s+children)',
        r'\d+\s+(?:collected|gathered|info|information)'
    ]
    
    is_stat_logging = any(re.search(pattern, text.lower()) for pattern in stat_patterns)
        
    # Load conversation memory
    memory = load_conversation_memory()
    
    # Check if this is a query request vs stat logging
    text_lower = text.lower()
    import re
    
    # FIRST: Check for clear query patterns (these take priority)
    query_keywords = [
        'how many', 'what is', 'what was', "what's", 'tell me', 'give me', 'show me',
        'average', 'last week', 'this week', 'last month', 'this month', 'count', 'query', 'data', 
        'has had', 'had this year', 'had this month', 'had last', 'compare', 'comparison', 
        'vs', 'versus', 'between', 'year over year', 'review', 'annual review', 
        'mid year review', 'mid-year review', 'midyear'
    ]
    
    contains_year = bool(re.search(r'\b20\d{2}\b', text_lower))
    contains_quarter = any(q in text_lower for q in ['q1', 'q2', 'q3', 'q4', 'quarter 1', 'quarter 2', 'quarter 3', 'quarter 4', 'first quarter', 'second quarter', 'third quarter', 'fourth quarter'])
    
    # Enhanced query detection with better natural language understanding
    is_query = False
    
    # Check for query patterns with improved detection
    query_indicators = [
        # Question words
        any(word in text_lower for word in ['what', 'how', 'when', 'where', 'why', 'which', 'who']),
        # Request words
        any(phrase in text_lower for phrase in ['tell me', 'show me', 'give me', 'can you', 'could you', 'would you']),
        # Information seeking
        any(phrase in text_lower for phrase in ['what is', 'what was', 'what are', 'what were', 'how many', 'how much']),
        # Analysis words
        any(word in text_lower for word in ['average', 'total', 'sum', 'count', 'number', 'compare', 'comparison']),
        # Time references
        any(phrase in text_lower for phrase in ['this week', 'this month', 'this year', 'last week', 'last month', 'last year']),
        # Report words
        any(word in text_lower for word in ['report', 'summary', 'overview', 'recap', 'review', 'trend', 'trends']),
        # Year/quarter references
        contains_year or contains_quarter,
        # Starts with question words
        text_lower.startswith(('what', 'how', 'show', 'give', 'tell', 'can you', 'could you'))
    ]
    
    is_query = any(query_indicators)
    
    # Validate campus exists if provided (AFTER query detection)
    if campus and campus.lower() != 'all_campuses':  # Skip validation for all_campuses
        try:
            campuses_data = get_campuses_for_user()
            valid_campus_ids = [c['id'] for c in campuses_data.get('campuses', [])]
            
            if campus.lower() not in [c_id.lower() for c_id in valid_campus_ids]:
                return jsonify({
                    'error': f'Invalid campus: {campus}. Please select a valid campus.',
                    'text': f'Invalid campus selected. Please choose from the available campuses.',
                    'requires_campus_selection': True
                }), 400
                
        except Exception as e:
            logger.warning(f"Could not validate campus access: {str(e)}")
            # Continue processing if campus validation fails (for backward compatibility)

    # Load conversation memory
    memory = load_conversation_memory()
    
    # Check if this is a query request vs stat logging
    text_lower = text.lower()
    import re
    
    # FIRST: Check for clear query patterns (these take priority)
    query_keywords = [
        'how many', 'what is', 'what was', "what's", 'tell me', 'give me', 'show me',
        'average', 'last week', 'this week', 'last month', 'this month', 'count', 'query', 'data', 
        'has had', 'had this year', 'had this month', 'had last', 'compare', 'comparison', 
        'vs', 'versus', 'between', 'year over year', 'review', 'annual review', 
        'mid year review', 'mid-year review', 'midyear'
    ]
    
    contains_year = bool(re.search(r'\b20\d{2}\b', text_lower))
    contains_quarter = any(q in text_lower for q in ['q1', 'q2', 'q3', 'q4', 'quarter 1', 'quarter 2', 'quarter 3', 'quarter 4', 'first quarter', 'second quarter', 'third quarter', 'fourth quarter'])
    
    # Enhanced query detection with better natural language understanding
    is_query = False
    
    # Check for query patterns with improved detection
    query_indicators = [
        # Question words
        any(word in text_lower for word in ['what', 'how', 'when', 'where', 'why', 'which', 'who']),
        # Request words
        any(phrase in text_lower for phrase in ['tell me', 'show me', 'give me', 'can you', 'could you', 'would you']),
        # Information seeking
        any(phrase in text_lower for phrase in ['what is', 'what was', 'what are', 'what were', 'how many', 'how much']),
        # Analysis words
        any(word in text_lower for word in ['average', 'total', 'sum', 'count', 'number', 'compare', 'comparison']),
        # Time references
        any(phrase in text_lower for phrase in ['this week', 'this month', 'this year', 'last week', 'last month', 'last year']),
        # Report words
        any(word in text_lower for word in ['report', 'summary', 'overview', 'recap', 'review', 'trend', 'trends']),
        # Year/quarter references
        contains_year or contains_quarter,
        # Starts with question words
        text_lower.startswith(('what', 'how', 'show', 'give', 'tell', 'can you', 'could you'))
    ]
    
    is_query = any(query_indicators)
    
    # If it's not clearly a query, check for stat logging patterns
    if not is_query:
        stat_logging_patterns = [
            r'\d+\s+(?:people|attendance|total|had|got|there were)',
            r'\d+\s+(?:new(?:\s+people|visitors?|guests?)?|np)',
            r'\d+\s+(?:salvations|new\s+christians|decisions|baptisms?|nc)',
            r'\d+\s+(?:youth(?:\s+group|\s+ministry)?|teens?|yout)',
            r'\d+\s+(?:kids|children|kids\s+ministry|nursery)',
            r'\d+\s+(?:connect\s+groups?|small\s+groups?|connects?|life\s+groups?)',
            r'\$?\d+(?:,\d{3})*(?:\.\d{2})?\s+(?:tithe|offering|giving|in\s+tithe)',
            r'\d+\s+(?:volunteers?|team\s+members?|servers?)'
        ]
        
        # Only treat as stat logging if it contains actual numbers and no query keywords
        contains_stat_logging = any(re.search(pattern, text_lower) for pattern in stat_logging_patterns)
        
        # Final check: if it has stat logging patterns but also query words, it's a query
        if contains_stat_logging and any(word in text_lower for word in query_keywords):
            is_query = True
    
    # Handle case where no campus is detected
    if campus is None or campus == "None" or campus == "null":
        # For queries, apply smart defaulting based on user role
        if is_query and current_user.is_authenticated:
            if current_user.role in ['senior_pastor', 'lead_pastor', 'admin']:
                campus = 'all_campuses'
                logger.info(f"Query with no campus - defaulting to all_campuses for senior leadership")
            elif current_user.role == 'campus_pastor':
                campus = getattr(current_user, 'campus', 'all_campuses')
                logger.info(f"Query with no campus - using campus pastor's assigned campus: {campus}")
        else:
            campus = 'all_campuses'  # Default for other roles
            logger.info(f"Query with no campus - defaulting to all_campuses for other roles")
    
    # For stat logging, require campus selection
            return jsonify({
                "text": "I'd be happy to help you input stats! Which campus would you like to input stats for? You can say something like 'Salisbury campus', 'South campus', or just 'Salisbury' or 'South'.",
                "campus": None,
                "stats": {},
                "missing_stats": [],
                "suggestions": ["Try saying: 'Salisbury campus', 'South campus', 'Paradise campus', 'Adelaide City campus'"],
                "insights": ["Please select a campus first"]
            })
    
    # Check permissions based on operation type
    if is_query:
        # Check if user has recall permissions
        if not current_user.has_permission('recall_stats'):
            error_text = "I'm sorry, you don't have permission to query statistics data. You can only log new statistics."
            
            # Generate audio with ElevenLabs if available
            audio_url = None
            if elevenlabs_api_key:
                audio_url = generate_audio_with_elevenlabs(error_text)
            
            return jsonify({
                "error": "You do not have permission to query statistics data",
                "text": error_text,
                "campus": campus,
                "stats": {},
                "missing_stats": [],
                "suggestions": [],
                "insights": ["Permission denied for data queries"],
                "audio_url": audio_url
            }), 403
            
        # For campus pastors, validate they can only access their campus data
        if current_user.role == 'campus_pastor':
            detected_campus = detect_campus(text)
            if detected_campus and detected_campus != 'all_campuses':
                if not current_user.has_permission('recall_stats', detected_campus):
                    error_text = f"I'm sorry, you can only access data for {safe_campus_name(current_user.campus)[1]} campus."
                    
                    # Generate audio with ElevenLabs if available
                    audio_url = None
                    if elevenlabs_api_key:
                        audio_url = generate_audio_with_elevenlabs(error_text)
                    
                    return jsonify({
                        "error": f"You can only access data for {safe_campus_name(current_user.campus)[1]} campus",
                        "text": error_text,
                        "campus": campus,
                        "stats": {},
                        "missing_stats": [],
                        "suggestions": [],
                        "insights": ["Access restricted to your campus only"],
                        "audio_url": audio_url
                    }), 403
            elif detected_campus == 'all_campuses' or not detected_campus:
                # Modify query to restrict to user's campus
                text = text + f" for {safe_campus_name(current_user.campus)[1]}"
                
        # Call the query endpoint internally
        query_data = {"question": text}
    else:
        # Check if user has log permissions for stat logging
        if not current_user.has_permission('log_stats'):
            error_text = "I'm sorry, you don't have permission to log statistics data."
            
            # Generate audio with ElevenLabs if available
            audio_url = None
            if elevenlabs_api_key:
                audio_url = generate_audio_with_elevenlabs(error_text)
            
            return jsonify({
                "error": "You do not have permission to log statistics",
                "text": error_text,
                "campus": campus,
                "stats": {},
                "missing_stats": [],
                "suggestions": [],
                "insights": ["Permission denied for data logging"],
                "audio_url": audio_url
            }), 403

    # Process based on operation type
    if is_query:
        # Call the query endpoint internally
        query_data = {"question": text}
        query_response = query_data_internal(query_data)
        if not query_response:
            return jsonify({"error": "No response from query_data_internal"}), 500
        # Format response for frontend
        if query_response and "error" in query_response:
            response_text = query_response["error"]
        else:
            # Use the actual report text if available, otherwise fallback
            response_text = query_response.get("text", query_response.get("answer", "I couldn't find that information."))
        
        # Generate audio with ElevenLabs if available - ONLY for voice input
        audio_url = None
        if elevenlabs_api_key and input_type == 'voice':
            audio_url = generate_audio_with_elevenlabs(response_text)
        
        # Format response for frontend - preserve all query fields and force popup
        response = {
            "text": response_text,
            "campus": display_campus_name(campus),
            "stats": {},
            "missing_stats": [],
            "suggestions": [],
            "insights": [response_text],
            "audio_url": audio_url,
            "popup": True  # Force popup for all queries
        }
        
        # Preserve all query fields from query_response
        if "report" in query_response:
            response["report"] = query_response["report"]
        if "analysis" in query_response:
            response["analysis"] = query_response["analysis"]
        if "question" in query_response:
            response["question"] = query_response["question"]
        if "answer" in query_response:
            response["answer"] = query_response["answer"]
        # Preserve comparison fields
        if "comparison" in query_response:
            response["comparison"] = query_response["comparison"]
        if "reports" in query_response:
            response["reports"] = query_response["reports"]
        if "percent_changes" in query_response:
            response["percent_changes"] = query_response["percent_changes"]
        if "years" in query_response:
            response["years"] = query_response["years"]
        if "period_type" in query_response:
            response["period_type"] = query_response["period_type"]
        if "period_value" in query_response:
            response["period_value"] = query_response["period_value"]
        
        return jsonify(response)
    
    # Extract stats with enhanced context
    result = extract_stats_with_context(text, campus)
    
    # Generate insights with memory
    insights = generate_encouragement_with_memory(text, campus, memory)
    
    # Detect missing stats
    missing_stats = detect_missing_stats(text, campus)
    
    # Update memory
    if campus not in memory:
        memory[campus] = []
    memory[campus].append(result)
    save_conversation_memory(memory)

    # Log to Google Sheet if available
    if sheet:
        try:
            # Use Adelaide timezone for Australian campuses
            from zoneinfo import ZoneInfo
            adelaide_tz = ZoneInfo('Australia/Adelaide')
            now = datetime.now(adelaide_tz)
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            
            # Calculate Sunday date (the Sunday that just passed)
            today = datetime.now()
            days_since_sunday = (today.weekday() + 1) % 7
            sunday_date = (today - timedelta(days=days_since_sunday)).strftime('%Y-%m-%d')
            
            date = sunday_date
            
            # Create row in exact column order matching full structure:
            # A=Timestamp, B=Date, C=Campus, D=Total Attendance, E=First Time Visitors, F=Visitors, G=Cards Back,
            # H=First Time Christians, I=Rededications, J=Youth Attendance, K=Youth Salvations, L=Youth New People,
            # M=Kids Attendance, N=Kids Leaders, O=New Kids, P=New Kids Salvations, Q=Connect Groups, R=Dream Team, S=Tithe, T=Baptisms, U=Child Dedications
            row = [
                timestamp,  # A - Timestamp
                date,  # B - Date (Sunday date)
                result.get("Campus", display_campus_name(campus)),  # C - Campus
                result.get("Total Attendance", ""),  # D - Total Attendance
                result.get("First Time Visitors", ""),  # E - First Time Visitors
                result.get("Visitors", ""),  # F - Visitors
                result.get("Cards Back", ""),  # G - Cards Back
                result.get("First Time Christians", ""),  # H - First Time Christians
                result.get("Rededications", ""),  # I - Rededications
                result.get("Youth Attendance", ""),  # J - Youth Attendance
                result.get("Youth Salvations", ""),  # K - Youth Salvations
                result.get("Youth New People", ""),  # L - Youth New People
                result.get("Kids Attendance", ""),  # M - Kids Attendance
                result.get("Kids Leaders", ""),  # N - Kids Leaders
                result.get("New Kids", ""),  # O - New Kids
                result.get("New Kids Salvations", ""),  # P - New Kids Salvations
                result.get("Connect Groups", ""),  # Q - Connect Groups
                result.get("Dream Team", ""),  # R - Dream Team
                result.get("Tithe", ""),  # S - Tithe
                result.get("Baptisms", ""),  # T - Baptisms
                result.get("Child Dedications", "")  # U - Child Dedications
            ]
            sheet.append_row(row, value_input_option='USER_ENTERED', table_range='A1')
        except Exception as e:
            logger.error(f"Failed to log to Google Sheets: {e}")

    # Always return campus and stats in a way the frontend expects
    # Convert result to frontend-expected format
    frontend_stats = {}
    for key, value in result.items():
        if key in ["Total Attendance", "New People", "New Christians", "Youth Attendance", "Kids Total", "Connect Groups", "Tithe Amount", "Volunteers"]:
            # Convert to frontend expected keys
            frontend_key = key.lower().replace(" ", "_")
            if value and str(value).strip():
                frontend_stats[frontend_key] = value
                logger.info(f"✅ Converting {key} -> {frontend_key} = {value}")
            else:
                logger.info(f"❌ Skipping {key} -> {frontend_key} (empty value: {value})")
        else:
            logger.info(f"⚠️ Skipping unknown key: {key}")
    
    # Debug logging
    logger.info(f"Extracted stats: {result}")
    logger.info(f"Frontend stats: {frontend_stats}")
    
    # Generate response text
    response_text = insights[0] if insights else "Thanks for inputting those stats!"
    
    # Generate audio with ElevenLabs if available
    audio_url = None
    if elevenlabs_api_key:
        audio_url = generate_audio_with_elevenlabs(response_text)
    
    return jsonify({
        "text": response_text,
        "campus": display_campus_name(campus),
        "stats": frontend_stats,
        "missing_stats": missing_stats,
        "suggestions": missing_stats,
        "insights": insights,
        "audio_url": audio_url
    })

@app.route('/api/memory/<campus>')
def get_campus_memory(campus: str):
    """Get conversation memory for a specific campus"""
    memory = load_conversation_memory()
    campus_history = memory.get(campus, [])
    return jsonify({
        "campus": campus,
        "history": campus_history[-10:],  # Last 10 entries
        "total_entries": len(campus_history)
    })

@app.route('/api/campuses')
@login_required
def get_campuses():
    """Get list of active campuses for dropdowns based on user permissions"""
    active_campuses = get_active_campuses()
    
    # Filter campuses based on user role and permissions
    if current_user.role == 'admin' or current_user.role == 'senior_leader':
        # Admin and senior leaders see all campuses
        filtered_campuses = active_campuses
        default_campus = "all_campuses"
    elif current_user.role == 'campus_pastor':
        # Campus pastors only see their assigned campus
        filtered_campuses = [c for c in active_campuses if c['id'] == current_user.campus]
        default_campus = current_user.campus
    elif current_user.role == 'finance':
        # Finance users see all campuses (for logging purposes)
        filtered_campuses = active_campuses
        default_campus = "all_campuses"
    elif current_user.role == 'pastor':
        # Pastors see all campuses (for logging purposes)
        filtered_campuses = active_campuses
        default_campus = "all_campuses"
    else:
        # Default to all campuses for unknown roles
        filtered_campuses = active_campuses
        default_campus = "all_campuses"
    
    return jsonify({
        "campuses": [{'id': c['id'], 'name': c['name']} for c in filtered_campuses],
        "default": default_campus
    })

@app.route('/api/campuses/public')
def get_campuses_public():
    """Public endpoint for campuses - no authentication required"""
    try:
        active_campuses = get_active_campuses()
        return jsonify({
            "campuses": [{
                'id': c['id'], 
                'name': c['name'],
                'region_id': c.get('region_id'),
                'region_code': c.get('region_code')
            } for c in active_campuses],
            "default": "all_campuses"
        })
    except Exception as e:
        logger.error(f"Error getting public campuses: {e}")
        return jsonify({"campuses": [], "default": "all_campuses"})

@app.route('/api/campuses/create', methods=['POST'])
@admin_required
def create_campus_api():
    """Create a new campus via API"""
    if not request.is_json:
        return jsonify({"error": "Expected JSON request"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing or invalid JSON body"}), 400
    
    # Extract campus data
    campus_name = data.get('name', '').strip()
    campus_address = data.get('address', '').strip()
    campus_pastor = data.get('pastor', '').strip()
    campus_status = data.get('status', 'active')
    
    if not campus_name:
        return jsonify({"error": "Campus name is required"}), 400
    
    # Load existing campuses
    campuses_db = load_campuses_database()
    
    # Generate campus ID from name
    campus_id = campus_name.lower().replace(' ', '_').replace('-', '_')
    
    # Check if campus already exists
    if campus_id in campuses_db.get('campuses', {}):
        return jsonify({"error": "Campus already exists"}), 400
    
    # Create new campus
    new_campus = {
        "id": campus_id,
        "name": campus_name,
        "display_name": campus_name,
        "slug": campus_id,
        "active": campus_status == 'active',
        "address": campus_address,
        "pastor": campus_pastor,
        "detection_patterns": [campus_name.lower()],
        "created_date": datetime.now().strftime('%Y-%m-%d'),
        "notes": None
    }
    
    # Add to database
    campuses_db['campuses'][campus_id] = new_campus
    
    # Save database
    if save_campuses_database(campuses_db):
        return jsonify({
            "success": True,
            "message": "Campus created successfully",
            "campus": new_campus
        })
    else:
        return jsonify({"error": "Failed to save campus"}), 500

@app.route('/api/campuses/<campus_id>/edit', methods=['POST'])
@admin_required
def edit_campus_api(campus_id):
    """Edit an existing campus via API"""
    if not request.is_json:
        return jsonify({"error": "Expected JSON request"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing or invalid JSON body"}), 400
    
    # Load existing campuses
    campuses_db = load_campuses_database()
    
    # Check if campus exists
    if campus_id not in campuses_db.get('campuses', {}):
        return jsonify({"error": "Campus not found"}), 404
    
    # Update campus data
    campus = campuses_db['campuses'][campus_id]
    
    if 'name' in data:
        campus['name'] = data['name'].strip()
        campus['display_name'] = data['name'].strip()
    
    if 'address' in data:
        campus['address'] = data['address'].strip()
    
    if 'pastor' in data:
        campus['pastor'] = data['pastor'].strip()
    
    if 'status' in data:
        campus['active'] = data['status'] == 'active'
    
    # Save database
    if save_campuses_database(campuses_db):
        return jsonify({
            "success": True,
            "message": "Campus updated successfully",
            "campus": campus
        })
    else:
        return jsonify({"error": "Failed to save campus"}), 500

@app.route('/api/campuses/<campus_id>/delete', methods=['POST'])
@admin_required
def delete_campus_api(campus_id):
    """Delete a campus via API"""
    # Load existing campuses
    campuses_db = load_campuses_database()
    
    # Check if campus exists
    if campus_id not in campuses_db.get('campuses', {}):
        return jsonify({"error": "Campus not found"}), 404
    
    # Check if it's a special campus that shouldn't be deleted
    if campus_id == 'all_campuses':
        return jsonify({"error": "Cannot delete special campus 'all_campuses'"}), 400
    
    # Remove campus
    del campuses_db['campuses'][campus_id]
    
    # Save database
    if save_campuses_database(campuses_db):
        return jsonify({
            "success": True,
            "message": "Campus deleted successfully"
        })
    else:
        return jsonify({"error": "Failed to save campus"}), 500

@app.route('/api/query', methods=['POST'])
@log_endpoint
@login_required
def query():
    """Query historical data and answer questions about stats"""
    if not request.is_json:
        return jsonify({"error": "Expected JSON request"}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body"}), 400

    # Check if user has recall permissions
    if not current_user.has_permission('recall_stats'):
        return jsonify({"error": "You do not have permission to recall statistics data"}), 403

    # For campus pastors, validate they can only access their campus data
    if current_user.role == 'campus_pastor':
        # Extract campus from query if possible
        question = data.get('question', '').lower()
        detected_campus = detect_campus(question)
        
        # If a specific campus is detected, check if user can access it
        if detected_campus and detected_campus != 'all_campuses':
            if not current_user.has_permission('recall_stats', detected_campus):
                return jsonify({
                    "error": f"You can only access data for {safe_campus_name(current_user.campus)[1]} campus"
                }), 403
        # If query is for all campuses, restrict to user's campus
        elif detected_campus == 'all_campuses' or not detected_campus:
            data['question'] = data.get('question', '') + f" for {safe_campus_name(current_user.campus)[1]}"

    # Use the internal function that has review intent handling
    result = query_data_internal(data)
    
    # If there's an error, return it
    if "error" in result:
        return jsonify(result), 400
    
    # If there's a report, return it with the report structure
    if "report" in result:
        return jsonify(result)
    
    # Otherwise, return the normal response
    return jsonify(result)

@app.route('/api/bulk_review', methods=['POST'])
def bulk_review():
    """Parse multi-line review text and return a structured report of all detected stats"""
    if not request.is_json:
        return jsonify({"error": "Expected JSON request"}), 400
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body"}), 400
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": "Missing text"}), 400

    # Split text into lines and try to detect stat/campus/year for each block
    import re
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    campus = None
    # Try to detect campus from the header or any line
    for line in lines:
        detected = detect_campus(line)
        if detected:
            campus = detected
            break
    if not campus:
        campus = "main"  # fallback
    campus_normalized = normalize_campus(campus)

    # Define stat label to stat type mapping (expand as needed)
    stat_map = {
        'souls': 'new_christians',
        'attendance': 'attendance',
        'new people': 'new_people',
        'cg': 'connect_groups', 'cgs': 'connect_groups', 'connect groups': 'connect_groups',
        'dt': 'dream_team', 'dream team': 'dream_team', 'team': 'dream_team',
        'yth': 'youth', 'youth': 'youth',
        'kids': 'kids',
    }
    # For each stat block, look for lines like 'Total Souls:', 'Average Attendance:', etc.
    results = []
    for i, line in enumerate(lines):
        # Try to match stat label
        stat_label_match = re.match(r'(total|average)?\s*([a-zA-Z\u2019\'\s]+):', line, re.IGNORECASE)
        if stat_label_match:
            intent = stat_label_match.group(1) or ''
            stat_label = stat_label_match.group(2).strip().lower()
            # Map to stat type
            stat_type = None
            for key, value in stat_map.items():
                if key in stat_label:
                    stat_type = value
                    break
            if not stat_type:
                continue  # skip unknown stat
            # Look ahead for year lines (e.g., '2025 YTD:', '2024 YTD:')
            year_lines = []
            for j in range(i+1, min(i+5, len(lines))):
                year_match = re.match(r'(20\d{2})\s*(ytd)?', lines[j], re.IGNORECASE)
                if year_match:
                    year = int(year_match.group(1))
                    ytd = bool(year_match.group(2))
                    year_lines.append((year, ytd))
            # For each year, run the stat query
            for year, ytd in year_lines:
                # Use the same stat/campus/year detection logic as comparison
                # For YTD, use Jan 1 to now; else, use full year
                if ytd:
                    start_date = datetime(year, 1, 1)
                    end_date = datetime.now() if year == datetime.now().year else datetime(year, 12, 31)
        else:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
        
        # Get rows data
        rows = []
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
            except Exception as e:
                logger.error(f"Failed to get stats from Google Sheets: {e}")
                rows = []
        if not rows:
            memory = load_conversation_memory()
            # Try all possible normalizations for the campus key
            session_stats = memory.get("session_stats", {})
            campus_history = session_stats.get(campus, [])
            if not campus_history:
                campus_capitalized = campus.title()
                campus_history = session_stats.get(campus_capitalized, [])
            if not campus_history:
                for k in session_stats:
                    if normalize_campus(k) == campus_normalized:
                        campus_history = session_stats[k]
                        break
                if campus_history:
                    campus = campus_capitalized
            rows = campus_history
        # Filter rows by date
        filtered_rows = []
        unique_campuses = set()
        for row in rows:
            row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
            unique_campuses.add(row_campus)
            if row_campus == campus_normalized or campus_normalized in row_campus:
                timestamp_str = row.get("Timestamp", "")
                if timestamp_str:
                    try:
                        if "T" in timestamp_str:
                            row_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            row_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if start_date <= row_date <= end_date:
                            filtered_rows.append(row)
                    except Exception:
                        filtered_rows.append(row)
                else:
                    filtered_rows.append(row)
        print(f"[DEBUG] Unique campuses in data: {sorted(unique_campuses)}")
        # Calculate stat value
        total = 0
        avg = 0
        count = 0
        values = []
        for entry in filtered_rows:
            if stat_type == "attendance":
                val = safe_int(entry.get("Total Attendance") or entry.get("total_attendance"))
            elif stat_type == "new_people":
                val = safe_int(entry.get("New People") or entry.get("new_people"))
            elif stat_type == "new_christians":
                val = safe_int(entry.get("New Christians") or entry.get("new_christians"))
            elif stat_type == "youth":
                val = safe_int(entry.get("Youth Attendance") or entry.get("youth_attendance"))
            elif stat_type == "kids":
                val = safe_int(entry.get("Kids Total") or entry.get("kids_total"))
            elif stat_type == "connect_groups":
                val = safe_int(entry.get("Connect Groups") or entry.get("connect_groups"))
            elif stat_type == "dream_team":
                val = safe_int(entry.get("Volunteers") or entry.get("volunteers"))
            else:
                val = 0
            print(f"[DEBUG] Stat: {stat_type}, Value: {val}, Entry: {entry}")
            if val > 0:
                values.append(val)
                total += val
                count += 1
        if count > 0:
            avg = total / count
        results.append({
            "stat": stat_type,
            "intent": intent.strip().lower() or "total",
            "year": year,
            "ytd": ytd,
            "campus": display_campus_name(campus),
            "total": total,
            "average": round(avg, 1),
            "count": count
        })
    return jsonify({"results": results})

@app.route('/api/test')
def test_route():
    """Test route to verify Flask is working and check Google Sheets data"""
    logger.info("Test route called")
    if sheet:
        try:
            rows = safe_sheets_request(sheet.get_all_records)
            # Get unique campus names
            campus_names = set()
            for row in rows:
                campus = row.get("Campus") or row.get("campus") or ""
                if campus:
                    campus_names.add(campus)
            
            return jsonify({
                "message": "Test route working",
                "total_rows": len(rows),
                "unique_campuses": list(campus_names),
                "sample_row_keys": list(rows[0].keys()) if rows else []
            })
        except Exception as e:
            return jsonify({"error": str(e)})
    else:
        return jsonify({"error": "Google Sheets not connected"})

# Admin routes for campus management
@app.route('/api/admin/campuses', methods=['GET'])
@login_required
def get_admin_campuses():
    """Get all campuses and their service times for admin management"""
    if not current_user.has_permission('system_settings'):
        return jsonify({"error": "Insufficient permissions"}), 403
    
    try:
        global CAMPUS_SERVICE_TIMES
        return jsonify({
            "campuses": CAMPUS_SERVICE_TIMES,
            "success": True
        })
    except Exception as e:
        logger.error(f"Failed to get admin campuses: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/campuses', methods=['POST'])
@login_required
def add_campus():
    """Add a new campus with service times"""
    if not current_user.has_permission('system_settings'):
        return jsonify({"error": "Insufficient permissions"}), 403
    
    try:
        data = request.get_json()
        campus_name = data.get('name', '').strip()
        service_times = data.get('service_times', [])
        
        if not campus_name:
            return jsonify({"error": "Campus name is required"}), 400
        
        if not service_times:
            return jsonify({"error": "At least one service time is required"}), 400
        
        # Validate service times format
        for time in service_times:
            if not isinstance(time, str) or not time.strip():
                return jsonify({"error": "Invalid service time format"}), 400
        
        global CAMPUS_SERVICE_TIMES
        CAMPUS_SERVICE_TIMES[campus_name] = service_times
        
        if save_campus_config(CAMPUS_SERVICE_TIMES):
            logger.info(f"Added new campus: {campus_name} with service times: {service_times}")
            return jsonify({
                "message": f"Campus '{campus_name}' added successfully",
                "campus": {
                    "name": campus_name,
                    "service_times": service_times
                },
                "success": True
            })
        else:
            return jsonify({"error": "Failed to save campus configuration"}), 500
            
    except Exception as e:
        logger.error(f"Failed to add campus: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/campuses/<campus_name>', methods=['PUT'])
@login_required
def update_campus(campus_name):
    """Update service times for an existing campus"""
    if not current_user.has_permission('system_settings'):
        return jsonify({"error": "Insufficient permissions"}), 403
    
    try:
        data = request.get_json()
        service_times = data.get('service_times', [])
        
        if not service_times:
            return jsonify({"error": "At least one service time is required"}), 400
        
        # Validate service times format
        for time in service_times:
            if not isinstance(time, str) or not time.strip():
                return jsonify({"error": "Invalid service time format"}), 400
        
        global CAMPUS_SERVICE_TIMES
        if campus_name not in CAMPUS_SERVICE_TIMES:
            return jsonify({"error": "Campus not found"}), 404
        
        CAMPUS_SERVICE_TIMES[campus_name] = service_times
        
        if save_campus_config(CAMPUS_SERVICE_TIMES):
            logger.info(f"Updated campus: {campus_name} with service times: {service_times}")
            return jsonify({
                "message": f"Campus '{campus_name}' updated successfully",
                "campus": {
                    "name": campus_name,
                    "service_times": service_times
                },
                "success": True
            })
        else:
            return jsonify({"error": "Failed to save campus configuration"}), 500
            
    except Exception as e:
        logger.error(f"Failed to update campus: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/campuses/<campus_name>', methods=['DELETE'])
@login_required
def delete_campus(campus_name):
    """Delete a campus"""
    if not current_user.has_permission('system_settings'):
        return jsonify({"error": "Insufficient permissions"}), 403
    
    try:
        global CAMPUS_SERVICE_TIMES
        if campus_name not in CAMPUS_SERVICE_TIMES:
            return jsonify({"error": "Campus not found"}), 404
        
        if campus_name == 'all_campuses':
            return jsonify({"error": "Cannot delete the 'all_campuses' entry"}), 400
        
        del CAMPUS_SERVICE_TIMES[campus_name]
        
        if save_campus_config(CAMPUS_SERVICE_TIMES):
            logger.info(f"Deleted campus: {campus_name}")
            return jsonify({
                "message": f"Campus '{campus_name}' deleted successfully",
                "success": True
            })
        else:
            return jsonify({"error": "Failed to save campus configuration"}), 500
            
    except Exception as e:
        logger.error(f"Failed to delete campus: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# NEW REGION-AWARE CAMPUS MANAGEMENT API
# ============================================================================

@app.route('/api/weekly-submission-status', methods=['GET'])
@login_required
def get_weekly_submission_status():
    """Get submission status for all campuses for the current week (Saturday-Sunday weekend)"""
    try:
        # Only admins and lead pastors can see this
        if current_user.role not in ['admin', 'lead_pastor', 'senior_pastor', 'senior_leader']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if not sheet:
            return jsonify({'error': 'Google Sheets not connected'}), 500
        
        # Get all records from the sheet with force_refresh to ensure real-time data
        all_records = safe_sheets_request(sheet.get_all_records, force_refresh=True)
        if not all_records:
            return jsonify({'campuses': []})
        
        # Get the most recent Sunday (or today if it's Sunday)
        today = datetime.now()
        days_since_sunday = (today.weekday() + 1) % 7  # Monday is 0, Sunday is 6
        most_recent_sunday = today - timedelta(days=days_since_sunday)
        most_recent_sunday = most_recent_sunday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Also check for Saturday submissions (many campuses submit Saturday evening)
        most_recent_saturday = most_recent_sunday - timedelta(days=1)
        
        # Define campus list
        campus_list = [
            {'id': 'paradise', 'name': 'Paradise'},
            {'id': 'adelaide_city', 'name': 'Adelaide City'},
            {'id': 'salisbury', 'name': 'Salisbury'},
            {'id': 'south', 'name': 'South'},
            {'id': 'mt_barker', 'name': 'Mt Barker'},
            {'id': 'clare_valley', 'name': 'Clare Valley'},
            {'id': 'victor_harbour', 'name': 'Victor Harbor'},
            {'id': 'copper_coast', 'name': 'Copper Coast'}
        ]
        
        # Check submission status for each campus
        campus_status = []
        for campus_info in campus_list:
            campus_id = campus_info['id']
            campus_name = campus_info['name']
            
            # Find the most recent submission for this campus
            latest_submission = None
            latest_date = None
            
            for row in all_records:
                try:
                    # Normalize both campus names for proper comparison
                    row_campus_raw = row.get('Campus', '')
                    row_campus_normalized = normalize_campus(row_campus_raw)
                    campus_id_normalized = normalize_campus(campus_id)
                    
                    # Try to get timestamp - could be in 'Timestamp', first column, or 'Date'
                    timestamp_str = row.get('Timestamp', '') or row.get('timestamp', '') or list(row.values())[0] if row else ''
                    date_str = row.get('Date', '')
                    
                    # Use timestamp if available, otherwise fall back to date
                    date_to_parse = timestamp_str if timestamp_str else date_str
                    
                    if not date_to_parse or row_campus_normalized != campus_id_normalized:
                        continue
                    
                    # Parse date/timestamp with more formats
                    row_date = None
                    date_formats = [
                        '%Y-%m-%d %H:%M:%S',  # 2025-10-15 00:46:43
                        '%Y-%m-%d %H:%M',     # 2025-10-15 00:46
                        '%m/%d/%Y %H:%M:%S',  # 10/15/2025 00:46:43
                        '%d/%m/%Y %H:%M:%S',  # 15/10/2025 00:46:43
                        '%Y-%m-%d',           # 2025-10-15
                        '%m/%d/%Y',           # 10/15/2025
                        '%d/%m/%Y'            # 15/10/2025
                    ]
                    for date_format in date_formats:
                        try:
                            row_date = datetime.strptime(date_to_parse.strip(), date_format)
                            break
                        except ValueError:
                            continue
                    
                    # Accept data from Saturday onwards (not just Sunday)
                    if row_date and row_date >= most_recent_saturday:
                        if latest_date is None or row_date > latest_date:
                            latest_date = row_date
                            latest_submission = row
                except Exception as e:
                    logger.error(f"Error parsing row for {campus_id}: {e}")
                    continue
            
            # Determine status
            status = 'submitted' if latest_submission else 'not_submitted'
            last_submitted = latest_date.strftime('%A, %I:%M %p') if latest_date else None
            
            campus_status.append({
                'id': campus_id,
                'name': campus_name,
                'status': status,
                'last_submitted': last_submitted,
                'week_start': most_recent_saturday.strftime('%B %d, %Y')  # Show Saturday as week start
            })
        
        return jsonify({
            'campuses': campus_status,
            'week_start': most_recent_saturday.strftime('%B %d, %Y')  # Show Saturday as week start
        })
        
    except Exception as e:
        logger.error(f"Error getting weekly submission status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/regions', methods=['GET'])
def get_regions():
    """Get all regions"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, code, display_name, timezone, currency, active, coming_soon, launch_date
            FROM regions
            ORDER BY active DESC, display_name ASC
        """)
        
        regions = []
        for row in cursor.fetchall():
            regions.append({
                'id': row[0],
                'name': row[1],
                'code': row[2],
                'display_name': row[3],
                'timezone': row[4],
                'currency': row[5],
                'active': bool(row[6]),
                'coming_soon': bool(row[7]),
                'launch_date': row[8]
            })
        
        return jsonify({'regions': regions})
    except Exception as e:
        logger.error(f"Failed to get regions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v2/campuses', methods=['GET'])
@login_required
def get_campuses_v2():
    """Get all campuses with region information"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get campuses with region info
        cursor.execute("""
            SELECT 
                c.id, c.campus_id, c.name, c.display_name, c.region_id,
                c.pastor_name, c.pastor_email, c.address, c.city, c.state,
                c.postal_code, c.country, c.active, c.service_times,
                c.detection_patterns, c.notes, c.created_at,
                r.name as region_name, r.code as region_code, r.display_name as region_display_name
            FROM campuses_new c
            LEFT JOIN regions r ON c.region_id = r.id
            ORDER BY r.display_name, c.display_name
        """)
        
        campuses = []
        for row in cursor.fetchall():
            service_times = json.loads(row[13]) if row[13] else []
            detection_patterns = json.loads(row[14]) if row[14] else []
            
            campuses.append({
                'id': row[0],
                'campus_id': row[1],
                'name': row[2],
                'display_name': row[3],
                'region_id': row[4],
                'pastor_name': row[5],
                'pastor_email': row[6],
                'address': row[7],
                'city': row[8],
                'state': row[9],
                'postal_code': row[10],
                'country': row[11],
                'active': bool(row[12]),
                'service_times': service_times,
                'detection_patterns': detection_patterns,
                'notes': row[15],
                'created_at': row[16],
                'region': {
                    'name': row[17],
                    'code': row[18],
                    'display_name': row[19]
                }
            })
        
        return jsonify({'campuses': campuses})
    except Exception as e:
        logger.error(f"Failed to get campuses: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v2/campuses', methods=['POST'])
@admin_required
def create_campus_v2():
    """Create a new campus"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['name', 'display_name', 'region_id']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate campus_id from name
        campus_id = data['name'].lower().replace(' ', '_').replace('-', '_')
        
        # Prepare service times and detection patterns
        service_times = json.dumps(data.get('service_times', []))
        detection_patterns = json.dumps(data.get('detection_patterns', [campus_id.replace('_', ' ')]))
        
        # Insert into database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO campuses_new 
            (campus_id, name, display_name, region_id, pastor_name, pastor_email, 
             address, city, state, postal_code, country, active, service_times, 
             detection_patterns, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            campus_id,
            data['name'],
            data['display_name'],
            data['region_id'],
            data.get('pastor_name', ''),
            data.get('pastor_email', ''),
            data.get('address', ''),
            data.get('city', ''),
            data.get('state', ''),
            data.get('postal_code', ''),
            data.get('country', ''),
            1 if data.get('active', True) else 0,
            service_times,
            detection_patterns,
            data.get('notes', '')
        ))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Campus created successfully",
            "campus_id": campus_id
        })
    except Exception as e:
        logger.error(f"Failed to create campus: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v2/campuses/<campus_id>', methods=['PUT'])
@admin_required
def update_campus_v2(campus_id):
    """Update an existing campus"""
    try:
        data = request.get_json()
        
        # Prepare service times and detection patterns
        service_times = json.dumps(data.get('service_times', []))
        detection_patterns = json.dumps(data.get('detection_patterns', []))
        
        # Update database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE campuses_new
            SET name = ?, display_name = ?, region_id = ?, pastor_name = ?, 
                pastor_email = ?, address = ?, city = ?, state = ?, postal_code = ?,
                country = ?, active = ?, service_times = ?, detection_patterns = ?, notes = ?
            WHERE campus_id = ?
        """, (
            data.get('name'),
            data.get('display_name'),
            data.get('region_id'),
            data.get('pastor_name', ''),
            data.get('pastor_email', ''),
            data.get('address', ''),
            data.get('city', ''),
            data.get('state', ''),
            data.get('postal_code', ''),
            data.get('country', ''),
            1 if data.get('active', True) else 0,
            service_times,
            detection_patterns,
            data.get('notes', ''),
            campus_id
        ))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Campus updated successfully"
        })
    except Exception as e:
        logger.error(f"Failed to update campus: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v2/campuses/<campus_id>', methods=['DELETE'])
@admin_required
def delete_campus_v2(campus_id):
    """Delete a campus"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM campuses_new WHERE campus_id = ?", (campus_id,))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Campus deleted successfully"
        })
    except Exception as e:
        logger.error(f"Failed to delete campus: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# END NEW REGION-AWARE CAMPUS MANAGEMENT API
# ============================================================================

@app.route('/api/service-times', methods=['GET'])
def get_service_times():
    """Get service times for all campuses or a specific campus"""
    campus = request.args.get('campus')
    
    if campus:
        service_times = get_campus_service_times(campus)
        return jsonify({
            "campus": display_campus_name(campus),
            "service_times": service_times
        })
    else:
        all_service_times = get_all_service_times()
        return jsonify({
            "all_campuses": all_service_times
        })

@app.route('/api/service-times', methods=['POST'])
@login_required
@admin_required
def update_service_times():
    """Update service times for a campus (admin only)"""
    try:
        data = request.get_json()
        campus = data.get('campus')
        service_times = data.get('service_times', [])
        
        if not campus or not service_times:
            return jsonify({"error": "Campus and service_times are required"}), 400
        
        # Validate service times format
        valid_times = []
        for time_str in service_times:
            # Basic validation - could be enhanced
            if isinstance(time_str, str) and len(time_str) > 0:
                valid_times.append(time_str)
        
        if not valid_times:
            return jsonify({"error": "No valid service times provided"}), 400
        
        # Update the configuration (in a real app, this would be saved to database)
        campus_key = display_campus_name(campus)
        CAMPUS_SERVICE_TIMES[campus_key] = valid_times
        
        return jsonify({
            "success": True,
            "campus": campus_key,
            "service_times": valid_times,
            "message": f"Service times updated for {campus_key}"
        })
        
    except Exception as e:
        logger.error(f"Error updating service times: {e}")
        return jsonify({"error": "Failed to update service times"}), 500

@app.route('/api/test_voice', methods=['POST'])
def test_voice_processing():
    """Test voice processing functionality with enhanced debugging"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        text = data.get('text', '')
        campus = data.get('campus', '')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Test preprocessing
        processed_text = preprocess_voice_text(text)
        
        # Test stat extraction
        stats = extract_stats_with_context(text, campus)
        
        # Test campus detection
        detected_campus = detect_campus(text)
        
        # Test pattern matching for debugging
        pattern_matches = {}
        search_text = processed_text if processed_text else text
        for key, pattern in patterns.items():
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                pattern_matches[key] = {
                    "matched_text": match.group(0),
                    "extracted_value": match.group(1),
                    "pattern": pattern
                }
        
        # Test query detection
        text_lower = text.lower()
        query_keywords = [
            'how many', 'what is', 'what was', "what's", 'tell me', 'give me', 'show me',
            'average', 'last week', 'this week', 'last month', 'this month', 'count', 'query', 'data'
        ]
        is_query = any(word in text_lower for word in query_keywords)
        
        return jsonify({
            "original_text": text,
            "processed_text": processed_text,
            "detected_campus": detected_campus,
            "extracted_stats": stats,
            "pattern_matches": pattern_matches,
            "patterns_matched": len(pattern_matches),
            "total_patterns": len(patterns),
            "is_query": is_query,
            "message": "Voice processing test completed with enhanced debugging"
        })
        
    except Exception as e:
        logger.error(f"Voice test error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test_voice_enhanced', methods=['POST'])
def test_voice_parsing_enhanced():
    """Enhanced voice parsing test with detailed debugging and confidence scoring"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        text = data.get('text', '')
        campus = data.get('campus', '')
        confidence = data.get('confidence', 0)
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Enhanced preprocessing with confidence tracking
        original_text = text
        processed_text = preprocess_voice_text(text)
        
        # Test stat extraction with confidence
        stats = extract_stats_with_context(text, campus)
        
        # Test campus detection with confidence
        detected_campus = detect_campus(text)
        
        # Enhanced pattern matching with confidence scoring
        pattern_matches = {}
        search_text = processed_text if processed_text else text
        total_confidence = 0
        match_count = 0
        
        for key, pattern in patterns.items():
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                match_count += 1
                # Calculate pattern confidence based on match quality
                match_text = match.group(0)
                pattern_confidence = min(1.0, len(match_text) / len(search_text) + 0.3)
                total_confidence += pattern_confidence
                
                pattern_matches[key] = {
                    "matched_text": match_text,
                    "extracted_value": match.group(1),
                    "pattern": pattern,
                    "confidence": pattern_confidence,
                    "position": match.start()
                }
        
        # Calculate overall parsing confidence
        overall_confidence = (total_confidence / max(match_count, 1)) * confidence if match_count > 0 else 0
        
        # Test query detection with enhanced patterns
        text_lower = text.lower()
        query_keywords = [
            'how many', 'what is', 'what was', "what's", 'tell me', 'give me', 'show me',
            'average', 'last week', 'this week', 'last month', 'this month', 'count', 'query', 'data',
            'has had', 'had this year', 'had this month', 'had last', 'compare', 'comparison',
            'vs', 'versus', 'between', 'year over year', 'review', 'annual review',
            'mid year review', 'mid-year review', 'midyear', 'trend', 'trends', 'growth',
            'percentage', 'percent', '%', 'increase', 'decrease', 'up', 'down'
        ]
        
        query_confidence = 0
        query_matches = []
        for keyword in query_keywords:
            if keyword in text_lower:
                query_matches.append(keyword)
                query_confidence += 0.1
        
        is_query = query_confidence > 0.1
        
        # Enhanced campus detection with fuzzy matching
        campus_confidence = 0
        campus_matches = []
        if detected_campus:
            campus_confidence = 0.8
            campus_matches.append(detected_campus)
        
        # Test for common voice recognition issues
        voice_issues = []
        if len(text.split()) < 3:
            voice_issues.append("Very short input - may be incomplete")
        if confidence < 0.5:
            voice_issues.append("Low confidence - consider retrying")
        if not any(char.isdigit() for char in text):
            voice_issues.append("No numbers detected - may be a query")
        
        # Generate suggestions for improvement
        suggestions = []
        if overall_confidence < 0.5:
            suggestions.append("Try speaking more clearly and including specific numbers")
        if not is_query and match_count == 0:
            suggestions.append("Consider rephrasing as a question or including specific stats")
        if campus_confidence < 0.5:
            suggestions.append("Try mentioning a specific campus name")
        
        return jsonify({
            "original_text": original_text,
            "processed_text": processed_text,
            "voice_confidence": confidence,
            "overall_parsing_confidence": overall_confidence,
            "detected_campus": detected_campus,
            "campus_confidence": campus_confidence,
            "campus_matches": campus_matches,
            "extracted_stats": stats,
            "pattern_matches": pattern_matches,
            "patterns_matched": len(pattern_matches),
            "total_patterns": len(patterns),
            "is_query": is_query,
            "query_confidence": query_confidence,
            "query_matches": query_matches,
            "voice_issues": voice_issues,
            "suggestions": suggestions,
            "processing_quality": {
                "text_length": len(text),
                "word_count": len(text.split()),
                "has_numbers": any(char.isdigit() for char in text),
                "has_campus_mention": bool(detected_campus),
                "has_query_keywords": is_query,
                "has_stat_patterns": match_count > 0
            },
            "message": "Enhanced voice parsing test completed with detailed analysis"
        })
        
    except Exception as e:
        logger.error(f"Enhanced voice test error: {e}")
        return jsonify({"error": str(e)}), 500

# Update greeting_audio endpoint to use the correct filename
@app.route('/api/greeting_audio')
def greeting_audio():
    """Generate and serve the greeting audio using ElevenLabs, cache for reuse."""
    logger.info("Greeting audio endpoint called")
    greeting_text = "Connected to Futures Link, how can I help you today?"
    
    # Use absolute path for temp_audio directory
    temp_audio_dir = os.path.join(os.path.dirname(__file__), "temp_audio")
    audio_filename = os.path.join(temp_audio_dir, "greeting_elevenlabs.mp3")
    
    try:
        if not os.path.exists(audio_filename):
            logger.info("Greeting audio file does not exist, generating with ElevenLabs...")
            os.makedirs(temp_audio_dir, exist_ok=True)
            audio_url = generate_audio_with_elevenlabs(greeting_text, filename=audio_filename)
            if not audio_url or not os.path.exists(audio_filename):
                logger.error("Failed to generate greeting audio file with ElevenLabs.")
                return jsonify({"error": "Failed to generate greeting audio file."}), 500
            logger.info(f"Greeting audio file generated: {audio_filename}")
        else:
            logger.info(f"Greeting audio file already exists: {audio_filename}")
        logger.info(f"Serving greeting audio file: {audio_filename}")
        return send_from_directory(temp_audio_dir, 'greeting_elevenlabs.mp3')
    except Exception as e:
        logger.error(f"Error in greeting_audio route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/recent_entries', methods=['GET'])
@login_required
def get_recent_entries():
    """Get recent entries for the user's campus (last 7 days)"""
    try:
        # Get campus from query parameter or user's default campus
        campus = request.args.get('campus', '').strip()
        if not campus and hasattr(current_user, 'campus'):
            campus = current_user.campus
        
        if not campus:
            return jsonify({"entries": []}), 200
        
        # Calculate date range (last 7 days) - use date objects for comparison
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        logger.info(f"[RECENT_ENTRIES] Looking for entries from {start_date} to {end_date} for campus '{campus}'")
        
        # Get data from Google Sheets
        entries = []
        if sheet:
            try:
                all_records = safe_sheets_request(sheet.get_all_records)
                
                # Handle "all_campuses" - show entries from all campuses
                show_all_campuses = campus.lower() in ['all_campuses', 'all', 'australia']
                
                print(f"[RECENT_ENTRIES] Requested campus: '{campus}', show_all_campuses: {show_all_campuses}")
                
                if not show_all_campuses:
                    campus_normalized = normalize_campus(campus)
                    logger.info(f"[RECENT_ENTRIES] Processing {len(all_records)} total records, filtering by campus: '{campus_normalized}'")
                else:
                    logger.info(f"[RECENT_ENTRIES] Processing {len(all_records)} total records, showing ALL campuses")
                
                for record in all_records:
                    record_campus_str = record.get('Campus', '')
                    record_date_str = record.get('Date', '')
                    
                    # Skip if no date
                    if not record_date_str:
                        continue
                    
                    # Check campus match (skip if filtering by campus)
                    if not show_all_campuses:
                        record_campus = normalize_campus(record_campus_str)
                        campus_match = (record_campus == campus_normalized or 
                                       campus_normalized in record_campus or
                                       record_campus in campus_normalized)
                        if not campus_match:
                            continue
                    
                    # Check if date is within last 7 days
                    try:
                        # Try different date formats
                        record_date = None
                        for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                            try:
                                record_date = datetime.strptime(str(record_date_str), date_format).date()
                                break
                            except:
                                continue
                        
                        if record_date and start_date <= record_date <= end_date:
                            # Calculate New People and New Christians from the actual field names
                            first_time_visitors = safe_int(record.get('First Time Visitors', 0))
                            visitors = safe_int(record.get('Visitors', 0))
                            new_people = first_time_visitors + visitors
                            
                            first_time_christians = safe_int(record.get('First Time Christians', 0))
                            rededications = safe_int(record.get('Rededications', 0))
                            new_christians = first_time_christians + rededications
                            
                            # Calculate Total Attendance from service times
                            service_times = ['9:00 AM', '10:00 AM', '11:00 AM', '5:00 PM', '5:30 PM']
                            total_attendance = sum(safe_int(record.get(service, 0)) for service in service_times)
                            
                            # If no service time data, try the stored Total Attendance field
                            if total_attendance == 0:
                                total_attendance = safe_int(record.get('Total Attendance', 0))
                            
                            # Calculate Kids Attendance from kids service times
                            kids_service_times = ['Kids 9:00 AM', 'Kids 10:00 AM', 'Kids 11:00 AM', 'Kids 5:00 PM', 'Kids 5:30 PM']
                            kids_attendance = sum(safe_int(record.get(service, 0)) for service in kids_service_times)
                            
                            # If no kids service time data, try the stored Kids Attendance field
                            if kids_attendance == 0:
                                kids_attendance = safe_int(record.get('Kids Attendance', 0))
                            
                            # Ensure we have the required stats fields
                            stats = {
                                'Total Attendance': total_attendance,
                                'Kids Attendance': kids_attendance,
                                'Youth Attendance': safe_int(record.get('Youth Attendance', 0)),
                                'New People': new_people,
                                'New Christians': new_christians,
                                # Include all other fields from the record
                                **record
                            }
                            
                            entries.append({
                                'date': record_date_str,
                                'campus': record_campus_str,  # Always show actual campus name from data
                                'stats': stats
                            })
                            print(f"[RECENT_ENTRIES] Added entry: {record_date_str} for campus '{record_campus_str}'")
                            logger.debug(f"[RECENT_ENTRIES] Added entry: {record_date_str} for {record_campus_str}")
                    except Exception as e:
                        logger.debug(f"[RECENT_ENTRIES] Error parsing date '{record_date_str}': {e}")
                        continue
                
                # Sort by date descending (most recent first), then by campus
                entries.sort(key=lambda x: (x['date'], x['campus']), reverse=True)
                logger.info(f"[RECENT_ENTRIES] Found {len(entries)} matching entries")
                
            except Exception as e:
                logger.error(f"Error fetching recent entries: {e}", exc_info=True)
                return jsonify({"entries": []}), 200
        
        return jsonify({"entries": entries}), 200
        
    except Exception as e:
        logger.error(f"Recent entries error: {e}")
        return jsonify({"entries": []}), 200

@app.route('/api/quick_input', methods=['POST'])
@login_required
def quick_input():
    """Handle quick input form submissions"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        campus = data.get('campus', '').strip()
        date_str = data.get('date', '').strip()
        stats = data.get('stats', {})
        
        if not campus:
            return jsonify({"error": "Campus is required"}), 400
        
        if not date_str:
            return jsonify({"error": "Date is required"}), 400
        
        # Check if user has permission to log stats
        if not current_user.has_permission('log_stats'):
            return jsonify({"error": "You don't have permission to log stats"}), 403
        
        # Save to Google Sheets using the exact headers format
        try:
            # Use the existing sheet connection
            if not sheet:
                return jsonify({"error": "Google Sheets not connected"}), 500
            
            # Get the actual headers from the sheet
            all_records = safe_sheets_request(sheet.get_all_records)
            headers = list(all_records[0].keys()) if all_records else []
            
            # Debug: Log incoming stats
            print(f"[DEBUG] Quick input received stats: {stats}")
            
            # Prepare the row data with the exact Google Sheets headers
            # For empty/zero values, use empty string to match Google Sheets format
            def safe_value(key, default=0):
                val = stats.get(key, default)
                if val == 0 or val == '':
                    return ''
                return safe_int(val)
            
            # Use Adelaide timezone for Australian campuses
            from zoneinfo import ZoneInfo
            adelaide_tz = ZoneInfo('Australia/Adelaide')
            now_adelaide = datetime.now(adelaide_tz)
            
            row_data = {
                'Timestamp': now_adelaide.strftime('%Y-%m-%d %H:%M:%S'),
                'Date': date_str,
                'Campus': campus,
                'Total People in Campus': safe_value('Total People in Campus'),
                'Total Attendance': safe_value('Total Attendance'),
                '9:00 AM': safe_value('9:00 AM'),
                '10:00 AM': safe_value('10:00 AM'),
                '11:00 AM': safe_value('11:00 AM'),
                '5:00 PM': safe_value('5:00 PM'),
                '5:30 PM': safe_value('5:30 PM'),
                'Kids 9:00 AM': safe_value('Kids 9:00 AM'),
                'Kids 10:00 AM': safe_value('Kids 10:00 AM'),
                'Kids 11:00 AM': safe_value('Kids 11:00 AM'),
                'Kids 5:00 PM': safe_value('Kids 5:00 PM'),
                'Kids 5:30 PM': safe_value('Kids 5:30 PM'),
                'Kids Attendance': safe_value('Kids Attendance'),
                'Kids Leaders': safe_value('Kids Leaders'),
                'New Kids': safe_value('New Kids'),
                'New Kids Salvations': safe_value('New Kids Salvations'),
                'First Time Visitors': safe_value('First Time Visitors'),
                'Visitors': safe_value('Visitors'),
                'Cards Back': safe_value('Cards Back'),
                'First Time Christians': safe_value('First Time Christians'),
                'Rededications': safe_value('Rededications'),
                'Salvation Cards Returned': safe_value('Salvation Cards Returned'),
                'Youth Attendance': safe_value('Youth Attendance'),
                'Youth Salvations': safe_value('Youth Salvations'),
                'Youth New People': safe_value('Youth New People'),
                'Connect Groups': safe_value('Connect Groups'),
                'Dream Team': safe_value('Dream Team'),
                'Tithe': safe_value('Tithe'),
                'Baptisms': safe_value('Baptisms'),
                'Child Dedications': safe_value('Child Dedications')
            }
            
            print(f"[DEBUG] Row data prepared: {row_data}")
            
            # Add any missing headers with default values
            for header in headers:
                if header not in row_data:
                    row_data[header] = ''
            
            # Convert to list format for Google Sheets
            row_values = []
            for header in headers:
                value = row_data.get(header, '')
                row_values.append(value)
            
            # Append the row using the sheet's append_row method with explicit parameters
            # This ensures data starts at column A and appends to the next available row
            sheet.append_row(row_values, value_input_option='USER_ENTERED', table_range='A1')
            
            # Clear cache so new entry shows up immediately
            clear_sheets_cache('Stats')
            
            # Generate response text
            total_stats = len([v for v in stats.values() if v and v != 0])
            response_text = f"Successfully input {total_stats} stats for {campus} campus on {date_str}!"
            
            return jsonify({
                "success": True,
                "text": response_text,
                "stats": stats,
                "campus": campus,
                "date": date_str,
                "version": "FULL_FUNCTIONALITY_2025"
            })
            
        except Exception as e:
            logger.error(f"Failed to save to Google Sheets: {e}")
            return jsonify({"error": f"Failed to save to database: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Quick input error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/quick_input/update', methods=['POST'])
@login_required
def quick_input_update():
    """Handle quick input form updates - find and update existing row"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        campus = data.get('campus', '').strip()
        date_str = data.get('date', '').strip()
        stats = data.get('stats', {})
        original_campus = data.get('originalCampus', campus).strip()
        original_date = data.get('originalDate', date_str).strip()
        
        print(f"[EDIT_REQUEST] Received edit request:")
        print(f"  campus: '{campus}'")
        print(f"  date_str: '{date_str}'")
        print(f"  original_campus: '{original_campus}'")
        print(f"  original_date: '{original_date}'")
        logger.info(f"[EDIT_REQUEST] Received edit request:")
        logger.info(f"  campus: '{campus}'")
        logger.info(f"  date_str: '{date_str}'")
        logger.info(f"  original_campus: '{original_campus}'")
        logger.info(f"  original_date: '{original_date}'")
        
        if not campus:
            return jsonify({"error": "Campus is required"}), 400
        
        if not date_str:
            return jsonify({"error": "Date is required"}), 400
        
        # Check if user has permission to log stats
        if not current_user.has_permission('log_stats'):
            return jsonify({"error": "You don't have permission to update stats"}), 403
        
        # Find and update in Google Sheets
        try:
            if not sheet:
                return jsonify({"error": "Google Sheets not connected"}), 500
            
            # Try multiple times to find the entry (in case of API caching)
            row_index = None
            headers = []
            all_records = []
            
            for attempt in range(3):  # Try up to 3 times
                # Get all records to find the row to update
                all_records = safe_sheets_request(sheet.get_all_records)
                if not all_records:
                    if attempt < 2:
                        time.sleep(2)  # Wait 2 seconds before retrying (increased from 1)
                        continue
                    return jsonify({"error": "No data available"}), 404
                
                headers = list(all_records[0].keys()) if all_records else []
                
                # Find the row index (add 2 because: 1 for header, 1 for 1-indexed)
                search_campus_norm = normalize_campus(original_campus)
                search_campus_variants = [
                    original_campus,
                    original_campus.lower(),
                    original_campus.replace('_', ' '),
                    original_campus.replace('_', ' ').title(),
                    original_campus.replace('_', ' ').lower(),
                    search_campus_norm,
                    # Add more variations for better matching
                    original_campus.replace('_', '').lower(),
                    original_campus.replace('_', '').title()
                ]
                logger.info(f"[Attempt {attempt + 1}] Searching for date='{original_date}', campus variants: {search_campus_variants}")
                
                # First, try to find the most recent entry with matching date (more forgiving)
                matching_date_entries = []
                for idx, record in enumerate(all_records):
                    record_date = str(record.get('Date', ''))
                    if record_date == original_date:
                        matching_date_entries.append((idx, record))
                
                print(f"[EDIT_DEBUG] Found {len(matching_date_entries)} entries with date {original_date}")
                logger.info(f"Found {len(matching_date_entries)} entries with date {original_date}")
                
                # Log all entries on this date for debugging
                for idx, record in matching_date_entries:
                    print(f"  Entry {idx}: Campus='{record.get('Campus')}', Total='{record.get('Total Attendance')}', 9AM='{record.get('9:00 AM')}'")
                    logger.info(f"  Entry {idx}: Campus='{record.get('Campus')}', Total='{record.get('Total Attendance')}', 9AM='{record.get('9:00 AM')}'")
                
                for idx, record in matching_date_entries:
                    record_campus_raw = str(record.get('Campus', ''))
                    record_campus = normalize_campus(record_campus_raw)
                    
                    logger.info(f"Trying to match '{original_campus}' (normalized: '{search_campus_norm}') against '{record_campus_raw}' (normalized: '{record_campus}')")
                    
                    # Very flexible campus matching - try multiple variants
                    campus_match = False
                    for variant in search_campus_variants:
                        variant_norm = normalize_campus(variant)
                        variant_lower = variant.lower()
                        record_lower = record_campus_raw.lower()
                        
                        # Multiple matching strategies
                        if (variant_norm in record_campus or 
                            record_campus in variant_norm or 
                            variant_norm == record_campus or
                            variant_lower == record_lower or
                            variant_lower.replace('_', ' ') == record_lower.replace('_', ' ') or
                            variant_lower.replace('_', '') == record_lower.replace('_', '') or
                            # Check if any word from variant matches any word from record
                            any(word in record_lower.split() for word in variant_lower.split() if len(word) > 2) or
                            any(word in variant_lower.split() for word in record_lower.split() if len(word) > 2)):
                            campus_match = True
                            logger.info(f"✓ MATCHED using variant '{variant}' against '{record_campus_raw}' (normalized: '{record_campus}')")
                            break
                        else:
                            logger.debug(f"  No match: variant '{variant}' (norm: '{variant_norm}') vs record '{record_campus_raw}' (norm: '{record_campus}')")
                    
                    if campus_match:
                        row_index = idx + 2  # +1 for header, +1 for 1-indexed
                        logger.info(f"✓ Found row to update at index {row_index}: '{record_campus_raw}' on {record_date}")
                        break
                
                if row_index:
                    break  # Found it!
                    
                # Not found, wait and retry with longer delay
                if attempt < 2:
                    wait_time = 2 if attempt == 0 else 3  # 2 seconds first retry, 3 seconds second retry
                    logger.warning(f"Entry not found on attempt {attempt + 1}, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
            
            if not row_index:
                # Entry not found - try one more fallback: use the most recent entry on this date
                logger.warning(f"Exact campus match not found. Trying fallback: most recent entry on {original_date}")
                
                # Sort by timestamp to get the most recent entry
                entries_on_date = [r for r in all_records if r.get('Date') == original_date]
                if entries_on_date:
                    # Try to sort by timestamp if available
                    try:
                        entries_on_date.sort(key=lambda x: x.get('Timestamp', ''), reverse=True)
                    except:
                        pass  # If timestamp sorting fails, use original order
                    
                    # Use the most recent entry
                    most_recent_entry = entries_on_date[0]
                    most_recent_idx = all_records.index(most_recent_entry)
                    row_index = most_recent_idx + 2
                    
                    logger.warning(f"Using fallback: most recent entry at index {row_index} for campus '{most_recent_entry.get('Campus')}' on {original_date}")
                    logger.warning(f"This will UPDATE the existing entry instead of creating a new one")
                else:
                    # No entries on this date at all
                    logger.error(f"No entries found on {original_date} at all. Recent entries:")
                    for r in all_records[-5:]:
                        logger.error(f"  Campus: '{r.get('Campus')}', Date: '{r.get('Date')}', Normalized: '{normalize_campus(r.get('Campus', ''))}'")
                    
                    return jsonify({
                        "error": f"Entry not found for {original_campus} on {original_date}. This usually means Google Sheets is still syncing. Please wait 10-15 seconds and try again.",
                        "suggestion": "wait"
                    }), 404
            
            # Prepare the row data
            def safe_value(key, default=0):
                val = stats.get(key, default)
                if val == 0 or val == '':
                    return ''
                return safe_int(val)
            
            # Use Adelaide timezone
            from zoneinfo import ZoneInfo
            adelaide_tz = ZoneInfo('Australia/Adelaide')
            now_adelaide = datetime.now(adelaide_tz)
            
            row_data = {
                'Timestamp': now_adelaide.strftime('%Y-%m-%d %H:%M:%S'),
                'Date': date_str,
                'Campus': campus,
                'Total People in Campus': safe_value('Total People in Campus'),
                'Total Attendance': safe_value('Total Attendance'),
                '9:00 AM': safe_value('9:00 AM'),
                '10:00 AM': safe_value('10:00 AM'),
                '11:00 AM': safe_value('11:00 AM'),
                '5:00 PM': safe_value('5:00 PM'),
                '5:30 PM': safe_value('5:30 PM'),
                'Kids 9:00 AM': safe_value('Kids 9:00 AM'),
                'Kids 10:00 AM': safe_value('Kids 10:00 AM'),
                'Kids 11:00 AM': safe_value('Kids 11:00 AM'),
                'Kids 5:00 PM': safe_value('Kids 5:00 PM'),
                'Kids 5:30 PM': safe_value('Kids 5:30 PM'),
                'Kids Attendance': safe_value('Kids Attendance'),
                'Kids Leaders': safe_value('Kids Leaders'),
                'New Kids': safe_value('New Kids'),
                'New Kids Salvations': safe_value('New Kids Salvations'),
                'First Time Visitors': safe_value('First Time Visitors'),
                'Visitors': safe_value('Visitors'),
                'Information Gathered': safe_value('Information Gathered'),
                'First Time Christians': safe_value('First Time Christians'),
                'Rededications': safe_value('Rededications'),
                'Youth Attendance': safe_value('Youth Attendance'),
                'Youth Salvations': safe_value('Youth Salvations'),
                'Youth New People': safe_value('Youth New People'),
                'Connect Groups': safe_value('Connect Groups'),
                'Dream Team': safe_value('Dream Team'),
                'Tithe': safe_value('Tithe'),
                'Baptisms': safe_value('Baptisms'),
                'Child Dedications': safe_value('Child Dedications')
            }
            
            # Add any missing headers with default values
            for header in headers:
                if header not in row_data:
                    row_data[header] = ''
            
            # Convert to list format for Google Sheets
            row_values = []
            for header in headers:
                value = row_data.get(header, '')
                row_values.append(value)
            
            # Update the specific row
            # Column range: A to the last column based on headers
            # Convert column number to letter (handles AA, AB, etc.)
            def col_num_to_letter(n):
                """Convert column number to Excel-style letter (1=A, 27=AA, etc.)"""
                result = ""
                while n > 0:
                    n -= 1
                    result = chr(65 + (n % 26)) + result
                    n //= 26
                return result
            
            last_col_letter = col_num_to_letter(len(headers))
            range_notation = f'A{row_index}:{last_col_letter}{row_index}'
            
            sheet.update(range_notation, [row_values], value_input_option='USER_ENTERED')
            
            # Clear cache so updated entry shows up immediately
            clear_sheets_cache('Stats')
            logger.info(f"Updated row {row_index} for {campus} on {date_str}")
            
            total_stats = len([v for v in stats.values() if v and v != 0])
            response_text = f"Successfully updated {total_stats} stats for {campus} campus on {date_str}!"
            
            return jsonify({
                "success": True,
                "text": response_text,
                "stats": stats,
                "campus": campus,
                "date": date_str,
                "row_updated": row_index
            })
            
        except Exception as e:
            logger.error(f"Failed to update in Google Sheets: {e}")
            return jsonify({"error": f"Failed to update in database: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Quick input update error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/voices', methods=['GET'])
@login_required
def get_available_voices():
    """Get available voices from ElevenLabs"""
    if not elevenlabs_api_key:
        return jsonify({"error": "ElevenLabs API key not configured"}), 500
    
    try:
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {
            "Accept": "application/json",
            "xi-api-key": elevenlabs_api_key
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            voices = response.json().get('voices', [])
            # Filter to only include English voices and format for frontend
            english_voices = []
            for voice in voices:
                if voice.get('labels', {}).get('language') == 'en':
                    english_voices.append({
                        'id': voice.get('voice_id'),
                        'name': voice.get('name'),
                        'description': voice.get('description', ''),
                        'category': voice.get('category', ''),
                        'language': voice.get('labels', {}).get('language', 'en')
                    })
            return jsonify({"voices": english_voices})
        else:
            logger.error(f"ElevenLabs voices API error: {response.status_code} - {response.text}")
            return jsonify({"error": "Failed to fetch voices"}), 500
            
    except Exception as e:
        logger.error(f"Failed to fetch voices: {e}")
        return jsonify({"error": "Failed to fetch voices"}), 500

@app.route('/api/generate_audio', methods=['POST'])
@login_required
def generate_audio():
    """Generate audio using ElevenLabs for any text with custom voice support"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        voice_id = data.get('voice_id', elevenlabs_voice_id)  # Use provided voice or default
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Create temp_audio directory if it doesn't exist
        temp_audio_dir = os.path.join(os.path.dirname(__file__), "temp_audio")
        if not os.path.exists(temp_audio_dir):
            os.makedirs(temp_audio_dir)
        
        # Generate unique filename based on text hash and voice
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        voice_suffix = f"_v{voice_id}" if voice_id != elevenlabs_voice_id else ""
        audio_filename = os.path.join(temp_audio_dir, f"query_{text_hash}{voice_suffix}.mp3")
        
        # Check if audio file already exists
        if os.path.exists(audio_filename):
            return jsonify({
                "audio_url": f"/temp_audio/query_{text_hash}{voice_suffix}.mp3",
                "voice_id": voice_id
            })
        
        # Generate new audio with specified voice
        audio_url = generate_audio_with_elevenlabs(text, filename=audio_filename, voice_id=voice_id)
        
        if audio_url:
            return jsonify({
                "audio_url": f"/temp_audio/query_{text_hash}{voice_suffix}.mp3",
                "voice_id": voice_id
            })
        else:
            return jsonify({"error": "Failed to generate audio"}), 500
            
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return jsonify({"error": "Failed to generate audio"}), 500

# Update demo_status to use the correct filename for greeting audio
# Insights API endpoint removed - will be rebuilt from scratch

@app.route('/api/sheets/headers')
@login_required
def get_sheets_headers():
    """Debug endpoint to check Google Sheets headers"""
    try:
        if not sheet:
            return jsonify({'error': 'Google Sheets not available'}), 500
        
        # Get first row to see headers
        data = safe_sheets_request(sheet.get_all_records)
        if data and len(data) > 0:
            first_row = data[0]
            headers = list(first_row.keys())
            
            # Sample first few rows for debugging
            sample_data = data[:3] if len(data) >= 3 else data
            
            return jsonify({
                'available_headers': headers,
                'expected_headers': [
                    'Timestamp', 'Date', 'Campus', 'Total Attendance', 'First Time Visitors', 
                    'Visitors', 'Cards Back', 'First Time Christians', 'Rededications',
                    'Youth Attendance', 'Youth Salvations', 'Youth New People', 'Kids Attendance',
                    'Kids Leaders', 'New Kids', 'New Kids Salvations', 'Connect Groups', 
                    'Dream Team', 'Tithe', 'Baptisms', 'Child Dedications'
                ],
                'sample_data': sample_data,
                'total_rows': len(data)
            })
        else:
            return jsonify({'error': 'No data found in sheets', 'available_headers': []})
            
    except Exception as e:
        logger.error(f"Error getting sheets headers: {e}")
        return jsonify({'error': f'Failed to get headers: {str(e)}'}), 500

@app.route('/api/demo_status')
def demo_status():
    """Check all services for demo readiness"""
    status = {
        "backend": "running",
        "claude": claude is not None,
        "elevenlabs": elevenlabs_api_key is not None,
        "google_sheets": sheet is not None,
        "greeting_audio": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    try:
        greeting_text = "Connected to Futures Link, how can I help you today?"
        
        # Use absolute path for temp_audio directory
        temp_audio_dir = os.path.join(os.path.dirname(__file__), "temp_audio")
        audio_filename = os.path.join(temp_audio_dir, "greeting_elevenlabs.mp3")
        
        if not os.path.exists(audio_filename):
            if elevenlabs_api_key:
                os.makedirs(temp_audio_dir, exist_ok=True)
                audio_url = generate_audio_with_elevenlabs(greeting_text, filename=audio_filename)
                status["greeting_audio"] = "generated" if audio_url else "failed"
            else:
                status["greeting_audio"] = "no_elevenlabs_key"
        else:
            status["greeting_audio"] = "cached"
    except Exception as e:
        status["greeting_audio"] = f"error: {str(e)}"
    return jsonify(status)

@app.route('/api/test_dashboard')
def test_dashboard():
    """Test endpoint for dashboard data without authentication"""
    try:
        # Get dashboard data using existing function
        dashboard_data = get_dashboard_data('all_campuses', 'last_12_months')
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Test dashboard error: {e}")
        return jsonify({"error": "Failed to load dashboard data"}), 500

@app.route('/api/weekend_report/<campus>')
@login_required
def get_weekend_report(campus):
    """Get weekend report for a specific campus"""
    try:
        date_str = request.args.get('date', None)
        report = generate_weekend_report(campus, date_str)
        return jsonify(report)
    except Exception as e:
        logger.error(f"Weekend report error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/senior_leadership_weekend_report')
@login_required
@admin_required
def get_senior_leadership_weekend_report():
    """Get comprehensive weekend report for senior leadership across all campuses"""
    try:
        date_str = request.args.get('date', None)
        report = generate_senior_leadership_weekend_report(date_str)
        return jsonify(report)
    except Exception as e:
        logger.error(f"Senior leadership weekend report error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/q1_campus_report/<campus>')
@login_required
def get_q1_campus_report(campus):
    """Get Q1 report for a specific campus"""
    try:
        # Check if user has access to this campus
        if not current_user.has_permission('recall_data', campus):
            return jsonify({'success': False, 'error': 'Access denied. You do not have permission to view this campus data.'}), 403
        
        year = request.args.get('year', datetime.now().year)
        try:
            year = int(year)
        except ValueError:
            year = datetime.now().year
        
        report = generate_q1_campus_report(campus, year)
        
        if 'error' in report:
            return jsonify({'success': False, 'error': report['error']}), 500
        
        return jsonify({'success': True, 'report': report})
        
    except Exception as e:
        logger.error(f"Error getting Q1 campus report: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred while generating the report'}), 500

@app.route('/api/q1_leadership_report')
@login_required
@admin_required
def get_q1_leadership_report():
    """Get Q1 leadership report for all campuses"""
    try:
        # Only users with admin access can access this
        if not current_user.has_permission('admin_access'):
            return jsonify({'success': False, 'error': 'Access denied. Admin access required.'}), 403
        
        year = request.args.get('year', datetime.now().year)
        try:
            year = int(year)
        except ValueError:
            year = datetime.now().year
        
        report = generate_q1_leadership_report(year)
        
        if 'error' in report:
            return jsonify({'success': False, 'error': report['error']}), 500
        
        return jsonify({'success': True, 'report': report})
        
    except Exception as e:
        logger.error(f"Error getting Q1 leadership report: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred while generating the report'}), 500

@app.route('/api/any_time_frame_campus_report/<campus>')
@login_required
def get_any_time_frame_campus_report(campus):
    """Get any time frame campus report"""
    try:
        # Get date parameters from query string
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'start_date and end_date parameters are required'}), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400
        
        # Check permissions
        if not current_user.has_permission('recall_stats', campus):
            return jsonify({'error': 'Access denied'}), 403
        
        report = generate_any_time_frame_campus_report(campus, start_date, end_date)
        return jsonify(report)
    except Exception as e:
        logger.error(f"Error getting any time frame campus report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/any_time_frame_leadership_report')
@login_required
@admin_required
def get_any_time_frame_leadership_report():
    """Get any time frame leadership report"""
    try:
        # Get date parameters from query string
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'start_date and end_date parameters are required'}), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400
        
        report = generate_any_time_frame_leadership_report(start_date, end_date)
        return jsonify(report)
    except Exception as e:
        logger.error(f"Error getting any time frame leadership report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard_data_public')
def get_dashboard_data_public():
    """Public endpoint for dashboard data without any authentication"""
    try:
        campus = request.args.get('campus', 'all_campuses')
        date_filter = request.args.get('date_filter', 'last_12_months')
        custom_start_date = request.args.get('custom_start_date', '')
        custom_end_date = request.args.get('custom_end_date', '')
        show_previous_year = request.args.get('show_previous_year', 'false').lower() == 'true'
        
        # Use the working Google Sheets function directly
        dashboard_data = get_dashboard_data(campus, date_filter, custom_start_date, custom_end_date, show_previous_year)
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Public dashboard API error: {e}")
        return jsonify({"error": "Failed to load dashboard data"}), 500

@app.route('/api/campus_dashboard_data')
def get_campus_dashboard_data():
    """Campus-specific dashboard data with enhanced metrics"""
    try:
        campus_id = request.args.get('campus_id', 'all_campuses')
        date_filter = request.args.get('date_filter', 'last_12_months')
        custom_start_date = request.args.get('custom_start_date', '')
        custom_end_date = request.args.get('custom_end_date', '')
        show_previous_year = request.args.get('show_previous_year', 'false').lower() == 'true'
        
        # Get base dashboard data with all date parameters
        dashboard_data = get_dashboard_data(campus_id, date_filter, custom_start_date, custom_end_date, show_previous_year)
        
        # Enhance with campus-specific metrics
        enhanced_data = enhance_campus_data(dashboard_data, campus_id)
        
        return jsonify(enhanced_data)
    except Exception as e:
        print(f"[ERROR] Campus dashboard data error: {e}")
        return jsonify({"error": "Failed to load campus dashboard data"}), 500

def enhance_campus_data(data, campus_id):
    """Enhance dashboard data with campus-specific metrics"""
    try:
        stats = data.get('stats', {})
        
        # Calculate additional metrics
        total_people = stats.get('total_people', 0)  # This would need to be added to the data source
        sunday_attendance = stats.get('sunday_attendance', stats.get('total_attendance', 0))
        connect_groups = stats.get('connect_groups', 0)
        
        # Calculate percentages
        attendance_percentage = (stats.get('total_attendance', 0) / total_people * 100) if total_people > 0 else 0
        connect_group_percentage = (connect_groups / sunday_attendance * 100) if sunday_attendance > 0 else 0
        
        # Add enhanced metrics
        enhanced_stats = {
            **stats,
            'total_people': total_people,
            'sunday_attendance': sunday_attendance,
            'attendance_percentage': round(attendance_percentage, 1),
            'connect_group_percentage': round(connect_group_percentage, 1),
            'services_breakdown': get_services_breakdown(campus_id),
            'kids_services_breakdown': get_kids_services_breakdown(campus_id)
        }
        
        return {
            **data,
            'stats': enhanced_stats,
            'campus_id': campus_id
        }
        
    except Exception as e:
        print(f"[ERROR] Error enhancing campus data: {e}")
        return data

def get_services_breakdown(campus_id):
    """Get breakdown of services for a campus"""
    # This would typically come from your database
    # For now, return mock data
    return [
        {'service': '9:00 AM', 'attendance': 150},
        {'service': '11:00 AM', 'attendance': 200}
    ]

def get_kids_services_breakdown(campus_id):
    """Get breakdown of kids services for a campus"""
    # This would typically come from your database
    # For now, return mock data
    return [
        {'service': 'Kids 9:00 AM', 'attendance': 45},
        {'service': 'Kids 11:00 AM', 'attendance': 60}
    ]

@app.route('/api/dashboard/data')
def get_dashboard_api_data():
    """API endpoint for dashboard data - temporarily without authentication for testing"""
    """API endpoint for dashboard data"""
    try:
        campus = request.args.get('campus', 'all_campuses')
        date_filter = request.args.get('date_filter', 'last_12_months')
        custom_start_date = request.args.get('custom_start_date', '')
        custom_end_date = request.args.get('custom_end_date', '')
        
        # Get dashboard data using existing function with custom date support
        print(f"[DEBUG] API calling get_dashboard_data with: campus={campus}, date_filter={date_filter}")
        dashboard_data = get_dashboard_data(campus, date_filter, custom_start_date, custom_end_date)
        print(f"[DEBUG] API received data: {dashboard_data.get('stats', {}).get('total_attendance', 'No data')}")
        print(f"[DEBUG] API returning: {dashboard_data}")
        print(f"[DEBUG] API stats keys: {list(dashboard_data.get('stats', {}).keys()) if isinstance(dashboard_data, dict) else 'No stats'}")
        
        # Return JSON response
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Dashboard API error: {e}")
        return jsonify({"error": "Failed to load dashboard data"}), 500

@app.route('/api/users/create', methods=['POST'])
@admin_required
def create_user_api():
    """API endpoint for creating a new user"""
    try:
        data = request.get_json()
        
        # Strip whitespace from username to prevent login issues
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        # Insert into database
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if username already exists (using TRIM for comparison)
        cursor.execute('SELECT id FROM users WHERE TRIM(username) = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "Username already exists"}), 400
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, email, role, campus, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            username,
            generate_password_hash(password),
            data.get('full_name', username).strip() if data.get('full_name') else username,
            data.get('email', f"{username}@futures.church").strip() if data.get('email') else f"{username}@futures.church",
            data.get('role', 'campus_pastor'),
            data.get('campus', 'all_campuses'),
            1
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created new user: {username}")
        return jsonify({"success": True, "message": "User created successfully"})
    except Exception as e:
        logger.error(f"Create user API error: {e}", exc_info=True)
        return jsonify({"error": "Failed to create user"}), 500

@app.route('/api/users/<user_id>/edit', methods=['POST'])
@admin_required
def edit_user_api(user_id):
    """API endpoint for editing a user"""
    try:
        data = request.get_json()
        
        # Update in database
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
        existing_user = cursor.fetchone()
        
        if not existing_user:
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Build update query
        update_fields = []
        params = []
        
        if data.get('username'):
            update_fields.append('username = ?')
            params.append(data['username'])
        
        if data.get('password'):
            update_fields.append('password_hash = ?')
            params.append(generate_password_hash(data['password']))
        
        if data.get('full_name') is not None:
            update_fields.append('full_name = ?')
            params.append(data['full_name'])
        
        if data.get('email') is not None:
            update_fields.append('email = ?')
            params.append(data['email'])
        
        if data.get('role'):
            update_fields.append('role = ?')
            params.append(data['role'])
        
        if data.get('campus') is not None:
            update_fields.append('campus = ?')
            params.append(data['campus'])
        
        if update_fields:
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        
        logger.info(f"Updated user ID: {user_id}")
        return jsonify({"success": True, "message": "User updated successfully"})
    except Exception as e:
        logger.error(f"Edit user API error: {e}", exc_info=True)
        return jsonify({"error": "Failed to update user"}), 500

@app.route('/api/users/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user_api(user_id):
    """API endpoint for deleting a user"""
    try:
        # Delete from database (soft delete by setting active = 0)
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Soft delete (set active = 0)
        cursor.execute('UPDATE users SET active = 0 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted user ID: {user_id}")
        return jsonify({"success": True, "message": "User deleted successfully"})
    except Exception as e:
        logger.error(f"Delete user API error: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete user"}), 500

# PROFILE MANAGEMENT ROUTES
@app.route('/api/profile/change-password', methods=['POST'])
@login_required
def profile_change_password():
    """Allow users to change their own password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({"error": "Missing required fields"}), 400
        
        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        users_data = load_users_database()
        user_id = str(session.get('user_id'))
        user = users_data.get('users', {}).get(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Verify current password
        if not check_password_hash(user.get('password_hash', ''), current_password):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Update password
        user['password_hash'] = generate_password_hash(new_password)
        save_users_database(users_data)
        
        return jsonify({"success": True, "message": "Password changed successfully"})
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({"error": "Failed to change password"}), 500

@app.route('/api/profile/update-email', methods=['POST'])
@login_required
def profile_update_email():
    """Allow users to update their email"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email or '@' not in email:
            return jsonify({"error": "Invalid email address"}), 400
        
        users_data = load_users_database()
        user_id = str(session.get('user_id'))
        user = users_data.get('users', {}).get(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Update email
        user['email'] = email
        save_users_database(users_data)
        
        return jsonify({"success": True, "message": "Email updated successfully"})
    except Exception as e:
        logger.error(f"Update email error: {e}")
        return jsonify({"error": "Failed to update email"}), 500

# DATA EXPORT ROUTES
@app.route('/api/export/attendance', methods=['GET'])
@login_required
def export_attendance():
    """Export attendance data to CSV"""
    try:
        import csv
        from io import StringIO
        
        campus = request.args.get('campus', 'all_campuses')
        date_filter = request.args.get('date_filter', 'last_12_months')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Get data from Google Sheets
        if not sheet:
            return jsonify({"error": "Google Sheets not available"}), 503
        
        rows = safe_sheets_request(sheet.get_all_records)
        if not rows:
            return jsonify({"error": "No data available"}), 404
        
        # Filter by campus if not all_campuses
        if campus != 'all_campuses':
            campus_normalized = normalize_campus(campus)
            filtered_rows = []
            for row in rows:
                row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
                if campus_normalized in row_campus or row_campus in campus_normalized:
                    filtered_rows.append(row)
            rows = filtered_rows
        
        # Create CSV
        output = StringIO()
        if rows:
            fieldnames = list(rows[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        # Create response
        response_data = output.getvalue()
        output.close()
        
        response = Response(response_data, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=attendance_export_{datetime.now().strftime("%Y%m%d")}.csv'
        return response
        
    except Exception as e:
        logger.error(f"Export attendance error: {e}")
        return jsonify({"error": "Failed to export data"}), 500

@app.route('/api/export/finance', methods=['GET'])
@login_required
def export_finance():
    """Export financial data to CSV"""
    try:
        import csv
        from io import StringIO
        
        campus = request.args.get('campus', 'all_campuses')
        
        # Get data from Tithe sheet
        if not finance_sheet:
            return jsonify({"error": "Finance data not available"}), 503
        
        rows = safe_sheets_request(finance_sheet.get_all_records)
        if not rows:
            return jsonify({"error": "No data available"}), 404
        
        # Filter by campus if not all_campuses
        if campus != 'all_campuses':
            campus_normalized = normalize_campus(campus)
            filtered_rows = []
            for row in rows:
                row_campus = normalize_campus(row.get("Campus") or "")
                if campus_normalized in row_campus or row_campus in campus_normalized:
                    filtered_rows.append(row)
            rows = filtered_rows
        
        # Create CSV
        output = StringIO()
        if rows:
            fieldnames = list(rows[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        # Create response
        response_data = output.getvalue()
        output.close()
        
        response = Response(response_data, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=finance_export_{datetime.now().strftime("%Y%m%d")}.csv'
        return response
        
    except Exception as e:
        logger.error(f"Export finance error: {e}")
        return jsonify({"error": "Failed to export data"}), 500

@app.route('/api/export/users', methods=['GET'])
@admin_required
def export_users():
    """Export user list to CSV (admin only)"""
    try:
        import csv
        from io import StringIO
        
        users_data = load_users_database()
        users = list(users_data.get('users', {}).values())
        
        if not users:
            return jsonify({"error": "No users found"}), 404
        
        # Remove sensitive data
        for user in users:
            user.pop('password_hash', None)
        
        # Create CSV
        output = StringIO()
        if users:
            fieldnames = ['id', 'username', 'full_name', 'email', 'role', 'campus', 'active', 'created_date', 'last_login']
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(users)
        
        # Create response
        response_data = output.getvalue()
        output.close()
        
        response = Response(response_data, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=users_export_{datetime.now().strftime("%Y%m%d")}.csv'
        return response
        
    except Exception as e:
        logger.error(f"Export users error: {e}")
        return jsonify({"error": "Failed to export data"}), 500

def normalize_campus(name):
    """Normalize campus name for comparison - handle various formats"""
    if not name:
        return ""
    
    # Convert to string and strip whitespace
    name = str(name).strip()
    
    # Handle common variations
    name = name.lower()
    name = name.replace("_", " ")
    name = name.replace("-", " ")
    
    # Handle specific campus name variations
    campus_mappings = {
        "mt barker": "mount barker",
        "mount barker": "mount barker",
        "barker": "mount barker",
        "hills": "mount barker",
        "adelaide city": "adelaide city",
        "adelaide": "adelaide city",
        "city": "adelaide city",
        "cbd": "adelaide city",
        "victor harbor": "victor harbor",
        "victor": "victor harbor",
        "copper coast": "copper coast",
        "kadina": "copper coast",
        "cc": "copper coast",
        "clare valley": "clare valley",
        "clare": "clare valley",
        "paradise": "paradise",
        "south": "south",
        "salisbury": "salisbury"
    }
    
    # Remove extra spaces
    name = " ".join(name.split())
    
    # Check for specific mappings
    if name in campus_mappings:
        return campus_mappings[name]
    
    return name

# Add this helper near the top of the file (after imports)
def display_campus_name(name):
    return str(name).replace('_', ' ').title()

def safe_campus_name(campus_attr) -> tuple:
    """Safely get campus name and display name from user campus attribute"""
    if campus_attr is None:
        return 'main', 'Main Campus'
    elif isinstance(campus_attr, str):
        return campus_attr, campus_attr.replace('_', ' ').title()
    elif isinstance(campus_attr, dict):
        # If it's a dict, try to get a name field
        campus_name = campus_attr.get('name', campus_attr.get('id', 'main'))
        if isinstance(campus_name, str):
            return campus_name, campus_name.replace('_', ' ').title()
    
    # Fallback
    return 'main', 'Main Campus'

def detect_simple_stat_query(question: str) -> Optional[tuple]:
    """Detect if this is a simple stat query that should get a direct answer"""
    question_lower = question.lower()
    
    # Simple stat keywords
    stat_keywords = {
        'attendance': ['attendance', 'total attendance', 'total', 'people', 'how many people'],
        'new_people': ['new people', 'newpeople', 'np', 'new', 'visitors', 'how many new people'],
        'new_christians': ['new christians', 'christians', 'souls', 'salvations', 'conversions', 'how many new christians'],
        'youth': ['youth attendance', 'youth', 'teens', 'teenagers', 'how many youth'],
        'kids': ['kids total', 'kids', 'children', 'children total', 'how many kids'],
        'connect_groups': ['connect groups', 'connectgroups', 'groups', 'small groups', 'cell groups', 'how many connect groups'],
        'dream_team': ['dream team', 'dreamteam', 'dt', 'team members', 'serving team', 'volunteers', 'how many dream team', 'how many team members']
    }
    
    # Flatten and sort keywords by length (longest first)
    keyword_to_stat = []
    for stat_type, keywords in stat_keywords.items():
        for keyword in keywords:
            keyword_to_stat.append((keyword, stat_type))
    keyword_to_stat.sort(key=lambda x: -len(x[0]))
    
    # Simple question patterns that indicate direct stat requests
    simple_patterns = [
        r'how many\s+\w+',
        r'what is the\s+\w+',
        r'what\'s the\s+\w+',
        r'give me the\s+\w+',
        r'tell me the\s+\w+',
        r'what was the\s+\w+',
        r'how much\s+\w+',
        r'total\s+\w+',
        r'average\s+\w+',
        r'what was the average\s+\w+',
        r'what is the average\s+\w+',
        r"what's the average\s+\w+"
    ]
    
    import re
    
    # Check for simple patterns first (including average patterns)
    for pattern in simple_patterns:
        if re.search(pattern, question_lower):
            # Find which stat they're asking about (longest keyword first)
            for keyword, stat_type in keyword_to_stat:
                if keyword in question_lower:
                    return (stat_type, keyword)
    
    # Check for direct stat keywords without complex analysis words
    analysis_words = ['trend', 'trends', 'pattern', 'growth', 'improve', 'attention', 'working', 'compare', 'vs', 'versus', 'against', 'difference', 'analysis', 'insight', 'why', 'how are we', 'what areas', 'review', 'report']
    
    has_analysis_words = any(word in question_lower for word in analysis_words)
    
    if not has_analysis_words:
        # Check for simple stat requests (longest keyword first)
        for keyword, stat_type in keyword_to_stat:
            if keyword in question_lower:
                return (stat_type, keyword)
    
    return None

def detect_multiple_stats(question: str) -> list:
    """Detect multiple stat requests like 'np and nc' or 'new people and new christians'"""
    question_lower = question.lower()
    
    stat_keywords = {
        'attendance': ['attendance', 'people attended', 'how many people', 'total attendance', 'people came', 'came to church'],
        'new_people': ['new people', 'new visitors', 'visitors', 'first time', 'np', 'new guests'],
        'new_christians': ['new christians', 'salvations', 'souls', 'decisions', 'gave their lives', 'nc', 'new believers'],
        'youth': ['youth', 'teens', 'teenagers', 'young people', 'youth ministry', 'youth group'],
        'kids': ['kids', 'children', 'little ones', 'nursery', 'kids ministry'],
        'connect_groups': ['connect groups', 'connectgroups', 'groups', 'small groups', 'cell groups', 'how many connect groups'],
        'dream_team': ['dream team', 'dreamteam', 'dt', 'team members', 'serving team', 'volunteers', 'how many dream team', 'how many team members']
    }
    
    detected_stats = []
    
    # Check for each stat type in the question
    for stat_type, keywords in stat_keywords.items():
        for keyword in keywords:
            if keyword in question_lower:
                if stat_type not in detected_stats:
                    detected_stats.append(stat_type)
                break
    
    # Special handling for common abbreviations combinations
    if 'np and nc' in question_lower or 'new people and new christians' in question_lower:
        detected_stats = ['new_people', 'new_christians']
    elif 'youth and kids' in question_lower:
        detected_stats = ['youth', 'kids']
    elif 'attendance and new people' in question_lower:
        detected_stats = ['attendance', 'new_people']
    
    return detected_stats

def create_targeted_report_data(stat_types, analysis_data: dict, year: int, count: int) -> list:
    """Create report data showing only the requested stat(s) instead of all stats"""
    # Handle single stat type or list of stat types
    if isinstance(stat_types, str):
        stat_types = [stat_types]
    
    stat_mapping = {
        'attendance': {
            'label': 'Total Attendance',
            'total': analysis_data.get('total_attendance', 0),
            'average': analysis_data.get('averages', {}).get('attendance', 0)
        },
        'new_people': {
            'label': 'New People',
            'total': analysis_data.get('total_new_people', 0),
            'average': analysis_data.get('averages', {}).get('new_people', 0)
        },
        'new_christians': {
            'label': 'New Christians',
            'total': analysis_data.get('total_new_christians', 0),
            'average': analysis_data.get('averages', {}).get('new_christians', 0)
        },
        'youth': {
            'label': 'Youth',
            'total': analysis_data.get('total_youth', 0),
            'average': analysis_data.get('averages', {}).get('youth', 0)
        },
        'kids': {
            'label': 'Kids',
            'total': analysis_data.get('total_kids', 0),
            'average': analysis_data.get('averages', {}).get('kids', 0)
        },
        'connect_groups': {
            'label': 'Connect Groups',
            'total': analysis_data.get('total_connect_groups', 0),
            'average': analysis_data.get('averages', {}).get('connect_groups', 0)
        }
    }
    
    # Build report data for the requested stats
    report_data = []
    valid_stats_found = False
    
    for stat_type in stat_types:
        if stat_type in stat_mapping:
            valid_stats_found = True
            stat_info = stat_mapping[stat_type]
            report_data.append({
                "label": stat_info['label'],
                "total": stat_info['total'],
                "average": stat_info['average'],
                "count": count,
                "year": year
            })
    
    # If no valid stats found, fallback to all stats
    if not valid_stats_found:
        return [
            {"label": "Total Attendance", "total": analysis_data.get("total_attendance", 0), "average": analysis_data.get("averages", {}).get("attendance", 0), "count": count, "year": year},
            {"label": "New People", "total": analysis_data.get("total_new_people", 0), "average": analysis_data.get("averages", {}).get("new_people", 0), "count": count, "year": year},
            {"label": "New Christians", "total": analysis_data.get("total_new_christians", 0), "average": analysis_data.get("averages", {}).get("new_christians", 0), "count": count, "year": year},
            {"label": "Youth", "total": analysis_data.get("total_youth", 0), "average": analysis_data.get("averages", {}).get("youth", 0), "count": count, "year": year},
            {"label": "Kids", "total": analysis_data.get("total_kids", 0), "average": analysis_data.get("averages", {}).get("kids", 0), "count": count, "year": year},
            {"label": "Connect Groups", "total": analysis_data.get("total_connect_groups", 0), "average": analysis_data.get("averages", {}).get("connect_groups", 0), "count": count, "year": year},
        ]
    
    return report_data

def generate_simple_stat_answer(stat_type: str, analysis_data: dict, campus: str, date_range: str) -> str:
    """Generate a simple, direct answer for stat queries"""
    stat_labels = {
        'attendance': 'attendance',
        'new_people': 'new people', 
        'new_christians': 'new christians',
        'youth': 'youth',
        'kids': 'kids',
        'connect_groups': 'connect groups',
        'dream_team': 'dream team'
    }
    
    stat_label = stat_labels.get(stat_type, stat_type)
    
    # Check if this is a cross-campus response
    is_cross_campus = campus.lower() in ['futures church', 'all campuses', 'church-wide']
    
    # Get the total for the requested stat
    stat_totals = {
        'attendance': analysis_data.get('total_attendance', 0),
        'new_people': analysis_data.get('total_new_people', 0),
        'new_christians': analysis_data.get('total_new_christians', 0),
        'youth': analysis_data.get('total_youth', 0),
        'kids': analysis_data.get('total_kids', 0),
        'connect_groups': analysis_data.get('total_connect_groups', 0),
        'dream_team': analysis_data.get('total_dream_team', 0)
    }
    
    # Get averages for cross-campus queries
    stat_averages = {
        'attendance': analysis_data.get('averages', {}).get('attendance', 0),
        'new_people': analysis_data.get('averages', {}).get('new_people', 0),
        'new_christians': analysis_data.get('averages', {}).get('new_christians', 0),
        'youth': analysis_data.get('averages', {}).get('youth', 0),
        'kids': analysis_data.get('averages', {}).get('kids', 0),
        'connect_groups': analysis_data.get('averages', {}).get('connect_groups', 0),
        'dream_team': analysis_data.get('averages', {}).get('dream_team', 0)
    }
    
    total = stat_totals.get(stat_type, 0)
    average = stat_averages.get(stat_type, 0)
    
    # Clean up date range - remove generic or empty date ranges
    generic_ranges = ["None", "recent data", " recent data", "recent", " recent"]
    clean_date_range = ""
    if date_range and date_range.strip() not in generic_ranges:
        clean_date_range = f" {date_range.strip()}" if not date_range.strip().startswith(" ") else date_range
    
    if is_cross_campus:
        return f"Futures Church had {total:,} total {stat_label} across all campuses with an average of {average:.1f} per week{clean_date_range}."
    else:
        # For single campus queries, also include the average per week across all campuses
        cross_campus_avg = analysis_data.get('cross_campus_averages', {}).get(stat_type, 0)
        if cross_campus_avg > 0:
            return f"{campus} had {total:,} total {stat_label}{clean_date_range}. Across all campuses, the average is {cross_campus_avg:.1f} per week."
        else:
            return f"{campus} had {total:,} total {stat_label}{clean_date_range}."



def detect_cross_campus_review(question: str) -> Optional[tuple]:
    """Detect if this is a cross-campus review request"""
    question_lower = question.lower()
    
    # Cross-campus review indicators
    cross_campus_indicators = [
        'all campuses', 'all campus', 'every campus', 'across all', 'all sites', 'every site',
        'church wide', 'churchwide', 'whole church', 'entire church', 'all locations',
        'futures church', 'across futures', 'church total', 'total church'
    ]
    
    has_cross_campus = any(indicator in question_lower for indicator in cross_campus_indicators)
    
    if not has_cross_campus:
        return None
    
    # Check for review types (order matters: most specific first)
    review_indicators = [
        ('weekly', [
            'this week', 'this weekend', 'weekend', 'sunday', 'this sunday', 'weekly',
            'weekend review', 'sunday review', 'weekend report', 'sunday report'
        ]),
        ('mid_year', ['mid year', 'mid-year', 'midyear', 'mid year review', 'mid-year review']),
        ('quarterly', ['quarter', 'q1', 'q2', 'q3', 'q4', 'first quarter', 'second quarter', 'third quarter', 'fourth quarter']),
        ('monthly', ['this month', 'month', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']),
        ('annual', ['annual', 'year', 'yearly', 'this year', '2024', '2025'])
    ]
    
    for review_type, keywords in review_indicators:
        if any(keyword in question_lower for keyword in keywords):
            return (review_type, question_lower)
    
    # Default to weekly if 'review' or 'report' is present and no period is specified
    if 'review' in question_lower or 'report' in question_lower:
        return ('weekly', question_lower)
    
    # Otherwise, default to annual
    return ('annual', question_lower)

def generate_cross_campus_report(review_type: str, date_range: str) -> dict:
    """Generate a comprehensive cross-campus report with robust filtering and debug output."""
    # Get data from all campuses
    if sheet:
        try:
            rows = safe_sheets_request(sheet.get_all_records)
        except Exception as e:
            logger.error(f"Failed to get stats from Google Sheets: {e}")
            rows = []
    else:
        rows = []

    # Set up date ranges based on review type and date_range parameter
    now = datetime.now()
    
    if review_type == 'weekly':
        # Use proper weekend date range (Monday to Sunday)
        today = now
        # Find the most recent Sunday
        days_since_sunday = today.weekday() + 1  # Monday=0, so Sunday=6
        if days_since_sunday == 7:  # Today is Sunday
            days_since_sunday = 0
        most_recent_sunday = today - timedelta(days=days_since_sunday)
        
        # Weekend is Monday to Sunday (7 days ending on Sunday)
        start_date = most_recent_sunday - timedelta(days=6)  # Monday
        end_date = most_recent_sunday  # Sunday
        period_label = f"for the week ending {end_date.strftime('%Y-%m-%d')} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"
    elif review_type == 'monthly':
        # Parse month and year from date_range (e.g., "January 2024")
        if date_range and ' ' in date_range:
            try:
                month_name, year_str = date_range.split(' ')
                month_num = {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
                }[month_name]
                year = int(year_str)
                start_date = datetime(year, month_num, 1)
                if month_num == 12:
                    end_date = datetime(year, month_num, 31)
                else:
                    end_date = datetime(year, month_num + 1, 1) - timedelta(days=1)
                period_label = f"for {month_name} {year}"
            except (ValueError, KeyError):
                # Fallback to current month
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now
                period_label = f"for {now.strftime('%B %Y')}"
        else:
            # Default to current month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            period_label = f"for {now.strftime('%B %Y')}"
    elif review_type == 'quarterly':
        # Parse quarter and year from date_range (e.g., "Q1 2024")
        if date_range and ' ' in date_range:
            try:
                quarter_str, year_str = date_range.split(' ')
                quarter = int(quarter_str[1])  # Extract number from "Q1", "Q2", etc.
                year = int(year_str)
                start_month = 3 * (quarter - 1) + 1
                start_date = datetime(year, start_month, 1)
                if quarter == 4:
                    end_date = datetime(year, 12, 31)
                else:
                    end_date = datetime(year, start_month + 2, 28)  # Approximate end of quarter
                    if start_month + 2 <= 12:
                        end_date = datetime(year, start_month + 3, 1) - timedelta(days=1)
                period_label = f"for Q{quarter} {year}"
            except (ValueError, IndexError):
                # Fallback to current quarter
                quarter = (now.month - 1) // 3 + 1
                start_month = 3 * (quarter - 1) + 1
                start_date = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
                if quarter == 4:
                    end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
                else:
                    end_date = now.replace(month=start_month + 2, day=28, hour=23, minute=59, second=59, microsecond=999999)
                period_label = f"for Q{quarter} {now.year}"
        else:
            # Default to current quarter
            quarter = (now.month - 1) // 3 + 1
            start_month = 3 * (quarter - 1) + 1
            start_date = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            if quarter == 4:
                end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            else:
                end_date = now.replace(month=start_month + 2, day=28, hour=23, minute=59, second=59, microsecond=999999)
            period_label = f"for Q{quarter} {now.year}"
    elif review_type == 'mid_year':
        # Parse year from date_range (e.g., "Jan-Jun 2024")
        if date_range and ' ' in date_range:
            try:
                _, year_str = date_range.split(' ')
                year = int(year_str)
                start_date = datetime(year, 1, 1)
                end_date = datetime(year, 6, 30)
                period_label = f"for Jan-Jun {year}"
            except ValueError:
                # Fallback to current year
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(month=6, day=30, hour=23, minute=59, second=59, microsecond=999999)
                period_label = f"for Jan-Jun {now.year}"
        else:
            # Default to current year
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(month=6, day=30, hour=23, minute=59, second=59, microsecond=999999)
            period_label = f"for Jan-Jun {now.year}"
    else:  # annual
        # Use current year by default
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        period_label = f"for {now.year}"

    print(f"[CROSS-CAMPUS DEBUG] start_date={start_date}, end_date={end_date}, now={now}")

    # Filter rows by date range and valid stats/campus
    filtered_rows = []
    debug_included = 0
    debug_excluded = 0
    for row in rows:
        try:
            # Use Date field instead of Timestamp for more accurate date filtering
            date_str = row.get("Date", "")
            row_date = None
            if date_str:
                try:
                    row_date = datetime.strptime(date_str, "%Y-%m-%d")
                except Exception as e:
                    logger.warning(f"Could not parse date for row: {e}")
            if not row_date or not (start_date <= row_date <= end_date):
                debug_excluded += 1
                continue
            campus = row.get("Campus", "").strip()
            if not campus:
                debug_excluded += 1
                continue
            # At least one stat must be > 0
            stat_fields = ["Total Attendance", "New People", "New Christians", "First Time Christians", "Youth Attendance", "Kids Total", "Kids Attendance", "Connect Groups", "Tithe"]
            has_stat = False
            for field in stat_fields:
                val = row.get(field, "")
                try:
                    if val and int(str(val).replace(",", "").strip()) > 0:
                        has_stat = True
                        break
                except Exception:
                    continue
            if not has_stat:
                debug_excluded += 1
                continue
            filtered_rows.append(row)
            debug_included += 1
        except Exception as e:
            logger.warning(f"Error processing row: {e}")
            debug_excluded += 1
    print(f"[CROSS-CAMPUS DEBUG] Included {debug_included} rows, Excluded {debug_excluded} rows for period {period_label}")
    
    # DEBUG: Show what data was actually found
    if filtered_rows:
        print(f"[CROSS-CAMPUS DEBUG] Found data from these rows:")
        for i, row in enumerate(filtered_rows[:5]):  # Show first 5 rows
            campus = row.get("Campus", "Unknown")
            timestamp = row.get("Timestamp", "Unknown")
            attendance = row.get("Total Attendance", 0)
            new_people = row.get("New People", 0)
            new_christians = row.get("New Christians", 0)
            youth = row.get("Youth Attendance", 0)
            kids = row.get("Kids Total", 0)
            connect_groups = row.get("Connect Groups", 0)
            print(f"  {i+1}. {campus} ({timestamp}): Att={attendance}, NP={new_people}, NC={new_christians}, Youth={youth}, Kids={kids}, CG={connect_groups}")

    if not filtered_rows:
        return {
            "type": f"Cross-Campus {review_type.title()} Report",
            "campus": "Futures Church (All Campuses)",
            "date_range": period_label,
            "summary": f"No valid stats found for any campus {period_label}.",
            "stats": {},
            "entry_count": 0
        }

    # Use comprehensive stats calculation
    analysis_data = calculate_stats_from_filtered_rows(filtered_rows)
    # Create comprehensive stats structure
    comprehensive_stats = {}
    stat_mappings = [
        ("total_attendance", "attendance", "Total Attendance"),
        ("total_first_time_visitors", "first_time_visitors", "First Time Visitors"),
        ("total_information_gathered", "information_gathered", "Cards Back"),
        ("total_new_christians", "new_christians", "New Christians"),
        ("total_rededications", "rededications", "Rededications"),
        ("total_youth_attendance", "youth_attendance", "Youth Attendance"),
        ("total_youth_salvations", "youth_salvations", "Youth Salvations"),
        ("total_youth_new_people", "youth_new_people", "Youth New People"),
        ("total_kids_attendance", "kids_attendance", "Kids Attendance"),
        ("total_kids_leaders", "kids_leaders", "Kids Leaders"),
        ("total_new_kids", "new_kids", "New Kids"),
        ("total_new_kids_salvations", "new_kids_salvations", "New Kids Salvations"),
        ("total_connect_groups", "connect_groups", "Connect Groups"),
        ("total_dream_team", "dream_team", "Dream Team"),
        ("total_tithe", "tithe", "Tithe"),
        ("total_baptisms", "baptisms", "Baptisms"),
        ("total_child_dedications", "child_dedications", "Child Dedications"),
        ("total_new_people", "new_people", "New People"),  # Keep for backward compatibility
    ]
    
    for stat_key, avg_key, label in stat_mappings:
        total = analysis_data.get(stat_key, 0)
        average = analysis_data.get("averages", {}).get(avg_key, 0)
        
        # Include all stats that have data or are important to show (including tithe)
        if total > 0 or label in ["Total Attendance", "First Time Visitors", "New People", "New Christians", "Rededications", "Youth Attendance", "Youth Salvations", "Youth New People", "Kids Attendance", "Kids Leaders", "New Kids", "New Kids Salvations", "Connect Groups", "Dream Team", "Tithe", "Baptisms", "Child Dedications", "Cards Back"]:
            comprehensive_stats[avg_key] = {
                "total": total,
                "average": round(average, 1),
                "label": label
            }
    
    report = {
        "type": f"Cross-Campus {review_type.title()} Report",
        "campus": "Futures Church (All Campuses)",
        "date_range": period_label,
        "summary": f"Futures Church {review_type} report across all campuses {period_label}",
        "stats": comprehensive_stats,
        "entry_count": analysis_data.get("total_entries", 0)
    }
    return report

def generate_weekend_report(campus: str, date_str: str = None) -> dict:
    """Generate a comprehensive weekend report for a specific campus"""
    try:
        # If no date provided, use the most recent weekend
        if not date_str:
            today = datetime.now()
            # Find the most recent Sunday
            days_since_sunday = today.weekday() + 1  # Monday=0, so Sunday=6
            if days_since_sunday == 7:  # Today is Sunday
                days_since_sunday = 0
            most_recent_sunday = today - timedelta(days=days_since_sunday)
            date_str = most_recent_sunday.strftime('%Y-%m-%d')
        
        # Parse the date
        report_date = datetime.strptime(date_str, '%Y-%m-%d')
        start_date = report_date - timedelta(days=6)  # Week starts Monday
        end_date = report_date
        
        # Get data
        rows = []
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
            except Exception as e:
                logger.error(f"Failed to get stats from Google Sheets: {e}")
                rows = []
        
        if not rows:
            rows = load_local_data()
        
        # Filter by campus and date range
        filtered_rows = []
        campus_normalized = normalize_campus(campus)
        
        for row in rows:
            row_campus = normalize_campus(row.get("Campus") or row.get("campus") or "")
            if row_campus == campus_normalized or campus_normalized in row_campus:
                timestamp_str = row.get("Timestamp", "")
                if timestamp_str:
                    try:
                        if "T" in timestamp_str:
                            row_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            row_date = parse_any_date(timestamp_str)
                        if start_date <= row_date <= end_date:
                            filtered_rows.append(row)
                    except Exception:
                        continue
        
        # Calculate comprehensive stats
        stats = {
            'total_attendance': 0,
            'services_count': 0,
            'new_people': 0,
            'new_christians': 0,
            'youth_attendance': 0,
            'kids_attendance': 0,
            'connect_groups': 0,
            'dream_team': 0,
            'tithe': 0,
            'baptisms': 0,
            'child_dedications': 0,
            'first_time_visitors': 0,
            'visitors': 0,
            'rededications': 0,
            'youth_salvations': 0,
            'youth_new_people': 0,
            'kids_leaders': 0,
            'new_kids': 0,
            'new_kids_salvations': 0,
            'information_gathered': 0
        }
        
        # Track individual service data
        service_breakdown = {}
        
        for row in filtered_rows:
            if isinstance(row, dict):
                def safe_int_stat(val):
                    try:
                        if val is None or val == '':
                            return 0
                        return int(str(val).replace(',', '').strip())
                    except Exception:
                        return 0
                
                # Main stats
                stats['total_attendance'] += safe_int_stat(row.get('Total Attendance', 0))
                stats['new_people'] += safe_int_stat(row.get('First Time Visitors', 0)) + safe_int_stat(row.get('Visitors', 0))
                stats['new_christians'] += safe_int_stat(row.get('First Time Christians', 0)) + safe_int_stat(row.get('Rededications', 0))
                stats['youth_attendance'] += safe_int_stat(row.get('Youth Attendance', 0))
                stats['kids_attendance'] += safe_int_stat(row.get('Kids Attendance', 0))
                stats['connect_groups'] += safe_int_stat(row.get('Connect Groups', 0))
                stats['dream_team'] += safe_int_stat(row.get('Dream Team', 0))
                stats['tithe'] += safe_int_stat(row.get('Tithe', 0))
                stats['baptisms'] += safe_int_stat(row.get('Baptisms', 0))
                stats['child_dedications'] += safe_int_stat(row.get('Child Dedications', 0))
                stats['first_time_visitors'] += safe_int_stat(row.get('First Time Visitors', 0))
                stats['visitors'] += safe_int_stat(row.get('Visitors', 0))
                stats['rededications'] += safe_int_stat(row.get('Rededications', 0))
                stats['youth_salvations'] += safe_int_stat(row.get('Youth Salvations', 0))
                stats['youth_new_people'] += safe_int_stat(row.get('Youth New People', 0))
                stats['kids_leaders'] += safe_int_stat(row.get('Kids Leaders', 0))
                stats['new_kids'] += safe_int_stat(row.get('New Kids', 0))
                stats['new_kids_salvations'] += safe_int_stat(row.get('New Kids Salvations', 0))
                stats['information_gathered'] += safe_int_stat(row.get('Cards Back', 0))
                
                # Service breakdown
                service_time = row.get('Date', 'Unknown')
                if service_time not in service_breakdown:
                    service_breakdown[service_time] = {
                        'attendance': 0,
                        'new_people': 0,
                        'new_christians': 0,
                        'youth': 0,
                        'kids': 0
                    }
                
                service_breakdown[service_time]['attendance'] += safe_int_stat(row.get('Total Attendance', 0))
                service_breakdown[service_time]['new_people'] += safe_int_stat(row.get('First Time Visitors', 0)) + safe_int_stat(row.get('Visitors', 0))
                service_breakdown[service_time]['new_christians'] += safe_int_stat(row.get('First Time Christians', 0)) + safe_int_stat(row.get('Rededications', 0))
                service_breakdown[service_time]['youth'] += safe_int_stat(row.get('Youth Attendance', 0))
                service_breakdown[service_time]['kids'] += safe_int_stat(row.get('Kids Attendance', 0))
        
        stats['services_count'] = len(service_breakdown)
        
        # Calculate averages
        if stats['services_count'] > 0:
            stats['avg_attendance'] = round(stats['total_attendance'] / stats['services_count'])
            stats['avg_new_people'] = round(stats['new_people'] / stats['services_count'], 1)
            stats['avg_new_christians'] = round(stats['new_christians'] / stats['services_count'], 1)
            stats['avg_youth'] = round(stats['youth_attendance'] / stats['services_count'])
            stats['avg_kids'] = round(stats['kids_attendance'] / stats['services_count'])
        else:
            stats['avg_attendance'] = 0
            stats['avg_new_people'] = 0
            stats['avg_new_christians'] = 0
            stats['avg_youth'] = 0
            stats['avg_kids'] = 0
        
        # Generate insights
        insights = []
        if stats['total_attendance'] > 0:
            if stats['new_people'] > 0:
                conversion_rate = (stats['new_christians'] / stats['new_people']) * 100
                insights.append(f"Conversion rate: {conversion_rate:.1f}% of new people made decisions")
            
            if stats['youth_attendance'] > 0:
                youth_percentage = (stats['youth_attendance'] / stats['total_attendance']) * 100
                insights.append(f"Youth represented {youth_percentage:.1f}% of total attendance")
            
            if stats['kids_attendance'] > 0:
                kids_percentage = (stats['kids_attendance'] / stats['total_attendance']) * 100
                insights.append(f"Kids represented {kids_percentage:.1f}% of total attendance")
        
        return {
            'campus': campus,
            'date': date_str,
            'week_start': start_date.strftime('%Y-%m-%d'),
            'week_end': end_date.strftime('%Y-%m-%d'),
            'stats': stats,
            'service_breakdown': service_breakdown,
            'insights': insights,
            'data_points': len(filtered_rows)
        }
        
    except Exception as e:
        logger.error(f"Weekend report error: {e}")
        return {'error': str(e)}

def generate_senior_leadership_weekend_report(date_str: str = None) -> dict:
    """Generate a comprehensive weekend report for senior leadership across all campuses"""
    try:
        # If no date provided, use the most recent weekend
        if not date_str:
            today = datetime.now()
            days_since_sunday = today.weekday() + 1
            if days_since_sunday == 7:
                days_since_sunday = 0
            most_recent_sunday = today - timedelta(days=days_since_sunday)
            date_str = most_recent_sunday.strftime('%Y-%m-%d')
        
        report_date = datetime.strptime(date_str, '%Y-%m-%d')
        start_date = report_date - timedelta(days=6)
        end_date = report_date
        
        # Get all campuses
        campuses_data = load_campuses_database()
        active_campuses = [campus for campus in campuses_data.get('campuses', {}).values() if campus.get('active', True)]
        
        # Get data
        rows = []
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
            except Exception as e:
                logger.error(f"Failed to get stats from Google Sheets: {e}")
                rows = []
        
        if not rows:
            rows = load_local_data()
        
        # Generate reports for each campus
        campus_reports = {}
        total_stats = {
            'total_attendance': 0,
            'services_count': 0,
            'new_people': 0,
            'new_christians': 0,
            'youth_attendance': 0,
            'kids_attendance': 0,
            'connect_groups': 0,
            'dream_team': 0,
            'tithe': 0,
            'baptisms': 0,
            'child_dedications': 0
        }
        
        for campus_id, campus_info in active_campuses.items():
            campus_name = campus_info.get('display_name', campus_id)
            campus_report = generate_weekend_report(campus_name, date_str)
            if 'error' not in campus_report:
                campus_reports[campus_id] = campus_report
                # Add to totals
                stats = campus_report.get('stats', {})
                total_stats['total_attendance'] += stats.get('total_attendance', 0)
                total_stats['services_count'] += stats.get('services_count', 0)
                total_stats['new_people'] += stats.get('new_people', 0)
                total_stats['new_christians'] += stats.get('new_christians', 0)
                total_stats['youth_attendance'] += stats.get('youth_attendance', 0)
                total_stats['kids_attendance'] += stats.get('kids_attendance', 0)
                total_stats['connect_groups'] += stats.get('connect_groups', 0)
                total_stats['dream_team'] += stats.get('dream_team', 0)
                total_stats['tithe'] += stats.get('tithe', 0)
                total_stats['baptisms'] += stats.get('baptisms', 0)
                total_stats['child_dedications'] += stats.get('child_dedications', 0)
        
        # Calculate organization-wide averages
        if total_stats['services_count'] > 0:
            total_stats['avg_attendance'] = round(total_stats['total_attendance'] / total_stats['services_count'])
            total_stats['avg_new_people'] = round(total_stats['new_people'] / total_stats['services_count'], 1)
            total_stats['avg_new_christians'] = round(total_stats['new_christians'] / total_stats['services_count'], 1)
        else:
            total_stats['avg_attendance'] = 0
            total_stats['avg_new_people'] = 0
            total_stats['avg_new_christians'] = 0
        
        # Generate senior leadership insights
        insights = []
        if total_stats['total_attendance'] > 0:
            if total_stats['new_people'] > 0:
                org_conversion_rate = (total_stats['new_christians'] / total_stats['new_people']) * 100
                insights.append(f"Organization-wide conversion rate: {org_conversion_rate:.1f}%")
            
            if total_stats['youth_attendance'] > 0:
                org_youth_percentage = (total_stats['youth_attendance'] / total_stats['total_attendance']) * 100
                insights.append(f"Youth represent {org_youth_percentage:.1f}% of total attendance")
            
            if total_stats['kids_attendance'] > 0:
                org_kids_percentage = (total_stats['kids_attendance'] / total_stats['total_attendance']) * 100
                insights.append(f"Kids represent {org_kids_percentage:.1f}% of total attendance")
        
        # Find top performing campuses
        campus_performance = []
        for campus_id, report in campus_reports.items():
            if 'error' not in report:
                stats = report.get('stats', {})
                campus_performance.append({
                    'campus_id': campus_id,
                    'campus_name': report.get('campus', campus_id),
                    'attendance': stats.get('total_attendance', 0),
                    'new_people': stats.get('new_people', 0),
                    'new_christians': stats.get('new_christians', 0),
                    'services_count': stats.get('services_count', 0)
                })
        
        # Sort by attendance
        campus_performance.sort(key=lambda x: x['attendance'], reverse=True)
        
        return {
            'date': date_str,
            'week_start': start_date.strftime('%Y-%m-%d'),
            'week_end': end_date.strftime('%Y-%m-%d'),
            'total_stats': total_stats,
            'campus_reports': campus_reports,
            'campus_performance': campus_performance,
            'insights': insights,
            'total_campuses': len(active_campuses),
            'reporting_campuses': len(campus_reports)
        }
        
    except Exception as e:
        logger.error(f"Senior leadership weekend report error: {e}")
        return {'error': str(e)}

def generate_q1_leadership_report(year: int) -> dict:
    """Generate a comprehensive Q1 report for senior leadership across all campuses"""
    try:
        # Q1 dates: January 1 to March 31
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 3, 31)
        
        # Get all campuses
        campuses_data = load_campuses_database()
        active_campuses = [campus for campus in campuses_data.get('campuses', {}).values() if campus.get('active', True)]
        
        # Get data
        rows = []
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
            except Exception as e:
                logger.error(f"Failed to get stats from Google Sheets: {e}")
                rows = []
        
        if not rows:
            rows = load_local_data()
        
        # Generate reports for each campus
        campus_reports = {}
        total_stats = {
            'total_attendance': 0,
            'services_count': 0,
            'new_people': 0,
            'new_christians': 0,
            'youth_attendance': 0,
            'kids_attendance': 0,
            'connect_groups': 0,
            'dream_team': 0,
            'tithe': 0,
            'baptisms': 0,
            'child_dedications': 0
        }
        
        # Monthly totals across all campuses
        monthly_totals = {
            'january': {'attendance': 0, 'services': 0, 'new_people': 0, 'new_christians': 0, 'tithe': 0},
            'february': {'attendance': 0, 'services': 0, 'new_people': 0, 'new_christians': 0, 'tithe': 0},
            'march': {'attendance': 0, 'services': 0, 'new_people': 0, 'new_christians': 0, 'tithe': 0}
        }
        
        for campus_id, campus_info in active_campuses.items():
            campus_name = campus_info.get('display_name', campus_id)
            campus_report = generate_q1_campus_report(campus_name, year)
            if 'error' not in campus_report:
                campus_reports[campus_id] = campus_report
                # Add to totals
                stats = campus_report.get('stats', {})
                total_stats['total_attendance'] += stats.get('total_attendance', 0)
                total_stats['services_count'] += stats.get('services_count', 0)
                total_stats['new_people'] += stats.get('new_people', 0)
                total_stats['new_christians'] += stats.get('new_christians', 0)
                total_stats['youth_attendance'] += stats.get('youth_attendance', 0)
                total_stats['kids_attendance'] += stats.get('kids_attendance', 0)
                total_stats['connect_groups'] += stats.get('connect_groups', 0)
                total_stats['dream_team'] += stats.get('dream_team', 0)
                total_stats['tithe'] += stats.get('tithe', 0)
                total_stats['baptisms'] += stats.get('baptisms', 0)
                total_stats['child_dedications'] += stats.get('child_dedications', 0)
                
                # Add to monthly totals
                monthly_breakdown = campus_report.get('monthly_breakdown', {})
                for month in monthly_totals:
                    if month in monthly_breakdown:
                        monthly_totals[month]['attendance'] += monthly_breakdown[month]['attendance']
                        monthly_totals[month]['services'] += monthly_breakdown[month]['services']
                        monthly_totals[month]['new_people'] += monthly_breakdown[month]['new_people']
                        monthly_totals[month]['new_christians'] += monthly_breakdown[month]['new_christians']
                        monthly_totals[month]['tithe'] += monthly_breakdown[month]['tithe']
        
        # Calculate organization-wide averages
        if total_stats['services_count'] > 0:
            total_stats['avg_attendance'] = round(total_stats['total_attendance'] / total_stats['services_count'])
            total_stats['avg_new_people'] = round(total_stats['new_people'] / total_stats['services_count'], 1)
            total_stats['avg_new_christians'] = round(total_stats['new_christians'] / total_stats['services_count'], 1)
        else:
            total_stats['avg_attendance'] = 0
            total_stats['avg_new_people'] = 0
            total_stats['avg_new_christians'] = 0
        
        # Generate senior leadership insights
        insights = []
        if total_stats['total_attendance'] > 0:
            if total_stats['new_people'] > 0:
                org_conversion_rate = (total_stats['new_christians'] / total_stats['new_people']) * 100
                insights.append(f"Organization-wide Q1 conversion rate: {org_conversion_rate:.1f}%")
            
            if total_stats['youth_attendance'] > 0:
                org_youth_percentage = (total_stats['youth_attendance'] / total_stats['total_attendance']) * 100
                insights.append(f"Youth represent {org_youth_percentage:.1f}% of total attendance")
            
            if total_stats['kids_attendance'] > 0:
                org_kids_percentage = (total_stats['kids_attendance'] / total_stats['total_attendance']) * 100
                insights.append(f"Kids represent {org_kids_percentage:.1f}% of total attendance")
        
        # Find top performing campuses
        campus_performance = []
        for campus_id, report in campus_reports.items():
            if 'error' not in report:
                stats = report.get('stats', {})
                campus_performance.append({
                    'campus_id': campus_id,
                    'campus_name': report.get('campus', campus_id),
                    'attendance': stats.get('total_attendance', 0),
                    'new_people': stats.get('new_people', 0),
                    'new_christians': stats.get('new_christians', 0),
                    'services_count': stats.get('services_count', 0),
                    'avg_attendance': stats.get('avg_attendance', 0)
                })
        
        # Sort by attendance
        campus_performance.sort(key=lambda x: x['attendance'], reverse=True)
        
        # Calculate Q1 growth trends
        growth_insights = []
        if monthly_totals['january']['attendance'] > 0 and monthly_totals['march']['attendance'] > 0:
            jan_avg = monthly_totals['january']['attendance'] / max(monthly_totals['january']['services'], 1)
            mar_avg = monthly_totals['march']['attendance'] / max(monthly_totals['march']['services'], 1)
            if jan_avg > 0:
                growth_rate = ((mar_avg - jan_avg) / jan_avg) * 100
                growth_insights.append(f"Organization-wide average attendance grew {growth_rate:+.1f}% from January to March")
        
        return {
            'year': year,
            'quarter': 1,
            'period': 'Q1',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'total_stats': total_stats,
            'monthly_totals': monthly_totals,
            'campus_reports': campus_reports,
            'campus_performance': campus_performance,
            'insights': insights,
            'growth_insights': growth_insights,
            'total_campuses': len(active_campuses),
            'reporting_campuses': len(campus_reports)
        }
        
    except Exception as e:
        logger.error(f"Q1 leadership report error: {e}")
        return {'error': str(e)}

def generate_any_time_frame_leadership_report(start_date: datetime, end_date: datetime) -> dict:
    """Generate a comprehensive any time frame report for senior leadership across all campuses"""
    try:
        # Get data
        rows = []
        if sheet:
            try:
                rows = safe_sheets_request(sheet.get_all_records)
            except Exception as e:
                logger.error(f"Failed to get stats from Google Sheets: {e}")
                rows = []
        
        if not rows:
            rows = load_local_data()
        
        # Get all campuses
        campuses_data = get_campuses_for_user()
        all_campuses = [campus['id'] for campus in campuses_data.get('campuses', []) if campus['id'] != 'all_campuses']
        
        # Generate individual campus reports
        campus_reports = {}
        organization_stats = {
            'total_attendance': 0,
            'total_services': 0,
            'total_new_people': 0,
            'total_new_christians': 0,
            'total_youth': 0,
            'total_kids': 0,
            'total_connect_groups': 0,
            'total_dream_team': 0,
            'total_tithe': 0,
            'total_baptisms': 0,
            'total_child_dedications': 0
        }
        
        for campus in all_campuses:
            campus_report = generate_any_time_frame_campus_report(campus, start_date, end_date)
            campus_reports[campus] = campus_report
            
            # Aggregate organization stats
            if 'stats' in campus_report:
                stats = campus_report['stats']
                organization_stats['total_attendance'] += stats.get('total_attendance', 0)
                organization_stats['total_services'] += stats.get('services_count', 0)
                organization_stats['total_new_people'] += stats.get('new_people', 0)
                organization_stats['total_new_christians'] += stats.get('new_christians', 0)
                organization_stats['total_youth'] += stats.get('youth_attendance', 0)
                organization_stats['total_kids'] += stats.get('kids_attendance', 0)
                organization_stats['total_connect_groups'] += stats.get('connect_groups', 0)
                organization_stats['total_dream_team'] += stats.get('dream_team', 0)
                organization_stats['total_tithe'] += stats.get('tithe', 0)
                organization_stats['total_baptisms'] += stats.get('baptisms', 0)
                organization_stats['total_child_dedications'] += stats.get('child_dedications', 0)
        
        # Calculate organization averages
        if organization_stats['total_services'] > 0:
            organization_stats['average_attendance'] = round(organization_stats['total_attendance'] / organization_stats['total_services'], 1)
            organization_stats['average_new_people'] = round(organization_stats['total_new_people'] / organization_stats['total_services'], 1)
            organization_stats['average_new_christians'] = round(organization_stats['total_new_christians'] / organization_stats['total_services'], 1)
        else:
            organization_stats['average_attendance'] = 0
            organization_stats['average_new_people'] = 0
            organization_stats['average_new_christians'] = 0
        
        # Campus performance ranking
        campus_performance = []
        for campus, report in campus_reports.items():
            if 'stats' in report and report['stats'].get('services_count', 0) > 0:
                campus_performance.append({
                    'campus': campus,
                    'campus_display_name': display_campus_name(campus),
                    'total_attendance': report['stats'].get('total_attendance', 0),
                    'average_attendance': report['stats'].get('average_attendance', 0),
                    'total_new_people': report['stats'].get('new_people', 0),
                    'total_new_christians': report['stats'].get('new_christians', 0),
                    'services_count': report['stats'].get('services_count', 0),
                    'tithe': report['stats'].get('tithe', 0)
                })
        
        # Sort by total attendance
        campus_performance.sort(key=lambda x: x['total_attendance'], reverse=True)
        
        # Generate insights
        insights = []
        if organization_stats['total_services'] > 0:
            insights.append(f"Organization-wide average attendance of {organization_stats['average_attendance']} people per service")
            if organization_stats['total_new_people'] > 0:
                org_conversion_rate = (organization_stats['total_new_christians'] / organization_stats['total_new_people']) * 100
                insights.append(f"Welcomed {organization_stats['total_new_people']} new people across all campuses")
                insights.append(f"Organization-wide conversion rate of {org_conversion_rate:.1f}%")
            if organization_stats['total_tithe'] > 0:
                avg_tithe_per_service = organization_stats['total_tithe'] / organization_stats['total_services']
                insights.append(f"Average tithe of ${avg_tithe_per_service:,.0f} per service across all campuses")
        
        # Format date range for display
        date_range_str = f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
        
        return {
            'date_range': date_range_str,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'organization_stats': organization_stats,
            'campus_reports': campus_reports,
            'campus_performance': campus_performance,
            'insights': insights,
            'total_campuses': len(all_campuses),
            'active_campuses': len([c for c in campus_reports.values() if c.get('stats', {}).get('services_count', 0) > 0])
        }
        
    except Exception as e:
        logger.error(f"Error generating any time frame leadership report: {e}")
        return {
            'error': f"Failed to generate leadership report: {str(e)}",
            'date_range': f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}",
            'organization_stats': {},
            'campus_reports': {},
            'campus_performance': [],
            'insights': [],
            'total_campuses': 0,
            'active_campuses': 0
        }

# Patch the review detection logic in query_data_internal
# ... existing code ...

# @app.route('/heartbeat')
# def heartbeat():
#     return render_template('heartbeat.html')

# @app.route('/journey')
# def journey():
#     return render_template('journey.html')

# Catch-all route for React Router - serve React app for all non-API routes
@app.route('/<path:path>')
def serve_react_app(path):
    """Serve React app for all non-API routes to support React Router"""
    # Skip API routes
    if path.startswith('api/') or path.startswith('temp_audio/'):
        return jsonify({"error": "Not found"}), 404
    
    # If path has an extension (like .json, .png, .js, etc), try to serve as static file
    if '.' in path.split('/')[-1]:
        try:
            # Try to serve the file from static folder
            return send_from_directory('static', path)
        except:
            # If file not found, return 404
            return jsonify({"error": "Not found"}), 404
    
    # For routes without extensions (React Router paths), serve the React app
    return send_from_directory('static', 'index.html')


# ============================================================================
# PULSE & PASSPORT API ROUTES
# Intelligent people-focused modules for Futures LINK
# ============================================================================

@app.route('/api/persons/demo', methods=['GET'])
def get_persons_demo():
    """Demo endpoint for testing Heartbeat interface (no auth required)"""
    try:
        # This is for demo/testing only - bypasses authentication
        campus_filter = request.args.get('campus', None)
        pulse_filter = request.args.get('pulse_status', None)
        search = request.args.get('search', '').strip()
        
        # Build query
        query = Person.query.filter_by(is_active=True)
        
        if campus_filter and campus_filter != 'all_campuses':
            query = query.filter(Person.campus == campus_filter)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Person.full_name.ilike(search_term),
                    Person.email.ilike(search_term),
                    Person.preferred_name.ilike(search_term)
                )
            )
        
        persons = query.order_by(Person.full_name).all()
        
        # Include engagement profile data
        result = []
        for person in persons:
            person_data = person.to_dict()
            
            # Add engagement profile data
            if person.engagement_profile:
                engagement_data = person.engagement_profile.to_dict()
                person_data['pulse_status'] = engagement_data['pulse_status']
                person_data['last_seen'] = engagement_data['last_seen']
                person_data['pulse_reasons'] = engagement_data['pulse_reasons']
                person_data['attendance_frequency'] = engagement_data['attendance_frequency']
                person_data['serving_frequency'] = engagement_data['serving_frequency']
                person_data['overall_engagement'] = engagement_data['overall_engagement']
            else:
                person_data['pulse_status'] = 'red'
                person_data['last_seen'] = None
                person_data['pulse_reasons'] = ['No engagement data']
                person_data['attendance_frequency'] = 0.0
                person_data['serving_frequency'] = 0.0
                person_data['overall_engagement'] = 0.0
            
            # Apply pulse filter if specified
            if pulse_filter and person_data['pulse_status'] != pulse_filter:
                continue
            
            result.append(person_data)
        
        return jsonify({
            'persons': result,
            'total': len(result),
            'filters': {
                'campus': campus_filter,
                'pulse_status': pulse_filter,
                'search': search
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching persons (demo): {e}")
        return jsonify({'error': 'Failed to fetch persons'}), 500


@app.route('/api/persons/demo/<person_id>', methods=['GET'])
def get_person_detail_demo(person_id):
    """Demo endpoint for person details (no auth required)"""
    try:
        person = Person.query.filter_by(id=person_id, is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Get person data
        person_data = person.to_dict()
        
        # Add full engagement profile
        if person.engagement_profile:
            engagement_data = person.engagement_profile.to_dict()
            person_data['engagement'] = engagement_data
        else:
            # Create engagement profile if it doesn't exist
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
            db.session.commit()
            person_data['engagement'] = engagement.to_dict()
        
        return jsonify(person_data)
        
    except Exception as e:
        logger.error(f"Error fetching person detail (demo): {e}")
        return jsonify({'error': 'Failed to fetch person details'}), 500


@app.route('/api/persons/demo/<person_id>', methods=['PUT'])
def update_person_demo(person_id):
    """Update person details (demo version - no auth required)"""
    try:
        person = Person.query.filter_by(id=person_id, is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update basic information
        if 'full_name' in data:
            person.full_name = data['full_name']
        if 'preferred_name' in data:
            person.preferred_name = data['preferred_name']
        if 'email' in data:
            # Check if email is already taken by another person
            existing = Person.query.filter_by(email=data['email'], is_active=True).first()
            if existing and existing.id != person.id:
                return jsonify({'error': 'Email already in use'}), 400
            person.email = data['email']
        if 'campus' in data:
            person.campus = data['campus']
        if 'connect_group' in data:
            person.connect_group = data['connect_group']
        if 'dream_team_roles' in data:
            person.dream_team_roles = data['dream_team_roles']
        
        # Update discipleship milestones (convert empty strings to None)
        milestone_fields = [
            'dna_completed', 'baptised_on', 'rise_attended', 
            'filled_holy_spirit', 'first_served_on'
        ]
        
        for field in milestone_fields:
            if field in data:
                value = data[field]
                if value == '' or value is None:
                    setattr(person, field, None)
                else:
                    # Try to parse the date
                    try:
                        if isinstance(value, str):
                            # Parse date string
                            from datetime import datetime
                            parsed_date = datetime.strptime(value, '%Y-%m-%d').date()
                            setattr(person, field, parsed_date)
                        else:
                            setattr(person, field, value)
                    except ValueError:
                        return jsonify({'error': f'Invalid date format for {field}'}), 400
        
        # Update engagement profile pulse status if attendance/serving changed
        # (Pulse will be recalculated automatically on next access)
        
        db.session.commit()
        
        # Return updated person data
        person_data = person.to_dict()
        if person.engagement_profile:
            person_data['engagement'] = person.engagement_profile.to_dict()
        
        return jsonify({
            'message': 'Person updated successfully',
            'person': person_data
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating person {person_id} (demo): {e}")
        return jsonify({'error': 'Failed to update person'}), 500


@app.route('/api/persons', methods=['GET'])
@login_required
def get_persons():
    """Get all persons with basic info (admin only)"""
    try:
        if not current_user.has_permission('query_access'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Get query parameters
        campus_filter = request.args.get('campus', None)
        pulse_filter = request.args.get('pulse_status', None)
        department_filter = request.args.get('department', None)
        search = request.args.get('search', '').strip()
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        
        # Build query
        if include_archived:
            query = Person.query
        else:
            query = Person.query.filter_by(is_active=True)
        
        if campus_filter and campus_filter != 'all_campuses':
            query = query.filter(Person.campus == campus_filter)
        
        if department_filter and department_filter != 'all':
            query = query.filter(Person.department == department_filter)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Person.full_name.ilike(search_term),
                    Person.email.ilike(search_term),
                    Person.preferred_name.ilike(search_term)
                )
            )
        
        persons = query.order_by(Person.full_name).all()
        
        # Include engagement profile data
        result = []
        for person in persons:
            person_data = person.to_dict()
            
            # Add engagement profile data
            if person.engagement_profile:
                engagement_data = person.engagement_profile.to_dict()
                person_data['pulse_status'] = engagement_data.get('pulse_status', 'red')
                person_data['last_seen'] = engagement_data.get('last_seen')
                person_data['pulse_reasons'] = engagement_data.get('pulse_reasons', ['No engagement data'])
                person_data['attendance_frequency'] = engagement_data.get('attendance_frequency', 0.0)
                person_data['serving_frequency'] = engagement_data.get('serving_frequency', 0.0)
                person_data['overall_engagement'] = engagement_data.get('overall_engagement', 0.0)
            else:
                person_data['pulse_status'] = 'red'
                person_data['last_seen'] = None
                person_data['pulse_reasons'] = ['No engagement data']
                person_data['attendance_frequency'] = 0.0
                person_data['serving_frequency'] = 0.0
                person_data['overall_engagement'] = 0.0
            
            # Apply pulse filter if specified
            if pulse_filter and person_data['pulse_status'] != pulse_filter:
                continue
            
            result.append(person_data)
        
        return jsonify({
            'persons': result,
            'total': len(result),
            'filters': {
                'campus': campus_filter,
                'pulse_status': pulse_filter,
                'department': department_filter,
                'search': search
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching persons: {e}")
        return jsonify({'error': 'Failed to fetch persons'}), 500


@app.route('/api/persons', methods=['POST'])
@login_required
def create_person():
    """Create new person with engagement profile (admin only)"""
    try:
        if not current_user.has_permission('query_access'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['full_name', 'email', 'campus']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if email already exists
        existing_person = Person.query.filter_by(email=data['email']).first()
        if existing_person:
            return jsonify({'error': 'Person with this email already exists'}), 400
        
        # Create person and engagement profile
        person, engagement = create_person_with_engagement(
            full_name=data['full_name'],
            email=data['email'],
            campus=data['campus'],
            preferred_name=data.get('preferred_name'),
            phone=data.get('phone'),
            department=data.get('department'),
            connect_group=data.get('connect_group'),
            dream_team_roles=data.get('dream_team_roles', []),
            birthday=datetime.strptime(data['birthday'], '%Y-%m-%d').date() if data.get('birthday') else None,
            pastoral_notes=data.get('pastoral_notes'),
            tags=data.get('tags', [])
        )
        
        # Add discipleship milestones if provided
        milestone_fields = ['dna_completed', 'baptised_on', 'filled_holy_spirit', 'rise_attended', 'first_served_on']
        for field in milestone_fields:
            if data.get(field):
                setattr(person, field, datetime.strptime(data[field], '%Y-%m-%d').date())
        
        db.session.commit()
        
        # Return created person with engagement data
        person_data = person.to_dict()
        person_data.update({
            'pulse_status': engagement.pulse_status,
            'last_seen': engagement.last_seen.isoformat() if engagement.last_seen else None,
            'pulse_reasons': engagement.get_pulse_reasons()
        })
        
        return jsonify(person_data), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating person: {e}")
        return jsonify({'error': 'Failed to create person'}), 500


@app.route('/api/persons/<person_id>', methods=['GET'])
@login_required
def get_person_detail(person_id):
    """Get detailed person info with full engagement profile (admin only)"""
    try:
        if not current_user.has_permission('query_access'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        person = Person.query.filter_by(id=person_id, is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Get person data
        person_data = person.to_dict()
        
        # Add full engagement profile
        if person.engagement_profile:
            engagement_data = person.engagement_profile.to_dict()
            person_data['engagement'] = engagement_data
        else:
            # Create engagement profile if it doesn't exist
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
            db.session.commit()
            person_data['engagement'] = engagement.to_dict()
        
        return jsonify(person_data)
        
    except Exception as e:
        logger.error(f"Error fetching person detail: {e}")
        return jsonify({'error': 'Failed to fetch person details'}), 500


@app.route('/api/persons/<person_id>', methods=['PUT'])
@login_required
def update_person(person_id):
    """Update person details (admin only)"""
    try:
        if not current_user.has_permission('query_access'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        person = Person.query.filter_by(id=person_id, is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update basic information
        if 'full_name' in data:
            person.full_name = data['full_name']
        if 'preferred_name' in data:
            person.preferred_name = data['preferred_name']
        if 'email' in data:
            # Check if email is already taken by another person
            existing = Person.query.filter_by(email=data['email'], is_active=True).first()
            if existing and existing.id != person.id:
                return jsonify({'error': 'Email already in use'}), 400
            person.email = data['email']
        if 'campus' in data:
            person.campus = data['campus']
        if 'department' in data:
            person.department = data['department'] if data['department'] else None
        if 'connect_group' in data:
            person.connect_group = data['connect_group']
        if 'dream_team_roles' in data:
            person.dream_team_roles = data['dream_team_roles']
        
        # Update discipleship milestones (convert empty strings to None)
        milestone_fields = [
            'dna_completed', 'baptised_on', 'rise_attended', 
            'filled_holy_spirit', 'first_served_on'
        ]
        
        for field in milestone_fields:
            if field in data:
                value = data[field]
                if value == '' or value is None:
                    setattr(person, field, None)
                else:
                    # Try to parse the date
                    try:
                        if isinstance(value, str):
                            # Parse date string
                            from datetime import datetime
                            parsed_date = datetime.strptime(value, '%Y-%m-%d').date()
                            setattr(person, field, parsed_date)
                        else:
                            setattr(person, field, value)
                    except ValueError:
                        return jsonify({'error': f'Invalid date format for {field}'}), 400
        
        # Update engagement profile pulse status if attendance/serving changed
        # (Pulse will be recalculated automatically on next access)
        
        db.session.commit()
        
        # Return updated person data
        person_data = person.to_dict()
        if person.engagement_profile:
            person_data['engagement'] = person.engagement_profile.to_dict()
        
        return jsonify({
            'message': 'Person updated successfully',
            'person': person_data
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating person {person_id}: {e}")
        return jsonify({'error': 'Failed to update person'}), 500


@app.route('/api/persons/<person_id>/archive', methods=['POST'])
@login_required
def archive_person(person_id):
    """Archive a person (soft delete - sets is_active to False)"""
    try:
        if not current_user.has_permission('query_access'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        person = Person.query.filter_by(id=person_id).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        person.is_active = False
        db.session.commit()
        
        logger.info(f"Person {person_id} archived by user {current_user.id}")
        return jsonify({
            'message': 'Person archived successfully',
            'person': person.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error archiving person {person_id}: {e}")
        return jsonify({'error': 'Failed to archive person'}), 500


@app.route('/api/persons/<person_id>/restore', methods=['POST'])
@login_required
def restore_person(person_id):
    """Restore an archived person (sets is_active to True)"""
    try:
        if not current_user.has_permission('query_access'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        person = Person.query.filter_by(id=person_id).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        person.is_active = True
        db.session.commit()
        
        logger.info(f"Person {person_id} restored by user {current_user.id}")
        return jsonify({
            'message': 'Person restored successfully',
            'person': person.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error restoring person {person_id}: {e}")
        return jsonify({'error': 'Failed to restore person'}), 500


@app.route('/api/persons/<person_id>', methods=['DELETE'])
@login_required
def delete_person(person_id):
    """Permanently delete a person from the database (hard delete)"""
    try:
        if not current_user.has_permission('query_access'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        person = Person.query.filter_by(id=person_id).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Delete engagement profile first (cascade should handle this, but being explicit)
        if person.engagement_profile:
            db.session.delete(person.engagement_profile)
        
        # Delete the person
        db.session.delete(person)
        db.session.commit()
        
        logger.info(f"Person {person_id} permanently deleted by user {current_user.id}")
        return jsonify({
            'message': 'Person permanently deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting person {person_id}: {e}")
        return jsonify({'error': 'Failed to delete person'}), 500


@app.route('/api/persons/import_pco', methods=['POST'])
@login_required
def import_pco_csv():
    """Import people from Planning Center Online CSV export"""
    try:
        if not current_user.has_permission('query_access'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        import csv
        from io import StringIO
        
        # Read CSV content
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        # Get active campuses for mapping
        active_campuses = get_active_campuses()
        campus_name_to_id = {c['name']: c['id'] for c in active_campuses}
        
        added_count = 0
        skipped_count = 0
        errors = []
        seen_emails = set()
        seen_pco_ids = set()
        
        for row in csv_reader:
            try:
                # Get PCO Person ID (use as primary key)
                pco_id = str(row.get('Person ID', '').strip())
                if not pco_id:
                    skipped_count += 1
                    continue
                
                # Check for duplicate PCO ID
                if pco_id in seen_pco_ids:
                    skipped_count += 1
                    continue
                seen_pco_ids.add(pco_id)
                
                # Check if person already exists
                existing = Person.query.filter_by(id=pco_id).first()
                if existing:
                    skipped_count += 1
                    continue
                
                # Get email (can be empty)
                email = row.get('Email', '').strip() or None
                
                # Check for duplicate email within this import
                if email and email in seen_emails:
                    skipped_count += 1
                    continue
                if email:
                    seen_emails.add(email)
                
                # Get name
                full_name = row.get('Name', '').strip()
                if not full_name:
                    skipped_count += 1
                    continue
                
                # Get campus and map to ID
                campus_name = row.get('Campus', '').strip()
                campus_id = campus_name_to_id.get(campus_name, 'all_campuses')
                
                # Get department (if available in CSV)
                department = row.get('Department', '').strip() or None
                
                # Create person
                person = Person(
                    id=pco_id,
                    full_name=full_name,
                    preferred_name=row.get('Preferred Name', '').strip() or None,
                    email=email or f'no-email-{pco_id}@futures.church',  # Placeholder if no email
                    phone=row.get('Phone', '').strip() or None,
                    campus=campus_id,
                    department=department,
                    connect_group=row.get('Connect Group', '').strip() or None,
                    is_active=True
                )
                
                db.session.add(person)
                
                # Create engagement profile
                engagement = EngagementProfile(person_id=person.id)
                db.session.add(engagement)
                
                added_count += 1
                
            except Exception as e:
                errors.append(f"Row error: {str(e)}")
                skipped_count += 1
                continue
        
        db.session.commit()
        
        return jsonify({
            'message': f'Import completed: {added_count} added, {skipped_count} skipped',
            'added': added_count,
            'skipped': skipped_count,
            'errors': errors[:10]  # Limit errors returned
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing PCO CSV: {e}")
        return jsonify({'error': f'Failed to import CSV: {str(e)}'}), 500


@app.route('/api/engagement/log_attendance', methods=['POST'])
def log_attendance():
    """Log attendance via beacon detection (public endpoint for mobile app)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['person_email', 'beacon_uuid', 'beacon_major', 'beacon_minor']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Find person by email
        person = Person.query.filter_by(email=data['person_email'], is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Find beacon zone
        zone = BeaconZone.find_zone(
            uuid=data['beacon_uuid'],
            major=data['beacon_major'],
            minor=data['beacon_minor']
        )
        if not zone:
            return jsonify({'error': 'Beacon zone not found'}), 404
        
        # Get or create engagement profile
        engagement = person.engagement_profile
        if not engagement:
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
        
        # Log attendance
        attendance_time = datetime.now()
        if data.get('timestamp'):
            try:
                attendance_time = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                pass  # Use current time if timestamp is invalid
        
        # Check for duplicate attendance (within 10 minutes)
        recent_attendance = engagement.attendance_log or []
        for record in recent_attendance[-5:]:  # Check last 5 records
            record_time = datetime.fromisoformat(record['timestamp'])
            time_diff = (attendance_time - record_time).total_seconds()
            if time_diff < 600:  # 10 minutes
                # Check if same zone
                if zone.zone_name in record['zones']:
                    return jsonify({
                        'message': 'Attendance already logged recently',
                        'duplicate': True
                    })
        
        # Add attendance record
        engagement.add_attendance(
            zones=[zone.zone_name],
            campus=zone.campus,
            attendance_time=attendance_time
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Attendance logged successfully',
            'person_id': person.id,
            'zone': zone.zone_name,
            'campus': zone.campus,
            'timestamp': attendance_time.isoformat(),
            'pulse_status': engagement.pulse_status
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging attendance: {e}")
        return jsonify({'error': 'Failed to log attendance'}), 500


@app.route('/api/engagement/log_serving', methods=['POST'])
@login_required
def log_serving():
    """Log serving activity (admin only)"""
    try:
        if not current_user.has_permission('pulse', 'write'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['person_id', 'role', 'location', 'campus']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Find person
        person = Person.query.filter_by(id=data['person_id'], is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Get or create engagement profile
        engagement = person.engagement_profile
        if not engagement:
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
        
        # Parse serving date
        serving_date = datetime.now().date()
        if data.get('date'):
            try:
                serving_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Add serving record
        engagement.add_serving_record(
            role=data['role'],
            campus=data['campus'],
            serving_date=serving_date,
            location=data.get('location')
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Serving activity logged successfully',
            'person_id': person.id,
            'role': data['role'],
            'location': data['location'],
            'campus': data['campus'],
            'date': serving_date.strftime('%Y-%m-%d'),
            'pulse_status': engagement.pulse_status
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging serving: {e}")
        return jsonify({'error': 'Failed to log serving activity'}), 500


@app.route('/api/engagement/log_bible', methods=['POST'])
def log_bible():
    """Log Bible reading (public endpoint for mobile app)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'person_email' not in data:
            return jsonify({'error': 'Missing required field: person_email'}), 400
        
        # Find person by email
        person = Person.query.filter_by(email=data['person_email'], is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Get or create engagement profile
        engagement = person.engagement_profile
        if not engagement:
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
        
        # Parse reading date
        reading_date = None
        if data.get('date'):
            try:
                reading_date = datetime.fromisoformat(data['date']).date()
            except (ValueError, AttributeError):
                try:
                    reading_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                except ValueError:
                    pass  # Use current date if invalid
        
        # Add Bible reading record
        engagement.add_bible_reading(reading_date=reading_date)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Bible reading logged successfully',
            'person_id': person.id,
            'date': reading_date.isoformat() if reading_date else datetime.now().date().isoformat(),
            'pulse_status': engagement.pulse_status
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging Bible reading: {e}")
        return jsonify({'error': 'Failed to log Bible reading'}), 500


@app.route('/api/engagement/log_giving', methods=['POST'])
def log_giving():
    """Log giving (public endpoint for mobile app or Stripe webhook)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'person_email' not in data:
            return jsonify({'error': 'Missing required field: person_email'}), 400
        if 'amount' not in data:
            return jsonify({'error': 'Missing required field: amount'}), 400
        
        # Find person by email
        person = Person.query.filter_by(email=data['person_email'], is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Get or create engagement profile
        engagement = person.engagement_profile
        if not engagement:
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
        
        # Parse giving date
        giving_date = None
        if data.get('date'):
            try:
                giving_date = datetime.fromisoformat(data['date']).date()
            except (ValueError, AttributeError):
                try:
                    giving_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                except ValueError:
                    pass  # Use current date if invalid
        
        # Add giving record
        engagement.add_giving(
            amount=data['amount'],
            giving_date=giving_date,
            campus=data.get('campus', person.campus)
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Giving logged successfully',
            'person_id': person.id,
            'amount': float(data['amount']),
            'date': giving_date.isoformat() if giving_date else datetime.now().date().isoformat(),
            'pulse_status': engagement.pulse_status
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging giving: {e}")
        return jsonify({'error': 'Failed to log giving'}), 500


@app.route('/api/engagement/log_group_attendance', methods=['POST'])
def log_group_attendance():
    """Log connect group attendance (for leader portal)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['person_id', 'group_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Find person
        person = Person.query.filter_by(id=data['person_id'], is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Verify person is in the group
        if person.connect_group != data['group_id']:
            return jsonify({'error': 'Person is not a member of this group'}), 400
        
        # Get or create engagement profile
        engagement = person.engagement_profile
        if not engagement:
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
        
        # Parse attendance date
        attendance_date = None
        if data.get('date'):
            try:
                attendance_date = datetime.fromisoformat(data['date']).date()
            except (ValueError, AttributeError):
                try:
                    attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                except ValueError:
                    pass  # Use current date if invalid
        
        # Add group attendance record
        engagement.add_group_attendance(
            group_id=data['group_id'],
            attendance_date=attendance_date,
            present=data.get('present', True)
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Group attendance logged successfully',
            'person_id': person.id,
            'group_id': data['group_id'],
            'date': attendance_date.isoformat() if attendance_date else datetime.now().date().isoformat(),
            'present': data.get('present', True),
            'pulse_status': engagement.pulse_status
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging group attendance: {e}")
        return jsonify({'error': 'Failed to log group attendance'}), 500


# ============================================================================
# CONNECT GROUPS API ROUTES
# ============================================================================

@app.route('/api/connect-groups', methods=['GET'])
@login_required
def get_connect_groups():
    """Get list of connect groups (campus-scoped)"""
    try:
        if not current_user.has_permission('groups', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        campus_filter = request.args.get('campus', None)
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        
        # Build query
        query = ConnectGroup.query
        
        # Apply campus scoping
        from utils.campus_scope import apply_campus_filter
        query = apply_campus_filter(query, 'groups')
        
        if campus_filter and campus_filter != 'all_campuses':
            query = query.filter(ConnectGroup.campus == campus_filter)
        
        if is_active:
            query = query.filter(ConnectGroup.is_active == True)
        
        groups = query.order_by(ConnectGroup.name).all()
        
        return jsonify({
            'groups': [g.to_dict() for g in groups],
            'total': len(groups)
        })
        
    except Exception as e:
        logger.error(f"Error fetching connect groups: {e}")
        return jsonify({'error': 'Failed to fetch connect groups'}), 500


@app.route('/api/connect-groups', methods=['POST'])
@login_required
def create_connect_group():
    """Create new connect group"""
    try:
        if not current_user.has_permission('groups', 'create'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'campus', 'leader_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate group ID
        import uuid
        group_id = f"cg_{data['campus'].lower().replace(' ', '_')}_{str(uuid.uuid4())[:8]}"
        
        # Verify leader exists
        leader = Person.query.filter_by(id=data['leader_id'], is_active=True).first()
        if not leader:
            return jsonify({'error': 'Leader not found'}), 404
        
        # Create group
        group = ConnectGroup(
            id=group_id,
            name=data['name'],
            campus=data['campus'],
            leader_id=data['leader_id'],
            co_leader_id=data.get('co_leader_id'),
            meeting_day=data.get('meeting_day'),
            meeting_time=data.get('meeting_time'),
            meeting_frequency=data.get('meeting_frequency', 'weekly'),
            location=data.get('location'),
            leader_access_code=data.get('leader_access_code')  # Simple password for leader portal
        )
        
        db.session.add(group)
        db.session.commit()
        
        return jsonify({
            'message': 'Connect group created successfully',
            'group': group.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating connect group: {e}")
        return jsonify({'error': 'Failed to create connect group'}), 500


@app.route('/api/connect-groups/<group_id>', methods=['GET'])
@login_required
def get_connect_group(group_id):
    """Get connect group details with members"""
    try:
        if not current_user.has_permission('groups', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        group = ConnectGroup.query.filter_by(id=group_id).first()
        if not group:
            return jsonify({'error': 'Connect group not found'}), 404
        
        # Get members
        members = group.get_members()
        
        # Get meetings (sorted by date, most recent first)
        meetings = ConnectGroupMeeting.query.filter_by(group_id=group_id).order_by(ConnectGroupMeeting.meeting_date.desc()).all()
        
        group_data = group.to_dict()
        group_data['members'] = [m.to_dict() for m in members]
        group_data['meetings'] = [m.to_dict() for m in meetings]
        
        return jsonify(group_data)
        
    except Exception as e:
        logger.error(f"Error fetching connect group: {e}")
        return jsonify({'error': 'Failed to fetch connect group'}), 500


@app.route('/api/connect-groups/<group_id>', methods=['PUT'])
@login_required
def update_connect_group(group_id):
    """Update connect group"""
    try:
        if not current_user.has_permission('groups', 'edit'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        group = ConnectGroup.query.filter_by(id=group_id).first()
        if not group:
            return jsonify({'error': 'Connect group not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            group.name = data['name']
        if 'leader_id' in data:
            leader = Person.query.filter_by(id=data['leader_id'], is_active=True).first()
            if not leader:
                return jsonify({'error': 'Leader not found'}), 404
            group.leader_id = data['leader_id']
        if 'co_leader_id' in data:
            if data['co_leader_id']:
                co_leader = Person.query.filter_by(id=data['co_leader_id'], is_active=True).first()
                if not co_leader:
                    return jsonify({'error': 'Co-leader not found'}), 404
            group.co_leader_id = data['co_leader_id']
        if 'meeting_day' in data:
            group.meeting_day = data['meeting_day']
        if 'meeting_time' in data:
            group.meeting_time = data['meeting_time']
        if 'meeting_frequency' in data:
            group.meeting_frequency = data['meeting_frequency']
        if 'location' in data:
            group.location = data['location']
        if 'leader_access_code' in data:
            group.leader_access_code = data['leader_access_code']
        if 'is_active' in data:
            group.is_active = data['is_active']
        
        group.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Connect group updated successfully',
            'group': group.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating connect group: {e}")
        return jsonify({'error': 'Failed to update connect group'}), 500


@app.route('/api/connect-groups/<group_id>/members', methods=['POST'])
@login_required
def add_group_member(group_id):
    """Add member to connect group"""
    try:
        if not current_user.has_permission('groups', 'edit'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        group = ConnectGroup.query.filter_by(id=group_id).first()
        if not group:
            return jsonify({'error': 'Connect group not found'}), 404
        
        data = request.get_json()
        person_id = data.get('person_id')
        
        if not person_id:
            return jsonify({'error': 'Missing person_id'}), 400
        
        person = Person.query.filter_by(id=person_id, is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Update person's connect_group
        person.connect_group = group_id
        db.session.commit()
        
        return jsonify({
            'message': 'Member added successfully',
            'person': person.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding group member: {e}")
        return jsonify({'error': 'Failed to add member'}), 500


@app.route('/api/connect-groups/<group_id>/members/<person_id>', methods=['DELETE'])
@login_required
def remove_group_member(group_id, person_id):
    """Remove member from connect group"""
    try:
        if not current_user.has_permission('groups', 'edit'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        person = Person.query.filter_by(id=person_id, is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        if person.connect_group != group_id:
            return jsonify({'error': 'Person is not a member of this group'}), 400
        
        person.connect_group = None
        db.session.commit()
        
        return jsonify({
            'message': 'Member removed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing group member: {e}")
        return jsonify({'error': 'Failed to remove member'}), 500


@app.route('/api/connect-groups/<group_id>/meetings', methods=['POST'])
def create_group_meeting(group_id):
    """Create a connect group meeting (allows leader access via email + access code)"""
    try:
        group = ConnectGroup.query.filter_by(id=group_id).first()
        if not group:
            return jsonify({'error': 'Connect group not found'}), 404
        
        data = request.get_json()
        
        # Check permissions - either logged-in admin/staff OR leader via email + access code
        is_leader = False
        is_authenticated_user = False
        
        # Check if user is logged in
        try:
            if current_user and hasattr(current_user, 'email'):
                leader_email = group.leader.email if group.leader else None
                co_leader_email = group.co_leader.email if group.co_leader else None
                is_leader = (leader_email == current_user.email) or (co_leader_email == current_user.email)
                is_authenticated_user = current_user.has_permission('groups', 'edit')
        except:
            pass  # Not logged in, check email + access code
        
        # If not authenticated user, check email + access code
        if not is_authenticated_user and not is_leader:
            leader_email = group.leader.email if group.leader else None
            co_leader_email = group.co_leader.email if group.co_leader else None
            provided_email = data.get('leader_email', '').lower()
            provided_code = data.get('access_code', '')
            
            if provided_email and (provided_email == leader_email.lower() or provided_email == co_leader_email.lower()):
                # Verify access code if set
                if group.leader_access_code:
                    if provided_code != group.leader_access_code:
                        return jsonify({'error': 'Invalid access code'}), 403
                is_leader = True
            else:
                return jsonify({'error': 'Insufficient permissions'}), 403
        
        if not (is_authenticated_user or is_leader):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Parse meeting date
        meeting_date = datetime.now().date()
        if data.get('meeting_date'):
            try:
                meeting_date = datetime.fromisoformat(data['meeting_date']).date()
            except (ValueError, AttributeError):
                try:
                    meeting_date = datetime.strptime(data['meeting_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Create meeting
        meeting = ConnectGroupMeeting(
            group_id=group_id,
            meeting_date=meeting_date,
            notes=data.get('notes')
        )
        
        db.session.add(meeting)
        db.session.flush()  # Get meeting ID
        
        # Create attendance records for all group members
        members = group.get_members()
        for member in members:
            attendance = ConnectGroupAttendance(
                meeting_id=meeting.id,
                person_id=member.id,
                present=False  # Default to absent, leader will mark present
            )
            db.session.add(attendance)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Meeting created successfully',
            'meeting': meeting.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating group meeting: {e}")
        return jsonify({'error': 'Failed to create meeting'}), 500


@app.route('/api/connect-groups/meetings/<meeting_id>', methods=['GET'])
def get_group_meeting(meeting_id):
    """Get meeting details with attendance"""
    try:
        meeting = ConnectGroupMeeting.query.filter_by(id=meeting_id).first()
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
        
        group = meeting.group
        
        # Get attendance records
        attendance_records = ConnectGroupAttendance.query.filter_by(meeting_id=meeting_id).all()
        
        meeting_data = meeting.to_dict()
        meeting_data['attendance'] = [att.to_dict() for att in attendance_records]
        
        return jsonify(meeting_data)
        
    except Exception as e:
        logger.error(f"Error fetching meeting: {e}")
        return jsonify({'error': 'Failed to fetch meeting'}), 500


@app.route('/api/connect-groups/meetings/<meeting_id>/attendance', methods=['POST'])
def submit_meeting_attendance(meeting_id):
    """Submit attendance for a meeting (allows leader access via email + access code)"""
    try:
        meeting = ConnectGroupMeeting.query.filter_by(id=meeting_id).first()
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
        
        group = meeting.group
        data = request.get_json()
        
        # Check permissions - either logged-in admin/staff OR leader via email + access code
        is_leader = False
        is_authenticated_user = False
        
        # Check if user is logged in
        try:
            if current_user and hasattr(current_user, 'email'):
                leader_email = group.leader.email if group.leader else None
                co_leader_email = group.co_leader.email if group.co_leader else None
                is_leader = (leader_email == current_user.email) or (co_leader_email == current_user.email)
                is_authenticated_user = current_user.has_permission('groups', 'edit')
        except:
            pass  # Not logged in, check email + access code
        
        # If not authenticated user, check email + access code
        if not is_authenticated_user and not is_leader:
            leader_email = group.leader.email if group.leader else None
            co_leader_email = group.co_leader.email if group.co_leader else None
            provided_email = data.get('leader_email', '').lower()
            provided_code = data.get('access_code', '')
            
            if provided_email and (provided_email == leader_email.lower() or provided_email == co_leader_email.lower()):
                # Verify access code if set
                if group.leader_access_code:
                    if provided_code != group.leader_access_code:
                        return jsonify({'error': 'Invalid access code'}), 403
                is_leader = True
            else:
                return jsonify({'error': 'Insufficient permissions'}), 403
        
        if not (is_authenticated_user or is_leader):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        attendance_list = data.get('attendance', [])  # [{person_id, present, notes?}]
        
        if not attendance_list:
            return jsonify({'error': 'No attendance data provided'}), 400
        
        # Update attendance records
        for att_data in attendance_list:
            person_id = att_data.get('person_id')
            present = att_data.get('present', False)
            
            if not person_id:
                continue
            
            # Find or create attendance record
            attendance = ConnectGroupAttendance.query.filter_by(
                meeting_id=meeting_id,
                person_id=person_id
            ).first()
            
            if attendance:
                attendance.present = present
                attendance.notes = att_data.get('notes')
            else:
                # Create new attendance record
                attendance = ConnectGroupAttendance(
                    meeting_id=meeting_id,
                    person_id=person_id,
                    present=present,
                    notes=att_data.get('notes')
                )
                db.session.add(attendance)
            
            # Update engagement profile if present
            if present:
                person = Person.query.filter_by(id=person_id).first()
                if person and person.engagement_profile:
                    person.engagement_profile.add_group_attendance(
                        group_id=group.id,
                        attendance_date=meeting.meeting_date,
                        present=True
                    )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Attendance submitted successfully',
            'meeting': meeting.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting attendance: {e}")
        return jsonify({'error': 'Failed to submit attendance'}), 500


@app.route('/api/pulse/<person_id>', methods=['GET'])
@login_required
def get_pulse_status(person_id):
    """Get pulse status and reasons for a person (admin only)"""
    try:
        if not current_user.has_permission('pulse', 'read'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        person = Person.query.filter_by(id=person_id, is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        engagement = person.engagement_profile
        if not engagement:
            return jsonify({
                'person_id': person_id,
                'pulse_status': 'red',
                'pulse_reasons': ['No engagement data'],
                'last_calculated': None
            })
        
        return jsonify({
            'person_id': person_id,
            'pulse_status': engagement.pulse_status,
            'pulse_reasons': engagement.get_pulse_reasons(),
            'last_calculated': engagement.pulse_last_calculated.isoformat(),
            'metrics': {
                'attendance_frequency': engagement.attendance_frequency,
                'serving_frequency': engagement.serving_frequency,
                'overall_engagement': engagement.overall_engagement,
                'last_seen': engagement.last_seen.isoformat() if engagement.last_seen else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching pulse status: {e}")
        return jsonify({'error': 'Failed to fetch pulse status'}), 500


@app.route('/api/beacon_zones', methods=['GET'])
@login_required
def get_beacon_zones():
    """Get all beacon zones (admin only)"""
    try:
        if not current_user.has_permission('pulse', 'read'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        campus_filter = request.args.get('campus', None)
        
        query = BeaconZone.query.filter_by(is_active=True)
        if campus_filter and campus_filter != 'all_campuses':
            query = query.filter(BeaconZone.campus == campus_filter)
        
        zones = query.order_by(BeaconZone.campus, BeaconZone.zone_name).all()
        
        return jsonify({
            'zones': [zone.to_dict() for zone in zones],
            'total': len(zones)
        })
        
    except Exception as e:
        logger.error(f"Error fetching beacon zones: {e}")
        return jsonify({'error': 'Failed to fetch beacon zones'}), 500


@app.route('/api/passport/<person_email>', methods=['GET'])
def get_passport_data(person_email):
    """Get passport/discipleship data for a user (public endpoint)"""
    try:
        # Find person by email
        person = Person.query.filter_by(email=person_email, is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Return only positive, step-focused data (no attendance or pulse status)
        passport_data = {
            'person': {
                'full_name': person.full_name,
                'preferred_name': person.preferred_name,
                'campus': person.campus
            },
            'milestones': {
                'dna_completed': person.dna_completed.isoformat() if person.dna_completed else None,
                'baptised_on': person.baptised_on.isoformat() if person.baptised_on else None,
                'filled_holy_spirit': person.filled_holy_spirit.isoformat() if person.filled_holy_spirit else None,
                'rise_attended': person.rise_attended.isoformat() if person.rise_attended else None,
                'first_served_on': person.first_served_on.isoformat() if person.first_served_on else None
            },
            'current_involvement': {
                'connect_group': person.connect_group,
                'dream_team_roles': person.dream_team_roles or []
            },
            'next_steps': []
        }
        
        # Calculate suggested next steps
        next_steps = []
        if not person.dna_completed:
            next_steps.append({
                'title': 'Complete DNA',
                'description': 'Discover your purpose and calling',
                'priority': 'high',
                'category': 'discipleship'
            })
        elif not person.baptised_on:
            next_steps.append({
                'title': 'Get Baptised',
                'description': 'Take the next step in your faith journey',
                'priority': 'high',
                'category': 'discipleship'
            })
        elif not person.rise_attended:
            next_steps.append({
                'title': 'Attend RISE',
                'description': 'Deepen your relationship with the Holy Spirit',
                'priority': 'medium',
                'category': 'discipleship'
            })
        
        if not person.connect_group:
            next_steps.append({
                'title': 'Join a Connect Group',
                'description': 'Build meaningful relationships and grow together',
                'priority': 'high',
                'category': 'community'
            })
        
        if not person.dream_team_roles or len(person.dream_team_roles) == 0:
            next_steps.append({
                'title': 'Join the Dream Team',
                'description': 'Use your gifts to serve others',
                'priority': 'medium',
                'category': 'serving'
            })
        
        passport_data['next_steps'] = next_steps
        
        return jsonify(passport_data)
        
    except Exception as e:
        logger.error(f"Error fetching passport data: {e}")
        return jsonify({'error': 'Failed to fetch passport data'}), 500


# ============================================================================
# END PULSE & PASSPORT API ROUTES
# ============================================================================

# PRAYER REQUEST SYSTEM ROUTES
from prayer_api import prayer_bp
app.register_blueprint(prayer_bp)

# SERVING MODULE ROUTES
from serving_api import serving_bp
app.register_blueprint(serving_bp)

# WEBHOOK ROUTES
from webhooks import webhooks_bp
app.register_blueprint(webhooks_bp)

# USER MANAGEMENT ROUTES
@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """Get all users (admin and leadership roles only)"""
    try:
        if current_user.role not in ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        users_db = load_users_database()
        users_list = []
        
        for user_id, user_data in users_db.get('users', {}).items():
            # Don't send password hash to frontend
            user_info = {
                'id': user_data.get('id'),
                'username': user_data.get('username'),
                'email': user_data.get('email', ''),
                'full_name': user_data.get('full_name'),
                'role': user_data.get('role'),
                'campus': user_data.get('campus'),
                'active': user_data.get('active', True),
                'last_login': user_data.get('last_login'),
                'created_date': user_data.get('created_date')
            }
            users_list.append(user_info)
        
        return jsonify({'users': users_list, 'success': True})
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({'error': 'Failed to fetch users'}), 500

# COMMUNICATIONS PLATFORM ROUTES
@app.route('/api/communications/campaigns', methods=['GET'])
@admin_required
def get_communications_campaigns():
    """Get all communication campaigns"""
    try:
        # Mock data for now - replace with database integration
        campaigns = [
            {
                'id': '1',
                'name': 'Weekly Update',
                'type': 'email',
                'status': 'active',
                'created_at': '2025-01-15T10:00:00Z',
                'recipients': 1250,
                'open_rate': 68.5
            },
            {
                'id': '2', 
                'name': 'Youth Event Reminder',
                'type': 'sms',
                'status': 'scheduled',
                'created_at': '2025-01-14T14:30:00Z',
                'recipients': 320,
                'open_rate': 0
            }
        ]
        return jsonify({'campaigns': campaigns})
    except Exception as e:
        logger.error(f"Error fetching campaigns: {e}")
        return jsonify({'error': 'Failed to fetch campaigns'}), 500

@app.route('/api/communications/campaigns', methods=['POST'])
@admin_required
def create_communications_campaign():
    """Create a new communication campaign"""
    try:
        data = request.get_json()
        # Mock creation - replace with database integration
        new_campaign = {
            'id': str(uuid.uuid4()),
            'name': data.get('name', 'New Campaign'),
            'type': data.get('type', 'email'),
            'status': 'draft',
            'created_at': datetime.now().isoformat(),
            'recipients': 0,
            'open_rate': 0
        }
        return jsonify({'campaign': new_campaign, 'message': 'Campaign created successfully'})
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        return jsonify({'error': 'Failed to create campaign'}), 500

@app.route('/api/communications/campaigns/<campaign_id>', methods=['PUT'])
@admin_required
def update_communications_campaign(campaign_id):
    """Update an existing communication campaign"""
    try:
        data = request.get_json()
        # Mock update - replace with database integration
        updated_campaign = {
            'id': campaign_id,
            'name': data.get('name', 'Updated Campaign'),
            'type': data.get('type', 'email'),
            'status': data.get('status', 'draft'),
            'updated_at': datetime.now().isoformat(),
            'recipients': 0,
            'open_rate': 0
        }
        return jsonify({'campaign': updated_campaign, 'message': 'Campaign updated successfully'})
    except Exception as e:
        logger.error(f"Error updating campaign: {e}")
        return jsonify({'error': 'Failed to update campaign'}), 500

@app.route('/api/communications/campaigns/<campaign_id>', methods=['DELETE'])
@admin_required
def delete_communications_campaign(campaign_id):
    """Delete a communication campaign"""
    try:
        # Mock deletion - replace with database integration
        return jsonify({'message': 'Campaign deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting campaign: {e}")
        return jsonify({'error': 'Failed to delete campaign'}), 500

@app.route('/api/communication/stats/overview', methods=['GET'])
@admin_required
def get_communication_stats():
    """Get communication dashboard statistics"""
    try:
        # Mock data for now - replace with database integration
        stats = {
            'total_campaigns': 12,
            'active_campaigns': 3,
            'draft_campaigns': 5,
            'completed_campaigns': 4
        }
        
        recent_campaigns = [
            {
                'id': '1',
                'name': 'Weekly Update',
                'type': 'email',
                'status': 'active',
                'recipients': 1250,
                'open_rate': 68.5,
                'created_at': '2025-01-15T10:00:00Z'
            },
            {
                'id': '2',
                'name': 'Youth Event Reminder',
                'type': 'sms',
                'status': 'scheduled',
                'recipients': 320,
                'open_rate': 0,
                'created_at': '2025-01-14T14:30:00Z'
            },
            {
                'id': '3',
                'name': 'Connect Group Invitation',
                'type': 'email',
                'status': 'completed',
                'recipients': 890,
                'open_rate': 72.1,
                'created_at': '2025-01-10T09:00:00Z'
            }
        ]
        
        return jsonify({
            'success': True,
            'stats': stats,
            'recent_campaigns': recent_campaigns
        })
    except Exception as e:
        logger.error(f"Error fetching communication stats: {e}")
        return jsonify({'error': 'Failed to fetch communication stats'}), 500

# DEVOTIONS MODULE ROUTES
@app.route('/api/devotions', methods=['GET'])
@admin_required
def get_devotions():
    """Get all devotions with optional filtering"""
    try:
        plan_id = request.args.get('plan_id')
        status = request.args.get('status')
        
        # Mock data for now - replace with database integration
        devotions = [
            {
                'id': '1',
                'title': 'Walking in Faith',
                'content': 'Today we explore what it means to walk by faith and not by sight...',
                'scripture_reference': 'Hebrews 11:1',
                'scripture_text': 'Now faith is confidence in what we hope for and assurance about what we do not see.',
                'plan': {'id': 'acts-study', 'name': 'Acts Study', 'total_days': 30},
                'day_number': 1,
                'status': 'published',
                'author': 'Pastor Sarah',
                'created_at': '2025-01-10T06:00:00Z',
                'scheduled_date': '2025-01-15T06:00:00Z',
                'tags': ['faith', 'trust', 'hope']
            },
            {
                'id': '2',
                'title': 'The Power of Prayer',
                'content': 'Prayer is not just talking to God, but developing a relationship with Him...',
                'scripture_reference': '1 Thessalonians 5:17',
                'scripture_text': 'Pray continually.',
                'plan': {'id': 'daily-devotional', 'name': 'Daily Devotional', 'total_days': 365},
                'day_number': 15,
                'status': 'draft',
                'author': 'Pastor John',
                'created_at': '2025-01-12T06:00:00Z',
                'scheduled_date': None,
                'tags': ['prayer', 'relationship', 'communication']
            }
        ]
        
        # Apply filters
        if plan_id and plan_id != 'all':
            devotions = [d for d in devotions if d['plan']['id'] == plan_id]
        if status and status != 'all':
            devotions = [d for d in devotions if d['status'] == status]
            
        return jsonify({'devotions': devotions})
    except Exception as e:
        logger.error(f"Error fetching devotions: {e}")
        return jsonify({'error': 'Failed to fetch devotions'}), 500

@app.route('/api/devotions/<devotion_id>', methods=['GET'])
@admin_required
def get_devotion(devotion_id):
    """Get a specific devotion by ID"""
    try:
        # Mock data - replace with database integration
        devotion = {
            'id': devotion_id,
            'title': 'Walking in Faith',
            'content': 'Today we explore what it means to walk by faith and not by sight...',
            'scripture_reference': 'Hebrews 11:1',
            'scripture_text': 'Now faith is confidence in what we hope for and assurance about what we do not see.',
            'plan': {'id': 'acts-study', 'name': 'Acts Study', 'total_days': 30},
            'day_number': 1,
            'status': 'published',
            'author': 'Pastor Sarah',
            'created_at': '2025-01-10T06:00:00Z',
            'scheduled_date': '2025-01-15T06:00:00Z',
            'tags': ['faith', 'trust', 'hope']
        }
        return jsonify({'devotion': devotion})
    except Exception as e:
        logger.error(f"Error fetching devotion: {e}")
        return jsonify({'error': 'Failed to fetch devotion'}), 500

@app.route('/api/devotions/plans', methods=['GET'])
@admin_required
def get_devotion_plans():
    """Get all devotion plans"""
    try:
        # Mock data for now - replace with database integration
        plans = [
            {
                'id': 'acts-study',
                'name': 'Acts Study',
                'description': 'A 30-day journey through the Book of Acts',
                'total_days': 30,
                'current_day': 15,
                'status': 'active',
                'created_at': '2025-01-01T06:00:00Z',
                'tags': ['bible-study', 'acts', 'apostles']
            },
            {
                'id': 'daily-devotional',
                'name': 'Daily Devotional',
                'description': '365 days of daily inspiration and reflection',
                'total_days': 365,
                'current_day': 200,
                'status': 'active',
                'created_at': '2024-01-01T06:00:00Z',
                'tags': ['daily', 'inspiration', 'reflection']
            },
            {
                'id': 'prayer-journey',
                'name': 'Prayer Journey',
                'description': 'Deepening your prayer life in 21 days',
                'total_days': 21,
                'current_day': 0,
                'status': 'draft',
                'created_at': '2025-01-10T06:00:00Z',
                'tags': ['prayer', 'spiritual-growth', '21-days']
            }
        ]
        return jsonify({'plans': plans})
    except Exception as e:
        logger.error(f"Error fetching devotion plans: {e}")
        return jsonify({'error': 'Failed to fetch devotion plans'}), 500

# BLUETOOTH BEACON SYSTEM ROUTES
@app.route('/api/beacons/attendance', methods=['POST'])
def log_beacon_attendance():
    """Log attendance via beacon detection (public endpoint for mobile app)"""
    try:
        data = request.get_json()
        required_fields = ['person_email', 'beacon_uuid', 'beacon_major', 'beacon_minor']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Find beacon zone
        zone = BeaconZone.find_zone(
            uuid=data['beacon_uuid'],
            major=data['beacon_major'],
            minor=data['beacon_minor']
        )
        
        if not zone:
            return jsonify({'error': 'Beacon zone not found'}), 404
        
        # Log attendance
        attendance = EngagementProfile(
            person_email=data['person_email'],
            campus=zone.campus,
            activity_type='attendance',
            activity_date=datetime.now().date(),
            notes=f'Beacon detection in {zone.zone_name}'
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'message': 'Attendance logged successfully',
            'zone': zone.zone_name,
            'campus': zone.campus
        })
        
    except Exception as e:
        logger.error(f"Error logging beacon attendance: {e}")
        return jsonify({'error': 'Failed to log attendance'}), 500

@app.route('/api/beacons/zones', methods=['GET'])
def get_beacon_zones_public():
    """Get all active beacon zones (public endpoint)"""
    try:
        zones = BeaconZone.query.filter_by(is_active=True).all()
        zones_data = []
        for zone in zones:
            zones_data.append({
                'zone_name': zone.zone_name,
                'campus': zone.campus,
                'uuid': zone.uuid,
                'major': zone.major,
                'minor': zone.minor
            })
        return jsonify({'zones': zones_data})
    except Exception as e:
        logger.error(f"Error fetching beacon zones: {e}")
        return jsonify({'error': 'Failed to fetch beacon zones'}), 500

@app.route('/api/beacons/zones', methods=['POST'])
@admin_required
def create_beacon_zone():
    """Create a new beacon zone (admin only)"""
    try:
        data = request.get_json()
        required_fields = ['zone_name', 'campus', 'uuid', 'major', 'minor']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        new_zone = BeaconZone(
            zone_name=data['zone_name'],
            campus=data['campus'],
            uuid=data['uuid'],
            major=data['major'],
            minor=data['minor'],
            is_active=True
        )
        
        db.session.add(new_zone)
        db.session.commit()
        
        return jsonify({
            'message': 'Beacon zone created successfully',
            'zone': {
                'id': new_zone.id,
                'zone_name': new_zone.zone_name,
                'campus': new_zone.campus
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating beacon zone: {e}")
        return jsonify({'error': 'Failed to create beacon zone'}), 500


# Events API endpoints
@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all events with optional filtering"""
    try:
        # Get query parameters
        campus = request.args.get('campus', 'all_campuses')
        category = request.args.get('category', 'all')
        status = request.args.get('status', 'all')
        upcoming = request.args.get('upcoming', 'true')
        cancelled = request.args.get('cancelled', 'false')
        search = request.args.get('search', '')
        public_only = request.args.get('public_only', 'false')
        
        # Build query
        query = Event.query.filter_by(is_active=True)
        
        # Filter by public_only parameter
        if public_only == 'true':
            query = query.filter_by(is_public=True)
        
        # Filter by campus
        if campus != 'all_campuses':
            query = query.filter(Event.campus.in_(['all_campuses', campus]))
        
        # Filter by category
        if category != 'all':
            query = query.join(EventCategory).filter(EventCategory.key == category)
        
        # Filter by status
        if status == 'upcoming':
            query = query.filter(Event.start_datetime > datetime.now())
        elif status == 'past':
            query = query.filter(Event.start_datetime < datetime.now())
        elif status == 'cancelled':
            query = query.filter_by(is_cancelled=True)
        
        # Filter by upcoming/past
        if upcoming == 'true':
            query = query.filter(Event.start_datetime > datetime.now())
        elif upcoming == 'false':
            query = query.filter(Event.start_datetime < datetime.now())
        
        # Filter by cancelled
        if cancelled == 'true':
            query = query.filter_by(is_cancelled=True)
        elif cancelled == 'false':
            query = query.filter_by(is_cancelled=False)
        
        # Search by title or description
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Event.title.ilike(search_term),
                    Event.description.ilike(search_term)
                )
            )
        
        # Order by start date
        query = query.order_by(Event.start_datetime.asc())
        
        events = query.all()
        
        # Convert to JSON
        events_data = []
        for event in events:
            # Get category info
            category_info = None
            if event.category:
                category_info = {
                    'key': event.category.key,
                    'name': event.category.name,
                    'color': event.category.color
                }
            
            # Calculate registration count (placeholder for now)
            registration_count = 0  # TODO: Implement actual registration counting
            
            events_data.append({
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'short_description': event.short_description,
                'category': category_info,
                'campus': event.campus,
                'location': event.location,
                'virtual_link': event.virtual_link,
                'start_datetime': event.start_datetime.isoformat() if event.start_datetime else None,
                'end_datetime': event.end_datetime.isoformat() if event.end_datetime else None,
                'is_all_day': event.is_all_day,
                'registration_required': event.registration_required,
                'registration_opens': event.registration_opens.isoformat() if event.registration_opens else None,
                'registration_closes': event.registration_closes.isoformat() if event.registration_closes else None,
                'max_capacity': event.max_capacity,
                'allow_waitlist': event.allow_waitlist,
                'is_public': event.is_public,
                'requires_approval': event.requires_approval,
                'minimum_age': event.minimum_age,
                'maximum_age': event.maximum_age,
                'required_departments': event.required_departments,
                'image_url': event.image_url,
                'additional_info': event.additional_info,
                'contact_person': event.contact_person,
                'contact_email': event.contact_email,
                'contact_phone': event.contact_phone,
                'registration_count': registration_count,
                'can_register': event.registration_required and not event.is_cancelled,
                'is_cancelled': event.is_cancelled,
                'created_at': event.created_at.isoformat(),
                'updated_at': event.updated_at.isoformat()
            })
        
        return jsonify({'events': events_data})
        
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return jsonify({'error': 'Failed to fetch events'}), 500

@app.route('/api/admin/resource-categories', methods=['GET'])
@admin_required_json
def get_admin_resource_categories():
    """Get all resource categories (admin only)"""
    try:
        
        # Try to get categories from database, but handle case where table doesn't exist yet
        try:
            categories = ResourceCategory.query.filter_by(is_active=True).order_by(ResourceCategory.sort_order.asc(), ResourceCategory.display_name.asc()).all()
            categories_data = [category.to_dict() for category in categories]
        except Exception as db_error:
            # Table might not exist yet - create it
            logger.warning(f"ResourceCategory table might not exist: {db_error}")
            try:
                db.create_all()
                categories_data = []
            except Exception as create_error:
                logger.error(f"Failed to create ResourceCategory table: {create_error}")
                categories_data = []
        
        return jsonify({'categories': categories_data})
    except Exception as e:
        logger.error(f"Error fetching resource categories: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch resource categories'}), 500

@app.route('/api/admin/resource-categories', methods=['POST'])
@admin_required_json
def create_resource_category():
    """Create a new resource category (admin only)"""
    try:
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('displayName'):
            return jsonify({'error': 'Display name is required'}), 400
        
        if not data.get('slug'):
            return jsonify({'error': 'Slug is required'}), 400
        
        # Ensure table exists
        try:
            db.create_all()
        except Exception as create_error:
            logger.warning(f"Table creation check: {create_error}")
        
        # Check if slug already exists
        existing = ResourceCategory.query.filter_by(slug=data['slug']).first()
        if existing:
            return jsonify({'error': 'A category with this slug already exists'}), 400
        
        # Create new category
        category = ResourceCategory(
            display_name=data['displayName'],
            slug=data['slug'],
            description=data.get('description', ''),
            folder_id=data.get('folderId', ''),
            sort_order=data.get('sortOrder', 0),
            links=json.dumps(data.get('links', [])),
            is_active=True
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'message': 'Resource category created successfully',
            'category': category.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating resource category: {e}")
        return jsonify({'error': f'Failed to create resource category: {str(e)}'}), 500

@app.route('/api/admin/resource-categories/<category_id>', methods=['PUT'])
@admin_required_json
def update_resource_category(category_id):
    """Update a resource category (admin only)"""
    try:
        
        data = request.get_json()
        
        # Find category by slug or ID
        category = ResourceCategory.query.filter(
            (ResourceCategory.slug == category_id) | (ResourceCategory.id == category_id)
        ).first()
        
        if not category:
            return jsonify({'error': 'Resource category not found'}), 404
        
        # Update fields
        if 'displayName' in data:
            category.display_name = data['displayName']
        if 'slug' in data:
            # Check if new slug conflicts with another category
            existing = ResourceCategory.query.filter_by(slug=data['slug']).first()
            if existing and existing.id != category.id:
                return jsonify({'error': 'A category with this slug already exists'}), 400
            category.slug = data['slug']
        if 'description' in data:
            category.description = data.get('description', '')
        if 'folderId' in data:
            category.folder_id = data.get('folderId', '')
        if 'sortOrder' in data:
            category.sort_order = data.get('sortOrder', 0)
        if 'links' in data:
            category.links = json.dumps(data.get('links', []))
        
        category.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Resource category updated successfully',
            'category': category.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating resource category: {e}")
        return jsonify({'error': f'Failed to update resource category: {str(e)}'}), 500

@app.route('/api/resources/categories', methods=['GET'])
@admin_required_json
def get_resource_categories():
    """Get all resource categories"""
    try:
        
        # Try to get categories from database, but handle case where table doesn't exist yet
        try:
            categories = ResourceCategory.query.filter_by(is_active=True).order_by(ResourceCategory.sort_order.asc(), ResourceCategory.display_name.asc()).all()
            categories_data = [category.to_dict() for category in categories]
        except Exception as db_error:
            # Table might not exist yet - create it
            logger.warning(f"ResourceCategory table might not exist: {db_error}")
            try:
                db.create_all()
                categories_data = []
            except Exception as create_error:
                logger.error(f"Failed to create ResourceCategory table: {create_error}")
                categories_data = []
        
        return jsonify({'categories': categories_data})
    except Exception as e:
        logger.error(f"Error fetching resource categories: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch resource categories'}), 500

@app.route('/api/google/auth-url', methods=['GET'])
@admin_required_json
def get_google_auth_url():
    """Get Google Drive OAuth URL"""
    try:
        
        # Check if OAuth credentials are configured
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        redirect_uri = os.getenv('GOOGLE_OAUTH_REDIRECT_URI')
        
        if not client_id or not client_secret:
            return jsonify({
                'error': 'Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.',
                'auth_url': None
            }), 503
        
        # Use request origin for redirect URI if not set
        if not redirect_uri:
            # Get the origin from the request
            origin = request.headers.get('Origin') or request.host_url.rstrip('/')
            redirect_uri = f"{origin}/api/google/callback"
        
        # Generate state token for security
        import secrets
        state_token = secrets.token_urlsafe(32)
        session['google_oauth_state'] = state_token
        session['google_oauth_user_id'] = current_user.id
        
        # Google OAuth scopes for Drive
        scopes = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.file'
        ]
        scope_string = ' '.join(scopes)
        
        # Build OAuth URL
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope_string}&"
            f"state={state_token}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        
        return jsonify({
            'auth_url': auth_url,
            'state': state_token
        })
    except Exception as e:
        logger.error(f"Error getting Google auth URL: {e}", exc_info=True)
        return jsonify({'error': f'Failed to get Google auth URL: {str(e)}'}), 500

@app.route('/api/google/callback', methods=['GET'])
def google_oauth_callback():
    """Handle Google OAuth callback"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return jsonify({'error': f'OAuth error: {error}'}), 400
        
        if not code:
            return jsonify({'error': 'Missing authorization code'}), 400
        
        # Verify state token
        expected_state = session.get('google_oauth_state')
        if not expected_state or state != expected_state:
            return jsonify({'error': 'Invalid state token'}), 400
        
        user_id = session.get('google_oauth_user_id')
        if not user_id:
            return jsonify({'error': 'Session expired'}), 401
        
        # Exchange code for tokens
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        redirect_uri = os.getenv('GOOGLE_OAUTH_REDIRECT_URI')
        
        if not redirect_uri:
            origin = request.headers.get('Origin') or request.host_url.rstrip('/')
            redirect_uri = f"{origin}/api/google/callback"
        
        # Exchange authorization code for tokens
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(token_url, data=token_data)
        
        if not token_response.ok:
            logger.error(f"Token exchange failed: {token_response.text}")
            return jsonify({'error': 'Failed to exchange authorization code'}), 500
        
        tokens = token_response.json()
        
        # Store tokens in session
        session['google_drive_access_token'] = tokens.get('access_token')
        session['google_drive_refresh_token'] = tokens.get('refresh_token')
        session['google_drive_token_expiry'] = datetime.now(timezone.utc).timestamp() + tokens.get('expires_in', 3600)
        session['google_drive_authenticated'] = True
        
        # Clear OAuth state
        session.pop('google_oauth_state', None)
        session.pop('google_oauth_user_id', None)
        
        # Return success page that handles both popup and redirect scenarios
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Google Drive Connected</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    padding: 20px;
                }
                .container {
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 400px;
                }
                h1 { margin-top: 0; }
                .checkmark {
                    font-size: 64px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="checkmark">✓</div>
                <h1>Google Drive Connected!</h1>
                <p>You can close this window or return to the app.</p>
            </div>
            <script>
                // Immediately try to notify parent/opener
                try {
                    if (window.opener) {
                        // Desktop popup scenario
                        window.opener.postMessage({ type: 'googleAuthSuccess' }, '*');
                        setTimeout(() => window.close(), 500);
                    } else if (window.parent && window.parent !== window) {
                        // Iframe scenario
                        window.parent.postMessage({ type: 'googleAuthSuccess' }, '*');
                    }
                } catch (e) {
                    console.log('Could not post message:', e);
                }
                
                // For mobile redirects, always redirect back to app immediately
                // This ensures we get back to the app even if postMessage fails
                if (!window.opener) {
                    // Store success in sessionStorage for the app to detect
                    try {
                        sessionStorage.setItem('google_oauth_success', 'true');
                    } catch (e) {
                        console.log('Could not set sessionStorage:', e);
                    }
                    
                    // Redirect immediately
                    window.location.href = '/';
                }
            </script>
        </body>
        </html>
        '''
    except Exception as e:
        logger.error(f"Error in Google OAuth callback: {e}", exc_info=True)
        return jsonify({'error': f'OAuth callback failed: {str(e)}'}), 500

@app.route('/api/resources/<category_id>', methods=['GET'])
@admin_required_json
def get_resource_category_files(category_id):
    """Get files for a specific resource category"""
    try:
        
        # Get category to retrieve links
        category = ResourceCategory.query.filter(
            (ResourceCategory.slug == category_id) | (ResourceCategory.id == category_id)
        ).filter_by(is_active=True).first()
        
        if category:
            links = json.loads(category.links) if category.links else []
            # For now, return links from category - Google Drive files not yet implemented
            return jsonify({
                'files': [],  # Google Drive files not yet implemented
                'links': links
            })
        else:
            return jsonify({'files': [], 'links': []})
    except Exception as e:
        logger.error(f"Error fetching resource category files: {e}")
        return jsonify({'error': 'Failed to fetch resource files'}), 500

@app.route('/api/events/categories', methods=['GET'])
def get_event_categories():
    """Get all event categories"""
    try:
        categories = EventCategory.query.filter_by(is_active=True).order_by(EventCategory.display_order.asc()).all()
        categories_data = [category.to_dict() for category in categories]
        return jsonify({'categories': categories_data})
    except Exception as e:
        logger.error(f"Error fetching event categories: {e}")
        return jsonify({'error': 'Failed to fetch event categories'}), 500

@app.route('/api/events', methods=['POST'])
@admin_required
def create_event():
    """Create a new event (admin only)"""
    try:
        data = request.get_json()
        required_fields = ['title', 'category_id', 'start_datetime']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse datetime
        start_datetime = datetime.fromisoformat(data['start_datetime'].replace('Z', '+00:00'))
        end_datetime = None
        if data.get('end_datetime'):
            end_datetime = datetime.fromisoformat(data['end_datetime'].replace('Z', '+00:00'))
        
        registration_opens = None
        if data.get('registration_opens'):
            registration_opens = datetime.fromisoformat(data['registration_opens'].replace('Z', '+00:00'))
        
        registration_closes = None
        if data.get('registration_closes'):
            registration_closes = datetime.fromisoformat(data['registration_closes'].replace('Z', '+00:00'))
        
        new_event = Event(
            title=data['title'],
            description=data.get('description'),
            short_description=data.get('short_description'),
            category_id=data['category_id'],
            campus=data.get('campus', 'all_campuses'),
            location=data.get('location'),
            virtual_link=data.get('virtual_link'),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            is_all_day=data.get('is_all_day', False),
            registration_required=data.get('registration_required', True),
            registration_opens=registration_opens,
            registration_closes=registration_closes,
            max_capacity=data.get('max_capacity'),
            allow_waitlist=data.get('allow_waitlist', True),
            is_public=data.get('is_public', True),
            requires_approval=data.get('requires_approval', False),
            minimum_age=data.get('minimum_age'),
            maximum_age=data.get('maximum_age'),
            required_departments=data.get('required_departments'),
            image_url=data.get('image_url'),
            additional_info=data.get('additional_info'),
            contact_person=data.get('contact_person'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone')
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        return jsonify({
            'message': 'Event created successfully',
            'event': {
                'id': new_event.id,
                'title': new_event.title
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return jsonify({'error': 'Failed to create event'}), 500

@app.route('/api/events/<event_id>', methods=['PUT'])
@admin_required
def update_event(event_id):
    """Update an existing event (admin only)"""
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'short_description' in data:
            event.short_description = data['short_description']
        if 'category_id' in data:
            event.category_id = data['category_id']
        if 'campus' in data:
            event.campus = data['campus']
        if 'location' in data:
            event.location = data['location']
        if 'virtual_link' in data:
            event.virtual_link = data['virtual_link']
        if 'start_datetime' in data:
            event.start_datetime = datetime.fromisoformat(data['start_datetime'].replace('Z', '+00:00'))
        if 'end_datetime' in data:
            if data['end_datetime']:
                event.end_datetime = datetime.fromisoformat(data['end_datetime'].replace('Z', '+00:00'))
            else:
                event.end_datetime = None
        if 'is_all_day' in data:
            event.is_all_day = data['is_all_day']
        if 'registration_required' in data:
            event.registration_required = data['registration_required']
        if 'registration_opens' in data:
            if data['registration_opens']:
                event.registration_opens = datetime.fromisoformat(data['registration_opens'].replace('Z', '+00:00'))
            else:
                event.registration_opens = None
        if 'registration_closes' in data:
            if data['registration_closes']:
                event.registration_closes = datetime.fromisoformat(data['registration_closes'].replace('Z', '+00:00'))
            else:
                event.registration_closes = None
        if 'max_capacity' in data:
            event.max_capacity = data['max_capacity']
        if 'allow_waitlist' in data:
            event.allow_waitlist = data['allow_waitlist']
        if 'is_public' in data:
            event.is_public = data['is_public']
        if 'requires_approval' in data:
            event.requires_approval = data['requires_approval']
        if 'minimum_age' in data:
            event.minimum_age = data['minimum_age']
        if 'maximum_age' in data:
            event.maximum_age = data['maximum_age']
        if 'required_departments' in data:
            event.required_departments = data['required_departments']
        if 'image_url' in data:
            event.image_url = data['image_url']
        if 'additional_info' in data:
            event.additional_info = data['additional_info']
        if 'contact_person' in data:
            event.contact_person = data['contact_person']
        if 'contact_email' in data:
            event.contact_email = data['contact_email']
        if 'contact_phone' in data:
            event.contact_phone = data['contact_phone']
        if 'is_cancelled' in data:
            event.is_cancelled = data['is_cancelled']
        
        event.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Event updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        return jsonify({'error': 'Failed to update event'}), 500

@app.route('/api/events/<event_id>', methods=['DELETE'])
@admin_required
def delete_event(event_id):
    """Delete an event (admin only)"""
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Soft delete - mark as inactive
        event.is_active = False
        event.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Event deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        return jsonify({'error': 'Failed to delete event'}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5002))
    print("Starting app.py")
    print(f"App running on: http://0.0.0.0:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)