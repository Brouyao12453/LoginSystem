# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Employee


class EmployeeRegisterForm(UserCreationForm):
    email = forms.EmailField(
        label="Work Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., john.doe@company.com',
        }),
        help_text="Must be a valid company email address.",
    )

    first_name = forms.CharField(
        label="First Name",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., John',
        }),
        help_text="Your legal first name.",
    )

    middle_name = forms.CharField(
        label="Middle Name (Optional)",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Michael',
        }),
    )

    last_name = forms.CharField(
        label="Last Name",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Doe',
        }),
        help_text="Your legal last name.",
    )

    phone_number = forms.CharField(
        label="Phone Number",
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., +1234567890',
        }),
        help_text="Format: +[CountryCode][Number]",
    )

    gender = forms.ChoiceField(
        label="Gender",
        choices=[("Male", "Male"), ("Female", "Female")],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    profile_image = forms.ImageField(
        label="Profile Picture (Optional)",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
    )

    reference_photo = forms.ImageField(
        label="Reference Photo (Optional)",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
    )

    position = forms.CharField(
        label="Job Position",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Software Engineer',
        }),
    )

    department = forms.CharField(
        label="Department",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., IT',
        }),
    )

    hourly_rate = forms.DecimalField(
        label="Hourly Rate ($)",
        max_digits=6,
        decimal_places=2,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 25.50',
            'step': '0.01',
        }),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Crispy forms adjustments
        for fieldname, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # First create the employee without ID to get the PK
            employee = Employee.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                middle_name=self.cleaned_data['middle_name'],
                last_name=self.cleaned_data['last_name'],
                phone_number=self.cleaned_data['phone_number'],
                gender=self.cleaned_data['gender'],
                profile_image=self.cleaned_data.get('profile_image'),
                reference_photo=self.cleaned_data.get('reference_photo'),
                position=self.cleaned_data['position'],
                department=self.cleaned_data['department'],
                hourly_rate=self.cleaned_data['hourly_rate'],
            )

            # Now generate the ID based on the created employee's PK
            first_part = self.cleaned_data['last_name'][:3].upper()  # First 3 of last name
            second_part = self.cleaned_data['first_name'][:3].upper()  # First 3 of first name
            employee_id = f"{employee.pk:04d}-{first_part}{second_part}"  # Combine with PK

            # Update the employee with the generated ID
            employee.employee_id = employee_id
            employee.save()

        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'phone_number',
            'gender',
            'profile_image',
            'reference_photo',
            'position',
            'department',
            'hourly_rate',
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'reference_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }
        labels = {
            'profile_image': 'Profile Picture',
            'reference_photo': 'Reference Photo',
        }
        help_texts = {
            'hourly_rate': 'Enter hourly wage rate',
        }