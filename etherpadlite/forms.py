from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _


class PadCreate(forms.Form):
    name = forms.CharField(label=_("Name"))
    group = forms.CharField(widget=forms.HiddenInput)


class GroupCreate(forms.ModelForm):
    class Meta:
        model = Group
        exclude = ('permissions',)

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput(render_value=True))

class SettingsForm(forms.Form):
    password = forms.CharField(max_length=100)
    is_public = forms.BooleanField()