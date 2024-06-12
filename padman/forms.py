from django import forms
from django.utils.translation import ugettext_lazy as _

from . import models


class PadCreate(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=256)
    category = forms.CharField(widget=forms.HiddenInput)
    server = forms.ModelChoiceField(queryset=models.PadServer.objects.all())

    def __init__(self, *args, **kwargs):
        kwargs['initial'].update({'server': models.PadServer.objects.all().first()})
        super().__init__(*args, **kwargs)

class GroupCreate(forms.ModelForm):
    class Meta:
        model = models.PadGroup
        exclude = ('groupID',)

class GroupSettingsForm(forms.ModelForm):
    class Meta:
        model = models.PadGroup
        exclude = ('groupID',)

class GroupPadImportForm(forms.Form):

    def import_unknown_pads(self, group):
        pads = group.unknown_pads()
        for padid in pads:
            pad = Pad()
            pad.group = group
            pad.server = group.server
            pad.name = padid
            pad.padid = group.groupID + '$' + padid
            pad.save()

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput(render_value=True))

class SettingsForm(forms.ModelForm):
    class Meta:
        model = models.Pad
        exclude = ("padid", "server", "group")

class SearchForm(forms.Form):
    query = forms.CharField()
    
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['group']=forms.ModelChoiceField(queryset=PadGroup.objects.all())
        self.fields['server']=forms.ModelChoiceField(queryset=PadServer.objects.all())
