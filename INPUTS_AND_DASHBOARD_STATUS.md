# All Inputs and Dashboard Status

This document lists all available input fields in the Stats Input form and indicates which ones are currently displayed on the Campus Dashboard.

## 📊 Input Fields List

### Campus Information
| Input Field | Backend Field Name | Shown on Dashboard? | Dashboard Location |
|------------|-------------------|---------------------|-------------------|
| Total People in Campus | `Total People in Campus` | ✅ Yes | Campus Overview card (as `total_people`) |

### Service Attendance (Adults)
| Input Field | Backend Field Name | Shown on Dashboard? | Dashboard Location |
|------------|-------------------|---------------------|-------------------|
| 9:00 AM | `9:00 AM` | ✅ Yes | Sunday Attendance modal (service breakdown) |
| 10:00 AM | `10:00 AM` | ✅ Yes | Sunday Attendance modal (service breakdown) |
| 11:00 AM | `11:00 AM` | ✅ Yes | Sunday Attendance modal (service breakdown) |
| 5:00 PM | `5:00 PM` | ✅ Yes | Sunday Attendance modal (service breakdown) |
| 5:30 PM | `5:30 PM` | ✅ Yes | Sunday Attendance modal (service breakdown) |

### Kids Ministry
| Input Field | Backend Field Name | Shown on Dashboard? | Dashboard Location |
|------------|-------------------|---------------------|-------------------|
| Kids 9:00 AM | `Kids 9:00 AM` | ✅ Yes | Kids modal (service breakdown) |
| Kids 10:00 AM | `Kids 10:00 AM` | ✅ Yes | Kids modal (service breakdown) |
| Kids 11:00 AM | `Kids 11:00 AM` | ✅ Yes | Kids modal (service breakdown) |
| Kids 5:00 PM | `Kids 5:00 PM` | ✅ Yes | Kids modal (service breakdown) |
| Kids 5:30 PM | `Kids 5:30 PM` | ✅ Yes | Kids modal (service breakdown) |
| Kids Leaders | `Kids Leaders` | ✅ Yes | Kids card & modal (as `avg_kids_leaders`) |
| New Kids | `New Kids` | ✅ Yes | Kids modal (as `new_kids`) |
| Kids Salvations | `New Kids Salvations` | ✅ Yes | Souls card & modal (as `new_kids_salvations`) |

### New People Section
| Input Field | Backend Field Name | Shown on Dashboard? | Dashboard Location |
|------------|-------------------|---------------------|-------------------|
| Packs Out | `Packs Out` | ❌ No | Not displayed |
| Cards Returned | `Cards Back` | ❌ No | Not displayed |
| First Time | `First Time Visitors` | ✅ Yes | New People card & modal (as `first_time_visitors`) |
| Visitors | `Visitors` | ✅ Yes | New People card & modal (as `visitors`) |
| **Hands up** | `Hands up` | ❌ No | **Not yet displayed** |

### Salvations Section
| Input Field | Backend Field Name | Shown on Dashboard? | Dashboard Location |
|------------|-------------------|---------------------|-------------------|
| First Time Decision | `First Time Christians` | ✅ Yes | Souls card & modal (as `first_time_christians`) |
| Rededication | `Rededications` | ✅ Yes | Souls modal (as `rededications`) |
| Salvation Cards Returned | `Salvation Cards Returned` | ✅ Yes | Souls modal (as `salvation_cards_returned`) |

### Youth Ministry (Friday)
| Input Field | Backend Field Name | Shown on Dashboard? | Dashboard Location |
|------------|-------------------|---------------------|-------------------|
| Youth Total | `Youth Attendance` | ✅ Yes | Youth card & modal (as `avg_youth_attendance`) |
| Youth NP | `Youth New People` | ✅ Yes | Youth modal (as `youth_new_people`) |
| Youth Salvations | `Youth Salvations` | ✅ Yes | Souls card & modal (as `youth_salvations`) |
| Youth Leaders | `Youth Leaders` | ✅ Yes | Youth modal (as `youth_leaders`) |

### Connect Groups & Ministry
| Input Field | Backend Field Name | Shown on Dashboard? | Dashboard Location |
|------------|-------------------|---------------------|-------------------|
| Saints | `Saints` | ✅ Yes | Sunday Attendance calculation (as `avg_saints`) |
| Connect Groups | `Connect Groups` | ✅ Yes | Connect Groups card & modal (as `avg_connect_groups`) |
| Dream Team | `Dream Team` | ✅ Yes | Campus Overview modal (as `avg_dream_team`) |
| Seniors | `Seniors` | ❌ No | Not displayed |

### Special Events
| Input Field | Backend Field Name | Shown on Dashboard? | Dashboard Location |
|------------|-------------------|---------------------|-------------------|
| Baptisms | `Baptisms` | ✅ Yes | Campus Overview modal (as `baptisms`) |
| Child Dedications | `Child Dedications` | ✅ Yes | Campus Overview modal (as `child_dedications`) |

### Finance (Not in Stats Input Form)
| Input Field | Backend Field Name | Shown on Dashboard? | Dashboard Location |
|------------|-------------------|---------------------|-------------------|
| Tithe | `Tithe` | ✅ Yes | Tithe card & modal (as `tithe` and `avg_tithe`) |

---

## Summary

### ✅ Shown on Dashboard (30 fields)
1. Total People in Campus
2. 9:00 AM
3. 10:00 AM
4. 11:00 AM
5. 5:00 PM
6. 5:30 PM
7. Kids 9:00 AM
8. Kids 10:00 AM
9. Kids 11:00 AM
10. Kids 5:00 PM
11. Kids 5:30 PM
12. Kids Leaders
13. New Kids
14. Kids Salvations
15. First Time
16. Visitors
17. First Time Decision
18. Rededication
19. Salvation Cards Returned
20. Youth Total
21. Youth NP
22. Youth Salvations
23. Youth Leaders
24. Saints
25. Connect Groups
26. Dream Team
27. Baptisms
28. Child Dedications
29. Tithe (separate input system)
30. Total Attendance (calculated from service times)

### ❌ NOT Shown on Dashboard (4 fields)
1. **Packs Out** - Not displayed anywhere
2. **Cards Returned** - Not displayed anywhere
3. **Hands up** - Just added, not yet displayed
4. **Seniors** - Not displayed anywhere

---

## Notes

- **Service Times**: Individual service times are shown in breakdown modals, but the main cards show aggregated totals/averages
- **Calculated Fields**: Some fields like "Total Attendance" are calculated from service times and shown on the dashboard
- **Averages vs Totals**: 
  - Attendance metrics show **averages per service**
  - New People and Salvations show **totals** for the selected period
- **Hands up**: This field was just added to the input form but is not yet integrated into the dashboard display logic

---

## Recommendations

1. **Hands up**: Consider adding this to the "New People" section of the dashboard
2. **Packs Out**: May be useful for tracking visitor engagement materials
3. **Cards Returned**: Could be displayed in the "New People" modal as "Info Gathered" or similar
4. **Seniors**: Could be added to a ministry breakdown section if needed

