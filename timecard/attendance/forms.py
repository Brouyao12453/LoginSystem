
from django import forms
import base64
from django.core.files.base import ContentFile


class PhotoUploadForm(forms.Form):
    photo = forms.CharField(widget=forms.HiddenInput())
    def clean_photo(self):
        photo_data = self.cleaned_data['photo']
        try:
            # Handle base64 image data
            if not photo_data.startswith('data:image/jpeg;base64,'):
                raise forms.ValidationError("Invalid image format")

            imgstr = photo_data.split(';base64,')[1]
            data = ContentFile(base64.b64decode(imgstr), name='capture.jpg')
            return data
        except Exception as e:
            raise forms.ValidationError(f"Invalid image data: {str(e)}")