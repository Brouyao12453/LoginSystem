
import datetime
import logging
from datetime import timedelta
# attendance/views.py
from datetime import date, datetime, timedelta
import calendar
import logging
from django.utils import timezone
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from attendance.models import Schedule, LeaveRequest, Payroll, ShiftLog, Employee
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, When, Value, IntegerField
from django.db.models.expressions import Case, F
from django.views.generic import TemplateView, FormView, DetailView
from django.db.models import F, Value, IntegerField, ExpressionWrapper, Case, When, Sum
from django.db.models.functions import Greatest, Least

from django.http import Http404
from attendance.utils import is_face_match
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from .forms import PhotoUploadForm
from .models import ShiftLog, Employee, Schedule, LeaveRequest, Payroll
from attendance.utils import is_ajax, FaceRecognitionValidationMixin
import calendar
from datetime import date, datetime, timedelta

from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from attendance.models import Schedule, LeaveRequest, Payroll, ShiftLog

logger = logging.getLogger(__name__)


class DashboardView(TemplateView):
    """ Dashboard view"""
    template_name = 'attendance/dashboard.html'

    def get_context_data(self, **kwargs):
        """ Get context data for the dashboard view"""
        context = super().get_context_data(**kwargs)
        try:
            employee = Employee.objects.get(user=self.request.user)
        except Employee.DoesNotExist:
            raise Http404("Employee profile not found. Please contact admin.")

        today_log = ShiftLog.objects.filter(employee=employee, clock_in__date=timezone.now().date()).first()
        context.update({
            'employee': employee,
            'today_log': today_log
        })
        return context

class ClockInView(LoginRequiredMixin, FormView):
    template_name = 'attendance/camera_upload.html'
    form_class = PhotoUploadForm
    success_url = reverse_lazy('attendance:dashboard')

    def form_valid(self, form):
        user = self.request.user
        employee = Employee.objects.get(user=user)
        print("I am printing the user", employee) # Here for debuginc code
        today = timezone.now().date()
        existing_log = ShiftLog.objects.filter(employee=employee, clock_in__date=today).first()
        print("existing_log", existing_log) # Here for debuginc code
        # Prevent double clock-in
        if existing_log and existing_log.clock_in:
            message = "You have already clocked in today."
            return self._response_error(form, message)

        # Face recognition
        uploaded_photo = form.cleaned_data['photo']
        reference_photo_path = employee.reference_photo.path
        uploaded_photo_file = uploaded_photo.file

        is_match, error = is_face_match(reference_photo_path, uploaded_photo_file)
        print("is_match, error", is_match, error)
        if not is_match:
            return self._response_error(form, error or "Face not matched")

        # Create or update today's ShiftLog
        if not existing_log:
            print("Creating new ShiftLog", employee.user.username)
            existing_log = ShiftLog(employee=employee)

        existing_log.clock_in = timezone.now()
        existing_log.clock_in_photo = uploaded_photo

        print("Before save:")
        print("clock_in:", existing_log.clock_in)
        print("clock_in_photo:", uploaded_photo)
        print("uploaded_photo.name:", uploaded_photo.name)
        print("uploaded_photo type:", type(uploaded_photo))

        try:
            existing_log.save()
            print("ShiftLog saved successfully!")
        except Exception as e:
            print("Error saving ShiftLog:", e)
            return self._response_error(form, "Error saving ShiftLog")

        if is_ajax(self.request):
            return JsonResponse({
                "success": True,
                "message": f'Clocked in successfully.{error}',
                "redirect_url": str(self.success_url)
            })
        messages.success(self.request, "Clocked in successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        return self._response_error(form, "Invalid form submission")

    def _response_error(self, form, message):
        if is_ajax(self.request):
            return JsonResponse({"success": False, "message": message})
        messages.warning(self.request, message)
        return super().form_invalid(form)


class StartBreakView(LoginRequiredMixin, FaceRecognitionValidationMixin, FormView):
    """ Start break view"""
    template_name = 'attendance/camera_upload_break_in.html'
    form_class = PhotoUploadForm
    success_url = reverse_lazy('attendance:dashboard')

    def form_valid(self, form):
        """ validate form and start break"""
        employee = Employee.objects.get(user=self.request.user)
        log = ShiftLog.objects.filter(employee=employee, clock_in__date=timezone.now().date()).first()

        # Must be clocked in and not clocked out
        if not log or not log.clock_in or log.clock_out:
            message = "Cannot start break: you must be clocked in and not clocked out."
            return JsonResponse({"success": False, "message": message}) if is_ajax(self.request) else self.form_invalid(form)

        # Must not already be on break
        if log.break_start and not log.break_end:
            message = "You are already on a break."
            return JsonResponse({"success": False, "message": message}) if is_ajax(self.request) else self.form_invalid(form)

        # Check if 3 hours have passed since clock-in
        elapsed = timezone.now() - log.clock_in
        if elapsed.total_seconds() < 3 * 3600:
            message = "You can only start a break after 3 hours of work."
            return JsonResponse({"success": False, "message": message}) if is_ajax(self.request) else self.form_invalid(form)

        # Face recognition
        is_match, error = self.validate_face(form)
        if not is_match:
            return JsonResponse({"success": False, "message": error}) if is_ajax(self.request) else self.form_invalid(form)

        log.break_start = timezone.now()
        log.break_start_photo = form.cleaned_data['photo']
        log.save()

        return JsonResponse({
            "success": True,
            "message": f"Break started.{error}",
            "redirect_url": str(self.success_url)
        }) if is_ajax(self.request) else super().form_valid(form)


class EndBreakView(LoginRequiredMixin, FaceRecognitionValidationMixin, FormView):
    """ End break view"""
    template_name = 'attendance/camera_upload_break_out.html'
    form_class = PhotoUploadForm
    success_url = reverse_lazy('attendance:dashboard')

    def form_valid(self, form):
        """ validate form and end break"""
        employee = Employee.objects.get(user=self.request.user)
        log = ShiftLog.objects.filter(employee=employee, clock_in__date=timezone.now().date()).first()

        # Must be on break
        if not log or not log.break_start or log.break_end:
            message = "No active break found to end."
            return JsonResponse({"success": False, "message": message}) if is_ajax(self.request) else self.form_invalid(form)

        # Must have been on break for at least 30 minutes
        elapsed = timezone.now() - log.break_start
        if elapsed.total_seconds() < 30 * 60:
            message = "You can only end a break after 30 minutes."
            return JsonResponse({"success": False, "message": message}) if is_ajax(self.request) else self.form_invalid(form)

        # Face validation
        is_match, error = self.validate_face(form)
        if not is_match:
            return JsonResponse({"success": False, "message": error}) if is_ajax(self.request) else self.form_invalid(form)

        log.break_end = timezone.now()
        log.break_end_photo = form.cleaned_data['photo']
        log.save()

        return JsonResponse({
            "success": True,
            "message": f"Break ended.{error}",
            "redirect_url": str(self.success_url)
        }) if is_ajax(self.request) else super().form_valid(form)


class ClockOutView(LoginRequiredMixin, FormView):

    template_name = 'attendance/camera_upload_clock_out.html'
    form_class = PhotoUploadForm
    success_url = reverse_lazy('attendance:dashboard')

    def form_valid(self, form):
        print("ClockOutView form_valid")
        employee = Employee.objects.get(user=self.request.user)
        log = ShiftLog.objects.filter(employee=employee, clock_in__date=timezone.now().date()).first()

        uploaded_photo = form.cleaned_data['photo']
        reference_photo_path = employee.reference_photo.path
        uploaded_photo_file = uploaded_photo.file

        is_match, error = is_face_match(reference_photo_path, uploaded_photo_file)
        print("is_match, error", is_match, error)

        if not is_match:
            if is_ajax(self.request):
                return JsonResponse({"success": False, "message": error or "Face not matched"})
            messages.error(self.request, error or "Face not matched")
            return self.form_invalid(form)

        if not log or log.clock_out:
            message = "Already clocked out or no clock in found."
            if is_ajax(self.request):
                return JsonResponse({"success": False, "message": message})
            messages.warning(self.request, message)
            return self.form_invalid(form)

        log.clock_out = timezone.now()
        log.clock_out_photo = uploaded_photo
        log.save()

        if is_ajax(self.request):
            return JsonResponse({
                "success": True,
                "message": f"Clocked out successfully.{ error}",
                "redirect_url": str(self.success_url)
            })

        messages.success(self.request, "Clocked out successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        if is_ajax(self.request):
            return JsonResponse({"success": False, "message": "Invalid form submission"})
        return super().form_invalid(form)

class ScheduleListViews(ListView):
    model = Schedule
    """
    The class is for display the list of the working the schedule 
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        return context


class TimeCardView(LoginRequiredMixin, DetailView):
    template_name = 'attendance/timecard.html'
    context_object_name = 'employee'

    def get_object(self):
        user = self.request.user
        if not isinstance(user, User):
            user = User.objects.get(username=user)
        try:
            employee = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            employee = Employee.get_for_user(user)
            print("this is where the leave stats", employee)
        return employee


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.object

        # --- Date range ---
        today = timezone.now().date()
        start_date = self.request.GET.get('start_date', today.replace(day=1))
        end_date = self.request.GET.get(
            'end_date',
            today.replace(day=calendar.monthrange(today.year, today.month)[1])
        )

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # --- Logs ---
        shift_logs = ShiftLog.objects.filter(
            employee=employee,
            clock_in__date__gte=start_date,
            clock_in__date__lte=end_date
        ).order_by('clock_in')

        total_hours = timedelta()
        overtime_hours = timedelta()

        for log in shift_logs:
            if log.clock_in and log.clock_out:
                duration = log.clock_out - log.clock_in
                if log.break_start and log.break_end:
                    duration -= (log.break_end - log.break_start)

                # attach to object for template
                log.worked_duration = duration

                total_hours += duration
                if duration > timedelta(hours=8):
                    overtime_hours += duration - timedelta(hours=8)
            else:
                log.worked_duration = None

        # --- Leave stats ---
        leave_stats = (
            LeaveRequest.objects.filter(
                employee=employee.pk,
                approved=True,
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            .values('type')
            .annotate(
                days=Sum(
                    ExpressionWrapper(
                        Least(F('end_date'), end_date) - Greatest(F('start_date'), start_date) + Value(1),
                        output_field=IntegerField(),
                    )
                )
            )
        )

        context.update({
            'shift_logs': shift_logs,
            'start_date': start_date,
            'end_date': end_date,
            'total_hours': total_hours,
            'overtime_hours': overtime_hours,
            'leave_stats': leave_stats,
        })
        print('value of the context',leave_stats)
        return context



class ScheduleCalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'attendance/calendar.html'
    logger = logging.getLogger(__name__)

    def get_employee(self):
        try:
            return self.request.user.employee_profile
        except Employee.DoesNotExist:
            return Employee.get_for_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_employee()
        today = timezone.now().date()
        year = int(kwargs.get('year', today.year))
        month = int(kwargs.get('month', today.month))
        month_start_date = date(year, month, 1)

        # Step 1: Build base day structure (working day logic)
        working_day_builder = WorkingDayStatusBuilder(employee, year, month)
        days = working_day_builder.build()

        # Step 2: Add clock-in/out and late status
        days = ClockingStatusBuilder(employee, year, month).enrich_days(days)

        # Step 3: Add payday flags
        paydays = PaydayChecker.get_paydays(employee, working_day_builder.first_day, working_day_builder.last_day)
        for day in days:
            day['is_payday'] = day['date'] in paydays

        # Step 4: Add missed punch status
        days = MissingPunchChecker.enrich_days(days)

        weeks = [days[i:i + 7] for i in range(0, len(days), 7)]
        prev_month_year = year if month > 1 else year - 1
        prev_month_num = month - 1 if month > 1 else 12
        next_month_year = year if month < 12 else year + 1
        next_month_num = month + 1 if month < 12 else 1

        context.update({
            'month_start_date': month_start_date,
            'weeks': weeks,
            'current_year': year,
            'current_month': month,
            'today': today,
            'prev_month': date(prev_month_year, prev_month_num, 1),
            'next_month': date(next_month_year, next_month_num, 1),
        })
        return context

    @staticmethod
    def get_employee_filter_value_static(model_field, employee):
        if model_field.remote_field.model.__name__ == 'User':
            return employee.user
        return employee


class WorkingDayStatusBuilder:
    def __init__(self, employee, year, month):
        self.employee = employee
        self.year = year
        self.month = month
        self.first_day = date(year, month, 1)
        self.last_day = date(year, month, calendar.monthrange(year, month)[1])
        self.cal = calendar.Calendar()

    def get_schedules(self):
        schedule_emp_value = ScheduleCalendarView.get_employee_filter_value_static(Schedule._meta.get_field('employee'), self.employee)
        return {
            (s['date'].date() if hasattr(s['date'], 'date') else s['date']): s
            for s in Schedule.objects.filter(
                employee=schedule_emp_value,
                date__range=(self.first_day, self.last_day)
            ).values('date', 'is_working_day', 'start_time')
        }

    def get_leaves(self):
        leave_emp_value = ScheduleCalendarView.get_employee_filter_value_static(LeaveRequest._meta.get_field('employee'), self.employee)
        return list(LeaveRequest.objects.filter(
            employee=leave_emp_value,
            start_date__lte=self.last_day,
            end_date__gte=self.first_day,
            approved=True
        ))

    def build(self):
        schedules = self.get_schedules()
        leaves = self.get_leaves()
        cal = calendar.Calendar(firstweekday=0)
        month_days = [d for d in cal.itermonthdates(self.year, self.month) if d.month == self.month]

        # Determine weekday of first and last day
        first_day = month_days[0]
        last_day = month_days[-1]

        # Pad at start
        while first_day.weekday() != 0:  # Monday
            first_day -= timedelta(days=1)
            month_days.insert(0, first_day)

        # Pad at end
        while last_day.weekday() != 6:  # Sunday
            last_day += timedelta(days=1)
            month_days.append(last_day)

        days = []
        for day in month_days:
            schedule = schedules.get(day)
            is_leave = any(leave.start_date <= day <= leave.end_date for leave in leaves)
            days.append({
                'date': day,
                'weekday': day.weekday(),
                'is_today': day == timezone.now().date(),
                'is_weekend': day.weekday() >= 5,
                'is_scheduled': bool(schedule and schedule['is_working_day']),
                'is_day_off': bool(schedule and not schedule['is_working_day']),
                'is_leave': is_leave,
                'schedule': schedule,
                'in_current_month': day.month == self.month,
            })
        return days


class PaydayChecker:
    @staticmethod
    def get_paydays(employee, start_date, end_date):
        payroll_emp_value = ScheduleCalendarView.get_employee_filter_value_static(Payroll._meta.get_field('employee'), employee)
        return set(Payroll.objects.filter(
            employee=payroll_emp_value,
            payday__range=(start_date, end_date)
        ).values_list('payday', flat=True))


class ClockingStatusBuilder:
    def __init__(self, employee, year, month):
        self.employee = employee
        self.year = year
        self.month = month
        self.first_day = date(year, month, 1)
        self.last_day = date(year, month, calendar.monthrange(year, month)[1])

    def get_shift_logs(self):
        shiftlog_emp_value = ScheduleCalendarView.get_employee_filter_value_static(ShiftLog._meta.get_field('employee'), self.employee)
        return {
            sl.clock_in.date(): sl for sl in ShiftLog.objects.filter(
                employee=shiftlog_emp_value,
                clock_in__date__range=(self.first_day, self.last_day)
            )
        }

    def enrich_days(self, days):
        shift_logs = self.get_shift_logs()
        for day in days:
            shift_log = shift_logs.get(day['date'])
            schedule = day.get('schedule')
            day.update({
                'has_clock_in': bool(shift_log and shift_log.clock_in),
                'has_clock_out': bool(shift_log and shift_log.clock_out),
                'is_late': self.check_late_arrival(shift_log, schedule),
                'shift_log': shift_log,  # Pass for punch checker
            })
        return days

    def check_late_arrival(self, shift_log, schedule):
        if not schedule or not schedule.get('start_time') or not shift_log or not shift_log.clock_in:
            return False
        scheduled_start = datetime.combine(shift_log.clock_in.date(), schedule['start_time'])
        return shift_log.clock_in > scheduled_start + timedelta(minutes=15)


class MissingPunchChecker:
    @staticmethod
    def enrich_days(days):
        today = timezone.now().date()
        for day in days:
            shift_log = day.get('shift_log')
            missed_punch = False
            if shift_log:
                if shift_log.clock_in and not shift_log.clock_out and shift_log.clock_in.date() != today:
                    missed_punch = True
                elif shift_log.break_start and not shift_log.break_end:
                    missed_punch = True
            day['missed_punch'] = missed_punch
        return days


class TimeDashboardView(LoginRequiredMixin, TemplateView):
    pass
