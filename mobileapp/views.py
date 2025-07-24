from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from screen.models import Student
from .forms import RoomLoginForm, MarkForm
import csv
import os
import re
from django.conf import settings


def mobile_login(request):
    if request.method == 'POST':
        form = RoomLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['room_name'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                return redirect('/mobileapp/redirect-after-login/')
    else:
        form = RoomLoginForm()
    return render(request, 'mobileapp/login.html', {'form': form})


@login_required
def room_view(request, room_name):
    try:
        room_number = int(''.join(filter(str.isdigit, room_name)))
    except ValueError:
        return redirect('/mobileapp/login')

    students = Student.objects.filter(room=room_number).exclude(status='finished').order_by('number')


    return render(request, 'mobileapp/room_view.html', {
        'room_name': room_name,
        'students': students

    })


@login_required
def mobile_redirect_view(request):
    username = request.user.username.lower()
    if username.startswith("room"):
        return redirect(f'/mobileapp/room/{username}/')
    else:
        return redirect('/screen/add-student')


@login_required
def mark_student_view(request, student_number):
    student = get_object_or_404(Student, number=student_number)

    if student.exam_type in ["غيبا", "gh"]:
        questions = ['الأول', 'الثاني', 'الثالث']  # 3 questions
        pass_threshold = 80
    else:  # "نظرا", "nz"
        questions = ['الأول', 'الثاني', 'الثالث', 'الرابع', 'الخامس']  # 5 questions
        pass_threshold = 90

    if request.method == 'POST':
        # Extract final_grade from POST (adjust input name as per your form)
        try:
            final_grade = float(request.POST.get("final_grade", "100"))
        except ValueError:
            final_grade = 100

        result = "ناجح" if final_grade >= pass_threshold else "إعادة"

        output_dir = os.path.join(settings.BASE_DIR, 'grades_output')
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, 'grades.csv')

        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([student.number, student.name, final_grade, result])

        room = student.room
        student.delete()

        next_student = Student.objects.filter(room=room, status='waiting').order_by('number').first()
        if next_student:
            next_student.status = 'in_exam'
            next_student.save()

        nxt_student = Student.objects.filter(room=room, status='on_waiting_list').order_by('number').first()
        if nxt_student:
            nxt_student.status = 'waiting'
            nxt_student.save()

        return redirect(f'/mobileapp/room/room{room}/')

    else:
        form = MarkForm()

    return render(request, 'mobileapp/mark_student.html', {
        'student': student,
        'form': form,
        'questions': questions,
    })
