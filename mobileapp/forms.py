from django import forms

class RoomLoginForm(forms.Form):
    room_name = forms.CharField(label='اسم المستخدم')
    password = forms.CharField(widget=forms.PasswordInput, label='كلمة المرور')

    
class MarkForm(forms.Form):
    mark = forms.IntegerField(label="الدرجة", min_value=0, max_value=100)
