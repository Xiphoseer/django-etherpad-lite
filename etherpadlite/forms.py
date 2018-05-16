from django import forms
from django.utils.translation import ugettext_lazy as _
from etherpadlite.models import PadGroup, PadServer, Pad


class PadCreate(forms.Form):
    name = forms.CharField(label=_("Name"))
    group = forms.CharField(widget=forms.HiddenInput)

class GroupCreate(forms.ModelForm):
    class Meta:
        model = PadGroup
        exclude = ('groupID',)

class GroupSettingsForm(forms.ModelForm):
    class Meta:
        model = PadGroup
        exclude = ('groupID',)

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput(render_value=True))

class SettingsForm(forms.ModelForm):
    class Meta:
        model = Pad
        exclude = ("padid", "server")

class SearchForm(forms.Form):
    query = forms.CharField()
    
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['group']=forms.ModelChoiceField(queryset=PadGroup.objects.all())
        self.fields['server']=forms.ModelChoiceField(queryset=PadServer.objects.all())