# 🤝 Serving/Volunteer Management Block

Complete serving and volunteer management system for churches. Manage teams, schedules, requests, and serving history.

## Features

✅ **Team Management** - Create and manage serving teams  
✅ **Role Management** - Define roles within teams  
✅ **Schedule Creation** - Create and assign serving schedules  
✅ **Request System** - Sign-up, time-off, and swap requests  
✅ **Availability Settings** - Set member availability preferences  
✅ **Serving History** - Track completed servings  
✅ **People Assignment** - Assign people to roles and schedules  
✅ **Template Management** - Reusable service planning templates  

## Quick Start

See [INTEGRATION.md](./INTEGRATION.md) for detailed integration instructions.

## Files Included

```
serving/
├── INTEGRATION.md
├── README.md
├── backend/
│   ├── serving_api.py       # Flask Blueprint with all API routes
│   ├── serving_models.py    # SQLAlchemy models
│   └── requirements.txt
├── frontend/
│   ├── components/          # 13 React components
│   │   ├── ServingManagement.jsx
│   │   ├── ServingTeams.jsx
│   │   ├── ServingSchedule.jsx
│   │   ├── ServingRequests.jsx
│   │   ├── ServingHistory.jsx
│   │   ├── TeamManagement.jsx
│   │   ├── ServicePlanning.jsx
│   │   ├── PlanManagement.jsx
│   │   ├── TemplateManagement.jsx
│   │   ├── AvailabilityForm.jsx
│   │   ├── PeopleAssignmentModal.jsx
│   │   └── ...
│   └── pages/
│       └── ServingDashboard.jsx
├── migrations/
│   └── 004_serving_module.sql
└── docs/
    └── API.md
```

## Dependencies

### Backend
- Flask (with Blueprint support)
- Flask-Login
- SQLAlchemy
- Flask-SQLAlchemy

### Frontend
- React
- Tailwind CSS (recommended)
- Heroicons (for icons)

## API Endpoints

- `GET /api/serving/teams` - List serving teams
- `POST /api/serving/teams` - Create team
- `GET /api/serving/roles` - List roles
- `POST /api/serving/roles` - Create role
- `GET /api/serving/schedules` - Get schedules
- `POST /api/serving/schedules` - Create schedule
- `GET /api/serving/requests` - List requests
- `POST /api/serving/requests` - Create request
- And many more...

See [docs/API.md](./docs/API.md) for complete API documentation.


