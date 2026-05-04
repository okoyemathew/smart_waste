from django.db import models
from django.contrib.auth.models import User


class Worker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.user.username


class RecyclingCenter(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class WasteCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    default_worker = models.ForeignKey('Worker', on_delete=models.SET_NULL, null=True, blank=True)
    default_center = models.ForeignKey('RecyclingCenter', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class Complaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    waste_type = models.ForeignKey(WasteCategory, on_delete=models.CASCADE, null=True, blank=True)
    location = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='complaints/', null=True, blank=True)
    status = models.CharField(max_length=50, default='Pending')
    recycling_center = models.ForeignKey(
        RecyclingCenter, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_cleared = models.BooleanField(default=False)

    def __str__(self):
        return self.waste_type.name if self.waste_type else 'Uncategorized'


class Assignment(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    recycling_center = models.ForeignKey(RecyclingCenter, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.complaint} -> {self.worker}"


class UserNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'complaint')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.message}"
