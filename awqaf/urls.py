from django.contrib import admin
from django.urls import path, include
from login.views import mobile_login  # Your custom login view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', mobile_login, name='home'),  # Use custom login as homepage
    path('mobileapp/', include('mobileapp.urls')),  # All /mobileapp/ routes
    path('screen/', include('screen.urls')),        # ✅ This ensures /screen/add-student/ works
    path('admin/', admin.site.urls),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),  # Logout redirect to login
]
