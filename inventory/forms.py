from django import forms
from .models import Transaction, Component, Beneficiary
from django.contrib.auth.models import User
from django import forms

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['borrower', 'quantity_taken']
        widgets = {
            'borrower': forms.Select(attrs={'class': 'form-select'}),
            'quantity_taken': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        self.component = kwargs.pop('component', None)
        super().__init__(*args, **kwargs)

    def clean_quantity_taken(self):
        quantity = self.cleaned_data['quantity_taken']
        if self.component and quantity > self.component.quantity:
            raise forms.ValidationError(f"Only {self.component.quantity} items available.")
        return quantity

class ComponentForm(forms.ModelForm):
    class Meta:
        model = Component
        fields = ['serial_number', 'name', 'category', 'box_number', 'quantity', 'image', 'description']
        widgets = {
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., SN12345'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Ultrasonic Sensor HC-SR04'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'box_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Box A1 or Shelf 3'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': '0'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional: Add any additional details about this component...'}),
        }
        help_texts = {
            'category': 'Select a category or add a new one from the admin panel if needed.',
        }

class BeneficiaryForm(forms.ModelForm):
    class Meta:
        model = Beneficiary
        fields = ['category', 'employee_id', 'stream', 'student_id', 'name', 'phone_number', 'email']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'id_category'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Employee ID'}),
            'stream': forms.Select(attrs={'class': 'form-select'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Student ID'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email (optional)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields not required initially - will validate in clean()
        self.fields['employee_id'].required = False
        self.fields['stream'].required = False
        self.fields['student_id'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        
        # Validate based on category
        if category == 'Employee':
            if not cleaned_data.get('employee_id'):
                self.add_error('employee_id', 'Employee ID is required for employees.')
            # Clear student fields
            cleaned_data['stream'] = None
            cleaned_data['student_id'] = None
                
        elif category == 'Student':
            if not cleaned_data.get('stream'):
                self.add_error('stream', 'Stream is required for students.')
            if not cleaned_data.get('student_id'):
                self.add_error('student_id', 'Student ID is required for students.')
            # Clear employee field
            cleaned_data['employee_id'] = None
                
        else:  # Intern or Other
            # Clear all ID fields
            cleaned_data['employee_id'] = None
            cleaned_data['stream'] = None
            cleaned_data['student_id'] = None
        
        return cleaned_data


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class BeneficiaryProfileForm(forms.ModelForm):
    class Meta:
        model = Beneficiary
        fields = ['phone_number', 'middle_name', 'designation', 'photo']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Middle name (optional)'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Student, Researcher'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
