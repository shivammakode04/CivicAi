from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    # 1. Admin & Auth
    path('admin/', admin.site.urls),
    path('', views.auth_view, name='auth'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('logout/', views.logout_view, name='logout_custom'),
    path('accounts/', include('django.contrib.auth.urls')),

    # 2. Main Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    # 3. Features
    path('update_pic/', views.update_profile_pic, name='update_profile_pic'), # Profile Photo
    path('submit/', views.submit_complaint, name='submit_complaint'),

    # 4. Action Logic
    path('solve/<int:id>/', views.mark_solved, name='mark_solved'),
    path('verify/<int:id>/', views.verify_close, name='verify_close'),
    path('reopen/<int:id>/', views.reopen_complaint, name='reopen_complaint'),
    
    # 5. NEW: Transfer Department
    path('transfer/<int:id>/', views.transfer_complaint, name='transfer_complaint'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)