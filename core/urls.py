from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    # Auth
    path('admin/', admin.site.urls),
    path('', views.auth_view, name='auth'),
    path('logout-user/', views.logout_view, name='user_logout'), # Fixed name conflict
    path('accounts/', include('django.contrib.auth.urls')),

    # Dashboard & Profile
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('update_pic/', views.update_profile_pic, name='update_profile_pic'),

    # Actions
    path('submit/', views.submit_complaint, name='submit_complaint'),
    path('solve/<int:id>/', views.mark_solved, name='mark_solved'),
    path('verify/<int:id>/', views.verify_close, name='verify_close'),
    path('transfer/<int:id>/', views.transfer_complaint, name='transfer_complaint'),
    path('reopen/<int:id>/', views.reopen_complaint, name='reopen_complaint'), # Ensure this exists

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)