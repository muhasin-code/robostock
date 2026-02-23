from django.shortcuts import render, get_object_or_404, redirect
from .models import Component, Transaction, Beneficiary, Category
from .forms import CheckoutForm, ComponentForm, BeneficiaryForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .forms import UserForm, BeneficiaryProfileForm
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from .forms import CheckoutForm, ComponentForm, BeneficiaryForm, EnhancedUserCreationForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST

def is_admin(user):
    return user.is_superuser

def dashboard(request):
    query = request.GET.get('q')
    if query:
        components = Component.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) | 
            Q(category__name__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(box_number__icontains=query)
        )
    else:
        components = Component.objects.all()
    
    context = {
        'components': components,
        'query': query,
    }
    return render(request, 'inventory/dashboard.html', context)

def component_detail(request, pk):
    component = get_object_or_404(Component, pk=pk)
    # Get active transactions (not returned yet)
    active_transactions = Transaction.objects.filter(component=component, return_time__isnull=True)
    return render(request, 'inventory/component_detail.html', {
        'component': component,
        'active_transactions': active_transactions
    })

def is_admin_or_staff(user):
    return user.is_superuser or user.is_staff

@login_required
def add_component(request):
    if request.method == 'POST':
        form = ComponentForm(request.POST, request.FILES)
        if form.is_valid():
            component = form.save()
            messages.success(request, f"Component '{component.name}' created successfully.")
            return redirect('component_detail', pk=component.pk)
    else:
        form = ComponentForm()
    return render(request, 'inventory/component_form.html', {'form': form, 'title': 'Add Component'})

@login_required
def edit_component(request, pk):
    component = get_object_or_404(Component, pk=pk)
    if request.method == 'POST':
        form = ComponentForm(request.POST, request.FILES, instance=component)
        if form.is_valid():
            form.save()
            messages.success(request, f"Component '{component.name}' updated successfully.")
            return redirect('component_detail', pk=component.pk)
    else:
        form = ComponentForm(instance=component)
    return render(request, 'inventory/component_form.html', {'form': form, 'title': 'Edit Component', 'component': component})


@login_required
@user_passes_test(is_admin_or_staff)
def delete_component(request, pk):
    component = get_object_or_404(Component, pk=pk)
    if request.method == 'POST':
        name = component.name
        component.delete()
        messages.success(request, f"Component '{name}' deleted successfully.")
        return redirect('dashboard')
    return render(request, 'inventory/component_confirm_delete.html', {'component': component})

@login_required
def checkout_component(request, pk):
    component = get_object_or_404(Component, pk=pk)
    if request.method == 'POST':
        form = CheckoutForm(request.POST, component=component)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.component = component
            transaction.authorized_by = request.user
            transaction.save()
            
            # Decrease quantity
            component.quantity -= transaction.quantity_taken
            component.save()
            
            # Send email notification if borrower has email
            if transaction.borrower.email:
                try:
                    subject = f"RoboStock: Component Checkout Notification - {component.name}"
                    message = f"""
Hello {transaction.borrower.name},

You have successfully checked out an item from the RoboStock Laboratory Inventory.

Details:
- Component: {component.name}
- Quantity: {transaction.quantity_taken}
- Checkout Time: {transaction.checkout_time.strftime('%Y-%m-%d %H:%M:%S')}
- Authorized By: {request.user.get_full_name() or request.user.username}

Please ensure the items are returned in good condition.

Best regards,
RoboStock Lab Management
                    """
                    send_mail(
                        subject,
                        message,
                        None, # Uses DEFAULT_FROM_EMAIL
                        [transaction.borrower.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Error sending email: {e}")

            messages.success(request, f"Checked out {transaction.quantity_taken} of {component.name} to {transaction.borrower.name}")
            return redirect('component_detail', pk=pk)
    else:
        form = CheckoutForm(component=component)
    
    context = {
        'form': form,
        'component': component,
        'current_date': timezone.now()
    }
    return render(request, 'inventory/checkout_form.html', context)

@login_required
def return_component(request, transaction_id):
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    if transaction.return_time:
        messages.warning(request, "This item has already been returned.")
        return redirect('component_detail', pk=transaction.component.pk)
        
    if request.method == 'POST':
        transaction.return_time = timezone.now()
        transaction.save()
        
        # Increase quantity back
        component = transaction.component
        component.quantity += transaction.quantity_taken
        component.save()
        
        # Send email notification if borrower has email
        if transaction.borrower.email:
            try:
                subject = f"RoboStock: Component Return Confirmation - {component.name}"
                message = f"""
Hello {transaction.borrower.name},

This email confirms that you have successfully returned the following item to the RoboStock Laboratory Inventory.

Details:
- Component: {component.name}
- Quantity Returned: {transaction.quantity_taken}
- Return Time: {transaction.return_time.strftime('%Y-%m-%d %H:%M:%S')}
- Processed By: {request.user.get_full_name() or request.user.username}

Thank you for returning the items on time.

Best regards,
RoboStock Lab Management
                """
                send_mail(
                    subject,
                    message,
                    None, # Uses DEFAULT_FROM_EMAIL
                    [transaction.borrower.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Error sending return email: {e}")

        messages.success(request, f"Returned {transaction.quantity_taken} of {component.name} from {transaction.borrower.name}")
        return redirect('component_detail', pk=component.pk)
    
    return render(request, 'inventory/return_confirm.html', {'transaction': transaction})

@login_required
def beneficiary_list(request):
    beneficiaries = Beneficiary.objects.all()
    return render(request, 'inventory/beneficiary_list.html', {'beneficiaries': beneficiaries})

@login_required
def add_beneficiary(request):
    if request.method == 'POST':
        form = BeneficiaryForm(request.POST)
        if form.is_valid():
            beneficiary = form.save(commit=False)
            beneficiary.added_by = request.user
            beneficiary.save()
            messages.success(request, f"Beneficiary '{beneficiary.name}' added successfully.")
            return redirect('beneficiary_list')
    else:
        form = BeneficiaryForm()
    return render(request, 'inventory/beneficiary_form.html', {'form': form, 'title': 'Add Beneficiary'})


@login_required
@user_passes_test(is_admin_or_staff)
def edit_beneficiary(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    if request.method == 'POST':
        form = BeneficiaryForm(request.POST, instance=beneficiary)
        if form.is_valid():
            form.save()
            messages.success(request, f"Beneficiary '{beneficiary.name}' updated successfully.")
            return redirect('beneficiary_detail', pk=beneficiary.pk)
    else:
        form = BeneficiaryForm(instance=beneficiary)
    return render(request, 'inventory/beneficiary_form.html', {'form': form, 'title': 'Edit Beneficiary', 'beneficiary': beneficiary})


@login_required
@user_passes_test(is_admin_or_staff)
def delete_beneficiary(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    if request.method == 'POST':
        name = beneficiary.name
        beneficiary.delete()
        messages.success(request, f"Beneficiary '{name}' deleted successfully.")
        return redirect('beneficiary_list')
    return render(request, 'inventory/beneficiary_confirm_delete.html', {'beneficiary': beneficiary})


@login_required
def edit_profile(request):
    user = request.user
    # Ensure beneficiary exists for this user
    try:
        beneficiary = user.beneficiary
    except Beneficiary.DoesNotExist:
        beneficiary = Beneficiary.objects.create(
            user=user,
            name=user.get_full_name() or user.username,
            email=user.email,
            phone_number='')

    if request.method == 'POST':
        uform = UserForm(request.POST, instance=user)
        bform = BeneficiaryProfileForm(request.POST, request.FILES, instance=beneficiary)
        if uform.is_valid() and bform.is_valid():
            uform.save()
            b = bform.save(commit=False)
            # Update display name
            parts = [user.first_name]
            if b.middle_name:
                parts.append(b.middle_name)
            parts.append(user.last_name)
            b.name = ' '.join([p for p in parts if p]) or user.username
            b.user = user
            b.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('dashboard')
    else:
        uform = UserForm(instance=user)
        bform = BeneficiaryProfileForm(instance=beneficiary)

    return render(request, 'inventory/profile_form.html', {'uform': uform, 'bform': bform})


@login_required
def checkout_self(request, pk):
    component = get_object_or_404(Component, pk=pk)
    user = request.user
    try:
        beneficiary = user.beneficiary
    except Beneficiary.DoesNotExist:
        beneficiary = Beneficiary.objects.create(
            user=user,
            name=user.get_full_name() or user.username,
            email=user.email,
            phone_number='')

    if request.method == 'POST':
        form = CheckoutForm(request.POST, component=component)
        # restrict borrower choices
        form.fields['borrower'].queryset = Beneficiary.objects.filter(pk=beneficiary.pk)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.component = component
            transaction.authorized_by = user
            transaction.save()
            component.quantity -= transaction.quantity_taken
            component.save()
            messages.success(request, f"Checked out {transaction.quantity_taken} of {component.name} to {transaction.borrower.name}")
            return redirect('component_detail', pk=pk)
    else:
        form = CheckoutForm(component=component, initial={'borrower': beneficiary.pk})
        form.fields['borrower'].queryset = Beneficiary.objects.filter(pk=beneficiary.pk)
        form.fields['borrower'].widget.attrs.update({'class': 'form-select'})

    return render(request, 'inventory/checkout_form.html', {'form': form, 'component': component, 'current_date': timezone.now()})

@login_required
def beneficiary_detail(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    transactions = Transaction.objects.filter(borrower=beneficiary).order_by('-checkout_time')
    return render(request, 'inventory/beneficiary_detail.html', {'beneficiary': beneficiary, 'transactions': transactions})


@login_required
def get_beneficiary_data(request, employee_id):
    """AJAX endpoint to fetch beneficiary data by employee_id or student_id."""
    # Note: employee_id is the URL parameter name, but we use it as a generic search_id
    search_id = employee_id
    try:
        beneficiary = Beneficiary.objects.filter(
            Q(employee_id=search_id) | Q(student_id=search_id)
        ).first()
        
        if not beneficiary:
            return JsonResponse({'exists': False})

        # Try to parse name into first and last
        name_parts = beneficiary.name.split(' ')
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        return JsonResponse({
            'exists': True,
            'name': beneficiary.name,
            'first_name': first_name,
            'last_name': last_name,
            'email': beneficiary.email,
            'designation': beneficiary.designation,
            'category': beneficiary.category,
        })
    except Exception as e:
        return JsonResponse({'exists': False, 'error': str(e)})

@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().order_by('username')
    return render(request, 'inventory/user_list.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def add_user(request):
    if request.method == 'POST':
        form = EnhancedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            # Check if beneficiary exists for this employee_id
            employee_id = form.cleaned_data.get('employee_id')
            beneficiary = None
            if employee_id:
                beneficiary = Beneficiary.objects.filter(employee_id=employee_id).first()
                if beneficiary:
                    beneficiary.user = user
                    beneficiary.designation = form.cleaned_data.get('designation')
                    beneficiary.save()
            
            if not beneficiary:
                # Create new beneficiary
                Beneficiary.objects.create(
                    user=user,
                    employee_id=employee_id,
                    category='Employee',
                    name=user.get_full_name(),
                    email=user.email,
                    designation=form.cleaned_data.get('designation'),
                    phone_number='', # Default
                    added_by=request.user
                )
                
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect('user_list')
    else:
        form = EnhancedUserCreationForm()
    return render(request, 'inventory/user_form.html', {'form': form, 'title': 'Add User'})


@login_required
@require_POST
def add_category(request):
    """AJAX endpoint — creates a Category and returns {id, name}."""
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Name is required.'}, status=400)
    category, created = Category.objects.get_or_create(name=name)
    if not created:
        return JsonResponse({'error': f"Category '{name}' already exists.", 'id': category.pk, 'name': category.name}, status=200)
    return JsonResponse({'id': category.pk, 'name': category.name}, status=201)


@login_required
@user_passes_test(is_admin)
def category_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'inventory/category_list.html', {'categories': categories})


@login_required
@user_passes_test(is_admin)
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f"Category '{name}' deleted.")
        return redirect('category_list')
    return render(request, 'inventory/category_confirm_delete.html', {'category': category})


@login_required
@user_passes_test(is_admin)
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if user.username == request.user.username:
            messages.error(request, "You cannot delete your own account while logged in.")
            return redirect('user_list')
        user.delete()
        messages.success(request, f"User '{user.username}' deleted.")
        return redirect('user_list')
    return render(request, 'inventory/user_confirm_delete.html', {'user_obj': user})
