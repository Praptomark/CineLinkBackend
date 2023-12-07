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

class CartProducts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seats, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"id: {self.pk}  - Seat: {self.seat}"

####################################################################################################
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cart_items = models.ManyToManyField(CartProducts)

    def __str__(self) -> str:
        return f"{self.user.username}"
####################################################################################################
class Booked(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

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

@receiver(post_save, sender=Booked)
def generate_tickets(sender, instance, created, **kwargs):
    if created:
        # Assuming each Booked instance corresponds to a user's booking
        user = instance.user

        # Get all CartProducts for the user
        cart_products = CartProducts.objects.filter(user=user)

        # Create a Tickets instance for each CartProduct
        for cart_product in cart_products:
            schedule = cart_product.seat.schedule
            seat_numbers = Seats.objects.filter(schedule=schedule)
            ticket = Tickets(user=user, schedule=schedule)
            ticket.save()

            # Add seat numbers to the ticket
            ticket.seat_numbers.add(*seat_numbers)

            # Mark seats as booked
            seat_numbers.update(is_booked=True)

        # Clear CartProducts and Cart for the user
        CartProducts.objects.filter(user=user).delete()
        Cart.objects.filter(user=user).delete()


@receiver(post_save, sender=Booked)
def set_seats_as_booked(sender, instance, **kwargs):
    # Set all seats in CartProducts to True
    cart_products = CartProducts.objects.filter(user=instance.user)
    for cart_product in cart_products:
        cart_product.seat.is_booked = True
        cart_product.seat.save()

    # Delete all CartProducts and the Cart
    CartProducts.objects.filter(user=instance.user).delete()
    Cart.objects.filter(user=instance.user).delete()