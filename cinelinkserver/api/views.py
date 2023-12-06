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
        try:
            seat_ids = request.data.get('seat_ids', [])
            user = request.user

            # Ensure seats exist
            seats = Seats.objects.filter(id__in=seat_ids, is_booked=False)
            if not seats.exists() or seats.count() != len(seat_ids):
                return Response({'detail': 'Invalid seat selection'}, status=status.HTTP_400_BAD_REQUEST)

            # Add seats to CartProducts
            cart_products = []
            for seat in seats:
                cart_product = CartProducts(user=user, seat=seat)
                cart_products.append(cart_product)

            CartProducts.objects.bulk_create(cart_products)

            # Update seat status to booked
            # seats.update(is_booked=True)

            serializer = CartProductsSerializer(cart_products, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

class CartCreateAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get user from the request
        user = self.request.user

        # Check if the user already has a cart
        cart, created = Cart.objects.get_or_create(user=user)

        # Get the CartProducts from the request data (assuming it's a list of CartProduct IDs)
        cart_product_ids = request.data.get('cart_product_ids', [])

        # Add CartProducts to the Cart
        for cart_product_id in cart_product_ids:
            try:
                cart_product = CartProducts.objects.get(id=cart_product_id, user=user)
                cart.cart_products.add(cart_product)
            except CartProducts.DoesNotExist:
                return Response({"error": f"CartProduct with ID {cart_product_id} not found for the user."}, status=status.HTTP_400_BAD_REQUEST)

        # Serialize the Cart for the response
        cart_serializer = CartSerializer(cart)

        return Response(cart_serializer.data, status=status.HTTP_201_CREATED)

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

class CreateBookedView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the user's cart
        cart = get_object_or_404(Cart, user=request.user)

        # Calculate the total amount based on the number of cart_products
        total_amount = taka * cart.cart_products.count()

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