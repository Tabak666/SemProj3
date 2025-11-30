from django import forms
from .models import Users
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

class RegistrationForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'First Name', 'required':'required'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Last Name', 'required':'required'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Username', 'required':'required'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password', 'required':'required'}))
    height = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'placeholder':'Height cm', 
            'required':'required',
            'min':'1',
            'max':'300',
            'step':'1'
        })
    )
    gender = forms.ChoiceField(choices=[('M','Male'),('F','Female')],
                               widget=forms.Select(attrs={'required':'required'}))


    class Meta: #tells django for which model is the form
        model = Users
        fields = ['first_name', 'last_name', 'username', 'password', 'gender', 'height']

    def clean_height(self):
        """Validate that height is positive"""
        height = self.cleaned_data.get('height')
        if height is not None and height <= 0:
            raise ValidationError('Height must be a positive number (greater than 0cm).')
        if height is not None and height > 300:
            raise ValidationError('Height must be less than or equal to 300 cm.')
        return height

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])#hashing the password
        if commit:
            user.save()
        return user
    
class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Username', 'required':'required'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password', 'required':'required'}))

class ForgotPasswordForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Username',
            'required': 'required',
            'id': 'id_username'
        })
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'New Password',
            'required': 'required',
            'id': 'id_new_password'
        })
    )
    repeat_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repeat New Password',
            'required': 'required',
            'id': 'id_repeat_password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        repeat_password = cleaned_data.get('repeat_password')
        username = cleaned_data.get('username')

        # Check if user exists
        if username:
            try:
                Users.objects.get(username=username)
            except Users.DoesNotExist:
                raise ValidationError('User with this username does not exist.')

        # Check if passwords match
        if new_password and repeat_password:
            if new_password != repeat_password:
                raise ValidationError('Passwords do not match.')

        return cleaned_data