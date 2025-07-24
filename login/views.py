from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from .forms import LoginForm

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user is not None and user.is_staff:
                auth_login(request, user)
                return redirect('/screen/add-student')   # Redirect to admin panel
            else:
                return render(request, 'login/login.html', {
                    'form': form,
                    'error': 'Invalid credentials or not admin/staff.'
                })
    else:
        form = LoginForm()
    return render(request, 'login/login.html', {'form': form})
