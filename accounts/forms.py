from django.contrib.auth import get_user_model
from django import forms

non_allowed_usernames = ['abc']
# Check for unique username and email


User = get_user_model()


class RegisterForm(forms.Form):
    username = forms.CharField()
    email = forms.EmailField()
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={"class": "form-control",
                   "id": "user-password"
                   }
        )
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(
            attrs={"class": "form-control",
                   "id": "user-confirmpassword"
                   }
        )
    )
    
    def clean(self):
        data = self.super().clean()
    
    def clean_username(self):
        username = self.cleaned_data.get("username")
        qs = User.objects.filter(username__iexact=username)
        # iexact means: thisIsMyUserName == thisismyusername
        if username in non_allowed_usernames:
            raise forms.ValidationError("This is an ivalid username, please pick another.")
        if not qs.exists():
            raise forms.ValidationError("This is an ivalid username, please pick another.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get("email")
        qs = User.objects.filter(email__iexact=email)
        if not qs.exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control",
                   "id": "user-password"
                   }
        )
    )
    
    # def clean(self):
    #  This is for the full form and will be executed at the end, i.e. after clean_* functions
    #     username = self.cleaned_data.get("username")
    #     password = self.cleaned_data.get("password")

    
    def clean_username(self):
        username = self.cleaned_data.get("username")
        qs = User.objects.filter(username__iexact=username)
        # iexact means: thisIsMyUserName == thisismyusername
        if username in non_allowed_usernames:
            raise forms.ValidationError("This is an ivalid username, please pick another.")
        if not qs.exists():
            raise forms.ValidationError("This is an ivalid username, please pick another.")
    
        return username
    
    def clean_username(self):
        username = self.cleaned_data.get("username")
        qs = User.objects.filter(username__iexact=username)
        # iexact means: thisIsMyUserName == thisismyusername
        if username in non_allowed_usernames:
            raise forms.ValidationError("This is an ivalid username, please pick another.")
        if not qs.exists():
            raise forms.ValidationError("This is an ivalid username, please pick another.")
    
        return username
