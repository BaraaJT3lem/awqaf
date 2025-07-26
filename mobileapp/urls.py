from django.urls import path
from . import views

urlpatterns = [
    path('room/<str:room_name>/', views.room_view, name='room_view'),
    path('redirect-after-login/', views.mobile_redirect_view, name='mobile_redirect'),
    path('mark/<int:student_number>/', views.mark_student_view, name='mark_student'),



]
