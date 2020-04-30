
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
        ('Date information', {'fields': ['pub_date']}),
    ]
    list_display = ('competition_game', 'competition_name', 'competition_text')
    list_filter = ['pub_date']
    search_fields = ['competition_text']


admin.site.register(Competition, CompetitionsAdmin)
