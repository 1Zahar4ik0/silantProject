from allauth.account.views import SignupView
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from service import views, api

router = DefaultRouter()
router.register('machines', api.MachineViewSet, basename='api-machine')
router.register('maintenances', api.MaintenanceViewSet, basename='api-maintenance')
router.register('claims', api.ClaimViewSet, basename='api-claim')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', LoginView.as_view(template_name='registration/login.html'), name='account_login'),
    path('accounts/logout/', LogoutView.as_view(), name='account_logout'),
    path('accounts/signup/', SignupView.as_view(), name='account_signup'),
    path('', views.home, name='home'),
    path('public/machines/<str:number>/', views.public_machine, name='public_machine'),
    path('directories/', views.directories, name='directories'),
    path('directories/add/', views.edit_directory, name='directory_add'),
    path('directories/<int:pk>/edit/', views.edit_directory, name='directory_edit'),
    path('records/<str:section>/', views.records, name='records'),
    path('records/<str:section>/add/', views.edit_record, name='record_add'),
    path('records/<str:section>/<int:pk>/', views.detail, name='detail'),
    path('records/<str:section>/<int:pk>/edit/', views.edit_record, name='record_edit'),
    path('api/docs/', TemplateView.as_view(template_name='service/api_docs.html'), name='api_docs'),
    path('api/', include(router.urls)),
]
