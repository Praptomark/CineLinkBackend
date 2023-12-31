from django.urls import path
from knox import views as knox_views
from .views import (
    LoginView,  
    MovieAPIView, 
    MovieCreateView,
    MovieUpdateView,
    MovieDeleteView,
    SchedulesAPIView, 
    SchedulesID_APIView,
    RegistrationAPIView,
    SeatsAPIView,
    HallRoomCreateView,
    HallRoomUpdateView,
    HallRoomDeleteView,
    ScheduleCreateView,
    ScheduleUpdateView,
    ScheduleDeleteView,
    SeatAPIView,
    UserUpdateView,
    UserDetailsView,
    UserDeleteView,
    CartAddAPIView,
    CartDeleteAPIView,
    CartListView,
    BookedListView,
    BookedDeleteAPIView,
    HallRoomListView,

    # CreateBookedFromCartView
    PaymentView
    )

urlpatterns = [
    # Authentication section########################################################################
    path('register/', RegistrationAPIView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='knox_login'),
    path('logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),

    # For All#######################################################################################
    path('hallrooms/', HallRoomListView.as_view(), name='hallroom-list'),

    path("movies/", MovieAPIView.as_view(), name="movies"),
    path("movies/<int:movie_id>", MovieAPIView.as_view(), name="movies"),

    path('schedules/', SchedulesAPIView.as_view(), name='schedule-list'),
    path('schedules/<int:id>/', SchedulesID_APIView.as_view(), name='schedule-detail'),

    path('seats/', SeatsAPIView.as_view(), name='seats-list'),
    path('seats/<int:id>', SeatAPIView.as_view(), name='seat-by-id'),

    # For Admin#####################################################################################
    path('movie-create/', MovieCreateView.as_view(), name='movie-create'),
    path('movie-update/<int:pk>', MovieUpdateView.as_view(), name='movie-update'),
    path('movie-delete/<int:pk>', MovieDeleteView.as_view(), name='movie-delete'),

    path('hallroom-create/', HallRoomCreateView.as_view(), name='hallroom-create'),
    path('hallroom-update/<int:pk>', HallRoomUpdateView.as_view(), name='hallroom-update'),
    path('hallroom-delete/<int:pk>', HallRoomDeleteView.as_view(), name='hallroom-delete'),

    path('schedule-create/', ScheduleCreateView.as_view(), name='schedule-create'),
    path('schedule-update/<int:pk>', ScheduleUpdateView.as_view(), name='schedule-update'),
    path('schedule-delete/<int:pk>', ScheduleDeleteView.as_view(), name='schedule-delete'),
    
    # For Authenticated#############################################################################
    path('user/', UserDetailsView.as_view(), name='user-details'),
    path('update-user/', UserUpdateView.as_view(), name='user-update'),
    path('delete-user/', UserDeleteView.as_view(), name='user-delete'),

    path('add-cart/', CartAddAPIView.as_view(), name='cart-add'),
    path('delete-cart/', CartDeleteAPIView.as_view(), name='cart-delete'),
    path('cart/', CartListView.as_view(), name='cart-list'),

    # path('payment/', CreateBookedFromCartView.as_view(), name='create-booked-from-cart'),
    path('payment/', PaymentView.as_view(), name='create-booked-from-cart'),

    path('booked/', BookedListView.as_view(), name='booked-list'),
    path('delete-book/', BookedDeleteAPIView.as_view(), name='booked-delete'),
]