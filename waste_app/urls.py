from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('complaint/', views.submit_complaint, name='complaint'),
    path('my-complaints/', views.view_complaints, name='my_complaints'),
    path('clear-complaint/<int:complaint_id>/', views.clear_citizen_complaint, name='clear_citizen_complaint'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/add-worker/', views.add_worker, name='add_worker'),
    path('admin-dashboard/add-center/', views.add_recycling_center, name='add_recycling_center'),
    path('admin-dashboard/delete-worker/<int:worker_id>/', views.delete_worker, name='delete_worker'),
    path('admin-dashboard/delete-center/<int:center_id>/', views.delete_recycling_center, name='delete_recycling_center'),
    path('admin-dashboard/add-waste-category/', views.add_waste_category, name='add_waste_category'),
    path('admin-dashboard/update-waste-category/<int:category_id>/', views.update_waste_category, name='update_waste_category'),
    path('admin-dashboard/delete-waste-category/', views.delete_waste_category, name='delete_waste_category'),
    path('assign/<int:complaint_id>/', views.assign_worker, name='assign_worker'),
    path('notify-user/<int:complaint_id>/', views.notify_user, name='notify_user'),
    path('clear-complaints/', views.clear_complaints, name='clear_complaints'),
    path('worker-dashboard/', views.worker_dashboard, name='worker_dashboard'),
    path('update-status/<int:complaint_id>/', views.update_status, name='update_status'),
    path('clear-worker-complaint/<int:complaint_id>/', views.clear_worker_complaint, name='clear_worker_complaint'),
]




