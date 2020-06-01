
from django.contrib import admin

# Register your models here.
from django.contrib import admin
from . import models
from .models import Competition


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
    ]
    list_display = ('competition_game', 'competition_name', 'competition_text', 'date_start', 'date_end', 'attend_start', 'attend_end')
    list_filter = ['pub_date']
    search_fields = ['competition_text']


admin.site.register(Competition, CompetitionsAdmin)
