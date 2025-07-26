from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),  # root url
    path('mobileapp/logout/', views.mobile_logout, name='mobile_logout'),
    path('mobileapp/room/<str:room_name>/', views.room_view, name='room_view'),
    path('screen/add-student/', views.add_student_view, name='add_student'),
]