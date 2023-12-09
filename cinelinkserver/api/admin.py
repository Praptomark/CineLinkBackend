from django.contrib import admin
from .models import Movies, HallRoom, Schedules, Seats, Cart, Booked

# Register your models here.
admin.site.register(Movies)
admin.site.register(HallRoom)
admin.site.register(Schedules)
admin.site.register(Seats)
admin.site.register(Cart)
admin.site.register(Booked)
