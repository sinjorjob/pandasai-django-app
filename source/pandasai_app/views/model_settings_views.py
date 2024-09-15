from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import AIModelProvider, AIModelName, AIModel

@csrf_exempt
def save_model_settings(request):
    provider_name = request.POST.get('provider')
    is_active = request.POST.get('is_active') == 'true'
    
    try:
        provider, _ = AIModelProvider.objects.get_or_create(name=provider_name)
        provider.is_active = is_active
        provider.save()

        model_name, _ = AIModelName.objects.get_or_create(name=request.POST.get('name'))
        
        model, _ = AIModel.objects.get_or_create(provider=provider)
        model.model_name = model_name
        model.api_key = request.POST.get('api_key')
        model.api_version = request.POST.get('api_version')
        model.endpoint = request.POST.get('endpoint')
        model.save()

        return JsonResponse({'success': True, 'message': 'Model settings saved successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def get_model_settings(request):
    if request.method == 'GET':
        provider_name = request.GET.get('model_type')

        try:
            provider = AIModelProvider.objects.get(name=provider_name)
            model = AIModel.objects.filter(provider=provider).first()

            if model:
                response_data = {
                    'id': model.id,
                    'name': model.model_name.name,
                    'api_key': model.api_key,
                    'api_version': model.api_version,
                    'endpoint': model.endpoint,
                    'is_active': provider.is_active
                }
            else:
                response_data = {
                    'name': '',
                    'api_key': '',
                    'api_version': '',
                    'endpoint': '',
                    'is_active': provider.is_active
                }
            
            return JsonResponse(response_data)
        except AIModelProvider.DoesNotExist:
            return JsonResponse({'error': f'Provider not found: {provider_name}'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)

def get_model_names(request):
    if request.method == 'GET':
        try:
            model_names = AIModelName.objects.values_list('name', flat=True)
            return JsonResponse({'model_names': list(model_names)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)