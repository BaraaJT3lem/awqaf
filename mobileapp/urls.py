from django.urls import path
from . import views
from screen.views import submit_grade

urlpatterns = [
    # Redirect URLs with just room_name to room_name + default subroom (1)
    path('room/<str:room_name>/', views.room_redirect_default, name='room_redirect_default'),

    # Room view with room_name and subroom
    path('room/<str:room_name>/<int:subroom>/', views.room_view, name='room_view'),

    path('redirect-after-login/', views.mobile_redirect_view, name='mobile_redirect'),

    # Mark student view with student_number and subroom
    path('mark/<int:student_number>/<int:subroom>/', views.mark_student_view, name='mark_student'),

    # Submit grade POST handler
    path('submit-grade/<int:student_number>/<int:subroom>/', submit_grade, name='submit_grade'),

]
