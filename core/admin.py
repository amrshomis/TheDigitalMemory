from django.contrib import admin
from django.utils.html import format_html
from .models import Magazine

@admin.register(Magazine)
class MagazineAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active', 'view_link')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)} if False else {} # We use custom save for slugs
    
    def view_link(self, obj):
        if obj.slug:
            url = f"/magazine/{obj.slug}/"
            return format_html('<a href="{}" target="_blank">فتح المجلة</a>', url)
        return "-"
    view_link.short_description = "رابط العرض"

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'pdf_file', 'cover_image', 'is_active')
        }),
        ('معلومات إضافية', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at',)
