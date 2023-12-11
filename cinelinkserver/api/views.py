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
from .serializers import MovieSerializer, ScheduleSerializer, UserSerializer, SeatSerializer, HallRoomSerializer, CartSerializer, BookedSerializer
from .models import Movies, Schedules, Seats, HallRoom, Cart, Booked
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import stripe

User = get_user_model()

stripe.api_key = ""
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

class CartAddAPIView(APIView): # For Seat to Cart
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            seat_id = request.data.get('seat_id')
            seat = Seats.objects.get(pk=seat_id)
        except Seats.DoesNotExist:
            return Response({"error": "Seat not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        cart_item = Cart.objects.create(user=user, seat=seat)
        serializer = CartSerializer(cart_item)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CartDeleteAPIView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def delete(self, request, *args, **kwargs):
        try:
            # Extracting Seats id from the JSON body
            seat_id = request.data.get('seat_id')

            # Retrieving the Cart object based on user and seat
            cart = Cart.objects.get(user=request.user, seat__id=seat_id)

            # Deleting the Cart object
            cart.delete()

            return Response({'detail': 'Seat removed from the cart successfully.'}, status=status.HTTP_204_NO_CONTENT)

        except Cart.DoesNotExist:
            return Response({'detail': 'Seat not found in the cart.'}, status=status.HTTP_404_NOT_FOUND)

        except Seats.DoesNotExist:
            return Response({'detail': 'Seat not found.'}, status=status.HTTP_404_NOT_FOUND)

class CartListView(ListAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter Cart instances based on the authenticated user
        return Cart.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class BookedListView(ListAPIView):
    queryset = Booked.objects.all()
    serializer_class = BookedSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter Booked instances based on the authenticated user
        return Booked.objects.filter(user=self.request.user)

class BookedDeleteAPIView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        # Get the Booked ID from the request data
        booked_id = request.data.get("booked_id")

        try:
            # Retrieve the Booked instance
            booked_instance = Booked.objects.get(id=booked_id, user=request.user)
        except Booked.DoesNotExist:
            return Response({"detail": "Booked instance not found."}, status=status.HTTP_404_NOT_FOUND)

        # Delete the Booked instance
        booked_instance.delete()

        return Response({"detail": "Booked instance deleted successfully."}, status=status.HTTP_200_OK)

# class CreateBookedFromCartView(CreateAPIView): # Payment
#     authentication_classes = (TokenAuthentication,)
#     permission_classes = (permissions.IsAuthenticated,)

#     def create(self, request, *args, **kwargs):
#         user = self.request.user

#         # Get all carts for the authenticated user
#         carts = Cart.objects.filter(user=user)

#         # Create booked instances for each cart
#         for cart in carts:
#             Booked.objects.create(user=user, seat=cart.seat)

#         return Response({"detail": "Booked instances created successfully"}, status=status.HTTP_201_CREATED)
    
class PaymentView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # Assuming your frontend sends the Stripe payment information in the request data
            payment_info = request.data.get('stripe_info', {})

            # Calculate the total amount based on the number of seats in the user's cart
            cart_length = Cart.objects.filter(user=request.user).count()
            total_amount = taka * cart_length

            # Create a payment intent using Stripe
            payment_intent = stripe.PaymentIntent.create(
                amount=total_amount * 100,  # Amount in cents
                currency="bdt",
                payment_method=payment_info['payment_method'],
                confirmation_method='manual',
                confirm=True,
                return_url="https://your-frontend-return-url.com"  # Specify your frontend return URL
            )

            # Check if payment is successful
            if payment_intent['status'] == 'succeeded':
                # Generate Booked instances and delete the Cart
                cart_items = Cart.objects.filter(user=request.user)
                for cart_item in cart_items:
                    seat = cart_item.seat
                    booked_instance = Booked.objects.create(
                        user=request.user,
                        seat=seat
                    )
                    # You can do further processing with the booked_instance if needed

                cart_items.delete()  # Delete the cart after successful payment

                return Response({'message': 'Payment successful'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Payment failed'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)