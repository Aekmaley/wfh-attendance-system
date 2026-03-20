from django import forms
from django.contrib.auth.models import User
from .models import Attendance, Department, UserProfile


class AttendanceForm(forms.ModelForm):
    action = forms.ChoiceField(
        choices=[('checkin', 'ลงชื่อเข้า'), ('checkout', 'ลงชื่อออก')],
        widget=forms.RadioSelect,
        initial='checkin'
    )

    class Meta:
        model = Attendance
        fields = ['action', 'work_type', 'place_note', 'task_detail', 'evidence_image', 'gps_latitude', 'gps_longitude']
        widgets = {
            'work_type': forms.Select(attrs={'class': 'form-select'}),
            'place_note': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น บ้านเลขที่..., ออกพื้นที่เขตดุสิต'}),
            'task_detail': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'ระบุภารกิจหรือรายละเอียดงานที่ทำ'}),
            'evidence_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'gps_latitude': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'gps_longitude': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }


class UserForm(forms.ModelForm):
    full_name = forms.CharField(max_length=255)
    position = forms.CharField(max_length=255, required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.full_name = self.cleaned_data['full_name']
            profile.position = self.cleaned_data['position']
            profile.department = self.cleaned_data['department']
            profile.save()
        return user
