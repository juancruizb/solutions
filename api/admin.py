from django.contrib import admin
from .models import Solution, Topic


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display  = ('name', 'sdp_id', 'icon_key', 'solution_count')
    search_fields = ('name', 'sdp_id')
    ordering      = ('name',)

    def solution_count(self, obj):
        return obj.solutions.count()
    solution_count.short_description = '# Soluciones'


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display   = ('display_id', 'title', 'topic', 'status', 'author',
                      'hits', 'is_public', 'synced_at')
    list_filter    = ('topic', 'status', 'is_public')
    search_fields  = ('title', 'display_id', 'author', 'keywords')
    ordering       = ('-sdp_id',)
    readonly_fields = ('sdp_id', 'display_id', 'synced_at')
    list_per_page  = 25

    fieldsets = (
        ('Identificación', {
            'fields': ('sdp_id', 'display_id', 'title')
        }),
        ('Clasificación', {
            'fields': ('topic', 'status', 'is_public', 'keywords')
        }),
        ('Autoría', {
            'fields': ('author', 'updated_sdp', 'hits')
        }),
        ('Contenido', {
            'fields': ('description',),
            'classes': ('collapse',),
        }),
        ('Sincronización', {
            'fields': ('synced_at',)
        }),
    )
