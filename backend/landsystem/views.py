from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, FileResponse, HttpResponseForbidden
from django.db.models import Q, Count
from django.utils import timezone
from .models import Case, Citizen, OfficerProfile, CaseDocument
import json
import math


# Escalation hierarchy, lowest to highest. Matches OfficerProfile.LEVEL_CHOICES
# and Case.LEVEL_CHOICES.
LEVEL_ORDER = ['village', 'ward', 'district_land_officer', 'regional', 'high_court']

# These levels serve a specific place within their region, so registering one
# requires naming it (e.g. "Chamwino" village, "Makole" ward). Regional/High
# Court officers cover the whole region, so no specific place applies.
LEVELS_REQUIRING_JURISDICTION = ['village', 'ward', 'district_land_officer']


# Region coordinates for mapping
REGION_COORDS = {
    'arusha': {'lat': -3.3731, 'lng': 36.6753, 'name': 'Arusha Region'},
    'dar_es_salaam': {'lat': -6.8000, 'lng': 39.2800, 'name': 'Dar es Salaam'},
    'dodoma': {'lat': -6.1856, 'lng': 35.7382, 'name': 'Dodoma Region'},
    'iringa': {'lat': -7.7689, 'lng': 35.6998, 'name': 'Iringa Region'},
    'kagera': {'lat': -1.2921, 'lng': 31.8974, 'name': 'Kagera Region'},
    'mbeya': {'lat': -8.7731, 'lng': 33.4597, 'name': 'Mbeya Region'},
    'mwanza': {'lat': -2.5167, 'lng': 32.9000, 'name': 'Mwanza Region'},
    'tanga': {'lat': -5.0667, 'lng': 39.2000, 'name': 'Tanga Region'},
}


def get_region_from_coordinates(lat, lng):
    """Determine the region whose center is closest to the given coordinates."""
    def distance_km(lat1, lng1, lat2, lng2):
        radius_km = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lng = math.radians(lng2 - lng1)
        a = (math.sin(d_lat / 2) ** 2
             + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2)
        return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return min(
        REGION_COORDS,
        key=lambda region: distance_km(lat, lng, REGION_COORDS[region]['lat'], REGION_COORDS[region]['lng']),
    )


def assign_case_to_officer(case):
    """Assign a case to an officer at its current level, in its region."""
    try:
        officer = OfficerProfile.objects.filter(region=case.region, level=case.current_level).first()
        if officer:
            case.assigned_to = officer.user
            case.save()
    except Exception as e:
        print(f"Error assigning case: {e}")


def escalate_case(case):
    """Move a case to the next level up and reassign it there.

    Returns False if the case is already at the top of the hierarchy
    (High Court), since there's nowhere higher to escalate to.
    """
    try:
        current_index = LEVEL_ORDER.index(case.current_level)
    except ValueError:
        current_index = 0

    if current_index >= len(LEVEL_ORDER) - 1:
        return False

    case.current_level = LEVEL_ORDER[current_index + 1]
    case.level_updated_at = timezone.now()
    # Status stays a plain lifecycle value (pending/in_progress/resolved) -
    # the case is unclaimed at its new level, so it's pending again there.
    # The level change itself is surfaced separately (see current_level),
    # not folded into status.
    case.status = 'pending'
    case.assigned_to = None
    case.save()
    assign_case_to_officer(case)
    return True


def get_officer_profile(user):
    """Return the user's OfficerProfile, or None if they don't have one."""
    try:
        return user.officer_profile
    except OfficerProfile.DoesNotExist:
        return None


def is_admin_user(user, officer=None):
    """High Court is the top of the hierarchy and acts as the system admin,
    with visibility into every case. The Django superuser account is also
    treated as admin so there's always a way to register the first High
    Court officer."""
    if user.is_superuser:
        return True
    if officer is None:
        officer = get_officer_profile(user)
    return officer is not None and officer.level == 'high_court'


def build_case_summary():
    """Aggregate case counts by status, hierarchy level, and region - gives
    High Court (the system admin) an at-a-glance overview of every case."""
    status_labels = dict(Case.STATUS_CHOICES)
    level_labels = dict(Case.LEVEL_CHOICES)
    region_labels = dict(Case.REGION_CHOICES)

    def counts_by(field, labels):
        rows = Case.objects.values(field).annotate(count=Count('id')).order_by(field)
        return [{'label': labels.get(row[field], row[field]), 'count': row['count']} for row in rows]

    total = Case.objects.count()
    resolved = Case.objects.filter(status='resolved').count()
    return {
        'total': total,
        'resolved': resolved,
        'resolution_rate': round((resolved / total) * 100, 1) if total else 0,
        'by_status': counts_by('status', status_labels),
        'by_level': counts_by('current_level', level_labels),
        'by_region': counts_by('region', region_labels),
    }


def get_registered_officers():
    """All registered officers, ordered by hierarchy level (village to high
    court) then region - for the admin's officer list."""
    officers = list(OfficerProfile.objects.select_related('user'))
    officers.sort(key=lambda o: (
        LEVEL_ORDER.index(o.level) if o.level in LEVEL_ORDER else len(LEVEL_ORDER),
        o.region,
    ))
    return officers


# ===== OFFICER VIEWS =====
def login_view(request):
    """Handle officer/admin login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    
    return render(request, 'login.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    """Officer Dashboard showing assigned and all cases"""
    filter_status = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '').strip()

    officer = get_officer_profile(request.user)
    if officer is None:
        # Not an officer (e.g. a bootstrap superuser with no profile yet) -
        # nothing has been forwarded to them. They can still reach Reports.
        cases = Case.objects.none()
    else:
        # Show cases forwarded to this officer: ones assigned to them, or
        # unassigned cases sitting at their own level/region. This applies
        # the same way at every tier, including High Court - they only see
        # what's actually been escalated up to them, not every case in the
        # system. The system-wide overview lives on the Reports page instead.
        if filter_status == 'all':
            cases = Case.objects.filter(assigned_to=request.user) | Case.objects.filter(region=officer.region, current_level=officer.level, assigned_to__isnull=True)
        else:
            cases = Case.objects.filter(status=filter_status, assigned_to=request.user) | Case.objects.filter(status=filter_status, region=officer.region, current_level=officer.level, assigned_to__isnull=True)
    
    # Search by citizen name, or by exact case ID
    if search_query:
        search_filter = Q(citizen_name__icontains=search_query)
        if search_query.isdigit():
            search_filter |= Q(id=int(search_query))
        cases = cases.filter(search_filter)
    
    context = {
        'cases': cases,
        'filter_status': filter_status,
        'search_query': search_query,
        'pending_count': Case.objects.filter(status='pending').count(),
        'in_progress_count': Case.objects.filter(status='in_progress').count(),
        'resolved_count': Case.objects.filter(status='resolved').count(),
    }
    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def case_detail(request, case_id):
    """View detailed case information"""
    case = get_object_or_404(Case, id=case_id)

    # Check if user is authorized to view this specific case
    # Allow if: user is assigned to case, or user is admin/superuser
    can_view = False

    # Check if user is admin (High Court or superuser/staff)
    if is_admin_user(request.user) or (request.user.is_staff and request.user.is_active):
        can_view = True
    # Check if user is assigned to this specific case
    elif case.assigned_to == request.user:
        can_view = True

    if not can_view:
        return HttpResponseForbidden("You do not have permission to view this case. Only the assigned officer or administrators can access this case.")

    if request.method == 'POST':
        case.notes = request.POST.get('notes', case.notes)
        case.assigned_to = request.user if request.POST.get('assign_to_me') else case.assigned_to
        case.save()
        return redirect('case_detail', case_id=case.id)
    
    context = {
        'case': case,
    }
    return render(request, 'case_detail.html', context)


@login_required(login_url='login')
def case_map(request):
    """Display cases on a map - admins (High Court) see every case, other
    officers only see their own."""
    officer = get_officer_profile(request.user)
    if is_admin_user(request.user, officer):
        cases = Case.objects.all()
    elif officer is None:
        cases = Case.objects.none()
    else:
        cases = Case.objects.filter(assigned_to=request.user) | Case.objects.filter(region=officer.region, current_level=officer.level, assigned_to__isnull=True)
    cases_data = []
    
    for case in cases:
        cases_data.append({
            'id': case.id,
            'title': case.title,
            'lat': case.latitude,
            'lng': case.longitude,
            'status': case.status,
            'citizen': case.citizen_name,
            'location': case.location,
        })
    
    context = {
        'cases_json': json.dumps(cases_data),
        'cases': cases,
    }
    return render(request, 'case_map.html', context)


@login_required(login_url='login')
def assign_case(request, case_id):
    """Assign a case to current user"""
    case = get_object_or_404(Case, id=case_id)
    case.assigned_to = request.user
    case.save()
    return redirect('case_detail', case_id=case.id)


@login_required(login_url='login')
def update_case_status(request, case_id):
    """Update case status via quick action buttons"""
    case = get_object_or_404(Case, id=case_id)
    
    # Check if user is authorized to update this specific case
    # Only allow if: user is assigned to case, or user is admin/superuser
    can_update = False
    
    # Check if user is admin (High Court or superuser/staff)
    if is_admin_user(request.user) or (request.user.is_staff and request.user.is_active):
        can_update = True
    # Check if user is assigned to this specific case
    elif case.assigned_to == request.user:
        can_update = True
    
    if not can_update:
        return HttpResponseForbidden("You do not have permission to update this case. Only the assigned officer or administrators can update case status.")
    
    if request.method == 'POST':
        # Handle quick action buttons (name="status" with value)
        new_status = request.POST.get('status')

        # Validate status against available choices
        valid_statuses = [choice[0] for choice in Case.STATUS_CHOICES]
        if new_status and new_status in valid_statuses:
            if new_status == 'escalated':
                # Escalating moves the case to the next level up the
                # hierarchy and reassigns it there - a no-op if the case is
                # already at the High Court, the top of the chain. The case
                # has now left this officer's queue, so send them back to
                # the dashboard instead of a case_detail page they may no
                # longer have permission to view.
                escalate_case(case)
                return redirect('dashboard')
            case.status = new_status
            case.save()
            return redirect('case_detail', case_id=case.id)
    
    return redirect('case_detail', case_id=case_id)


@login_required(login_url='login')
def case_reports(request):
    """Admin-only: system-wide overview of how cases are progressing, as
    pie/bar charts - status breakdown, hierarchy level, and region."""
    if not is_admin_user(request.user):
        return HttpResponseForbidden("Only administrators can view reports.")

    summary = build_case_summary()
    context = {
        'summary': summary,
        'status_chart_data': json.dumps({
            'labels': [row['label'] for row in summary['by_status']],
            'counts': [row['count'] for row in summary['by_status']],
        }),
        'level_chart_data': json.dumps({
            'labels': [row['label'] for row in summary['by_level']],
            'counts': [row['count'] for row in summary['by_level']],
        }),
        'region_chart_data': json.dumps({
            'labels': [row['label'] for row in summary['by_region']],
            'counts': [row['count'] for row in summary['by_region']],
        }),
    }
    return render(request, 'reports.html', context)


@login_required(login_url='login')
def officer_list(request):
    """Admin-only: list every registered officer and their level/region,
    with a button to register a new one."""
    if not is_admin_user(request.user):
        return HttpResponseForbidden("Only administrators can view officers.")

    return render(request, 'officers.html', {'officers': get_registered_officers()})


@login_required(login_url='login')
def register_officer(request):
    """Admin-only: register a new officer at a given hierarchy level and region.
    High Court is the top of the hierarchy and acts as the main admin, so it
    can register officers too; the superuser account remains as a bootstrap
    path for registering the first High Court officer."""
    if not is_admin_user(request.user):
        return HttpResponseForbidden("Only administrators can register officers.")

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        level = request.POST.get('level')
        region = request.POST.get('region')
        jurisdiction = request.POST.get('jurisdiction', '').strip()

        common_context = {
            'levels': OfficerProfile.LEVEL_CHOICES,
            'regions': OfficerProfile.REGION_CHOICES,
        }

        if not all([first_name, last_name, email, phone, username, password, password_confirm, level, region]):
            return render(request, 'register_officer.html', {'error': 'Please fill in all fields', **common_context})

        if password != password_confirm:
            return render(request, 'register_officer.html', {'error': 'Passwords do not match', **common_context})

        if User.objects.filter(username=username).exists():
            return render(request, 'register_officer.html', {'error': 'Username already exists', **common_context})

        valid_levels = [choice[0] for choice in OfficerProfile.LEVEL_CHOICES]
        valid_regions = [choice[0] for choice in OfficerProfile.REGION_CHOICES]
        if level not in valid_levels or region not in valid_regions:
            return render(request, 'register_officer.html', {'error': 'Invalid level or region', **common_context})

        if level in LEVELS_REQUIRING_JURISDICTION and not jurisdiction:
            level_label = dict(OfficerProfile.LEVEL_CHOICES)[level]
            return render(request, 'register_officer.html', {
                'error': f'Please enter which {level_label.replace(" Officer", "").lower()} this officer serves.',
                **common_context,
            })

        # Regional/High Court officers cover the whole region, not a
        # specific place, so any jurisdiction entered for them is ignored.
        if level not in LEVELS_REQUIRING_JURISDICTION:
            jurisdiction = ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        officer = OfficerProfile.objects.create(user=user, region=region, level=level, jurisdiction=jurisdiction, phone=phone)

        place = f'{jurisdiction}, {officer.get_region_display()}' if jurisdiction else officer.get_region_display()
        messages.success(request, f'{first_name} {last_name} registered as {officer.get_level_display()} for {place}.')
        return redirect('officer_list')

    return render(request, 'register_officer.html', {
        'levels': OfficerProfile.LEVEL_CHOICES,
        'regions': OfficerProfile.REGION_CHOICES,
        'initial_level': request.GET.get('level', ''),
        'initial_region': request.GET.get('region', ''),
    })


@login_required(login_url='login')
def delete_officer(request, officer_id):
    """Admin-only: remove an officer. Any cases currently assigned to them
    must be handed off to another officer first, chosen by the admin."""
    if not is_admin_user(request.user):
        return HttpResponseForbidden("Only administrators can delete officers.")

    officer = get_object_or_404(OfficerProfile, pk=officer_id)

    if officer.user == request.user:
        messages.error(request, "You cannot delete your own officer account.")
        return redirect('officer_list')

    assigned_cases = Case.objects.filter(assigned_to=officer.user)
    # Only officers at the same level and region are valid replacements -
    # that's how cases get routed (see assign_case_to_officer).
    other_officers = OfficerProfile.objects.filter(
        region=officer.region, level=officer.level,
    ).exclude(pk=officer.pk).select_related('user')

    if request.method == 'POST':
        reassign_to_id = request.POST.get('reassign_to')

        if assigned_cases.exists():
            if not reassign_to_id:
                messages.error(request, "Select an officer to take over this officer's cases before deleting.")
                return render(request, 'delete_officer_confirm.html', {
                    'officer': officer,
                    'assigned_cases': assigned_cases,
                    'other_officers': other_officers,
                })

            new_officer = get_object_or_404(other_officers, pk=reassign_to_id)
            assigned_cases.update(assigned_to=new_officer.user)

        officer_name = officer.user.get_full_name() or officer.user.username
        officer.user.delete()  # cascades to OfficerProfile
        messages.success(request, f'{officer_name} has been removed.')
        return redirect('officer_list')

    return render(request, 'delete_officer_confirm.html', {
        'officer': officer,
        'assigned_cases': assigned_cases,
        'other_officers': other_officers,
    })


@login_required(login_url='login')
def settings(request):
    """Officer/Admin Settings Page"""
    try:
        officer = request.user.officer_profile
    except OfficerProfile.DoesNotExist:
        officer = None
    
    if request.method == 'POST':
        # Update user profile
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()
        
        # Update officer profile if exists
        if officer:
            officer.phone = request.POST.get('phone', officer.phone)
            officer.save()
        
        # Change password if provided
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if old_password and new_password and confirm_password:
            if not request.user.check_password(old_password):
                return render(request, 'settings.html', {
                    'officer': officer,
                    'error': 'Old password is incorrect'
                })
            if new_password != confirm_password:
                return render(request, 'settings.html', {
                    'officer': officer,
                    'error': 'Passwords do not match'
                })
            request.user.set_password(new_password)
            request.user.save()
            login(request, request.user)  # Re-login with new password
            return render(request, 'settings.html', {
                'officer': officer,
                'success': 'Settings updated successfully!'
            })
        
        return render(request, 'settings.html', {
            'officer': officer,
            'success': 'Settings updated successfully!'
        })
    
    context = {
        'officer': officer,
    }
    return render(request, 'settings.html', context)


# ===== CITIZEN VIEWS =====
def citizen_register(request):
    """Citizen registration"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        region = request.POST.get('region', '')

        # Validation
        if password != password_confirm:
            return render(request, 'citizen_register.html', {'error': 'Passwords do not match'})

        if User.objects.filter(username=username).exists():
            return render(request, 'citizen_register.html', {'error': 'Username already exists'})

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create citizen profile
        Citizen.objects.create(
            user=user,
            phone=phone,
            region=region
        )
        
        # Log in user
        login(request, user)
        return redirect('citizen_dashboard')
    
    return render(request, 'citizen_register.html')


def citizen_login(request):
    """Citizen login"""
    if request.user.is_authenticated:
        try:
            request.user.citizen_profile
            return redirect('citizen_dashboard')
        except Citizen.DoesNotExist:
            pass
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            try:
                user.citizen_profile
                login(request, user)
                return redirect('citizen_dashboard')
            except Citizen.DoesNotExist:
                return render(request, 'citizen_login.html', {'error': 'Invalid citizen account'})
        else:
            return render(request, 'citizen_login.html', {'error': 'Invalid username or password'})
    
    return render(request, 'citizen_login.html')


def citizen_logout(request):
    """Citizen logout"""
    logout(request)
    return redirect('citizen_login')


@login_required(login_url='citizen_login')
def citizen_dashboard(request):
    """Citizen dashboard showing their submitted cases"""
    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return redirect('citizen_login')

    filter_status = request.GET.get('status', 'all')

    if filter_status == 'all':
        cases = Case.objects.filter(citizen=citizen)
    else:
        cases = Case.objects.filter(citizen=citizen, status=filter_status)
    
    context = {
        'cases': cases,
        'filter_status': filter_status,
        'pending_count': Case.objects.filter(citizen=citizen, status='pending').count(),
        'in_progress_count': Case.objects.filter(citizen=citizen, status='in_progress').count(),
        'resolved_count': Case.objects.filter(citizen=citizen, status='resolved').count(),
    }
    return render(request, 'citizen_dashboard.html', context)


@login_required(login_url='citizen_login')
def citizen_profile(request):
    """Citizen profile - view and edit personal details"""
    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return redirect('citizen_login')
    
    if request.method == 'POST':
        # Update user profile
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Validate
        if not all([first_name, last_name, email, phone]):
            context = {
                'citizen': citizen,
                'error': 'All fields are required'
            }
            return render(request, 'citizen_profile.html', context)
        
        # Update user
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()
        
        # Update citizen profile
        citizen.phone = phone
        citizen.save()
        
        context = {
            'citizen': citizen,
            'success': 'Profile updated successfully!'
        }
        return render(request, 'citizen_profile.html', context)
    
    context = {
        'citizen': citizen,
    }
    return render(request, 'citizen_profile.html', context)


@login_required(login_url='citizen_login')
def submit_case(request):
    """Submit a new case with geolocation and file uploads"""
    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return redirect('citizen_login')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        location = request.POST.get('detected_region', '').strip()  # Form field is named 'detected_region'
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        
        # Validate required fields
        if not all([title, description, location, latitude, longitude]):
            error_msg = 'Please fill in all required fields (title, description, and location with coordinates)'
            return render(request, 'submit_case.html', {'error': error_msg})
        
        try:
            lat = float(latitude)
            lng = float(longitude)
        except (ValueError, TypeError):
            return render(request, 'submit_case.html', {'error': 'Invalid coordinates. Please ensure location is properly pinned on the map.'})
        
        # Determine region from coordinates
        region = get_region_from_coordinates(lat, lng)
        
        # Create case
        case = Case.objects.create(
            title=title,
            description=description,
            location=location,
            latitude=lat,
            longitude=lng,
            region=region,
            citizen=citizen,
            citizen_name=f"{request.user.first_name} {request.user.last_name}",
            citizen_phone=citizen.phone,
            citizen_email=request.user.email,
        )
        
        # Handle file uploads
        uploaded_files = request.FILES.getlist('documents')
        for uploaded_file in uploaded_files:
            # Validate file size (5MB max)
            max_size = 5 * 1024 * 1024  # 5MB
            if uploaded_file.size > max_size:
                continue  # Skip files that are too large
            
            # Save document
            CaseDocument.objects.create(
                case=case,
                title=uploaded_file.name,
                file=uploaded_file,
                uploaded_by=request.user,
                document_type='evidence'
            )
        
        # Assign to officer in the region
        assign_case_to_officer(case)
        
        return redirect('case_submitted', case_id=case.id)
    
    context = {}
    return render(request, 'submit_case.html', context)


@login_required(login_url='citizen_login')
def case_submitted(request, case_id):
    """Show case submission confirmation"""
    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return redirect('citizen_login')
    
    case = get_object_or_404(Case, id=case_id, citizen=citizen)
    
    context = {
        'case': case,
    }
    return render(request, 'case_submitted.html', context)


@login_required(login_url='citizen_login')
def citizen_case_detail(request, case_id):
    """View case details for citizen"""
    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return redirect('citizen_login')
    
    case = get_object_or_404(Case, id=case_id, citizen=citizen)

    context = {
        'case': case,
    }
    return render(request, 'citizen_case_detail.html', context)


@login_required(login_url='citizen_login')
def download_document(request, document_id):
    """Download a case document - for citizens"""
    document = get_object_or_404(CaseDocument, id=document_id)
    
    # Check permissions - citizen can only download their own case documents
    try:
        citizen = request.user.citizen_profile
        if document.case.citizen != citizen:
            return HttpResponseForbidden("You don't have permission to download this document")
    except Citizen.DoesNotExist:
        return HttpResponseForbidden("You don't have permission to download this document")
    
    if document.file:
        return FileResponse(document.file.open('rb'), as_attachment=True, filename=document.file.name.split('/')[-1])
    else:
        return HttpResponseForbidden("Document file not found")


@login_required(login_url='login')
def download_document_officer(request, document_id):
    """Download a case document - for officers"""
    document = get_object_or_404(CaseDocument, id=document_id)
    
    # Check permissions - only officer viewing the case can download
    case = document.case
    try:
        officer = request.user.officer_profile
        if case.assigned_to != request.user and case.region != officer.region and not request.user.is_staff:
            return HttpResponseForbidden("You don't have permission to download this document")
    except OfficerProfile.DoesNotExist:
        if case.assigned_to != request.user and not request.user.is_staff:
            return HttpResponseForbidden("You don't have permission to download this document")
    
    if document.file:
        return FileResponse(document.file.open('rb'), as_attachment=True, filename=document.file.name.split('/')[-1])
    else:
        return HttpResponseForbidden("Document file not found")