from django.contrib import admin
from django.urls import path, include
from django.urls import path, include
from mobileapp.views import mobile_login  # import your custom login view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', mobile_login),  # ✅ make custom login the home page
    path('mobileapp/', include('mobileapp.urls')),
    path('screen/', include('screen.urls')),
    path('admin/', admin.site.urls),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    

]
