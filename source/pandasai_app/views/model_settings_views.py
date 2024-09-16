from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import AIModelProvider, AIModelName, AIModel
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def save_model_settings(request):
    provider_name = request.POST.get('provider')
    api_key = request.POST.get('api_key')
    name = request.POST.get('name')
    is_active = request.POST.get('is_active') == 'true'  # 文字列 'true' をブール値に変換
    
    logger.debug(f"Received data: provider={provider_name}, name={name}, is_active={is_active}")
    logger.debug(f"All POST data: {request.POST}")

    try:
        provider = AIModelProvider.objects.get(name=provider_name)
        provider.is_active = is_active  # プロバイダーのis_activeフィールドを更新
        provider.save()  # プロバイダーの変更を保存
        
        model, _ = AIModel.objects.get_or_create(provider=provider)
        
        model.api_key = api_key
        
        if provider_name == 'OpenAI':
            try:
                model_name = AIModelName.objects.get(name=name)
                model.model_name = model_name
                model.deployment_name = None
            except AIModelName.DoesNotExist:
                logger.error(f"AIModelName not found for name: {name}")
                return JsonResponse({'success': False, 'message': f'モデル名 "{name}" が見つかりません。'}, status=400)
        elif provider_name == 'AzureOpenAI':
            model.deployment_name = name
            model.model_name = None
            model.api_version = request.POST.get('api_version')
            model.endpoint = request.POST.get('endpoint')
        
        model.full_clean()
        model.save()
        return JsonResponse({'success': True, 'message': 'モデル設定が保存されました。', 'id': model.id})
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': f'エラーが発生しました: {str(e)}'}, status=500)



@require_http_methods(["GET"])
def get_model_settings(request):
    provider_name = request.GET.get('model_type')
    
    try:
        provider = AIModelProvider.objects.get(name=provider_name)
        model = AIModel.objects.filter(provider=provider).first()
        
        if model:
            response_data = {
                'id': model.id,
                'name': model.model_name.name if model.model_name else model.deployment_name,
                'api_key': model.api_key,
                'api_version': model.api_version,
                'endpoint': model.endpoint,
                'is_active': provider.is_active
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({
                'name': '',
                'api_key': '',
                'api_version': '',
                'endpoint': '',
                'is_active': provider.is_active
            })
    except AIModelProvider.DoesNotExist:
        return JsonResponse({'error': f'プロバイダーが見つかりません: {provider_name}'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'エラーが発生しました: {str(e)}'}, status=500)

@require_http_methods(["GET"])
def get_model_names(request):
    try:
        model_names = AIModelName.objects.values_list('name', flat=True)
        print("list(model_names)=",list(model_names))
        return JsonResponse({'model_names': list(model_names)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
