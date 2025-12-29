from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Value, IntegerField, Count
from .models import User, Complaint
from .ai_model.engine import ai_bot
import json

# --- AUTHENTICATION ---
def auth_view(request):
    if request.user.is_authenticated: return redirect('dashboard')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            u = request.POST.get('username')
            p = request.POST.get('password')
            user = authenticate(username=u, password=p)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'auth.html', {'error': 'Invalid Credentials'})
        elif action == 'signup':
            try:
                role = request.POST.get('role')
                u = request.POST.get('username')
                p = request.POST.get('password')
                phone = request.POST.get('phone')
                city = request.POST.get('city')
                aadhar = request.POST.get('aadhar')
                address = request.POST.get('address')
                gender = request.POST.get('gender')
                dob = request.POST.get('dob')
                
                if role == 'admin':
                    dept = request.POST.get('department')
                    user = User.objects.create_user(username=u, password=p, is_department_admin=True, department_name=dept, phone=phone, city=city, aadhar_id=aadhar, address=address, gender=gender, dob=dob)
                else:
                    user = User.objects.create_user(username=u, password=p, is_department_admin=False, phone=phone, city=city, aadhar_id=aadhar, address=address, gender=gender, dob=dob)
                login(request, user)
                return redirect('dashboard')
            except Exception as e:
                return render(request, 'auth.html', {'error': str(e)})
    return render(request, 'auth.html')

def logout_view(request):
    logout(request)
    return redirect('auth')

@login_required
def update_profile_pic(request):
    if request.method == 'POST' and request.FILES.get('profile_pic'):
        request.user.profile_pic = request.FILES['profile_pic']
        request.user.save()
    return redirect('dashboard')

# --- DASHBOARD LOGIC (Admin + User Updated) ---
@login_required
def dashboard_view(request):
    user = request.user
    
    # Priority Sorting Logic
    priority_order = Case(
        When(priority='High', then=Value(1)),
        When(priority='Medium', then=Value(2)),
        When(priority='Low', then=Value(3)),
        output_field=IntegerField(),
    )

    # --- ADMIN VIEW ---
    if user.is_department_admin:
        complaints = Complaint.objects.filter(department=user.department_name).annotate(sort=priority_order).order_by('sort', '-created_at')
        
        hotspots = Complaint.objects.filter(department=user.department_name).values('pincode', 'location_name').annotate(total=Count('id')).order_by('-total')[:5]

        # Admin Chart Data
        p_data = [
            complaints.filter(priority='High').count(),
            complaints.filter(priority='Medium').count(),
            complaints.filter(priority='Low').count()
        ]
        s_data = [
            complaints.filter(status='Pending').count(),
            complaints.filter(status='Solved').count(),
            complaints.filter(status='Closed').count()
        ]

        return render(request, 'dash_admin.html', {
            'complaints': complaints, 
            'hotspots': hotspots,
            'chart_prio': json.dumps(p_data),
            'chart_status': json.dumps(s_data)
        })
    
    # --- USER VIEW (UPDATED) ---
    else:
        complaints = Complaint.objects.filter(user=user).order_by('-created_at')
        
        # 1. Stats Calculation
        total_c = complaints.count()
        pending_c = complaints.filter(status='Pending').count()
        solved_c = complaints.filter(status='Solved').count()
        closed_c = complaints.filter(status='Closed').count()
        
        # 2. Gamification (Score: 50 points per closed complaint)
        impact_score = closed_c * 50
        
        # 3. Chart Data
        # [Pending+Solved (Active), Closed (Done)]
        active_count = pending_c + solved_c
        user_chart_data = [active_count, closed_c]

        return render(request, 'dash_user.html', {
            'complaints': complaints,
            'stats': {
                'total': total_c,
                'pending': pending_c,
                'solved': solved_c,
                'closed': closed_c,
                'score': impact_score
            },
            'chart_data': json.dumps(user_chart_data)
        })

# --- COMPLAINT ACTIONS ---
@login_required
def submit_complaint(request):
    if request.method == 'POST':
        desc = request.POST.get('description')
        loc = request.POST.get('location_name')
        pin = request.POST.get('pincode')
        img = request.FILES.get('image')
        dept, prio = ai_bot.predict(desc)
        Complaint.objects.create(user=request.user, description=desc, location_name=loc, pincode=pin, image=img, department=dept, priority=prio)
    return redirect('dashboard')

@login_required
def mark_solved(request, id):
    c = get_object_or_404(Complaint, id=id)
    if request.user.is_department_admin and request.user.department_name == c.department:
        c.status = 'Solved'
        c.save()
    return redirect('dashboard')

@login_required
def verify_close(request, id):
    c = get_object_or_404(Complaint, id=id)
    if c.user == request.user:
        c.status = 'Closed'
        c.save()
    return redirect('dashboard')

@login_required
def reopen_complaint(request, id):
    c = get_object_or_404(Complaint, id=id)
    if c.user == request.user:
        c.status = 'Pending'
        c.save()
    return redirect('dashboard')

@login_required
def transfer_complaint(request, id):
    if request.method == 'POST':
        c = get_object_or_404(Complaint, id=id)
        if request.user.is_department_admin and request.user.department_name == c.department:
            new_dept = request.POST.get('new_department')
            if new_dept:
                c.department = new_dept
                c.save()
    return redirect('dashboard')

@login_required
def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})