from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, FileResponse, HttpResponseForbidden
from django.db.models import Q
from .models import Case, Citizen, OfficerProfile, CaseDocument
import json


# Region coordinates for mapping
REGION_COORDS = {
    'arusha': {'lat': -3.3731, 'lng': 36.6753, 'name': 'Arusha Region'},
    'dar_es_salaam': {'lat': -6.8000, 'lng': 39.2800, 'name': 'Dar es Salaam'},
    'dodoma': {'lat': -6.1856, 'lng': 35.7382, 'name': 'Dodoma Region'},
    'iringa': {'lat': -8.7731, 'lng': 33.4597, 'name': 'Iringa Region'},
    'kagera': {'lat': -1.2921, 'lng': 31.8974, 'name': 'Kagera Region'},
    'mbeya': {'lat': -8.7731, 'lng': 33.4597, 'name': 'Mbeya Region'},
    'mwanza': {'lat': -2.5167, 'lng': 32.9000, 'name': 'Mwanza Region'},
    'tanga': {'lat': -5.0667, 'lng': 39.2000, 'name': 'Tanga Region'},
}


def get_region_from_coordinates(lat, lng):
    """Determine region from coordinates"""
    if lat < -7 and lng > 33:
        if lng > 34:
            return 'mbeya'
        return 'iringa'
    elif lat < -6 and lng < 40:
        return 'dodoma'
    elif lat < -6 and lng > 39:
        return 'dar_es_salaam'
    elif lat < -3 and lng > 36:
        return 'arusha'
    elif lat < -2 and lng > 31:
        return 'mwanza'
    elif lat > 0 and lng > 31:
        return 'kagera'
    elif lat < -5 and lng > 39:
        return 'tanga'
    else:
        return 'dodoma'  # Default


def assign_case_to_officer(case):
    """Automatically assign case to an officer in the case's region"""
    try:
        officer = OfficerProfile.objects.filter(region=case.region).first()
        if officer:
            case.assigned_to = officer.user
            case.save()
    except Exception as e:
        print(f"Error assigning case: {e}")


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
    
    # Check if user is an officer
    try:
        officer = request.user.officer_profile
        # Show all cases (assigned to officer or in their region)
        if filter_status == 'all':
            cases = Case.objects.filter(assigned_to=request.user) | Case.objects.filter(region=officer.region, assigned_to__isnull=True)
        else:
            cases = Case.objects.filter(status=filter_status, assigned_to=request.user) | Case.objects.filter(status=filter_status, region=officer.region, assigned_to__isnull=True)
    except OfficerProfile.DoesNotExist:
        # Show all cases for admins
        if filter_status == 'all':
            cases = Case.objects.all()
        else:
            cases = Case.objects.filter(status=filter_status)
    
    # Apply search filter
    if search_query:
        cases = cases.filter(
            Q(title__icontains=search_query) | 
            Q(citizen_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
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
    
    # Check if user is an officer or admin (citizens cannot view officer dashboard cases)
    is_officer_or_admin = False
    try:
        officer = request.user.officer_profile
        is_officer_or_admin = True
    except OfficerProfile.DoesNotExist:
        if request.user.is_staff:
            is_officer_or_admin = True
    
    if not is_officer_or_admin:
        return HttpResponseForbidden("You do not have permission to view this case.")
    
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
    """Display all cases on a map"""
    cases = Case.objects.all()
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
@login_required(login_url='login')
def update_case_status(request, case_id):
    """Update case status via quick action buttons"""
    # Check if user is an officer or admin
    is_officer_or_admin = False
    try:
        officer = request.user.officer_profile
        is_officer_or_admin = True
    except OfficerProfile.DoesNotExist:
        if request.user.is_staff:
            is_officer_or_admin = True
    
    if not is_officer_or_admin:
        return HttpResponseForbidden("You do not have permission to update this case. Only officers and administrators can update case status.")
    
    if request.method == 'POST':
        case = get_object_or_404(Case, id=case_id)
        
        # Handle quick action buttons (name="status" with value)
        new_status = request.POST.get('status')
        
        # Validate status against available choices
        valid_statuses = [choice[0] for choice in Case.STATUS_CHOICES]
        if new_status and new_status in valid_statuses:
            case.status = new_status
            case.save()
            return redirect('case_detail', case_id=case.id)
    
    return redirect('case_detail', case_id=case_id)


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
            phone=phone
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
def case_detail(request, case_id):
    """View case details for officer - handle updates and notes"""
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        case.notes = request.POST.get('notes', case.notes)
        case.save()
        return redirect('case_detail', case_id=case.id)
    
    context = {
        'case': case,
    }
    return render(request, 'case_detail.html', context)


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