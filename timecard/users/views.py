from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .forms import EmployeeRegisterForm, ProfileUpdateForm
from .models import Employee


class ProfileView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'users/profile.html'

    def get_object(self):
        return Employee.get_for_user(self.request.user)


class RegisterView(CreateView):
    form_class = EmployeeRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:profile')
        return super().dispatch(request, *args, **kwargs)


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('users:profile')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('users:login')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileUpdateForm
    template_name = 'users/profile_update.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user.employee_profile

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully!')
        return super().form_valid(form)