from django import forms
from .models import Practice, Comment
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

GAME=[
    ('overwatch', 'Overwatch'),
    ('lol', 'LOL'),
]

class PracticeCreateForm(forms.ModelForm):
    title = forms.CharField(max_length=200)
    text = forms.CharField(max_length=600, widget=forms.Textarea)
    game = forms.CharField(label='game', widget=forms.Select(choices=GAME))
    tier = forms.IntegerField()
    practice_time = forms.DateTimeField()

    class Meta:
        model = Practice
        fields = ['title', 'text', 'game', 'tier', 'practice_time']

class CommentForm(forms.ModelForm):
    content = forms.CharField(max_length=600, widget=forms.Textarea)

    class Meta:
        model = Comment
        fields = ['content']