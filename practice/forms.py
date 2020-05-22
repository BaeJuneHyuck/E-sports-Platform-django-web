from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

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
    practice_time = forms.DateTimeField(widget=forms.SelectDateWidget)

    class Meta:
        model = Practice
        fields = ['title', 'text', 'game', 'tier', 'practice_time']

    def clean_practice_time(self):
        now = timezone.now().strftime("%Y-%m-%d")
        practice_time = self.cleaned_data['practice_time'].strftime("%Y-%m-%d")
        if practice_time <= now:
            raise ValidationError('지난 시간은 선택할 수 없습니다.')
        return practice_time

class CommentForm(forms.ModelForm):
    content = forms.CharField(max_length=600, widget=forms.Textarea)

    class Meta:
        model = Comment
        fields = ['content']