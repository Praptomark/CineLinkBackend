from rest_framework import serializers
from .models import Movies, HallRoom, Seats, Schedules, Cart, Booked
from django.contrib.auth import models, get_user_model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'is_superuser')

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movies
        fields = '__all__'

class HallRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = HallRoom
        fields = '__all__'

class ScheduleSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()
    hallroom = HallRoomSerializer()

    class Meta:
        model = Schedules
        fields = '__all__'

class SeatSerializer(serializers.ModelSerializer):
    schedule = ScheduleSerializer()
    class Meta:
        model = Seats
        fields = '__all__'

class CartSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=models.User.objects.all())
    seat = SeatSerializer()

    class Meta:
        model = Cart
        fields = '__all__'

class BookedSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=models.User.objects.all())
    seat = SeatSerializer()

    class Meta:
        model = Booked
        fields = ["user", "seat", "ticket_number"]