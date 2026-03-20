from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    WORK_CHOICES = [
        ('home', 'บ้าน / Work From Home'),
        ('field', 'ออกปฏิบัติราชการ'),
        ('office', 'สำนักงาน'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    default_work_type = models.CharField(max_length=20, choices=WORK_CHOICES, default='home')

    def __str__(self):
        return self.full_name or self.user.username


class Attendance(models.Model):
    WORK_CHOICES = UserProfile.WORK_CHOICES

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    work_type = models.CharField(max_length=20, choices=WORK_CHOICES)
    task_detail = models.TextField()
    evidence_image = models.ImageField(upload_to='evidence/', null=True, blank=True)
    gps_latitude = models.CharField(max_length=50, blank=True)
    gps_longitude = models.CharField(max_length=50, blank=True)
    place_note = models.CharField(max_length=255, blank=True)
    check_in_time = models.DateTimeField(default=timezone.now)
    check_out_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-check_in_time']

    @property
    def status(self):
        return 'ปิดงานแล้ว' if self.check_out_time else 'กำลังปฏิบัติงาน'

    @property
    def duration_text(self):
        if not self.check_out_time:
            return '-'
        seconds = int((self.check_out_time - self.check_in_time).total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f'{hours} ชม. {minutes} นาที'

    def __str__(self):
        return f'{self.user.username} - {self.get_work_type_display()} - {self.check_in_time:%d/%m/%Y}'
