# myapp/middleware.py

from django.shortcuts import redirect
from django.urls import resolve, reverse
from screen.models import Student

class RoomAccessMiddleware:
    """
    Restrict access to rooms and student marks only to the logged-in user's room.
    Redirect unauthorized accesses back to user's allowed page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.username.startswith('room'):
            current_url = resolve(request.path_info)
            username = request.user.username.lower()
            user_room_num = int(''.join(filter(str.isdigit, username)))

            if current_url.url_name == 'room_view':
                requested_room = current_url.kwargs.get('room_name', '').lower()
                if requested_room != username:
                    # Redirect back to the user's room page
                    return redirect(reverse('room_view', kwargs={'room_name': username}))

            elif current_url.url_name == 'mark_student':
                student_number = current_url.kwargs.get('student_number')
                try:
                    student = Student.objects.get(number=student_number)
                except Student.DoesNotExist:
                    # Redirect to user's room if invalid student
                    return redirect(reverse('room_view', kwargs={'room_name': username}))

                if student.room != user_room_num:
                    # Redirect back to the user's room page
                    return redirect(reverse('room_view', kwargs={'room_name': username}))

        response = self.get_response(request)
        return response
