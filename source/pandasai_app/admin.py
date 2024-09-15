# admin.py
from django.contrib import admin
from .models import AIModelProvider, AIModelName, AIModel

@admin.register(AIModelProvider)
class AIModelProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            # 他のプロバイダーを非アクティブにする
            AIModelProvider.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)

@admin.register(AIModelName)
class AIModelNameAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ('provider', 'model_name', 'get_is_active')
    list_filter = ('provider', 'model_name', 'provider__is_active')
    search_fields = ('provider__name', 'model_name__name')
    
    fieldsets = (
        (None, {
            'fields': ('provider', 'model_name')
        }),
        ('API設定', {
            'fields': ('api_key', 'api_version', 'endpoint'),
            'classes': ('collapse',),
        }),
    )

    def get_is_active(self, obj):
        return obj.provider.is_active
    get_is_active.short_description = 'Is Active'
    get_is_active.boolean = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "provider":
            kwargs["queryset"] = AIModelProvider.objects.all().order_by('-is_active', 'name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)