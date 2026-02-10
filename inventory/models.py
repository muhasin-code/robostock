from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Component(models.Model):
    serial_number = models.CharField(max_length=100, unique=True, help_text="Unique identifier for this component")
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='components')
    description = models.TextField(blank=True)
    box_number = models.CharField(max_length=50, null=True, blank=True)
    datasheet_link = models.URLField(blank=True)
    quantity = models.IntegerField(default=0)
    location = models.CharField(max_length=100) # Keep for general location or legacy
    image = models.ImageField(upload_to='components/', blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Beneficiary(models.Model):
    CATEGORY_CHOICES = [
        ('Employee', 'Employee'),
        ('Student', 'Student'),
        ('Intern', 'Intern'),
        ('Other', 'Other'),
    ]
    
    STREAM_CHOICES = [
        ('BCA', 'BCA'),
        ('AI & Robotics', 'AI & Robotics'),
    ]
    
    # Category and identifiers
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    stream = models.CharField(max_length=50, choices=STREAM_CHOICES, blank=True, null=True)
    student_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Link to auth user (optional)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, null=True, blank=True, related_name='beneficiary')

    # Basic information
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    middle_name = models.CharField(max_length=50, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Legacy field (kept for compatibility)
    role = models.CharField(max_length=50, blank=True)
    
    added_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='added_beneficiaries')
    
    class Meta:
        verbose_name_plural = "Beneficiaries"

    def __str__(self):
        return f"{self.name} ({self.category})"

class Transaction(models.Model):
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    borrower = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, null=True)
    authorized_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    checkout_time = models.DateTimeField(auto_now_add=True)
    return_time = models.DateTimeField(null=True, blank=True)
    quantity_taken = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.borrower.name} - {self.component.name}"
