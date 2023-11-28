from django.contrib.auth import login
from rest_framework import permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.views import LoginView as KnoxLoginView
from rest_framework.views import APIView
from rest_framework.response import Response
from knox.auth import TokenAuthentication
from django.shortcuts import get_object_or_404
from knox.models import AuthToken
from rest_framework.generics import CreateAPIView, UpdateAPIView, DestroyAPIView, RetrieveAPIView
from .serializers import MovieSerializer, ScheduleSerializer, UserSerializer, SeatSerializer, HallRoomSerializer, CartSerializer, CartProductsSerializer, BookedSerializer, TicketSerializer
from .models import Movies, Schedules, Seats, HallRoom, Cart, CartProducts, Booked, Tickets
from django.contrib.auth import get_user_model
import stripe
from django.http import JsonResponse

User = get_user_model()
stripe.api_key = "your_stripe_secret_key"
taka = 400

####################################################################################################
# Authntication

class RegistrationAPIView(APIView): # For Sign up
    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            _, token = AuthToken.objects.create(user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(KnoxLoginView): # For Login
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super(LoginView, self).post(request, format=None)

####################################################################################################
# For All

class MovieAPIView(APIView): # Movie List and movie
    def get(self, request, movie_id=None):
        if movie_id is not None:
            # Return a specific movie by ID
            movie = get_object_or_404(Movies, pk=movie_id)
            serializer = MovieSerializer(movie)
        else:
            # Return all movies
            movies = Movies.objects.all()
            serializer = MovieSerializer(movies, many=True)

        return Response(serializer.data)

class SchedulesAPIView(APIView): # Schedules list
    def get(self, request, *args, **kwargs):
        schedules = Schedules.objects.all()
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

class SchedulesID_APIView(APIView): # Schedule
    def get(self, request, id, *args, **kwargs):
        schedule = get_object_or_404(Schedules, id=id)
        serializer = ScheduleSerializer(schedule)
        return Response(serializer.data)

class SeatsAPIView(APIView): # Seat Lists
    def get(self, request, format=None):
        seats = Seats.objects.all()
        serializer = SeatSerializer(seats, many=True)
        return Response(serializer.data)

####################################################################################################
# For Admin
class MovieCreateView(CreateAPIView): # Movie Create
    queryset = Movies.objects.all()
    serializer_class = MovieSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def perform_create(self, serializer):
        # Customize the creation process if needed
        serializer.save()

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # Optionally, generate and return the authentication token for the user
        user = self.request.user
        token, _ = AuthToken.objects.create(user)
        response.data['token'] = token
        return response

class MovieUpdateView(UpdateAPIView): # Update Movie
    queryset = Movies.objects.all()
    serializer_class = MovieSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_queryset(self):
        return Movies.objects.all()

class MovieDeleteView(DestroyAPIView): # Delete Movie
    queryset = Movies.objects.all()
    serializer_class = MovieSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class HallRoomCreateView(CreateAPIView): # Hall Room Create
    queryset = HallRoom.objects.all()
    serializer_class = HallRoomSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

class HallRoomUpdateView(UpdateAPIView): # Update HallRoom
    queryset = HallRoom.objects.all()
    serializer_class = HallRoomSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_queryset(self):
        return Movies.objects.all()

class HallRoomDeleteView(DestroyAPIView): # Delete HallRoom
    queryset = HallRoom.objects.all()
    serializer_class = HallRoomSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class ScheduleCreateView(CreateAPIView): # Hall Room Create
    queryset = Schedules.objects.all()
    serializer_class = ScheduleSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

class ScheduleUpdateView(UpdateAPIView): # Update HallRoom
    queryset = Schedules.objects.all()
    serializer_class = ScheduleSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_queryset(self):
        return Movies.objects.all()

class ScheduleDeleteView(DestroyAPIView): # Delete HallRoom
    queryset = Schedules.objects.all()
    serializer_class = ScheduleSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

####################################################################################################
# For Autheticated

class AddSeatToCartProductsView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartProductsSerializer

    def create(self, request, *args, **kwargs):
        user = self.request.user
        seat_id = request.data.get('seat_id')  # Assuming you send seat_id in the request data

        try:
            seat = Seats.objects.get(pk=seat_id, is_booked=False)
        except Seats.DoesNotExist:
            return Response({"error": "Seat not found or already booked"}, status=400)

        # Assuming you have a schedule_id in the request data
        schedule_id = request.data.get('schedule_id')
        schedule = Schedules.objects.get(pk=schedule_id)

        # Create CartProducts instance
        cart_product = CartProducts.objects.create(user=user, seat=seat, schedule=schedule)

        # Mark the seat as booked
        seat.is_booked = True
        seat.save()

        return Response({"success": "Seat added to the cart successfully"}, status=201)

class AddCartProductsView(CreateAPIView):
    serializer_class = CartProductsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = self.request.user
        cart, created = Cart.objects.get_or_create(user=user)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        seat_id = serializer.validated_data.get('seat')
        schedule_id = serializer.validated_data.get('schedule')

        seat = get_object_or_404(Seats, id=seat_id)
        schedule = get_object_or_404(Schedules, id=schedule_id)

        cart_product, created = CartProducts.objects.get_or_create(
            user=user, seat=seat, schedule=schedule
        )

        cart.cart_products.add(cart_product)
        cart.save()

        return Response({'detail': 'Cart Products added successfully'})

class CartProductsDeleteView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        # Get the user's cart
        user_cart = Cart.objects.get(user=request.user)

        # Get the CartProducts instance to be deleted
        cart_product_id = kwargs.get('pk')
        try:
            cart_product = CartProducts.objects.get(id=cart_product_id, user=request.user)
        except CartProducts.DoesNotExist:
            return Response({'detail': 'Cart product not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Remove the CartProducts from the cart
        user_cart.cart_products.remove(cart_product)

        return Response({'detail': 'Cart product deleted successfully.'}, status=status.HTTP_200_OK)

class CartAPIView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def get_object(self):
        # Return the Cart object associated with the authenticated user
        return Cart.objects.get(user=self.request.user)

class CreateBookedView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the user's cart
        cart = get_object_or_404(Cart, user=request.user)

        # Calculate the total amount based on the number of cart_products
        total_amount = 400 * cart.cart_products.count()

        try:
            # Create a payment intent using Stripe
            intent = stripe.PaymentIntent.create(
                amount=total_amount * 100,  # Amount in cents
                currency="bdt",
            )

            # Assuming payment is successful, create a Booked instance
            booked = Booked.objects.create(user=request.user, cart=cart)

            # Customize this part based on your needs
            booked.save()

            return Response({'clientSecret': intent.client_secret})
        except stripe.error.CardError as e:
            return JsonResponse({'error': str(e)}, status=403)

class BookedDeleteView(DestroyAPIView):
    queryset = Booked.objects.all()
    serializer_class = BookedSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Assuming your URL has a parameter named "pk" for the Booked instance id
        pk = self.kwargs.get('pk')
        return Booked.objects.get(pk=pk, user=self.request.user)

    def perform_destroy(self, instance):
        # Additional logic before deletion, if needed
        instance.delete()

class TicketsAPIView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TicketSerializer

    def get_object(self):
        # Assuming you want to retrieve the ticket for the currently authenticated user
        return Tickets.objects.get(user=self.request.user)
