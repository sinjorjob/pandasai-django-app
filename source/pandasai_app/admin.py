# admin.py
from django.contrib import admin
from .models import AIModelProvider, AIModelName, AIModel
from django.core.exceptions import ValidationError

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
    list_display = ('provider', 'get_name', 'get_is_active')
    list_filter = ('provider', 'provider__is_active')
    search_fields = ('provider__name', 'model_name__name', 'deployment_name')
    
    def get_fieldsets(self, request, obj=None):
        if obj and obj.provider.name == 'AzureOpenAI':
            return (
                (None, {
                    'fields': ('provider', 'deployment_name')
                }),
                ('API設定', {
                    'fields': ('api_key', 'api_version', 'endpoint'),
                    'classes': ('collapse',),
                }),
            )
        else:
            return (
                (None, {
                    'fields': ('provider', 'model_name')
                }),
                ('API設定', {
                    'fields': ('api_key',),
                    'classes': ('collapse',),
                }),
            )

    def get_name(self, obj):
        return obj.model_name.name if obj.model_name else obj.deployment_name
    get_name.short_description = 'Model/Deployment Name'

    def get_is_active(self, obj):
        return obj.provider.is_active
    get_is_active.short_description = 'Is Active'
    get_is_active.boolean = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "provider":
            kwargs["queryset"] = AIModelProvider.objects.all().order_by('-is_active', 'name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            self.message_user(request, f"Validation error: {e}", level='ERROR')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.provider.name == 'AzureOpenAI':
            form.base_fields['deployment_name'].required = True
            form.base_fields['api_version'].required = True
            form.base_fields['endpoint'].required = True
            if 'model_name' in form.base_fields:
                form.base_fields['model_name'].required = False
        elif obj and obj.provider.name == 'OpenAI':
            form.base_fields['model_name'].required = True
            if 'deployment_name' in form.base_fields:
                form.base_fields['deployment_name'].required = False
            if 'api_version' in form.base_fields:
                form.base_fields['api_version'].required = False
            if 'endpoint' in form.base_fields:
                form.base_fields['endpoint'].required = False
        return form