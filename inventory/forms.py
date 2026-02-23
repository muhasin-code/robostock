from django import forms
from django.db.models import Q
from .models import Transaction, Component, Beneficiary
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CheckoutForm(forms.ModelForm):
    borrower_id = forms.CharField(
        required=False, 
        label="Borrower ID (Student/Employee)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ID to search...'})
    )

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
        # Filter dropdown to only include Interns and Others
        self.fields['borrower'].queryset = Beneficiary.objects.filter(category__in=['Intern', 'Other'])
        self.fields['borrower'].required = False
        self.fields['borrower'].label = "Select Borrower (Intern/Other)"
        self.fields['borrower'].empty_label = "-- Select Borrower (Intern/Other) --"
        
        if self.component:
            self.fields['quantity_taken'].widget.attrs['max'] = self.component.quantity

    def clean(self):
        cleaned_data = super().clean()
        borrower_id = cleaned_data.get('borrower_id')
        borrower = cleaned_data.get('borrower')

        if not borrower_id and not borrower:
            raise forms.ValidationError("Please provide either a Borrower ID or select a borrower from the list.")

        if borrower_id:
            # Try to find beneficiary by employee_id or student_id
            beneficiary = Beneficiary.objects.filter(
                Q(employee_id=borrower_id) | Q(student_id=borrower_id)
            ).first()
            
            if beneficiary:
                cleaned_data['borrower'] = beneficiary
            else:
                if not borrower: # Only error if dropdown is also empty
                    self.add_error('borrower_id', "No beneficiary found with this ID.")
        
        return cleaned_data

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "-- Select Category --"

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
        
        self.fields['category'].empty_label = "-- Select Category --"
        self.fields['stream'].empty_label = "-- Select Stream (For Students) --"
    
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


class EnhancedUserCreationForm(UserCreationForm):
    employee_id = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Employee ID for autocompletion'}))
    designation = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Faculty, Lab Technician'}))
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            return username
            
        import re
        if not re.match(r'^[a-z0-9\.\-_]+$', username):
            raise forms.ValidationError(
                "Username should only contain lowercase letters, numbers, dots (.), hyphens (-), and underscores (_)."
            )
        return username

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'
            else:
                if 'form-control' not in self.fields[field].widget.attrs['class']:
                    self.fields[field].widget.attrs['class'] += ' form-control'
