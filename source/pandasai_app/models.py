from django.db import models
from django.core.exceptions import ValidationError


class AIModelProvider(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"

    def save(self, *args, **kwargs):
        if self.is_active:
            # 他のプロバイダーを非アクティブにする
            AIModelProvider.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

class AIModelName(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class AIModel(models.Model):
    provider = models.ForeignKey(AIModelProvider, on_delete=models.CASCADE)
    model_name = models.ForeignKey(AIModelName, on_delete=models.CASCADE, null=True, blank=True)
    deployment_name = models.CharField(max_length=255, null=True, blank=True)
    api_key = models.CharField(max_length=255)
    api_version = models.CharField(max_length=20, blank=True, null=True)
    endpoint = models.URLField(blank=True, null=True)

    def clean(self):
        if self.provider.name == 'OpenAI':
            if not self.model_name:
                raise ValidationError('OpenAIプロバイダーの場合、モデル名は必須です。')
            self.deployment_name = None
            self.api_version = None
            self.endpoint = None
        elif self.provider.name == 'AzureOpenAI':
            if not self.deployment_name:
                raise ValidationError('AzureOpenAIプロバイダーの場合、デプロイメント名は必須です。')
            if not self.api_version:
                raise ValidationError('AzureOpenAIプロバイダーの場合、API Versionは必須です。')
            if not self.endpoint:
                raise ValidationError('AzureOpenAIプロバイダーの場合、Endpointは必須です。')
            self.model_name = None

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('provider', 'model_name', 'deployment_name')


def initialize_model_data():
    # プロバイダーの作成
    providers = ['OpenAI', 'AzureOpenAI']
    created_providers = []
    for i, provider_name in enumerate(providers):
        provider, _ = AIModelProvider.objects.get_or_create(
            name=provider_name,
            defaults={'is_active': i == 0}  # 最初のプロバイダー（OpenAI）をアクティブに設定
        )
        created_providers.append(provider)

    # モデル名の作成 (OpenAI用)
    model_names = ['gpt-4o-mini', 'gpt-4o','o1-preview','o1-mini']
    for name in model_names:
        AIModelName.objects.get_or_create(name=name)

    # gpt-4o-miniモデルをプリセット
    gpt_4o_mini, _ = AIModelName.objects.get_or_create(name='gpt-4o-mini')
    
    for provider in created_providers:
        if provider.name == 'OpenAI':
            AIModel.objects.get_or_create(
                provider=provider,
                model_name=gpt_4o_mini,
                defaults={
                    'api_key': 'sk-openai-key-placeholder',
                }
            )
        elif provider.name == 'AzureOpenAI':
            AIModel.objects.get_or_create(
                provider=provider,
                defaults={
                    'deployment_name': 'deployment-name',
                    'api_key': 'azure-api-key-placeholder',
                    'api_version': '2023-05-15',  # 実際のAPIバージョンに更新してください
                    'endpoint': 'https://your-resource-name.openai.azure.com/'  # 実際のエンドポイントURLに更新してください
                }
            )

    print("Model data initialized successfully with appropriate presets for OpenAI and AzureOpenAI providers.")