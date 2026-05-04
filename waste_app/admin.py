from django.contrib import admin
from .models import Complaint, Worker, Assignment, RecyclingCenter, UserNotification, WasteCategory

# Register my models here.

admin.site.register(Complaint)
admin.site.register(Worker)
admin.site.register(Assignment)
admin.site.register(RecyclingCenter)
admin.site.register(UserNotification)
admin.site.register(WasteCategory)
