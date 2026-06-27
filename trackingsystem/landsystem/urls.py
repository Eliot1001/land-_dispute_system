from django.urls import path
from . import views

urlpatterns = [
    # Officer/Admin routes
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('case/<int:case_id>/', views.case_detail, name='case_detail'),
    path('case/<int:case_id>/assign/', views.assign_case, name='assign_case'),
    path('case/<int:case_id>/update-status/', views.update_case_status, name='update_case_status'),
    path('document/<int:document_id>/download/', views.download_document_officer, name='download_document_officer'),
    path('map/', views.case_map, name='case_map'),
    path('settings/', views.settings, name='settings'),
    
    # Citizen routes
    path('citizen/register/', views.citizen_register, name='citizen_register'),
    path('citizen/login/', views.citizen_login, name='citizen_login'),
    path('citizen/logout/', views.citizen_logout, name='citizen_logout'),
    path('citizen/dashboard/', views.citizen_dashboard, name='citizen_dashboard'),
    path('citizen/submit-case/', views.submit_case, name='submit_case'),
    path('citizen/case/<int:case_id>/submitted/', views.case_submitted, name='case_submitted'),
    path('citizen/case/<int:case_id>/', views.citizen_case_detail, name='citizen_case_detail'),
    path('citizen/document/<int:document_id>/download/', views.download_document, name='download_document'),
]