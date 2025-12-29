from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Basic Role Flags
    is_department_admin = models.BooleanField(default=False)
    department_name = models.CharField(max_length=50, blank=True, null=True)
    
    # --- NEW DETAILED FIELDS FOR SIGNUP ---
    phone = models.CharField(max_length=15, blank=True, null=True)
    aadhar_id = models.CharField(max_length=12, blank=True, null=True) # Aadhar Number
    address = models.TextField(blank=True, null=True)                  # Full Address
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default='Male')
    dob = models.DateField(blank=True, null=True)                      # Date of Birth
    city = models.CharField(max_length=50, default="Indore")
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Solved', 'Resolved (Waiting Verification)'),
        ('Closed', 'Closed (Verified)')
    ]
    PRIORITY_CHOICES = [('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    location_name = models.CharField(max_length=200)
    pincode = models.CharField(max_length=10)
    image = models.ImageField(upload_to='complaints/', blank=True, null=True)
    
    department = models.CharField(max_length=50) 
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Low')
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pincode} - {self.description[:20]}"