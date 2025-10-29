from django import forms
from .models import Users
from django.contrib.auth.hashers import make_password

class RegistrationForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'First Name', 'required':'required'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Last Name', 'required':'required'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Username', 'required':'required'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password', 'required':'required'}))
    height = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'Height cm', 'required':'required'}))
    gender = forms.ChoiceField(choices=[('M','Male'),('F','Female')],
                               widget=forms.Select(attrs={'required':'required'}))


    class Meta: #tells django for which model is the form
        model = Users
        fields = ['first_name', 'last_name', 'username', 'password', 'gender', 'height']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password'])#hashing the password
        if commit:
            user.save()
        return user
    
class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Username', 'required':'required'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password', 'required':'required'}))
