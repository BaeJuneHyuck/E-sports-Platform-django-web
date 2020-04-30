from django.contrib import admin
from  .models import Practice, PracticeParticipate

@admin.register(Practice)
class PracticeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'text', 'tier', 'date_published', 'time_practice', 'author')
    list_display_links = ('id', 'title')

    def date_published(self, obj):
        return obj.pub_date.strftime("%Y-%m-%d")

    def time_practice(self, obj):
        return obj.practice_time.strftime("%Y-%m-%d")

admin.site.register(PracticeParticipate)