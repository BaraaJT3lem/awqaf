from django import forms
from .models import Student, ScreenSettings
import datetime


from screen.models import RoomQueue

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'name', 'father_name', 'birth_year',  # 👈 changed from birth_date to birth_year
            'institute_name', 'exam_type', 'memorized_parts', 'room'
        ]
        labels = {
            'name': 'الاسم والكنية',
            'father_name': 'اسم الأب',
            'birth_year': 'سنة التولد',  # 👈 update label here
            'institute_name': 'اسم المعهد',
            'exam_type': 'غيباً/نظراً',
            'memorized_parts': 'الأجزاء المحفوظة',
            'room': 'اللجنة',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        room_count = ScreenSettings.get_room_count()
        self.fields['room'].widget = forms.Select(
            choices=[('', 'اختيار لجنة تلقائي')] + [(i, f'اللجنة {i}') for i in range(1, room_count + 1)]
        )

    def clean_room(self):
        room = self.cleaned_data['room']
        return int(room) if room else None


class ScreenSettingsForm(forms.ModelForm):
    exam_start_time = forms.TimeField(
        label="وقت بدء الامتحان",
        widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        required=True
    )

    class Meta:
        model = ScreenSettings
        fields = ['room_count', 'waiting_count', 'estimate_time_per_student', 'exam_start_time']
        labels = {
            'room_count': 'عدد اللجان',
            'waiting_count': 'عدد الطلاب في الانتظار',
            'estimate_time_per_student': 'المدة التقديرية لكل طالب (دقيقة)',
            'exam_start_time': 'وقت بدء الامتحان',
        }


class UploadExcelForm(forms.Form):
    file = forms.FileField(label="تحميل ملف Excel")
