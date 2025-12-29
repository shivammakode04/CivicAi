from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    # 1. Admin Site
    path('admin/', admin.site.urls),
    
    # 2. Authentication
    path('', views.auth_view, name='auth'),
    path('accounts/logout/', views.logout_view, name='logout'), # Catches default Django logout
    path('logout/', views.logout_view, name='logout_custom'),   # Our custom logout
    
    # 3. Password Reset (Django Built-in)
    path('accounts/', include('django.contrib.auth.urls')), 

    # 4. Main App Logic
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('submit/', views.submit_complaint, name='submit_complaint'),
    
    # 5. Complaint Status Actions
    path('solve/<int:id>/', views.mark_solved, name='mark_solved'),
    path('verify/<int:id>/', views.verify_close, name='verify_close'),
    path('reopen/<int:id>/', views.reopen_complaint, name='reopen_complaint'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)