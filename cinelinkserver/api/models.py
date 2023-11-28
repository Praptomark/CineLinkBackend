from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import random
import string
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Create your models here.
####################################################################################################
class Movies(models.Model):
    title = models.CharField(max_length=255)
    poster = models.ImageField(upload_to="movie_poster/")
    release_year = models.DateField()
    language = models.CharField(max_length=5)
    description = models.TextField()
    genre = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    upcomming = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.title} - {self.duration} - Upcomming: {self.upcomming}"

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

    def __init__(self, *args, **kwargs):
        super(Schedules, self).__init__(*args, **kwargs)
        current_time = timezone.localtime().time()

        # Check if the end_time is earlier than the current time
        if self.end_time and self.end_time < current_time:
            self.delete()

    def __str__(self) -> str:
        return f"{self.pk} - {self.movie.title} - {self.hallroom.hallroom_name} - Time:({self.start_time} - {self.end_time})"

####################################################################################################
class Seats(models.Model):
    hall_room = models.ForeignKey(HallRoom, on_delete=models.CASCADE)
    seat_number = models.SmallIntegerField(default=1)
    is_booked = models.BooleanField(default=False)

    @classmethod
    def create_seats_for_hallroom(cls, hall_room):
        seats = [cls(hall_room=hall_room, seat_number=seat_num) for seat_num in range(1, 151)]
        cls.objects.bulk_create(seats)

    def __str__(self) -> str:
        return f"{self.pk} - {self.hall_room.hallroom_name} - {self.seat_number} - Booked: {self.is_booked}"

####################################################################################################
class CartProducts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seats, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedules, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.username} - Seat: {self.seat} - {self.schedule}"

####################################################################################################
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cart_products = models.ManyToManyField(CartProducts)

    def __str__(self) -> str:
        return f"{self.user.username}"

####################################################################################################
class Booked(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    is_booked = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_booked:
            # Generate a Ticket when is_booked is True
            Tickets.objects.create(user=self.user, booked=self)
    
    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)

    #     # Check if there is no corresponding Tickets instance
    #     if not hasattr(self, 'tickets'):
    #         # Create a Tickets instance and link it to the Booked instance
    #         Tickets.objects.create(user=self.user, booked=self)

    def __str__(self) -> str:
        return f"{self.user.username} - Booked: {self.is_booked}"

####################################################################################################
class Tickets(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    booked = models.ForeignKey(Booked, on_delete=models.CASCADE)
    expired = models.BooleanField(default=False)
    ticket_number = models.CharField(unique=True, max_length=15)

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
@receiver(post_save, sender=HallRoom)
def create_seats_for_hallroom(sender, instance, created, **kwargs):
    if created:
        Seats.create_seats_for_hallroom(instance)

@receiver(post_save, sender=Tickets)
@receiver(post_delete, sender=Tickets)
def update_seats_status(sender, instance, **kwargs):
    # Check if the instance is being created or deleted
    created = kwargs.get('created', False)
    deleted = kwargs.get('signal', False) == post_delete

    # Check if the instance is a Tickets model
    if isinstance(instance, Tickets):
        # Check if the seat's pk is in the Tickets.booked.cart.cart_products.seat
        booked_seats_pks = instance.booked.cart.cart_products.values_list('seat__pk', flat=True)
        seats_to_update = Seats.objects.filter(pk__in=booked_seats_pks)

        # Update is_booked based on the condition
        if created and seats_to_update:
            seats_to_update.update(is_booked=True)
        elif deleted and seats_to_update:
            seats_to_update.update(is_booked=False)

        # Update is_booked for seats that are not in the booked seats
        Seats.objects.exclude(pk__in=booked_seats_pks).update(is_booked=False)