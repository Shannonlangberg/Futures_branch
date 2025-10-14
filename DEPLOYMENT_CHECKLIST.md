# 🚀 Futures LINK Deployment Checklist

## Pre-Deployment

### Files Verification
- [ ] `backend/app.py` exists and is clean
- [ ] `backend/users.json` exists with default users
- [ ] `backend/requirements.txt` has all dependencies
- [ ] `backend/credentials.json` is ready (NOT committed to git)
- [ ] `frontend/src/` has all essential pages
- [ ] `frontend/package.json` has correct dependencies
- [ ] `railway.json` or `Procfile` exists
- [ ] `.gitignore` excludes sensitive files

### Configuration
- [ ] Environment variables documented
- [ ] Google Sheets API credentials obtained
- [ ] Google Sheet created with correct tabs (Stats, Tithe)
- [ ] Service account has Sheet access
- [ ] Default passwords documented

### Database
- [ ] `011_regions_support.sql` migration exists
- [ ] `migrate_regions.py` script ready
- [ ] Database will initialize on first run

---

## Local Testing

### Backend
- [ ] `cd backend && python app.py` starts without errors
- [ ] Server runs on http://localhost:5002
- [ ] `/api/health` endpoint responds
- [ ] Google Sheets connection works
- [ ] Database created in `instance/`

### Frontend
- [ ] `cd frontend && npm run dev` starts
- [ ] Runs on http://localhost:5173
- [ ] No console errors
- [ ] Can build: `npm run build`
- [ ] Build creates `dist/` folder

### Features
- [ ] Login works (admin / futures2025)
- [ ] Dashboard loads
- [ ] Campus selector shows regions
- [ ] Campus dashboards display data
- [ ] Input page submits stats
- [ ] Finance page works
- [ ] Settings/Campus management functional

### User Roles
- [ ] Admin sees all campuses
- [ ] Finance sees only Finance page
- [ ] Campus pastor (if created) sees only their campus

---

## Railway Deployment

### Setup
- [ ] Railway account created
- [ ] Project created in Railway
- [ ] GitHub repo connected (optional)

### Environment Variables
Add these in Railway:
- [ ] `GOOGLE_CREDENTIALS_PATH`
- [ ] `SHEET_ID`
- [ ] `SECRET_KEY`
- [ ] `FLASK_ENV=production`
- [ ] `PORT=5002`

### Build & Deploy
- [ ] Build command runs successfully
- [ ] Start command runs successfully
- [ ] Health check passes
- [ ] Public URL accessible

### Post-Deployment Verification
- [ ] Login page loads
- [ ] Can authenticate
- [ ] Dashboard displays
- [ ] Data loads from Google Sheets
- [ ] Stats submission works
- [ ] Finance submission works
- [ ] No console errors

---

## Security Checklist

### Credentials
- [ ] `credentials.json` NOT in git
- [ ] `.env` NOT in git
- [ ] `.gitignore` properly configured
- [ ] Service account has minimal permissions (Sheet access only)

### Passwords
- [ ] Default admin password documented
- [ ] Plan to change default passwords
- [ ] Password hashing enabled
- [ ] Session secret key is random and strong

### API
- [ ] CORS configured for production domain
- [ ] Rate limiting considered
- [ ] HTTPS enforced in production

---

## Documentation

### User Documentation
- [ ] README.md created
- [ ] SETUP_GUIDE.md created
- [ ] DEPLOYMENT.md created
- [ ] USER_ACCESS_CONTROL.md exists
- [ ] Login credentials documented

### Technical Documentation
- [ ] API endpoints documented
- [ ] Database schema documented
- [ ] Google Sheets structure documented
- [ ] Environment variables documented

---

## Production URLs

| Environment | URL | Status |
|------------|-----|--------|
| **Production** | `https://your-app.railway.app` | ⏳ Pending |
| **Development** | `http://localhost:5173` | ✅ Working |
| **API** | `http://localhost:5002` | ✅ Working |

---

## Known Issues to Monitor

### Performance
- [ ] Google Sheets API rate limits (60/min)
- [ ] Response times under load
- [ ] Database query optimization

### Features to Add Later
- [ ] Heartbeat
- [ ] Communications
- [ ] Events
- [ ] Prayer Requests
- [ ] Devotions
- [ ] Mobile App integration

---

## Rollback Plan

If deployment fails:

1. **Railway**: Use "Rollback" button in deployments
2. **Database**: Restore from backup
3. **Code**: Git revert to previous version

---

## Support Plan

### Monitoring
- [ ] Railway logs accessible
- [ ] Error tracking setup
- [ ] Uptime monitoring

### Maintenance
- [ ] Backup schedule planned
- [ ] Update schedule planned
- [ ] Support contact documented

---

## Sign-Off

### Development Team
- [ ] Code reviewed
- [ ] Tests passed
- [ ] Documentation complete

### Deployment
- [ ] Backend deployed
- [ ] Frontend deployed
- [ ] Database migrated
- [ ] All features verified

### Go-Live
- [ ] Users notified
- [ ] Login credentials shared
- [ ] Support available
- [ ] Monitoring active

---

**Deployment Date**: _____________  
**Deployed By**: _____________  
**Production URL**: _____________  

---

## Quick Commands

### Local Development
```bash
# Backend
cd backend && python app.py

# Frontend
cd frontend && npm run dev
```

### Production Build
```bash
# Build frontend
cd frontend && npm run build

# Deploy backend
cd backend && python app.py
```

### Troubleshooting
```bash
# Check logs
cat backend/logs/*.log

# Restart backend
killall python && cd backend && python app.py

# Clear cache
rm -rf frontend/node_modules frontend/dist
```

---

**Status**: ⏳ Ready for Deployment  
**Version**: 5.1  
**Clean Build**: ✅ Complete


