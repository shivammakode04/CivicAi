from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Value, IntegerField, Count, Avg
from .models import User, Complaint, Notification
from .ai_model.engine import ai_bot
import json

# --- UTILS ---
def send_notif(user, message):
    Notification.objects.create(user=user, message=message)

# --- AUTH ---
def auth_view(request):
    if request.user.is_authenticated: return redirect('dashboard')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            u = request.POST.get('username')
            p = request.POST.get('password')
            user = authenticate(username=u, password=p)
            if user: login(request, user); return redirect('dashboard')
            else: return render(request, 'auth.html', {'error': 'Invalid Credentials'})
        elif action == 'signup':
            try:
                role = request.POST.get('role')
                u = request.POST.get('username')
                p = request.POST.get('password')
                phone = request.POST.get('phone', '')
                city = request.POST.get('city', 'Indore')
                aadhar = request.POST.get('aadhar_id', '')
                address = request.POST.get('address', '')
                
                if role == 'admin':
                    dept = request.POST.get('department', '')
                    user = User.objects.create_user(
                        username=u, 
                        password=p, 
                        is_department_admin=True, 
                        department_name=dept, 
                        phone=phone, 
                        city=city,
                        aadhar_id=aadhar,
                        address=address
                    )
                else:
                    user = User.objects.create_user(
                        username=u, 
                        password=p, 
                        is_department_admin=False, 
                        phone=phone, 
                        city=city,
                        aadhar_id=aadhar,
                        address=address
                    )
                login(request, user)
                return redirect('dashboard')
            except Exception as e: return render(request, 'auth.html', {'error': str(e)})
    return render(request, 'auth.html')

def logout_view(request): logout(request); return redirect('auth')

# --- PROFILE LOGIC ---
@login_required
def update_profile_pic(request):
    if request.method == 'POST' and request.FILES.get('profile_pic'):
        request.user.profile_pic = request.FILES['profile_pic']
        request.user.save()
    return redirect('dashboard')

@login_required
def profile_view(request):
    user = request.user
    if user.is_department_admin:
        # Show admin's department complaints
        complaints = Complaint.objects.filter(department=user.department_name, city__iexact=user.city).order_by('-created_at')
        return render(request, 'admin_profile.html', {'user': user, 'complaints': complaints})
    else:
        return render(request, 'profile.html', {'user': user})

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.aadhar_id = request.POST.get('aadhar_id', user.aadhar_id)
        user.address = request.POST.get('address', user.address)
        if request.FILES.get('profile_pic'):
            user.profile_pic = request.FILES['profile_pic']
        user.save()
        return redirect('profile_view')
    return redirect('dashboard')

# --- DASHBOARD ---
@login_required
def dashboard_view(request):
    user = request.user
    notifs = Notification.objects.filter(user=user).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    
    priority_order = Case(When(priority='High', then=Value(1)), When(priority='Medium', then=Value(2)), When(priority='Low', then=Value(3)), output_field=IntegerField())

    # ADMIN VIEW
    if user.is_department_admin:
        complaints = Complaint.objects.filter(department=user.department_name, city__iexact=user.city).annotate(sort=priority_order).order_by('sort', '-created_at')
        active_complaints = complaints.exclude(status='Closed')  # Active cases only
        hotspots = complaints.values('pincode', 'location_name').annotate(total=Count('id')).order_by('-total')[:5]
        avg_rating = complaints.aggregate(Avg('rating'))['rating__avg'] or 0
        map_data = list(complaints.exclude(latitude__isnull=True).exclude(status='Closed').values('ticket_id', 'description', 'latitude', 'longitude', 'priority', 'status', 'user__username', 'user__phone'))
        
        p_data = [complaints.filter(priority='High').count(), complaints.filter(priority='Medium').count(), complaints.filter(priority='Low').count()]
        s_data = [complaints.filter(status='Pending').count(), complaints.filter(status='Solved').count(), complaints.filter(status='Closed').count()]

        return render(request, 'dash_admin.html', {
            'complaints': complaints, 
            'active_count': active_complaints.count(),
            'hotspots': hotspots, 
            'chart_prio': json.dumps(p_data), 
            'chart_status': json.dumps(s_data), 
            'map_data': json.dumps(map_data), 
            'avg_rating': round(avg_rating, 1), 
            'notifs': notifs, 
            'unread_count': unread_count
        })

    # USER VIEW
   # --- USER VIEW ---
    else:
        complaints = Complaint.objects.filter(user=user).order_by('-created_at')
        closed_count = complaints.filter(status='Closed').count()
        
        # NEW PROFESSIONAL LOGIC
        level = "Active Resident"          # Level 1 (Entry)
        if closed_count > 5: 
            level = "Civic Steward"        # Level 2 (Intermediate)
        if closed_count > 15: 
            level = "Community Ambassador" # Level 3 (Top Tier)

        stats = {
            'total': complaints.count(),
            'pending': complaints.filter(status='Pending').count(),
            'solved': complaints.filter(status='Solved').count(),
            'closed': closed_count,
            'level': level
        }
        return render(request, 'dash_user.html', {
            'complaints': complaints, 'stats': stats, 'notifs': notifs, 'unread_count': unread_count
        })
# --- COMPLAINT ACTIONS ---
@login_required
def submit_complaint(request):
    if request.method == 'POST':
        desc = request.POST.get('description'); loc = request.POST.get('location_name'); pin = request.POST.get('pincode')
        img = request.FILES.get('image'); lat = request.POST.get('latitude') or None; lng = request.POST.get('longitude') or None
        
        dept, prio = ai_bot.predict(desc)
        # Fix: Default rating=0 to prevent DB error
        Complaint.objects.create(user=request.user, description=desc, location_name=loc, pincode=pin, image=img, department=dept, priority=prio, latitude=lat, longitude=lng, city=request.user.city, rating=0)
        send_notif(request.user, f"Complaint submitted! Assigned to {dept}.")
    return redirect('dashboard')

@login_required
def mark_solved(request, id):
    c = get_object_or_404(Complaint, id=id)
    if request.user.is_department_admin:
        c.status = 'Solved'; c.save()
        send_notif(c.user, f"Ticket #{c.ticket_id} resolved. Verify now!")
    return redirect('dashboard')

@login_required
def verify_close(request, id):
    c = get_object_or_404(Complaint, id=id)
    if c.user == request.user:
        if request.method == 'POST':
            # FIX: If rating is empty, default to 5. Stops IntegrityError (1048)
            rating_val = request.POST.get('rating')
            c.rating = int(rating_val) if rating_val else 5 
            
            c.feedback = request.POST.get('feedback')
            c.status = 'Closed'
            c.save()
            send_notif(c.user, f"Ticket #{c.ticket_id} Closed. +50 XP!")
    return redirect('dashboard')

@login_required
def transfer_complaint(request, id):
    if request.method == 'POST':
        c = get_object_or_404(Complaint, id=id)
        if request.user.is_department_admin:
            c.department = request.POST.get('new_department'); c.save()
    return redirect('dashboard')

@login_required
def reopen_complaint(request, id):
    c = get_object_or_404(Complaint, id=id)
    if c.user == request.user:
        c.status = 'Pending'; c.save()
        send_notif(c.user, f"Ticket #{c.ticket_id} reopened for review.")
    return redirect('dashboard')