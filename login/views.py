from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from screen.models import Student
from django.contrib import messages

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

@login_required(login_url='')
def home_view(request):
    user = request.user
    if user.is_staff or user.is_superuser:
        return redirect('/screen/add-student/')
    else:
        return redirect(f'/mobileapp/room/{user.username}/')

def mobile_login(request):
    if request.user.is_authenticated:
        user = request.user


        if user.is_staff or user.is_superuser:
            return redirect('/screen/add-student/')
        else:
            return redirect(f'/mobileapp/room/{user.username}/')

    if request.method == 'POST':
        room_name = request.POST.get('room_name', '').strip().lower()
        password = request.POST.get('password', '')

        user = authenticate(request, username=room_name, password=password)
        if user is not None:
            login(request, user)



            if user.is_staff or user.is_superuser:
                return redirect('/screen/add-student/')
            else:
                return redirect(f'/mobileapp/room/{room_name}/')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')

    return render(request, 'login/login.html')


@login_required(login_url='')
def mobile_logout(request):
    logout(request)
    return redirect('')

@login_required(login_url='')
def room_view(request, room_name):
    logged_in_username = request.user.username.lower()
    requested_room = room_name.lower()

    if logged_in_username != requested_room:
        return redirect(f'/mobileapp/room/{logged_in_username}/')

    try:
        room_number = int(''.join(filter(str.isdigit, requested_room)))
    except ValueError:
        return redirect(f'/mobileapp/room/{logged_in_username}/')

    students = Student.objects.filter(room=room_number).exclude(status='finished').order_by('position')

    return render(request, 'mobileapp/room_view.html', {
        'room_name': room_name,
        'students': students,
    })

@staff_member_required(login_url='')
def add_student_view(request):
    return render(request, 'screen/add_student.html')
