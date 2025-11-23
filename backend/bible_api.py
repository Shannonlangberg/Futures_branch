"""
Bible API Integration
Supports multiple Bible versions through various APIs
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
import requests
import re
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

bible_bp = Blueprint('bible', __name__, url_prefix='/api/bible')

# Bible version mappings
BIBLE_VERSIONS = {
    'NIV': {'name': 'New International Version', 'abbrev': 'NIV'},
    'ESV': {'name': 'English Standard Version', 'abbrev': 'ESV'},
    'KJV': {'name': 'King James Version', 'abbrev': 'KJV'},
    'NKJV': {'name': 'New King James Version', 'abbrev': 'NKJV'},
    'NLT': {'name': 'New Living Translation', 'abbrev': 'NLT'},
    'CSB': {'name': 'Christian Standard Bible', 'abbrev': 'CSB'},
    'NASB': {'name': 'New American Standard Bible', 'abbrev': 'NASB'},
    'MSG': {'name': 'The Message', 'abbrev': 'MSG'},
    'AMP': {'name': 'Amplified Bible', 'abbrev': 'AMP'},
    'RSV': {'name': 'Revised Standard Version', 'abbrev': 'RSV'}
}

def parse_scripture_reference(ref: str) -> Optional[Dict[str, Any]]:
    """
    Parse scripture reference like "John 3:16" or "Psalm 23:1-3"
    Returns: {book: 'John', chapter: 3, verse_start: 16, verse_end: 16}
    """
    try:
        # Remove common prefixes
        ref = ref.strip()
        ref = re.sub(r'^(?:The\s+)?', '', ref, flags=re.IGNORECASE)
        
        # Match pattern: Book Chapter:Verse(-Verse)
        pattern = r'^([1-3]?\s*[A-Za-z]+)\s+(\d+)(?::(\d+)(?:-(\d+))?)?$'
        match = re.match(pattern, ref)
        
        if not match:
            # Try alternative pattern for Psalms (Ps. 23:1)
            pattern2 = r'^([A-Za-z]+\.?)\s+(\d+)(?::(\d+)(?:-(\d+))?)?$'
            match = re.match(pattern2, ref)
        
        if match:
            book = match.group(1).strip()
            chapter = int(match.group(2))
            verse_start = int(match.group(3)) if match.group(3) else 1
            verse_end = int(match.group(4)) if match.group(4) else verse_start
            
            # Normalize book names
            book = normalize_book_name(book)
            
            return {
                'book': book,
                'chapter': chapter,
                'verse_start': verse_start,
                'verse_end': verse_end,
                'original_ref': ref
            }
        
        return None
    except Exception as e:
        logger.error(f"Error parsing scripture reference '{ref}': {e}")
        return None

def normalize_book_name(book: str) -> str:
    """Normalize book names to standard format"""
    book = book.strip().title()
    
    # Handle abbreviations
    abbrevs = {
        'Ps': 'Psalms', 'Ps.': 'Psalms', 'Psa': 'Psalms',
        '1Co': '1 Corinthians', '2Co': '2 Corinthians',
        '1Th': '1 Thessalonians', '2Th': '2 Thessalonians',
        '1Ti': '1 Timothy', '2Ti': '2 Timothy',
        'Php': 'Philippians', 'Phil': 'Philippians',
        'Col': 'Colossians',
        'Eph': 'Ephesians',
        'Gal': 'Galatians',
        'Rev': 'Revelation',
        'Jn': 'John', 'Jhn': 'John',
        'Mt': 'Matthew', 'Matt': 'Matthew',
        'Mk': 'Mark', 'Mr': 'Mark',
        'Lk': 'Luke', 'Luk': 'Luke',
        'Ac': 'Acts',
        'Ro': 'Romans', 'Rom': 'Romans',
        'Jas': 'James',
        '1Pe': '1 Peter', '2Pe': '2 Peter',
        '1Jn': '1 John', '2Jn': '2 John', '3Jn': '3 John',
        'Jude': 'Jude',
        'Heb': 'Hebrews'
    }
    
    if book in abbrevs:
        return abbrevs[book]
    
    return book

@bible_bp.route('/search', methods=['GET'])
@login_required
def search_scripture():
    """Search for scripture text by reference"""
    try:
        reference = request.args.get('reference', '').strip()
        version = request.args.get('version', 'NIV').upper()
        
        if not reference:
            return jsonify({'error': 'Reference is required'}), 400
        
        if version not in BIBLE_VERSIONS:
            version = 'NIV'
        
        # Parse reference
        parsed = parse_scripture_reference(reference)
        if not parsed:
            return jsonify({
                'success': False,
                'error': 'Could not parse scripture reference. Please use format like "John 3:16" or "Psalm 23:1-3"'
            }), 400
        
        # Try to fetch from Bible Gateway or other APIs
        # For now, we'll use a simple approach with Bible Gateway API
        # Note: Bible Gateway doesn't have a public API, but we can use web scraping
        # In production, consider using api.bible or other licensed APIs
        
        # For MVP, return structured data that can be filled from various sources
        result = {
            'success': True,
            'reference': reference,
            'parsed': parsed,
            'version': version,
            'book': parsed['book'],
            'chapter': parsed['chapter'],
            'verse_start': parsed['verse_start'],
            'verse_end': parsed['verse_end'],
            'text': f"[{reference} - {BIBLE_VERSIONS[version]['name']}] Scripture text will be fetched from Bible API",
            'note': 'Bible API integration in progress. Text will be fetched from licensed Bible API.'
        }
        
        # Try to fetch from API Bible (free tier available)
        try:
            # Using api.bible - requires API key in production
            # For now, return placeholder
            api_key = os.environ.get('BIBLE_API_KEY')
            if api_key:
                # Implement api.bible integration here
                pass
        except Exception as e:
            logger.warning(f"Bible API fetch failed: {e}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error searching scripture: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to search scripture: {str(e)}'
        }), 500

@bible_bp.route('/versions', methods=['GET'])
@login_required
def get_versions():
    """Get list of available Bible versions"""
    return jsonify({
        'versions': [
            {'id': k, 'name': v['name'], 'abbrev': v['abbrev']}
            for k, v in BIBLE_VERSIONS.items()
        ]
    })

@bible_bp.route('/books', methods=['GET'])
@login_required
def get_books():
    """Get list of Bible books"""
    books = [
        'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
        'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
        '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra',
        'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs',
        'Ecclesiastes', 'Song of Songs', 'Isaiah', 'Jeremiah', 'Lamentations',
        'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos',
        'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
        'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
        'Matthew', 'Mark', 'Luke', 'John', 'Acts',
        'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
        'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
        '1 Timothy', '2 Timothy', 'Titus', 'Philemon',
        'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John',
        'Jude', 'Revelation'
    ]
    
    return jsonify({'books': books})

