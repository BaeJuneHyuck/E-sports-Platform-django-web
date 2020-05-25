from django.contrib import admin
from .models import Team, TeamRelation, TeamInvitation
# Register your models here.


class TeamAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name']}),
        (None, {'fields': ['game']}),
        (None, {'fields': ['text']}),
        (None, {'fields': ['master']}),
        (None, {'fields' : ['visible']})
    ]
    list_display = ('name', 'game', 'text', 'master','visible')

admin.site.register(Team, TeamAdmin)


class TeamInvitationAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['team_pk']}),
        (None, {'fields': ['inviter_pk']}),
        (None, {'fields': ['invited_pk']}),
        (None, {'fields': ['accepted']}),
        (None, {'fields': ['checked']})

    ]
    list_display = ('team_pk', 'inviter_pk','invited_pk', 'accepted', 'checked')

admin.site.register(TeamInvitation, TeamInvitationAdmin)

class TeamRelationAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['team_pk']}),
        (None, {'fields': ['user_pk']})
    ]
    list_display = ('team_pk', 'user_pk')

admin.site.register(TeamRelation, TeamRelationAdmin)
