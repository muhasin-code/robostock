from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('component/<int:pk>/', views.component_detail, name='component_detail'),
    path('checkout/<int:pk>/', views.checkout_component, name='checkout_component'),
    path('return/<int:transaction_id>/', views.return_component, name='return_component'),
    path('component/add/', views.add_component, name='add_component'),
    path('component/<int:pk>/edit/', views.edit_component, name='edit_component'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('profile/', views.edit_profile, name='edit_profile'),
    path('checkout/self/<int:pk>/', views.checkout_self, name='checkout_self'),
    path('beneficiaries/', views.beneficiary_list, name='beneficiary_list'),
    path('beneficiary/add/', views.add_beneficiary, name='add_beneficiary'),
    path('beneficiary/<int:pk>/', views.beneficiary_detail, name='beneficiary_detail'),
]
