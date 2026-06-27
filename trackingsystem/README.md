# Land Dispute Case Management System

A professional web-based system for managing land dispute cases with GIS mapping integration, user authentication, and real-time case tracking.

## 🎯 Features Implemented

### ✅ Authentication System
- **Professional Login Page** - Beautiful gradient background with form validation
- **User Roles** - Admin and case officers with different permissions
- **Secure Sessions** - Django session-based authentication with logout functionality
- **Demo Credentials**:
  - Username: `admin`
  - Password: `admin`

### ✅ Case Management Dashboard
- **Responsive Grid Layout** - Cards display 8 test land dispute cases
- **Status Filtering** - Filter cases by: All, Pending, In Progress, Resolved, Escalated
- **Case Statistics** - Quick overview of case counts by status
- **Quick Actions** - View details and assign cases to yourself
- **User Welcome** - Personalized greeting with user information

### ✅ Case Detail Page
- **Complete Case Information**:
  - Citizen details (name, phone)
  - Location and GPS coordinates
  - Case description and timeline
  - Assignment status
  - Case notes section
- **Status Management** - Update case status through dropdown
- **Notes Addition** - Add internal notes for case tracking
- **Assignment System** - Assign unassigned cases to yourself
- **Map Integration** - Quick link to view case location on map

### ✅ GIS Mapping System
- **Interactive Map** - Built with Leaflet.js and OpenStreetMap
- **Case Markers** - Color-coded by status:
  - 🟠 Orange: Pending
  - 🔵 Blue: In Progress
  - 🟢 Green: Resolved
  - 🔴 Red: Escalated
- **Case Information Popup** - Click markers to view case details
- **Location Legend** - Visual guide to marker meanings
- **Zoom Controls** - Navigation and zoom functionality

### ✅ Professional UI/UX
- **Dark Sidebar Navigation** - Clean, modern design
- **Color-Coded Status Badges** - Quick visual identification
- **Responsive Layout** - Works on desktop and tablet
- **Font Awesome Icons** - Professional iconography
- **Hover Effects** - Interactive feedback for all elements
- **Consistent Styling** - Unified color scheme and typography

### ✅ Database Models
```python
Case Model:
- title (CharField)
- citizen_name (CharField)
- citizen_phone (CharField)
- description (TextField)
- location (CharField)
- latitude (FloatField) - GIS coordinate
- longitude (FloatField) - GIS coordinate
- status (CharField: pending, in_progress, escalated, resolved)
- assigned_to (ForeignKey to User)
- created_at (DateTimeField)
- updated_at (DateTimeField)
- notes (TextField)
```

## 🚀 Getting Started

### Running the Server
```bash
cd c:\Users\eliot\OneDrive\Desktop\cases\trackingsystem
python manage.py runserver
```

Server runs at: **http://127.0.0.1:8000/**

### Admin Panel
Access Django admin at: **http://127.0.0.1:8000/admin/**
- Username: `admin`
- Password: `admin`

## 📊 Test Data

The system comes pre-populated with 8 realistic test cases from various Tanzania regions:
1. **Land Boundary Dispute** - Mbeya Region (Pending)
2. **Farm Land Conflict** - Mwanza (In Progress)
3. **Inheritance Land Dispute** - Arusha (Resolved)
4. **Boundary Encroachment** - Dar es Salaam (Escalated)
5. **Land Lease Dispute** - Dodoma (In Progress)
6. **Communal Land Rights** - Kagera (Pending)
7. **Document Fraud Case** - Iringa (Escalated)
8. **Urban Plot Conflict** - Tanga (Resolved)

### Demo Users
- **admin** - Administrator (password: admin)
- **officer1** (John Smith) - Case Officer
- **officer2** (Jane Doe) - Case Officer
- **officer3** (Robert Johnson) - Case Officer

## 🔗 Application URLs

| Page | URL | Purpose |
|------|-----|---------|
| Login | `/login/` | User authentication |
| Dashboard | `/` | Main case list view |
| Case Details | `/case/<id>/` | Individual case information |
| Case Map | `/map/` | GIS map of all cases |
| Logout | `/logout/` | User logout |
| Admin | `/admin/` | Django admin panel |

## 🛠️ Technologies Used

- **Backend**: Django 6.0.5
- **Frontend**: HTML5, CSS3, JavaScript
- **Mapping**: Leaflet.js + OpenStreetMap
- **Database**: SQLite3
- **Authentication**: Django built-in auth
- **Icons**: Font Awesome 6.0.0
- **UI Framework**: Custom CSS

## 📁 Project Structure

```
trackingsystem/
├── manage.py
├── db.sqlite3
├── trackingsystem/          # Main project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── landsystem/              # Main app
    ├── models.py            # Case model
    ├── views.py             # All views
    ├── urls.py              # URL routing
    ├── admin.py             # Admin configuration
    ├── migrations/          # Database migrations
    ├── management/commands/ # Custom management commands
    ├── templates/           # HTML templates
    │   ├── login.html
    │   ├── dashboard.html
    │   ├── case_detail.html
    │   └── case_map.html
    └── static/              # Static files
        ├── css/
        │   ├── dashboard.css
        │   ├── case.css
        │   └── submitcase.css
        └── js/
            └── app.js
```

## 🎨 Design Highlights

### Color Scheme
- **Primary**: #3498db (Blue) - Actions, active states
- **Secondary**: #2c3e50 (Dark Blue) - Sidebar, headers
- **Success**: #27ae60 (Green) - Positive actions
- **Warning**: #f39c12 (Orange) - Pending status
- **Danger**: #e74c3c (Red) - Escalated/alerts

### Responsive Elements
- Fixed sidebar navigation (250px)
- Flexible main content area
- Grid-based case card layout
- Mobile-friendly form inputs

## 🔐 Security Features

- User authentication required for all pages (except login)
- CSRF token protection on all forms
- Secure password handling
- Django security middleware enabled
- Admin panel access restricted

## 📈 Future Enhancements

- [ ] Advanced search and filtering
- [ ] Case history and activity logs
- [ ] File attachments for cases
- [ ] Export to PDF/Excel reports
- [ ] Email notifications
- [ ] Mobile app
- [ ] Real-time case updates with WebSockets
- [ ] Document upload integration
- [ ] GPS tracking for field officers
- [ ] Advanced analytics dashboard

## 🤝 How to Use

### For Case Officers:

1. **Login**: Access the system with your credentials
2. **View Dashboard**: See all active cases
3. **Filter Cases**: Find cases by status
4. **Assign Cases**: Click "Assign to Me" for unassigned cases
5. **View Details**: Click case title to see full information
6. **Update Status**: Change case status as it progresses
7. **Add Notes**: Document your actions and findings
8. **Check Map**: View case locations on the interactive map

### For Admin:

- Access Django admin panel
- Manage users and permissions
- Add new cases to the system
- Review all system activity
- Configure system settings

## ✨ Successfully Completed!

Your Land Dispute Management System is now fully operational with:
- ✅ Professional login system
- ✅ Beautiful responsive dashboard
- ✅ Full case management capabilities
- ✅ GIS mapping integration
- ✅ User authentication and authorization
- ✅ 8 realistic test cases
- ✅ Multiple demo accounts
- ✅ Admin panel access

The system is ready for production deployment or further customization!
