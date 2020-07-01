
from django.contrib import admin

# Register your models here.
from django.contrib import admin
from . import models
from .models import Competition, CompetitionParticipate, Match


class CompetitionsAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['competition_game']}),
        (None, {'fields': ['competition_name']}),
        (None, {'fields': ['competition_text']}),
        (None, {'fields': ['origin_image']}),
        (None, {'fields': ['date_start']}),
        (None, {'fields': ['date_end']}),
        (None, {'fields': ['attend_start']}),
        (None, {'fields': ['attend_end']}),

        (None, {'fields': ['master']}),
        (None, {'fields': ['is_public']}),
        (None, {'fields': ['tournament_type']}),
        (None, {'fields': ['required_tier']}),
        (None, {'fields': ['total_teams']}),
        (None, {'fields': ['current_teams']}),
        (None, {'fields': ['rounds']}),
    ]
    list_display = ('competition_game', 'competition_name', 'competition_text', 'date_start', 'date_end', 'attend_start', 'attend_end' ,'rounds')
    list_filter = ['pub_date']
    search_fields = ['competition_text']


admin.site.register(Competition, CompetitionsAdmin)


class CompetitionParticipateAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['competition']}),
        (None, {'fields': ['team']}),
        (None, {'fields': ['team_number']}),
        (None, {'fields': ['avg_tier']}),
        (None, {'fields': ['win']}),
        (None, {'fields': ['lose']}),
    ]
    list_display = ('competition', 'team', 'team_number','avg_tier','win','lose')
    list_filter = ['competition']
    search_fields = ['competition']


admin.site.register(CompetitionParticipate, CompetitionParticipateAdmin)


class MatchAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['game']}),
        (None, {'fields': ['competition']}),
        (None, {'fields': ['number']}),
        (None, {'fields': ['group']}),
        (None, {'fields': ['round']}),
        (None, {'fields': ['team1']}),
        (None, {'fields': ['team2']}),
        (None, {'fields': ['result']}),
        (None, {'fields': ['result_lol']}),
        (None, {'fields': ['result_ow']}),
    ]
    list_display = ('game', 'competition', 'number', 'group', 'round', 'team1' ,'team2', 'result', 'result_lol', 'result_ow')
    list_filter = ['competition']
    search_fields = ['competition']


admin.site.register(Match, MatchAdmin)
