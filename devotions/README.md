# 📖 Devotions & Notes Block

A privacy-focused devotion and note-taking system for church members. Features full scripture text, rich notes, and positive-only guidance.

## Features

✅ **Devotion Library** - Assigned, in-progress, completed, and personal plans  
✅ **Full Scripture Text** - Never abridged, complete Bible passages  
✅ **Rich Notes** - Full note-taking with tags and plan integration  
✅ **Privacy-Safe** - Row-level security, private by default  
✅ **Reading Experience** - Adjustable fonts, themes (Dark/Light/Sepia)  
✅ **Sharing** - Time-limited, secure sharing tokens  
✅ **Positive-Only** - No attendance tracking or surveillance language  

## Quick Start

See [INTEGRATION.md](./INTEGRATION.md) for detailed integration instructions.

## Files Included

```
devotions/
├── INTEGRATION.md
├── README.md
├── backend/
│   ├── devotions_api.py        # API endpoints
│   ├── devotions_admin_api.py  # Admin endpoints
│   └── requirements.txt
├── frontend/
│   ├── components/
│   │   ├── ReadingViewer.jsx   # Full-featured reading experience
│   │   ├── NotesIndex.jsx      # Notes management
│   │   └── DevotionFormModal.jsx
│   └── pages/
│       ├── DevotionsAdmin.jsx
│       └── DevotionPlanManager.jsx
├── migrations/
│   └── 001_devotions_module.sql
└── docs/
    └── API.md
```

## Dependencies

### Backend
- Flask
- Flask-Login
- SQLAlchemy

### Frontend
- React
- Tailwind CSS (recommended)

## API Endpoints

- `GET /api/devotions/library` - Get user's devotion library
- `GET /api/devotions/plan/<id>` - Get plan details
- `POST /api/devotions/assign` - Assign plan to user
- `POST /api/devotions/progress` - Update progress
- `POST /api/notes` - Create note
- `GET /api/notes` - List notes
- `POST /api/notes/<id>/share` - Share note

See [docs/API.md](./docs/API.md) for complete API documentation.

## Privacy Features

- ✅ No attendance tracking
- ✅ No streak counting
- ✅ No score systems
- ✅ Row-level security enforced
- ✅ Positive language guard
- ✅ Private by default


