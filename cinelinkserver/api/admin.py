from django.contrib import admin
from .models import Movies, HallRoom, Schedules, Seats, Tickets, Cart, CartProducts, Booked

# Register your models here.
admin.site.register(Movies)
admin.site.register(HallRoom)
admin.site.register(Schedules)
admin.site.register(Seats)
admin.site.register(Tickets)
admin.site.register(Cart)
admin.site.register(CartProducts)
admin.site.register(Booked)
