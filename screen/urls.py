from django.urls import path
from . import views
from .views import upload_excel

urlpatterns = [
    path('add-student', views.add_student, name='add_student'),
    path('', views.public_screen, name='public_screen'),
    path('clear', views.clear_students, name='clear_students'),
    path('apply-status/', views.trigger_automatic_status, name='apply_automatic_status'),
    path('submit-grade/<int:student_number>/', views.submit_grade, name='submit_grade'),
    path('automatic-status/', views.trigger_automatic_status, name='trigger_automatic_status'),
    path('screen/settings/', views.edit_settings, name='edit_settings'),
    path('upload-excel/', upload_excel, name='upload_excel'),
    path('update-status/<int:student_number>/', views.update_student_status, name='update_student_status'),
    path('remove-student/<int:student_number>/', views.remove_student, name='remove_student'),
    path('clear-results-from-screen/', views.clear_all_results, name='clear_all_results'),
    path('export_excel/', views.export_students_excel, name='export_students_excel'),
    path('screen/move/<int:number>/', views.move_student_position, name='move_student_position')









]
