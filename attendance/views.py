from io import BytesIO
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font
from xhtml2pdf import pisa

from .forms import AttendanceForm, UserForm
from .models import Attendance, Department, UserProfile


def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)


def _today_range():
    now = timezone.localtime()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def _get_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'full_name': user.get_full_name() or user.username})
    return profile


@login_required
def dashboard(request):
    today_start, today_end = _today_range()
    today_qs = Attendance.objects.filter(check_in_time__range=(today_start, today_end))
    my_open = Attendance.objects.filter(user=request.user, check_out_time__isnull=True).first()

    context = {
        'profile': _get_profile(request.user),
        'today_total': today_qs.count(),
        'today_home': today_qs.filter(work_type='home').count(),
        'today_field': today_qs.filter(work_type='field').count(),
        'today_office': today_qs.filter(work_type='office').count(),
        'today_open': today_qs.filter(check_out_time__isnull=True).count(),
        'recent_items': today_qs.select_related('user')[:10],
        'my_open': my_open,
        'chart_labels': ['WFH', 'ราชการ', 'สำนักงาน'],
        'chart_values': [
            today_qs.filter(work_type='home').count(),
            today_qs.filter(work_type='field').count(),
            today_qs.filter(work_type='office').count(),
        ]
    }
    return render(request, 'attendance/dashboard.html', context)


@login_required
def attendance_form_view(request):
    profile = _get_profile(request.user)
    open_record = Attendance.objects.filter(user=request.user, check_out_time__isnull=True).first()

    if request.method == 'POST':
        form = AttendanceForm(request.POST, request.FILES)
        if form.is_valid():
            action = form.cleaned_data['action']
            if action == 'checkin':
                if open_record:
                    messages.warning(request, 'คุณมีรายการที่ยังไม่ได้ลงชื่อออก')
                else:
                    attendance = form.save(commit=False)
                    attendance.user = request.user
                    attendance.check_in_time = timezone.now()
                    attendance.save()
                    messages.success(request, 'ลงชื่อเข้าปฏิบัติงานเรียบร้อยแล้ว')
                    return redirect('history')
            else:
                if not open_record:
                    messages.warning(request, 'ไม่พบรายการที่เปิดงานอยู่สำหรับลงชื่อออก')
                else:
                    open_record.check_out_time = timezone.now()
                    open_record.work_type = form.cleaned_data['work_type']
                    open_record.place_note = form.cleaned_data['place_note']
                    open_record.task_detail = form.cleaned_data['task_detail']
                    if form.cleaned_data['evidence_image']:
                        open_record.evidence_image = form.cleaned_data['evidence_image']
                    open_record.gps_latitude = form.cleaned_data['gps_latitude']
                    open_record.gps_longitude = form.cleaned_data['gps_longitude']
                    open_record.save()
                    messages.success(request, 'ลงชื่อออกปฏิบัติงานเรียบร้อยแล้ว')
                    return redirect('history')
    else:
        initial = {'work_type': profile.default_work_type}
        if open_record:
            initial.update({
                'action': 'checkout',
                'work_type': open_record.work_type,
                'place_note': open_record.place_note,
                'task_detail': open_record.task_detail,
                'gps_latitude': open_record.gps_latitude,
                'gps_longitude': open_record.gps_longitude,
            })
        form = AttendanceForm(initial=initial)

    return render(request, 'attendance/attendance_form.html', {
        'form': form,
        'open_record': open_record,
        'now': timezone.localtime(),
    })


@login_required
def history_view(request):
    qs = Attendance.objects.filter(user=request.user)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        qs = qs.filter(check_in_time__date__gte=date_from)
    if date_to:
        qs = qs.filter(check_in_time__date__lte=date_to)

    return render(request, 'attendance/history.html', {
        'items': qs,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
@staff_required
def reports_view(request):
    qs = Attendance.objects.select_related('user').all()
    name = request.GET.get('name', '').strip()
    department = request.GET.get('department', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    work_type = request.GET.get('work_type', '').strip()

    if name:
        qs = qs.filter(
            Q(user__username__icontains=name) |
            Q(user__userprofile__full_name__icontains=name)
        )
    if department:
        qs = qs.filter(user__userprofile__department__name__icontains=department)
    if date_from:
        qs = qs.filter(check_in_time__date__gte=date_from)
    if date_to:
        qs = qs.filter(check_in_time__date__lte=date_to)
    if work_type:
        qs = qs.filter(work_type=work_type)

    summary = qs.aggregate(
        total=Count('id'),
        home=Count('id', filter=Q(work_type='home')),
        field=Count('id', filter=Q(work_type='field')),
        office=Count('id', filter=Q(work_type='office')),
        open_jobs=Count('id', filter=Q(check_out_time__isnull=True)),
    )

    return render(request, 'attendance/reports.html', {
        'items': qs[:200],
        'summary': summary,
        'departments': Department.objects.all(),
        'filters': {
            'name': name,
            'department': department,
            'date_from': date_from,
            'date_to': date_to,
            'work_type': work_type,
        }
    })


@login_required
@staff_required
def export_excel(request):
    qs = Attendance.objects.select_related('user').all()
    wb = Workbook()
    ws = wb.active
    ws.title = 'Attendance Report'
    headers = ['ชื่อผู้ใช้', 'ชื่อ-นามสกุล', 'หน่วยงาน', 'ประเภทงาน', 'เวลาเข้า', 'เวลาออก', 'สถานที่', 'รายละเอียดงาน', 'GPS']
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for item in qs:
        profile = getattr(item.user, 'userprofile', None)
        ws.append([
            item.user.username,
            profile.full_name if profile else item.user.username,
            profile.department.name if profile and profile.department else '',
            item.get_work_type_display(),
            timezone.localtime(item.check_in_time).strftime('%d/%m/%Y %H:%M'),
            timezone.localtime(item.check_out_time).strftime('%d/%m/%Y %H:%M') if item.check_out_time else '-',
            item.place_note,
            item.task_detail,
            f'{item.gps_latitude}, {item.gps_longitude}',
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=attendance_report.xlsx'
    wb.save(response)
    return response


@login_required
@staff_required
def export_pdf(request):
    qs = Attendance.objects.select_related('user')[:150]
    template = get_template('attendance/report_pdf.html')
    html = template.render({'items': qs, 'generated_at': timezone.localtime()})
    result = BytesIO()
    pisa.CreatePDF(html, dest=result)
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=attendance_report.pdf'
    return response


@login_required
@staff_required
def user_management(request):
    users = User.objects.select_related('userprofile').all().order_by('username')
    q = request.GET.get('q', '').strip()
    if q:
        users = users.filter(Q(username__icontains=q) | Q(userprofile__full_name__icontains=q))
    return render(request, 'attendance/user_management.html', {'users': users, 'q': q})


@login_required
@staff_required
def user_create(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มผู้ใช้งานเรียบร้อยแล้ว')
            return redirect('user_management')
    else:
        form = UserForm()
    return render(request, 'attendance/user_form.html', {'form': form, 'title': 'เพิ่มผู้ใช้งาน'})


@login_required
@staff_required
def user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    profile = _get_profile(user)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user, initial={
            'full_name': profile.full_name,
            'position': profile.position,
            'department': profile.department,
        })
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขข้อมูลผู้ใช้งานเรียบร้อยแล้ว')
            return redirect('user_management')
    else:
        form = UserForm(instance=user, initial={
            'full_name': profile.full_name,
            'position': profile.position,
            'department': profile.department,
        })
    return render(request, 'attendance/user_form.html', {'form': form, 'title': 'แก้ไขผู้ใช้งาน'})


@login_required
@staff_required
def user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'ลบผู้ใช้งานเรียบร้อยแล้ว')
        return redirect('user_management')
    return render(request, 'attendance/user_delete.html', {'user_obj': user})
