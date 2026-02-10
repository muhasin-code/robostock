from django.shortcuts import render, get_object_or_404, redirect
from .models import Component, Transaction, Beneficiary
from .forms import CheckoutForm, ComponentForm, BeneficiaryForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .forms import UserForm, BeneficiaryProfileForm
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages

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
@user_passes_test(is_admin_or_staff)
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
@user_passes_test(is_admin_or_staff)
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
@user_passes_test(is_admin_or_staff)
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
        
        messages.success(request, f"Returned {transaction.quantity_taken} of {component.name} from {transaction.borrower.name}")
        return redirect('component_detail', pk=component.pk)
    
    return render(request, 'inventory/return_confirm.html', {'transaction': transaction})

@login_required
@user_passes_test(is_admin_or_staff)
def beneficiary_list(request):
    beneficiaries = Beneficiary.objects.all()
    return render(request, 'inventory/beneficiary_list.html', {'beneficiaries': beneficiaries})

@login_required
@user_passes_test(is_admin_or_staff)
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
    return render(request, 'inventory/beneficiary_form.html', {'form': form})


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
@user_passes_test(is_admin_or_staff)
def beneficiary_detail(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    transactions = Transaction.objects.filter(borrower=beneficiary).order_by('-checkout_time')
    return render(request, 'inventory/beneficiary_detail.html', {'beneficiary': beneficiary, 'transactions': transactions})


@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().order_by('username')
    return render(request, 'inventory/user_list.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def add_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect('user_list')
    else:
        form = UserCreationForm()
    return render(request, 'inventory/user_form.html', {'form': form, 'title': 'Add User'})


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
