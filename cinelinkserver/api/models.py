from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import random
import string
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.db import transaction

# Create your models here.
####################################################################################################
class Movies(models.Model):
    title = models.CharField(max_length=255)
    poster = models.ImageField(upload_to="poster/")
    release_year = models.DateField()
    language = models.CharField(max_length=30)
    movie_info_link = models.URLField()
    genre = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    upcoming = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.title} - {self.duration} - Upcomming: {self.upcoming}"

####################################################################################################
class HallRoom(models.Model):
    hallroom_name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return f"{self.hallroom_name}"
    
####################################################################################################
class Schedules(models.Model):
    movie = models.ForeignKey(Movies, on_delete=models.CASCADE)
    hallroom = models.ForeignKey(HallRoom, on_delete=models.CASCADE)
    show_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self) -> str:
        return f"{self.pk} - {self.movie.title} - {self.hallroom.hallroom_name} - Time:({self.start_time} - {self.end_time})"

####################################################################################################
class Seats(models.Model):
    schedule = models.ForeignKey(Schedules, on_delete=models.CASCADE)
    seat_number = models.SmallIntegerField(default=1)
    is_booked = models.BooleanField(default=False)

    @classmethod
    def generate_seats(cls, schedule):
        seats = [cls(schedule=schedule, seat_number=i) for i in range(1, 151)]
        cls.objects.bulk_create(seats)

    def __str__(self) -> str:
        return f"id:{self.pk} - Movie: {self.schedule.movie.title} - Hall: {self.schedule.hallroom.hallroom_name}- Seat: {self.seat_number} - Booked: {self.is_booked}"

####################################################################################################
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.username}"
####################################################################################################

class CartProducts(models.Model):
    seat = models.ForeignKey(Seats, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"id: {self.pk}  - Seat: {self.seat}"
####################################################################################################
class Booked(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True)


    def __str__(self) -> str:
        return f"{self.user.username}"

####################################################################################################
class Tickets(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expired = models.BooleanField(default=False)
    ticket_number = models.CharField(unique=True, max_length=15)
    seat_numbers = models.ManyToManyField(Seats)
    schedule = models.ForeignKey(Schedules, on_delete=models.CASCADE, null=True)

    def generate_ticket_number(self):
        characters = string.ascii_uppercase + string.digits
        ticket_number = ''.join(random.choice(characters) for _ in range(10))
        return ticket_number

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.user.username} - Ticket_Number: {self.ticket_number}"

####################################################################################################
###
@receiver(post_save, sender=Schedules)
def create_seats(sender, instance, created, **kwargs):
    """
    Signal receiver to create seats when a schedule is created.
    """
    if created:
        Seats.generate_seats(instance)
###
@receiver(post_save, sender=Booked)
def create_tickets_and_update_seats(sender, instance, **kwargs):
    if kwargs.get('created', False):
        with transaction.atomic():
            cart_products = instance.cart.cart_products.all()

            # Update is_booked value for Seats in CartProducts
            for cart_product in cart_products:
                cart_product.seat.is_booked = True
                cart_product.seat.save()

            # Create Tickets and store Schedules and Seats
            for cart_product in cart_products:
                ticket = Tickets.objects.create(
                    user=instance.user,
                    schedule=cart_product.seat.schedule
                )
                ticket.seat_numbers.set([cart_product.seat])
                ticket.save()

            # Delete all CartProducts
            instance.cart.cart_products.all().delete()

###
@receiver(pre_delete, sender=CartProducts)
def delete_cart_if_empty(sender, instance, **kwargs):
    cart = Cart.objects.filter(user=instance.user).first()
    if cart and cart.cart_products.count() == 1:  # Check if the last CartProduct is being deleted
        cart.delete()