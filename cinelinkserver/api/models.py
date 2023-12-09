from django.db import models
from django.contrib.auth.models import User
import random
import string
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seats, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"id: {self.pk}  - Seat: {self.seat}"
####################################################################################################
class Booked(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seats, on_delete=models.CASCADE)
    ticket_number = models.CharField(unique=True, max_length=15)

    def generate_ticket_number(self, length=10):
        characters = string.ascii_uppercase + string.digits
        ticket_number = ''.join(random.choice(characters) for _ in range(length))
        return ticket_number

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"pk: {self.pk} - {self.user.username} - Ticket: {self.ticket_number}"

####################################################################################################
@receiver(post_save, sender=Schedules)
def create_seats(sender, instance, created, **kwargs):
    """
    Signal receiver to create seats when a schedule is created.
    """
    if created:
        Seats.generate_seats(instance)

# Set is_booked to True if in Booked
@receiver(post_save, sender=Booked)
def update_seats_status(sender, instance, **kwargs):
    # Check if the associated seat is already booked
    if instance.seat.is_booked == False:
        # Update the is_booked status to True
        instance.seat.is_booked = True
        instance.seat.save()

# Delete the Cart which are in the Booked
@receiver(post_save, sender=Booked)
def delete_cart_on_seat_booked(sender, instance, **kwargs):
    # Check if the booked seat has a corresponding Cart instance
    try:
        cart_instance = Cart.objects.get(user=instance.user, seat=instance.seat)
        cart_instance.delete()
    except Cart.DoesNotExist:
        pass  # No corresponding Cart instance found, nothing to delete