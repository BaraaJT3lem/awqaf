from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from screen.models import Student
from .forms import RoomLoginForm, MarkForm
import csv
import os
import re
from django.http import HttpResponse
from django.conf import settings
from screen.views import apply_automatic_status
from django.shortcuts import redirect
from django.contrib import messages
from screen.models import ExamResult
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Avg
from screen.models import Student

@login_required
def room_view(request, room_name, subroom):
    # Get numeric room number from room_name like "room1"
    match = re.match(r'room(\d+)', room_name)
    if not match:
        return HttpResponse("Invalid room name", status=400)
    
    room_number = int(match.group(1))
    students = Student.objects.filter(room=room_number).exclude(status='finished').order_by('position')


    return render(request, 'mobileapp/room_view.html', {
        'room_name': room_name,
        'room_number': room_number,
        'subroom': subroom,
        'students': students,
    })






@login_required
def mobile_redirect_view(request):
    username = request.user.username.lower()
    if username.startswith("room"):
        return redirect(f'/mobileapp/room/{username}/')
    else:
        return redirect('/screen/add-student')



@login_required
def mark_student_view(request, student_number, subroom):
    student = get_object_or_404(Student, number=student_number)

    # Get all grades for this student so far
    subroom_results = ExamResult.objects.filter(number=student.number).exclude(sub_room=0)  # exclude final average
    grades = [er.grade for er in subroom_results]

    # Calculate current average grade
    avg_grade = sum(grades)/len(grades) if grades else 100

    # Determine exam questions based on exam type
    if student.exam_type in ["غيبا", "gh"]:
        questions = ['الأول', 'الثاني', 'الثالث']  # 3 questions
    else:
        questions = ['الأول', 'الثاني', 'الثالث', 'الرابع', 'الخامس']  # 5 questions

    # Render grading page with current average grade shown
    return render(request, 'mobileapp/mark_student.html', {
        'student': student,
        'subroom': subroom,
        'avg_grade': avg_grade,
        'questions': questions,
    })


def some_view(request):
    username = request.user.username  # e.g. 'room1-2'
    match = re.match(r'(room\d+)-(\d+)', username)
    if match:
        room_name = match.group(1)
        subroom = int(match.group(2))
    else:
        room_name = username
        subroom = 1

    return redirect('room_view', room_name=room_name, subroom=subroom)
@login_required
def room_redirect_default(request, room_name):
    # Redirect to subroom 1 by default if subroom is missing
    return redirect('room_view', room_name=room_name, subroom=1)