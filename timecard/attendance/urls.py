"""
URL configuration for timecard project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.urls import path
from attendance.views import (
    DashboardView, ClockInView, StartBreakView, EndBreakView, ClockOutView,
    ScheduleCalendarView, TimeCardView
)

from timecard import settings
from attendance.views import ScheduleListViews, TimeDashboardView

app_name = 'attendance'

urlpatterns = [
    path('', ScheduleCalendarView.as_view(), name='calendar'),
    path('<int:year>/<int:month>/', ScheduleCalendarView.as_view(), name='calendar'),
    path('timecard/', TimeCardView.as_view(), name='timecard'),
    path('clock/', DashboardView.as_view(), name='dashboard'),
    path('clock-in/', ClockInView.as_view(), name='clock_in'),
    path('start-break/', StartBreakView.as_view(), name='start_break'),
    path('end-break/', EndBreakView.as_view(), name='end_break'),
    path('clock-out/', ClockOutView.as_view(), name='clock_out'),
    path("working-data/", ScheduleListViews.as_view(), name='working_date'),
    path('time_dashboard/', TimeDashboardView.as_view(), name='time_dashboard')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)