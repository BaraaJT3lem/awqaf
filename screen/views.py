from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from collections import defaultdict, Counter
from django.shortcuts import redirect, get_object_or_404
from django.db.models import OuterRef, Subquery
import random
from .models import Student, STATUS_CHOICES, ScreenSettings
from .forms import StudentForm
from django.db.models import Max
from django.utils.timezone import now, timedelta
import json
from django import forms
from .models import Student
from .forms import ScreenSettingsForm
from .models import ExamResult
import openpyxl
import os
import csv
from django.conf import settings
from django.contrib import messages
import datetime
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from django.utils.encoding import smart_str

def get_room_count():
    settings = ScreenSettings.objects.last()
    return settings.room_count if settings else 5

def get_least_loaded_room():
    room_count = get_room_count()
    rooms = list(range(1, room_count + 1))
    counts = Counter(Student.objects.values_list('room', flat=True))
    for r in rooms:
        counts.setdefault(r, 0)
    return min(rooms, key=lambda r: counts[r])
@login_required
def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)

            if not student.room:
                room_count = get_room_count()
                all_rooms = list(range(1, room_count + 1))

                # Count how many students are in each room
                room_counts = Counter(Student.objects.values_list('room', flat=True))

                # Ensure every room is present
                for room in all_rooms:
                    room_counts.setdefault(room, 0)

                # Find the minimum number of students in any room
                min_count = min(room_counts.values())

                # Filter only rooms with the fewest students
                candidate_rooms = [room for room, count in room_counts.items() if count == min_count]

                # Randomly choose one of those
                student.room = random.choice(candidate_rooms)

            student.save()
            return redirect('/screen/add-student')
    else:
        form = StudentForm()

    students_by_room = defaultdict(list)
    for student in Student.objects.all().order_by('number'):
        students_by_room[student.room].append(student)

    # Add this to get the distinct institutes for dropdown
    all_institutes = Student.objects.values_list('institute_name', flat=True).distinct().order_by('institute_name')

    return render(request, 'screen/add_student.html', {
        'form': form,
        'students_by_room': students_by_room,
        'rooms': range(1, get_room_count() + 1),
        'status_choices': STATUS_CHOICES,
        'all_institutes': all_institutes,  # Add this line
    })




def public_screen(request):
    # Get all students ordered by number
    students = list(Student.objects.all().order_by('number'))

    # Fetch the latest ExamResult for each student (by highest ID)
    latest_ids = (ExamResult.objects
                  .values('number')
                  .annotate(latest_id=Max('id'))
                  .values_list('latest_id', flat=True))

    results = ExamResult.objects.filter(id__in=latest_ids)

    # Map results to student number for fast lookup
    latest_results = {
        res.number: {
            'grade': res.grade,
            'result': res.result
        }
        for res in results
    }

    # Attach latest grade/result to student objects
    for student in students:
        result = latest_results.get(student.number)
        student.latest_grade = result['grade'] if result else None
        student.latest_result = result['result'] if result else None

    # Group students by their room number
    students_by_room = defaultdict(list)
    for student in students:
        students_by_room[student.room].append(student)

    # Sort each room's students so that finished students come last,
    # but keep ascending order by student number otherwise
    for room, room_students in students_by_room.items():
        room_students.sort(key=lambda s: (s.status == 'finished', s.number))

    # Estimated time from settings
    screen_settings = ScreenSettings.get_settings()
    estimate_minutes = screen_settings.estimate_time_per_student or 5

    # Compute estimated waiting time for students in waiting/on_waiting_list
    student_wait_times = {}
    for room, students_in_room in students_by_room.items():
        waiting_students = [s for s in students_in_room if s.status in ['waiting', 'on_waiting_list']]
        for idx, student in enumerate(waiting_students):
            student_wait_times[student.number] = (idx + 1) * estimate_minutes

    return render(request, 'screen/public_screen.html', {
        'students_by_room': students_by_room,
        'rooms': range(1, get_room_count() + 1),
        'student_wait_times': student_wait_times,
    })

@login_required
def clear_students(request):
    if request.method == 'POST':
        Student.objects.all().delete()
    return redirect('/screen/add-student')

def apply_automatic_status_for_room(room):
    students = Student.objects.filter(room=room).order_by('number')
    for i, student in enumerate(students):
        if i == 0:
            student.status = 'in_exam'
        elif 1 <= i <= 6:
            student.status = 'waiting'
        else:
            student.status = 'on_waiting_list'
        student.save()

def update_student_status(request, student_number):
    if request.method == 'POST':
        student = get_object_or_404(Student, number=student_number)
        new_status = request.POST.get('status')

        if new_status == "remove":
            student.delete()
            messages.success(request, f"تم حذف الطالب {student.name}")
        else:
            student.status = new_status
            student.save()
            messages.success(request, f"تم تحديث حالة الطالب {student.name} إلى {student.get_status_display()}")

    return redirect('add_student')


def apply_automatic_status():
    settings = ScreenSettings.objects.last()
    waiting_limit = settings.waiting_count if settings else 5

    rooms = Student.objects.values_list('room', flat=True).distinct()

    for room in rooms:
        students = Student.objects.filter(room=room).exclude(status='finished').order_by('number')
        for i, student in enumerate(students):
            if i == 0:
                student.status = 'in_exam'
            elif 1 <= i <= waiting_limit:
                student.status = 'waiting'
            else:
                student.status = 'on_waiting_list'
            student.save()


@login_required
def trigger_automatic_status(request):
    apply_automatic_status()
    return redirect('/screen/add-student')


@require_POST
@login_required
def submit_grade(request, student_number):
    student = get_object_or_404(Student, number=student_number)

    if student.exam_type == "gh":
        final_grade = float(request.POST.get("final_grade", "100"))
    elif student.exam_type == "nz":
        final_grade = float(request.POST.get("final_grade1", "100"))
    else:
        final_grade = 1 


    if student.exam_type == "gh":
        pass_threshold = 80
        expected_questions = 3
    else:  # nz
        pass_threshold = 90
        expected_questions = 5

    mistakes_json_str = request.POST.get("mistakes_json", "{}")
    try:
        mistakes = json.loads(mistakes_json_str)
    except json.JSONDecodeError:
        mistakes = {}

    # Validate number of questions in mistakes
    answered_questions = len(mistakes.keys())
    if answered_questions < expected_questions:
        # You can raise an error or handle as you want
        # For example:
        # return HttpResponseBadRequest("Not all questions answered.")
        pass  # or just continue

    result = "ناجح" if final_grade >= pass_threshold else "إعادة"

    ExamResult.objects.create(
        number=student.number,
        name=student.name,
        grade=final_grade,
        result=result,
        room=student.room
    )

    apply_automatic_status()

    student.status = 'finished'
    student.save()

    csv_path = os.path.join(settings.BASE_DIR, 'grades_log.csv')
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Student Number', 'Name', 'Final Grade', 'Result'])
        writer.writerow([student.number, student.name, final_grade, result])

    return redirect(f"/mobileapp/room/room{student.room}/")




@login_required
def edit_settings(request):
    settings = ScreenSettings.get_settings()

    if request.method == 'POST':
        form = ScreenSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return redirect('/screen/add-student')
    else:
        form = ScreenSettingsForm(instance=settings)

    return render(request, 'screen/edit_settings.html', {'form': form})

EXAM_TYPE_MAP = {
    "غيباً": "gh",
    "نظراً": "nz",
}

@login_required
@require_POST
def upload_excel(request):
    file = request.FILES.get("file")
    if not file or not file.name.endswith(".xlsx"):
        return redirect('/screen/add-student')

    wb = openpyxl.load_workbook(file)
    sheet = wb.active

    current_number = Student.objects.aggregate(Max('number'))['number__max'] or 0

    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not any(row):
            continue

        number_cell = str(row[0]).strip() if row[0] else ''
        name = str(row[1]).strip() if row[1] else ''

        if not name or "الاسم" in name:
            continue

        try:
            father_name = str(row[2]).strip() if row[2] else ''
            birth_year = int(row[3]) if row[3] else None
            institute = str(row[4]).strip() if row[4] else ''
            exam_type_arabic = str(row[5]).strip() if row[5] else ''
            exam_type = EXAM_TYPE_MAP.get(exam_type_arabic, None)
            parts = int(row[6]) if row[6] else 0

            if not exam_type:
                print(f"Unknown exam type: {exam_type_arabic} in row: {row}")
                continue  # skip invalid rows

            current_number += 1

            Student.objects.create(
                number=current_number,
                name=name,
                father_name=father_name,
                birth_date=f"{birth_year}-01-01" if birth_year else None,
                institute_name=institute,
                exam_type=exam_type,
                memorized_parts=parts
            )
        except Exception as e:
            print("Error in row:", row, str(e))
            continue

    return redirect('/screen/add-student')

def remove_student(request, student_number):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_number)
        student.delete()
        messages.success(request, "تم حذف الطالب بنجاح.")
    return redirect('add_student')  # or your relevant page name

@require_POST
@login_required
def clear_all_results(request):
    # Delete all ExamResult entries
    ExamResult.objects.all().delete()

    # Delete only students with status "finished"
    Student.objects.filter(status="finished").delete()

    # Redirect to the add-student page after clearing
    return redirect('/screen/add-student')



@login_required
def export_students_excel(request):
    institute_name = request.GET.get('institute')
    if not institute_name:
        return HttpResponse("يرجى اختيار اسم المعهد", status=400)

    settings = ScreenSettings.get_settings()
    estimated_time_per_student = settings.estimate_time_per_student or 5
    exam_start_time = settings.exam_start_time or datetime.time(8, 0)
    start_minutes = exam_start_time.hour * 60 + exam_start_time.minute

    # Build room-wise queues
    students = Student.objects.all().order_by('room', 'number')
    room_queues = defaultdict(list)
    for student in students:
        room_queues[student.room].append(student)

    # Assign estimated times based on position in room queue
    student_times = {}
    max_queue_length = max(len(queue) for queue in room_queues.values())
    for index in range(max_queue_length):
        for room in sorted(room_queues.keys()):
            queue = room_queues[room]
            if index < len(queue):
                student = queue[index]
                est_minutes = start_minutes + index * estimated_time_per_student
                est_time = f"{est_minutes // 60:02}:{est_minutes % 60:02}"
                student_times[student.number] = est_time

    # Create Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.sheet_view.rightToLeft = True
    current_row = 1

    def write_headers():
        nonlocal current_row
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
        ws.cell(row=current_row, column=1, value="الجمهورية العربية السورية").alignment = Alignment(horizontal='center')
        ws.cell(row=current_row, column=1).font = Font(size=14, bold=True)
        current_row += 1

        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
        ws.cell(row=current_row, column=1, value="استمارة  اختبار الأجزاء المتفرقة").alignment = Alignment(horizontal='center')
        ws.cell(row=current_row, column=1).font = Font(size=12, bold=True)
        current_row += 1

        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=4)
        ws.cell(row=current_row, column=1, value="وزارة الأوقاف").alignment = Alignment(horizontal='center')
        ws.cell(row=current_row, column=1).font = Font(bold=True)
        ws.merge_cells(start_row=current_row, start_column=5, end_row=current_row, end_column=8)
        ws.cell(row=current_row, column=5, value="مركز الحسنين").alignment = Alignment(horizontal='center')
        ws.cell(row=current_row, column=5).font = Font(bold=True)
        current_row += 1

        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
        ws.cell(row=current_row, column=1, value="مديرية معاهد تحفيظ القرآن الكريم بدمشق").alignment = Alignment(horizontal='center')
        ws.cell(row=current_row, column=1).font = Font(bold=True)
        current_row += 2

    def write_table_header():
        nonlocal current_row
        headers = ['الرقم', 'الاسم والكنية', 'اسم الأب', 'تاريخ الولادة', 'اسم المعهد', 'غيباً/نظراً', 'الأجزاء المحفوظة', 'الوقت المتوقع']
        for i, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=i, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        current_row += 1

    def write_student_row(student):
        nonlocal current_row
        exam_type = student.get_exam_type_display() if hasattr(student, 'get_exam_type_display') else student.exam_type
        est_time = student_times.get(student.number, '')
        ws.append([
            student.number,
            smart_str(student.name),
            smart_str(student.father_name or ''),
            student.birth_date.year if student.birth_date else '',
            smart_str(student.institute_name or ''),
            exam_type,
            student.memorized_parts or '',
            est_time
        ])
        current_row += 1

    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 20
    ws.column_dimensions['F'].width = 10
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 15

    if institute_name == '__all__':
        grouped = defaultdict(list)
        for s in students:
            grouped[s.institute_name].append(s)

        for institute in sorted(grouped.keys()):
            write_headers()
            ws.cell(row=current_row, column=1, value=f"المعهد: {institute}")
            current_row += 1
            write_table_header()
            # Sort by assigned time for this institute
            for stu in sorted(grouped[institute], key=lambda x: student_times.get(x.number, '')):
                write_student_row(stu)
            current_row += 2
        filename = f"All_Students_{datetime.date.today()}.xlsx"
    else:
        filtered_students = Student.objects.filter(institute_name=institute_name).order_by('room', 'number')
        write_headers()
        ws.cell(row=current_row, column=1, value=f"المعهد: {institute_name}")
        current_row += 1
        write_table_header()
        for student in sorted(filtered_students, key=lambda x: student_times.get(x.number, '')):
            write_student_row(student)
        filename = f"Students_{institute_name}_{datetime.date.today()}.xlsx"

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

