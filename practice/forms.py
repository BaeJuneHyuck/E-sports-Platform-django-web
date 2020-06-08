from datetime import datetime

from dateutil.relativedelta import relativedelta
from django import forms
from django.core.exceptions import ValidationError

from .models import Practice, Comment

GAME=[
    ('overwatch', 'Overwatch'),
    ('lol', 'LOL'),
]

TIER = [
    ('Iron, Unranker', 'IRON, UNRANKER'),
    ('Bronze', 'BRONZE'),
    ('Silver', 'SILVER'),
    ('Gold', 'GOLD'),
    ('Platinum', 'PLATINUM'),
    ('Diamond', 'DIAMOND'),
    ('Master', 'MASTER'),
    ('Grandmaster', 'GRANDMASTER'),
    ('Ranker/Challenger', 'RANKERE/CHALLENGER')
]

NOW = datetime.now() + relativedelta(seconds=3)
three_year_over = NOW + relativedelta(years=3)

class PracticeCreateForm(forms.ModelForm):
    title = forms.CharField(max_length=200)
    text = forms.CharField(max_length=600, widget=forms.Textarea)
    game = forms.CharField(label='game', widget=forms.Select(choices=GAME))
    tier = forms.CharField(widget=forms.Select(choices=TIER))
    practice_time = forms.DateTimeField(label='연습일',widget=forms.TextInput(
        attrs={'type': 'date'}
    ))
    class Meta:
        model = Practice
        fields = ['title', 'text', 'game', 'tier', 'practice_time']

    def clean_practice_time(self):
        practice_time = self.cleaned_data['practice_time'].strftime("%Y-%m-%d %H:%M")
        now = NOW.strftime("%Y-%m-%d %H:%M")
        Three_year_over = three_year_over.strftime("%Y-%m-%d %H:%M")
        if practice_time < now:
            raise ValidationError('지난 시간은 선택할 수 없습니다.')
        elif practice_time > Three_year_over:
            raise ValidationError('최대 3년까지 선택할 수 있습니다.')
        return practice_time

class CommentForm(forms.ModelForm):
    content = forms.CharField(max_length=600)

    class Meta:
        model = Comment
        fields = ['content']
