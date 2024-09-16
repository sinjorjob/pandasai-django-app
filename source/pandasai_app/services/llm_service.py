from django.conf import settings
from pandasai.llm import OpenAI
from ..models import AIModelProvider, AIModel
from pandasai.llm.azure_openai import AzureOpenAI


def initialize_llm():
    active_provider = AIModelProvider.objects.filter(is_active=True).first()
    if not active_provider:
        raise ValueError('No active AI model provider found')

    active_model = AIModel.objects.filter(provider=active_provider).first()
    if not active_model:
        raise ValueError('No AI model found for the active provider')

    if active_provider.name == 'OpenAI':
        llm = OpenAI(api_token=active_model.api_key, 
                     model_name=active_model.model_name.name,
                     temperature=0)
    elif active_provider.name == 'AzureOpenAI':
        llm = AzureOpenAI(
            api_token=active_model.api_key,
            azure_endpoint=active_model.endpoint,
            api_version=active_model.api_version,
            deployment_name=active_model.deployment_name,
            temperature=0
        )
    else:
        raise ValueError('Unsupported AI model provider')

    return llm