# Heartbeat Module - Development Roadmap

## ✅ Completed
- [x] Backend models (12 tables)
- [x] HeartbeatEngine calculation service
- [x] REST API endpoints
- [x] Frontend dashboard (list view)
- [x] Navigation integration
- [x] Seed script for initial data

## 🚧 Next Priority Features

### 1. Individual Person Detail View
**Status:** API exists, needs frontend enhancement
- [ ] Update PersonHealthReport.jsx to use new Heartbeat API
- [ ] Show detailed score breakdowns
- [ ] Display recent activity (attendance, serving, etc.)
- [ ] Show historical snapshots/charts
- [ ] Risk factors explanation

### 2. Data Integration
**Status:** Need to connect existing systems
- [ ] Auto-create AttendanceEvents from existing attendance tracking
- [ ] Connect to Connect Groups system
- [ ] Link to Serving/Teams system
- [ ] Integrate with Giving system
- [ ] Pull from existing Person data

### 3. Enhanced Dashboard Features
**Status:** Basic version done
- [ ] Export to CSV/Excel
- [ ] Bulk actions (recalculate multiple campuses)
- [ ] Advanced filters (date range, score thresholds)
- [ ] Sortable columns
- [ ] Pagination for large lists

### 4. Notifications & Alerts
**Status:** Not started
- [ ] Email alerts when person moves to "at_risk" or "critical"
- [ ] Dashboard notifications
- [ ] Weekly summary reports
- [ ] Custom alert rules

### 5. Historical Trends
**Status:** Data model supports it
- [ ] Trend charts (score over time)
- [ ] Compare periods
- [ ] Identify improvements/declines
- [ ] Historical snapshot viewer

### 6. Reporting
**Status:** Not started
- [ ] Campus health reports
- [ ] Department breakdowns
- [ ] Engagement trends
- [ ] Care case summaries

## 🎯 Quick Wins (Do First)

1. **Update PersonHealthReport** - Use new Heartbeat API
2. **Add Export Button** - CSV export of people list
3. **Better Empty States** - Helpful messages when no data
4. **Loading States** - Better UX during recalculation

## 🔮 Future Enhancements

- Mobile app integration
- Push notifications
- AI-powered insights
- Predictive analytics
- Automated care recommendations
- Integration with church management systems

