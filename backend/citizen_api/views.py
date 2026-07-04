from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from landsystem.models import Case, CaseDocument, Citizen
from landsystem.views import assign_case_to_officer, get_region_from_coordinates
from .models import PasswordResetCode


def serialize_profile(citizen):
    return {
        'username': citizen.user.username,
        'first_name': citizen.user.first_name,
        'last_name': citizen.user.last_name,
        'email': citizen.user.email,
        'phone': citizen.phone,
        'region': citizen.region,
        'date_joined': citizen.user.date_joined,
    }


def serialize_case(case, detail=False):
    # Citizens should never see "Escalated" as the case status - escalation
    # only moves the case to a higher authority; the underlying process is
    # still pending there. Some cases have status='escalated' stored directly
    # (e.g. set via the admin), so normalize that here rather than trusting
    # every write path to have kept status/level concerns separate.
    status_value = 'pending' if case.status == 'escalated' else case.status
    status_display = (
        dict(case.STATUS_CHOICES)['pending'] if case.status == 'escalated' else case.get_status_display()
    )
    data = {
        'id': case.id,
        'title': case.title,
        'status': status_value,
        'status_display': status_display,
        'region': case.region,
        'region_display': case.get_region_display(),
        'location': case.location,
        'created_at': case.created_at,
        'updated_at': case.updated_at,
        'is_escalated': case.current_level != 'village',
        'current_level': case.current_level,
        'current_level_display': case.get_current_level_display(),
    }
    if detail:
        data.update({
            'description': case.description,
            'latitude': case.latitude,
            'longitude': case.longitude,
            'notes': case.notes,
            'assigned_officer': case.assigned_to.get_full_name() if case.assigned_to else None,
            'documents': [
                {
                    'id': doc.id,
                    'title': doc.title,
                    'document_type': doc.document_type,
                    'file_extension': doc.file_extension,
                    'file_size_mb': doc.file_size_mb,
                    'uploaded_at': doc.uploaded_at,
                }
                for doc in case.documents.all()
            ],
        })
    return data


def get_citizen_or_403(request):
    try:
        return request.user.citizen_profile, None
    except Citizen.DoesNotExist:
        return None, Response({'error': 'This account is not a citizen account'}, status=status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    email = request.data.get('email', '')
    phone = request.data.get('phone', '')
    username = request.data.get('username')
    password = request.data.get('password')
    region = request.data.get('region', '')

    if not username or not password:
        return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    citizen = Citizen.objects.create(user=user, phone=phone, region=region)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'profile': serialize_profile(citizen)}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)

    if user is None:
        return Response({'error': 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        citizen = user.citizen_profile
    except Citizen.DoesNotExist:
        return Response({'error': 'Invalid citizen account'}, status=status.HTTP_403_FORBIDDEN)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'profile': serialize_profile(citizen)})


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_request(request):
    """Step 1 of password reset: if the username and email match a citizen
    account, email a 6-digit code to that address. Always returns the same
    generic message either way, so this can't be used to check which
    usernames exist."""
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()

    if not username or not email:
        return Response({'error': 'Please provide your username and email'}, status=status.HTTP_400_BAD_REQUEST)

    generic_response = Response({'message': 'If that account exists, a reset code has been sent to its email.'})

    try:
        user = User.objects.get(username=username)
        user.citizen_profile
    except (User.DoesNotExist, Citizen.DoesNotExist):
        return generic_response

    if not user.email or user.email.lower() != email.lower():
        return generic_response

    code = PasswordResetCode.generate_code()
    PasswordResetCode.objects.create(user=user, code=code)

    send_mail(
        subject='Your Land Dispute System password reset code',
        message=f'Your password reset code is {code}. It expires in 15 minutes.\n\n'
                f"If you didn't request this, you can safely ignore this email.",
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return generic_response


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_confirm(request):
    """Step 2 of password reset: verify the emailed code and set the new
    password."""
    username = request.data.get('username', '').strip()
    code = request.data.get('code', '').strip()
    new_password = request.data.get('new_password')
    new_password_confirm = request.data.get('new_password_confirm')

    if not all([username, code, new_password, new_password_confirm]):
        return Response({'error': 'Please fill in all fields'}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != new_password_confirm:
        return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)

    reset_code = (
        PasswordResetCode.objects
        .filter(user=user, code=code, used=False)
        .order_by('-created_at')
        .first()
    )
    if reset_code is None or reset_code.is_expired():
        return Response({'error': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)

    reset_code.used = True
    reset_code.save(update_fields=['used'])

    user.set_password(new_password)
    user.save()
    return Response({'message': 'Password reset successful. You can now log in.'})


@api_view(['POST'])
def logout_view(request):
    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'PUT'])
def profile(request):
    citizen, error = get_citizen_or_403(request)
    if error:
        return error

    if request.method == 'PUT':
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()
        email = request.data.get('email', '').strip()
        phone = request.data.get('phone', '').strip()

        if not all([first_name, last_name, email, phone]):
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()

        citizen.phone = phone
        citizen.save()

    return Response(serialize_profile(citizen))


@api_view(['GET', 'POST'])
def cases(request):
    citizen, error = get_citizen_or_403(request)
    if error:
        return error

    if request.method == 'POST':
        description = request.data.get('description', '').strip()
        location = request.data.get('location', '').strip()
        latitude = request.data.get('latitude', '')
        longitude = request.data.get('longitude', '')

        if not all([description, location, latitude, longitude]):
            return Response(
                {'error': 'Please provide description and location with coordinates'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lat = float(latitude)
            lng = float(longitude)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid coordinates'}, status=status.HTTP_400_BAD_REQUEST)

        # Citizens don't choose a title - the case ID is used as the title
        # instead, so it's only known once the row is created.
        case = Case.objects.create(
            title='',
            description=description,
            location=location,
            latitude=lat,
            longitude=lng,
            region=get_region_from_coordinates(lat, lng),
            citizen=citizen,
            citizen_name=f"{request.user.first_name} {request.user.last_name}",
            citizen_phone=citizen.phone,
            citizen_email=request.user.email,
        )
        case.title = f'Case #{case.id}'
        case.save(update_fields=['title'])

        for uploaded_file in request.FILES.getlist('documents'):
            if uploaded_file.size > 5 * 1024 * 1024:
                continue
            CaseDocument.objects.create(
                case=case,
                title=uploaded_file.name,
                file=uploaded_file,
                uploaded_by=request.user,
                document_type='evidence',
            )

        assign_case_to_officer(case)
        return Response(serialize_case(case, detail=True), status=status.HTTP_201_CREATED)

    # A case with status='escalated' stored directly (e.g. set via the admin)
    # displays to citizens as pending (see serialize_case), so it must count
    # and filter as pending here too, not as a separate literal status.
    pending_q = Q(status='pending') | Q(status='escalated')

    filter_status = request.query_params.get('status', 'all')
    qs = Case.objects.filter(citizen=citizen)
    if filter_status == 'pending':
        qs = qs.filter(pending_q)
    elif filter_status != 'all':
        qs = qs.filter(status=filter_status)

    return Response({
        'counts': {
            'pending': Case.objects.filter(citizen=citizen).filter(pending_q).count(),
            'in_progress': Case.objects.filter(citizen=citizen, status='in_progress').count(),
            'resolved': Case.objects.filter(citizen=citizen, status='resolved').count(),
        },
        'results': [serialize_case(c) for c in qs],
    })


@api_view(['GET'])
def case_detail(request, case_id):
    citizen, error = get_citizen_or_403(request)
    if error:
        return error

    case = get_object_or_404(Case, id=case_id, citizen=citizen)
    return Response(serialize_case(case, detail=True))


@api_view(['GET'])
def download_document(request, document_id):
    citizen, error = get_citizen_or_403(request)
    if error:
        return error

    document = get_object_or_404(CaseDocument, id=document_id, case__citizen=citizen)
    return FileResponse(document.file.open('rb'), as_attachment=True, filename=document.file.name.split('/')[-1])
