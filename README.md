# ระบบลงชื่อปฏิบัติงานออนไลน์ (WFH Attendance System)

โปรเจกต์ตัวอย่าง Web Application สำหรับใช้งานจริงด้วย Django รองรับ:
- Login
- Dashboard
- Check-in / Check-out
- เก็บรายละเอียดงาน, รูปหลักฐาน, GPS
- ประวัติย้อนหลัง
- Reports
- Export Excel / PDF
- Admin จัดการผู้ใช้งาน

## วิธีติดตั้ง
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

เปิดใช้งานที่:
- http://127.0.0.1:8000/
- Django admin: http://127.0.0.1:8000/admin-django/

## โครงสร้างหลัก
- `attendance/models.py` = ตารางข้อมูล Department, UserProfile, Attendance
- `attendance/views.py` = logic หน้า dashboard, attendance, reports, export
- `attendance/templates/` = หน้าเว็บทั้งหมด
- `static/css/style.css` = theme สีน้ำเงิน-ขาว-เทา

## ข้อแนะนำก่อนใช้งานจริง
1. เปลี่ยน `SECRET_KEY`
2. ปิด `DEBUG = False`
3. ตั้ง `ALLOWED_HOSTS`
4. ย้ายฐานข้อมูลเป็น PostgreSQL หรือ MySQL
5. ตั้งค่า web server เช่น Nginx/Apache
6. เก็บไฟล์ media/static ให้เหมาะกับ production
7. เพิ่มการตรวจสอบสิทธิ์และ log การใช้งาน

## หมายเหตุ
- ระบบนี้เป็นฐานสำหรับนำไปพัฒนาต่อใช้งานจริง
- ฝั่ง GPS ใช้ browser geolocation จึงต้องอนุญาตตำแหน่งบนมือถือ/เบราว์เซอร์
