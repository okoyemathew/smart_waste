from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache

from .models import (
    Complaint,
    Worker,
    Assignment,
    RecyclingCenter,
    UserNotification,
    WasteCategory,
)


def landing(request):
    return render(request, 'landing.html')


@never_cache
def register(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Account created successfully!")
        return redirect('login')

    return render(request, 'register.html')


@never_cache
def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if not user and username:
            matched_user = User.objects.filter(username__iexact=username).first()
            if matched_user:
                user = authenticate(request, username=matched_user.username, password=password)

        if user:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            if Worker.objects.filter(user=user).exists():
                return redirect('worker_dashboard')
            return redirect('dashboard')

        messages.error(request, "Invalid username or password")

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
@never_cache
def dashboard(request):
    total = Complaint.objects.filter(user=request.user).count()
    pending = Complaint.objects.filter(user=request.user, status="Pending").count()
    cleaned = Complaint.objects.filter(user=request.user, status="Cleaned").count()
    notifications = UserNotification.objects.filter(user=request.user)[:5]

    return render(request, 'dashboard.html', {
        'total': total,
        'pending': pending,
        'cleaned': cleaned,
        'notifications': notifications
    })


@login_required
@never_cache
def submit_complaint(request):
    if request.method == "POST":
        waste_type_id = request.POST.get('waste_type')
        location = request.POST.get('location')
        description = request.POST.get('description')
        image = request.FILES.get('image')

        if not image:
            messages.error(request, "Please upload an image of the waste.")
            return redirect('complaint')

        waste_type = get_object_or_404(WasteCategory, id=waste_type_id)

        complaint = Complaint.objects.create(
            user=request.user,
            waste_type=waste_type,
            location=location,
            description=description,
            image=image
        )

        if waste_type.default_center:
            complaint.recycling_center = waste_type.default_center
            complaint.save(update_fields=['recycling_center'])

        if waste_type.default_worker and waste_type.default_center:
            Assignment.objects.update_or_create(
                complaint=complaint,
                defaults={
                    'worker': waste_type.default_worker,
                    'recycling_center': waste_type.default_center,
                },
            )

        messages.success(request, "Complaint submitted successfully!")
        return redirect('dashboard')

    waste_types = WasteCategory.objects.all().order_by('name')
    return render(request, 'complaint.html', {'waste_types': waste_types})


@login_required
@never_cache
def view_complaints(request):
    complaints = Complaint.objects.filter(user=request.user)
    return render(request, 'view_complaints.html', {'complaints': complaints})


@login_required
@never_cache
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    complaints = Complaint.objects.select_related('waste_type', 'user', 'recycling_center').all()
    workers = Worker.objects.select_related('user').all()
    centers = RecyclingCenter.objects.all()
    waste_categories = WasteCategory.objects.select_related('default_worker__user', 'default_center').all()
    notified_ids = set(UserNotification.objects.values_list('complaint_id', flat=True))

    assignment_map = {
        a.complaint_id: a
        for a in Assignment.objects.select_related('worker__user', 'recycling_center').all()
    }

    for complaint in complaints:
        complaint.user_update_sent = complaint.id in notified_ids
        complaint.current_assignment = assignment_map.get(complaint.id)

    return render(request, 'admin_dashboard.html', {
        'complaints': complaints,
        'workers': workers,
        'centers': centers,
        'waste_categories': waste_categories,
    })


@login_required
@require_POST
def add_worker(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    phone = request.POST.get('phone', '').strip()

    if not username or not password or not phone:
        messages.error(request, "Username, password, and phone are required.")
        return redirect('admin_dashboard')

    if User.objects.filter(username=username).exists():
        messages.error(request, "This username already exists.")
        return redirect('admin_dashboard')

    user = User.objects.create_user(username=username, email=email, password=password)
    Worker.objects.create(user=user, phone=phone)
    messages.success(request, f"Worker account created for {username}.")
    return redirect('admin_dashboard')


@login_required
@require_POST
def add_recycling_center(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    name = request.POST.get('name', '').strip()
    location = request.POST.get('location', '').strip()

    if not name or not location:
        messages.error(request, "Center name and location are required.")
        return redirect('admin_dashboard')

    RecyclingCenter.objects.create(name=name, location=location)
    messages.success(request, f"Recycling center '{name}' added.")
    return redirect('admin_dashboard')


@login_required
@require_POST
def delete_worker(request, worker_id):
    if not request.user.is_superuser:
        return redirect('dashboard')

    worker = get_object_or_404(Worker.objects.select_related('user'), id=worker_id)
    username = worker.user.username
    worker.user.delete()
    messages.success(request, f"Worker '{username}' removed.")
    return redirect('admin_dashboard')


@login_required
@require_POST
def delete_recycling_center(request, center_id):
    if not request.user.is_superuser:
        return redirect('dashboard')

    center = get_object_or_404(RecyclingCenter, id=center_id)
    center_name = center.name
    center.delete()
    messages.success(request, f"Recycling center '{center_name}' removed.")
    return redirect('admin_dashboard')


@login_required
@require_POST
def add_waste_category(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    name = request.POST.get('name', '').strip()
    default_worker_id = request.POST.get('default_worker')
    default_center_id = request.POST.get('default_center')

    if not name:
        messages.error(request, "Waste category name is required.")
        return redirect('admin_dashboard')

    if WasteCategory.objects.filter(name__iexact=name).exists():
        messages.error(request, "This waste category already exists.")
        return redirect('admin_dashboard')

    default_worker = Worker.objects.filter(id=default_worker_id).first() if default_worker_id else None
    default_center = RecyclingCenter.objects.filter(id=default_center_id).first() if default_center_id else None

    WasteCategory.objects.create(
        name=name,
        default_worker=default_worker,
        default_center=default_center,
    )
    messages.success(request, f"Waste category '{name}' created.")
    return redirect('admin_dashboard')


@login_required
@require_POST
def update_waste_category(request, category_id):
    if not request.user.is_superuser:
        return redirect('dashboard')

    category = get_object_or_404(WasteCategory, id=category_id)

    name = request.POST.get('name', '').strip()
    default_worker_id = request.POST.get('default_worker')
    default_center_id = request.POST.get('default_center')

    if not name:
        messages.error(request, "Waste category name is required.")
        return redirect('admin_dashboard')

    duplicate = WasteCategory.objects.filter(name__iexact=name).exclude(id=category.id).exists()
    if duplicate:
        messages.error(request, "Another waste category already uses this name.")
        return redirect('admin_dashboard')

    default_worker = Worker.objects.filter(id=default_worker_id).first() if default_worker_id else None
    default_center = RecyclingCenter.objects.filter(id=default_center_id).first() if default_center_id else None

    category.name = name
    category.default_worker = default_worker
    category.default_center = default_center
    category.save()

    messages.success(request, f"Waste category '{name}' updated.")
    return redirect('admin_dashboard')


@login_required
@require_POST
def delete_waste_category(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    category_id = request.POST.get('category_id')
    if not category_id:
        messages.error(request, "Please select a waste category to remove.")
        return redirect('admin_dashboard')

    category = get_object_or_404(WasteCategory, id=category_id)
    linked_count = Complaint.objects.filter(waste_type=category).update(waste_type=None)
    name = category.name
    category.delete()
    if linked_count:
        messages.success(
            request,
            f"Waste category '{name}' removed. {linked_count} complaint(s) moved to Uncategorized."
        )
    else:
        messages.success(request, f"Waste category '{name}' removed.")
    return redirect('admin_dashboard')


@login_required
@require_POST
def assign_worker(request, complaint_id):
    if not request.user.is_superuser:
        return redirect('dashboard')

    worker_id = request.POST.get('worker')
    center_id = request.POST.get('center')
    status = request.POST.get('status')

    if status not in {"Pending", "Cleaned"}:
        messages.error(request, "Invalid status selected.")
        return redirect('admin_dashboard')

    complaint = get_object_or_404(Complaint, id=complaint_id)
    worker = get_object_or_404(Worker, id=worker_id)
    center = get_object_or_404(RecyclingCenter, id=center_id)

    Assignment.objects.update_or_create(
        complaint=complaint,
        defaults={'worker': worker, 'recycling_center': center}
    )

    complaint.recycling_center = center
    complaint.status = status
    complaint.save()

    messages.success(request, "Worker assigned successfully!")
    return redirect('admin_dashboard')


@login_required
@require_POST
def clear_complaints(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    Complaint.objects.all().delete()
    messages.success(request, "All complaints cleared!")
    return redirect('admin_dashboard')


@login_required
@require_POST
def notify_user(request, complaint_id):
    if not request.user.is_superuser:
        return redirect('dashboard')

    complaint = get_object_or_404(Complaint, id=complaint_id)

    if complaint.status != "Cleaned":
        messages.error(request, "User can be updated only after the task is cleaned.")
        return redirect('admin_dashboard')

    waste_name = complaint.waste_type.name if complaint.waste_type else "waste"
    message = (
        f"Your waste complaint for {waste_name} at "
        f"{complaint.location} has been cleaned."
    )

    UserNotification.objects.update_or_create(
        user=complaint.user,
        complaint=complaint,
        defaults={'message': message, 'is_read': False}
    )

    messages.success(request, "User updated successfully!")
    return redirect('admin_dashboard')


@login_required
@never_cache
def worker_dashboard(request):
    try:
        worker = Worker.objects.get(user=request.user)
        assignments = Assignment.objects.filter(worker=worker).select_related('complaint__waste_type')
    except Worker.DoesNotExist:
        assignments = []

    return render(request, 'worker_dashboard.html', {'assignments': assignments})


@login_required
@require_POST
def update_status(request, complaint_id):
    try:
        worker = Worker.objects.get(user=request.user)
    except Worker.DoesNotExist:
        messages.error(request, "Only workers can update assigned complaints.")
        return redirect('worker_dashboard')

    complaint = get_object_or_404(Complaint, id=complaint_id)

    if not Assignment.objects.filter(complaint=complaint, worker=worker).exists():
        messages.error(request, "Not authorized!")
        return redirect('worker_dashboard')

    complaint.status = "Cleaned"
    complaint.save()

    waste_name = complaint.waste_type.name if complaint.waste_type else "waste"
    message = (
        f"Your waste complaint for {waste_name} at "
        f"{complaint.location} has been cleaned."
    )
    UserNotification.objects.update_or_create(
        user=complaint.user,
        complaint=complaint,
        defaults={'message': message, 'is_read': False}
    )

    messages.success(request, "Status updated successfully!")
    return redirect('worker_dashboard')


@login_required
@require_POST
def clear_citizen_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if complaint.user != request.user:
        messages.error(request, "Not authorized!")
        return redirect('my_complaints')

    if complaint.status != "Cleaned":
        messages.error(request, "Only completed complaints can be cleared.")
        return redirect('my_complaints')

    complaint.is_cleared = True
    complaint.save()

    messages.success(request, "Complaint cleared successfully!")
    return redirect('my_complaints')


@login_required
@require_POST
def clear_worker_complaint(request, complaint_id):
    try:
        worker = Worker.objects.get(user=request.user)
    except Worker.DoesNotExist:
        messages.error(request, "Only workers can clear complaints.")
        return redirect('worker_dashboard')

    complaint = get_object_or_404(Complaint, id=complaint_id)

    if not Assignment.objects.filter(complaint=complaint, worker=worker).exists():
        messages.error(request, "Not authorized!")
        return redirect('worker_dashboard')

    if complaint.status != "Cleaned":
        messages.error(request, "Only completed complaints can be cleared.")
        return redirect('worker_dashboard')

    complaint.is_cleared = True
    complaint.save()

    messages.success(request, "Complaint cleared successfully!")
    return redirect('worker_dashboard')
