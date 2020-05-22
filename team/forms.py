from django import forms
from .models import Team, TeamRelation
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

GAME=[
    ('overwatch', 'Overwatch'),
    ('lol', 'LOL'),
]

class TeamCreateForm(forms.ModelForm):
    name = forms.CharField(max_length=200, label='팀명')
    game = forms.CharField(label='게임', widget=forms.Select(choices=GAME))
    text = forms.CharField(label='설명', max_length=600, widget=forms.Textarea, required=False)
    visible = forms.BooleanField(label='팀 공개', required=False)

    class Meta:
        model = Team
        fields = ['name', 'game', 'text', 'visible']
        widgets = {
            'master ': forms.HiddenInput,
        }

class TeamRelationCreateForm(forms.ModelForm):

    class Meta:
        model = TeamRelation
        fields = []
        widgets = {
            'team_pk ': forms.HiddenInput,
            'user_pk ': forms.HiddenInput
        }
