from django.contrib.auth import login
from rest_framework import permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.views import LoginView as KnoxLoginView
from rest_framework.views import APIView
from rest_framework.response import Response
from knox.auth import TokenAuthentication
from django.shortcuts import get_object_or_404
from knox.models import AuthToken
from rest_framework.generics import CreateAPIView, UpdateAPIView, DestroyAPIView, RetrieveAPIView, ListAPIView
from .serializers import MovieSerializer, ScheduleSerializer, UserSerializer, SeatSerializer, HallRoomSerializer, CartSerializer, CartProductsSerializer, BookedSerializer, TicketSerializer
from .models import Movies, Schedules, Seats, HallRoom, Cart, CartProducts, Booked, Tickets
from django.contrib.auth import get_user_model
import stripe
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password

User = get_user_model()
stripe.api_key = "your_stripe_secret_key"
taka = 400

####################################################################################################
# Authntication

class RegistrationAPIView(APIView): # For Sign up
    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # Hash the password before saving
            serializer.validated_data['password'] = make_password(serializer.validated_data['password'])
            
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

class SeatAPIView(RetrieveAPIView):
    queryset = Seats.objects.all()
    serializer_class = SeatSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        seat_id = self.kwargs.get('id')
        return Seats.objects.get(pk=seat_id)

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

class AddSeatToCartProductsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        seat_id = request.data.get('seat_id')

        if not seat_id:
            return Response({"error": "Seat ID is required in the request body"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            seat = Seats.objects.get(pk=seat_id)
        except Seats.DoesNotExist:
            return Response({"error": "Invalid seat ID"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        cart_product = CartProducts.objects.create(user=user, seat=seat)

        return Response({"message": "Seat added to CartProducts successfully"}, status=status.HTTP_201_CREATED)

class CartProductsDeleteView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        try:
            seat_id = request.data.get('seat_id')
            cart_product = CartProducts.objects.get(user=request.user, seat_id=seat_id)
            cart_product.delete()
            return Response({"detail": "Seat removed from CartProducts successfully."}, status=status.HTTP_204_NO_CONTENT)
        except CartProducts.DoesNotExist:
            return Response({"detail": "Seat not found in user's CartProducts."}, status=status.HTTP_404_NOT_FOUND)

class CartProductsListView(ListAPIView):
    queryset = CartProducts.objects.all()
    serializer_class = CartProductsSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter CartProducts based on the authenticated user
        return CartProducts.objects.filter(user=self.request.user)

class CartCreateAPIView(CreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CartSerializer  # Replace with your actual serializer

    def create(self, request, *args, **kwargs):
        # Get the user associated with the token
        user = request.user

        # Retrieve all CartProducts for the authenticated user
        cart_products = CartProducts.objects.filter(user=user)

        # Create a Cart instance or get existing one
        cart, created = Cart.objects.get_or_create(user=user)

        # Add CartProducts to the cart_items many-to-many field
        cart.cart_items.add(*cart_products)

        return Response(status=status.HTTP_201_CREATED)
    
class CartDeleteAPIView(DestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self):
        user = self.request.user
        return Cart.objects.get(user=user)

    def perform_destroy(self, instance):
        # Delete the user's cart
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CartAPIView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def get_object(self):
        # Return the Cart object associated with the authenticated user
        return Cart.objects.get(user=self.request.user)

# class CreateBookedView(APIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         # Get the user's cart
#         cart = get_object_or_404(Cart, user=request.user)

#         # Calculate the total amount based on the number of cart_products
#         total_amount = taka * cart.cart_products.count()

#         try:
#             # Create a payment intent using Stripe
#             intent = stripe.PaymentIntent.create(
#                 amount=total_amount * 100,  # Amount in cents
#                 currency="bdt",
#             )

#             # Assuming payment is successful, create a Booked instance
#             booked = Booked.objects.create(user=request.user, cart=cart)

#             # Customize this part based on your needs
#             booked.save()

#             return Response({'clientSecret': intent.client_secret})
#         except stripe.error.CardError as e:
#             return JsonResponse({'error': str(e)}, status=403)

class CreateBookedView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookedSerializer

    def perform_create(self, serializer):
        # Set the user and cart for the Booked instance
        serializer.save(user=self.request.user, cart=self.request.user.cart)

class TicketsAPIView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TicketSerializer

    def get_object(self):
        # Assuming you want to retrieve the ticket for the currently authenticated user
        return Tickets.objects.get(user=self.request.user)

class UserUpdateView(UpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class UserDetailsView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class UserDeleteView(DestroyAPIView):
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        # Optionally, you can invalidate the user's tokens on deletion
        AuthToken.objects.filter(user=instance).delete()
        instance.delete()

class TicketDeleteView(DestroyAPIView):
    queryset = Tickets.objects.all()
    serializer_class = TicketSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        instance.delete()