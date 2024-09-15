from django.db import models

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
    model_name = models.ForeignKey(AIModelName, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=255)
    api_version = models.CharField(max_length=20, blank=True, null=True)
    endpoint = models.URLField(blank=True, null=True)
    #is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('provider', 'model_name')

    def __str__(self):
        return f"{self.provider.name} - {self.model_name.name}"

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

    # モデル名の作成
    model_names = ['gpt-4o-mini', 'gpt-4o']
    for name in model_names:
        AIModelName.objects.get_or_create(name=name)

    # gpt-4o-miniモデルをプリセット
    gpt_4o_mini, _ = AIModelName.objects.get_or_create(name='gpt-4o-mini')
    for provider in created_providers:
        AIModel.objects.get_or_create(
            provider=provider,
            model_name=gpt_4o_mini,
            defaults={
                'api_key': 'default_key_please_change',
                'api_version': 'default_version_please_change' if provider.name == 'AzureOpenAI' else None,
                'endpoint': 'default_endpoint_please_change' if provider.name == 'AzureOpenAI' else None
            }
        )

    print("Model data initialized successfully with gpt-4o-mini preset for all providers.")