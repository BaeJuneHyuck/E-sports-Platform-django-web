from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Competition, CompetitionParticipate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from team.models import Team, TeamRelation
NOW = timezone.now()

GAME=[
    ('Overwatch', 'Overwatch'),
    ('LOL', 'LOL'),
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

TOURNAMENT_TYPE = [
    (-1, 'Single Elimination'),    # 1패 하면 탈락하는 토너먼트
    (-2, 'Double Elimination'),   # 패배시 패자전에서 한번더 기회있는 토너먼트
    (2, 'Round Robin'),            # 모든 상대팀과 N번 경기를 치룬다
]

class CompetitionCreateForm(forms.ModelForm):
    competition_name = forms.CharField(label='대회명', max_length=100 )
    competition_text = forms.CharField(label='대회설명',max_length=600, widget=forms.Textarea)
    competition_game = forms.CharField(label='대회종목', widget=forms.Select(choices=GAME))

    tournament_type = forms.CharField(label='대회 방식', widget=forms.Select(choices=TOURNAMENT_TYPE))
    required_tier = forms.CharField(label='최소 티어', widget = forms.Select(choices=TIER))
    total_teams = forms.IntegerField(label='참여 팀 수')
    date_start = forms.DateTimeField(label='대회 시작',widget = forms.TextInput(
        attrs={'type': 'date'}
    ))
    date_end = forms.DateTimeField(label='대회 종료',widget=forms.TextInput(
        attrs={'type': 'date'}
    ))

    attend_start = forms.DateTimeField(label='참가 신청 시작',widget=forms.TextInput(
        attrs={'type': 'date'}
    ))
    attend_end = forms.DateTimeField(label='참가 신청 종료',widget=forms.TextInput(
        attrs={'type': 'date'}
    ))

    is_public = forms.BooleanField(label='대회 공개', required=False)

    class Meta:
        model = Competition
        fields = ['competition_name', 'competition_text', 'competition_game', 'required_tier', 'total_teams', 'tournament_type',
                  'date_start', 'date_end', 'attend_start', 'attend_end', 'is_public']

    def clean_date_start(self):
        NOW = timezone.now()
        date_start = self.cleaned_data['date_start']
        if date_start <= NOW:
            raise ValidationError('지난 시간은 선택할 수 없습니다.')
        return date_start

class CompetitionAttendForm(forms.ModelForm):
    avg_tier = forms.IntegerField(required=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        relation =TeamRelation.objects.filter(user_pk=user)
        self.fields['team'].queryset =Team.objects.filter(teamrelation__in = relation)

    class Meta:
        model = CompetitionParticipate
        fields = ['team']
