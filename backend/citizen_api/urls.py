from django.urls import path
from . import views

urlpatterns = [
    path('auth/register/', views.register, name='api_register'),
    path('auth/login/', views.login_view, name='api_login'),
    path('auth/logout/', views.logout_view, name='api_logout'),
    path('profile/', views.profile, name='api_profile'),
    path('cases/', views.cases, name='api_cases'),
    path('cases/<int:case_id>/', views.case_detail, name='api_case_detail'),
    path('documents/<int:document_id>/download/', views.download_document, name='api_download_document'),
]
