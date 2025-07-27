# myapp/middleware.py

from django.shortcuts import redirect
from django.urls import resolve, reverse
from screen.models import Student

class RoomAccessMiddleware:
    """
    Restrict access to room pages and mark_student only for the authenticated room user.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.username.startswith('room'):
            current_url = resolve(request.path_info)
            username = request.user.username.lower()  # e.g., room1-2

            # Extract room_number and subroom from username
            room_parts = username.split('-')
            room_name = room_parts[0]              # room1
            subroom = int(room_parts[1]) if len(room_parts) > 1 else 1
            user_room_num = int(room_name.replace('room', ''))

            if current_url.url_name == 'room_view':
                requested_room = current_url.kwargs.get('room_name', '').lower()
                requested_subroom = current_url.kwargs.get('subroom')

                if requested_room != room_name or int(requested_subroom) != subroom:
                    return redirect(reverse('room_view', kwargs={
                        'room_name': room_name,
                        'subroom': subroom
                    }))

            elif current_url.url_name == 'mark_student':
                student_number = current_url.kwargs.get('student_number')
                try:
                    student = Student.objects.get(number=student_number)
                except Student.DoesNotExist:
                    return redirect(reverse('room_view', kwargs={
                        'room_name': room_name,
                        'subroom': subroom
                    }))

                if student.room != user_room_num:
                    return redirect(reverse('room_view', kwargs={
                        'room_name': room_name,
                        'subroom': subroom
                    }))

        return self.get_response(request)
