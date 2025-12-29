from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Value, IntegerField, Count
from .models import User, Complaint
from .ai_model.engine import ai_bot

# =========================================
# 1. AUTHENTICATION (Login & Signup)
# =========================================
def auth_view(request):
    # If user is already logged in, send them to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # --- LOGIN LOGIC ---
        if action == 'login':
            u = request.POST.get('username')
            p = request.POST.get('password')
            
            user = authenticate(username=u, password=p)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'auth.html', {'error': 'Invalid Username or Password'})
        
        # --- SIGNUP LOGIC ---
        elif action == 'signup':
            try:
                # Fetch all fields from the form
                role = request.POST.get('role')
                u = request.POST.get('username')
                p = request.POST.get('password')
                phone = request.POST.get('phone')
                city = request.POST.get('city')
                aadhar = request.POST.get('aadhar')
                address = request.POST.get('address')
                gender = request.POST.get('gender')
                dob = request.POST.get('dob')
                
                # Create Admin User
                if role == 'admin':
                    dept = request.POST.get('department')
                    user = User.objects.create_user(
                        username=u, password=p, 
                        is_department_admin=True, department_name=dept,
                        phone=phone, city=city, aadhar_id=aadhar, 
                        address=address, gender=gender, dob=dob
                    )
                # Create Citizen User
                else:
                    user = User.objects.create_user(
                        username=u, password=p, 
                        is_department_admin=False,
                        phone=phone, city=city, aadhar_id=aadhar, 
                        address=address, gender=gender, dob=dob
                    )
                
                login(request, user)
                return redirect('dashboard')

            except Exception as e:
                # Handle duplicate username or other errors
                return render(request, 'auth.html', {'error': f'Signup Failed: {e}'})

    return render(request, 'auth.html')

def logout_view(request):
    logout(request)
    return redirect('auth')


# =========================================
# 2. DASHBOARD (Admin & User Logic)
# =========================================
# @login_required
# def dashboard_view(request):
#     user = request.user
    
#     # Custom Sorting: High(1) > Medium(2) > Low(3)
#     priority_order = Case(
#         When(priority='High', then=Value(1)),
#         When(priority='Medium', then=Value(2)),
#         When(priority='Low', then=Value(3)),
#         output_field=IntegerField(),
#     )

#     # --- ADMIN VIEW ---
#     if user.is_department_admin:
#         # 1. Get Complaints for specific department
#         complaints = Complaint.objects.filter(department=user.department_name).annotate(
#             sort=priority_order
#         ).order_by('sort', '-created_at')

#         # 2. Calculate Hotspots (Red Zones)
#         hotspots = Complaint.objects.filter(department=user.department_name) \
#             .values('pincode', 'location_name') \
#             .annotate(total=Count('id')) \
#             .order_by('-total')[:5]

#         return render(request, 'dash_admin.html', {
#             'complaints': complaints, 
#             'hotspots': hotspots
#         })
    
#     # --- USER VIEW ---
#     else:
#         complaints = Complaint.objects.filter(user=user).order_by('-created_at')
#         return render(request, 'dash_user.html', {'complaints': complaints})


# core/views.py (Sirf dashboard_view replace karo)

@login_required
def dashboard_view(request):
    user = request.user
    
    # --- JADUI SORTING LOGIC (High Upar, Low Niche) ---
    priority_order = Case(
        When(priority='High', then=Value(1)),
        When(priority='Medium', then=Value(2)),
        When(priority='Low', then=Value(3)),
        output_field=IntegerField(),
    )
    # --------------------------------------------------

    if user.is_department_admin:
        # Admin View: Dept match karo + Priority Wise Sort karo
        complaints = Complaint.objects.filter(department=user.department_name).annotate(
            sort_val=priority_order
        ).order_by('sort_val', '-created_at') 
        # 'sort_val' (Priority) pehle, fir '-created_at' (Newest first)

        hotspots = Complaint.objects.filter(department=user.department_name) \
            .values('pincode', 'location_name') \
            .annotate(total=Count('id')) \
            .order_by('-total')[:5]

        return render(request, 'dash_admin.html', {
            'complaints': complaints, 
            'hotspots': hotspots
        })
    else:
        # User View: Sirf date wise
        complaints = Complaint.objects.filter(user=user).order_by('-created_at')
        return render(request, 'dash_user.html', {'complaints': complaints})
# =========================================
# 3. COMPLAINT ACTIONS (The Logic)
# =========================================
@login_required
def submit_complaint(request):
    if request.method == 'POST':
        desc = request.POST.get('description')
        loc = request.POST.get('location_name')
        pin = request.POST.get('pincode')
        img = request.FILES.get('image')
        
        # AI PREDICTION
        dept, prio = ai_bot.predict(desc)
        
        Complaint.objects.create(
            user=request.user, description=desc, 
            location_name=loc, pincode=pin, image=img, 
            department=dept, priority=prio
        )
        return redirect('dashboard')
    return redirect('dashboard')

@login_required
def mark_solved(request, id):
    """ Admin marks issue as Solved (Waiting for User) """
    c = get_object_or_404(Complaint, id=id)
    if request.user.is_department_admin and request.user.department_name == c.department:
        c.status = 'Solved'
        c.save()
    return redirect('dashboard')

@login_required
def verify_close(request, id):
    """ User verifies and Closes the issue permanently """
    c = get_object_or_404(Complaint, id=id)
    if c.user == request.user:
        c.status = 'Closed'
        c.save()
    return redirect('dashboard')

@login_required
def reopen_complaint(request, id):
    """ User is not satisfied, reopens ticket to Pending """
    c = get_object_or_404(Complaint, id=id)
    if c.user == request.user:
        c.status = 'Pending'
        c.save()
    return redirect('dashboard')


# =========================================
# 4. EXTRAS
# =========================================
@login_required
def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})