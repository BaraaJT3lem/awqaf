from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from screen.models import Student
from django.contrib import messages
from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
import re

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


@login_required
def room_view(request, room_name, subroom):
    # Parse room number from room_name like 'room1'
    match = re.match(r'room(\d+)', room_name)
    if not match:
        return HttpResponse("Invalid room name", status=400)

    room_number = int(match.group(1))

    students = Student.objects.filter(room=room_number, subroom=subroom).order_by('position')

    return render(request, 'mobileapp/room_view.html', {
        'students': students,
        'room': room_number,
        'subroom': subroom,
    })

@staff_member_required(login_url='')
def add_student_view(request):
    return render(request, 'screen/add_student.html')
@login_required



def custom_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Parse username 'roomX-Y'
            match = re.match(r'room(\d+)-(\d+)', username)
            if match:
                room_num = match.group(1)
                subroom_num = match.group(2)
                return redirect(f'/mobileapp/room/room{room_num}-{subroom_num}/')
            
            # fallback redirect
            return redirect('/')
        else:
            # invalid login
            pass
