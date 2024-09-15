# views.py
import japanize_matplotlib
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from pandasai import SmartDataframe
from pandasai.llm import OpenAI
import pandas as pd
import os
import html
from .models import AIModel, AIModelProvider, AIModelName
import matplotlib
matplotlib.use('Agg')  # バックエンドをAggに設定
import matplotlib.pyplot as plt
import base64
from pandasai.exceptions import NoResultFoundError
import base64
from io import BytesIO, StringIO
from .models import AIModel
from pandasai.llm import AzureOpenAI
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
import logging
import traceback
from openpyxl import load_workbook
from pandasai import Agent

logger = logging.getLogger(__name__)

# Set the font for matplotlib
plt.rcParams['font.sans-serif'] = ['SimHei']  # Use a font that supports Japanese characters
plt.rcParams['axes.unicode_minus'] = False  # Ensure the minus sign is displayed correctly


def translate_to_japanese(text, llm):
    translation_prompt = f"Translate the following English text to Japanese and answer only translated sentences:\n\n{text}"
    response = llm.client.create(
        model=llm.model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": translation_prompt}
        ]
    )
    translation_response = response.choices[0].message.content.strip()
    return translation_response

def generate_code_explanation(code, llm):
    # データ分析に関連する部分を抽出
    analysis_code = extract_analysis_code(code)
    
    explanation_prompt = f"""
以下のPythonコードの内容を、技術者ではない人でも理解できるように,１つ１つ丁寧に日本語で説明してください。
各行の目的と、全体としてどのようなデータ分析を行っているかを簡単な言葉で説明してください。
各行お説明対象のコードはコードブロック「```python ```」で囲ってください。
各行の説明の後は空行を入れて見やすい説明文になるように心がけてください。
また全体の説明はMarkdown形式の構造化された文章として作成してください。
コード:
{analysis_code}
"""
    response = llm.client.create(
        model=llm.model,
        messages=[
            {"role": "system", "content": "あなたは技術を分かりやすく説明する専門家です。"},
            {"role": "user", "content": explanation_prompt}
        ]
    )
    explanation = response.choices[0].message.content.strip()
    return explanation, analysis_code  # analysis_code も返すように変更

def extract_analysis_code(code):
    lines = code.split('\n')
    analysis_lines = []
    exclude_keywords = [
        # 'plt.',
        # 'sns.',
        'savefig',
        'result =',
        # 'tight_layout',
        # 'figure(',
        # 'xlabel(',
        # 'ylabel(',
        # 'title(',
        # 'legend(',
        # 'xticks(',
        # 'yticks('
    ]
    
    for line in lines:
        if not any(keyword in line for keyword in exclude_keywords):
            analysis_lines.append(line)
    
    return '\n'.join(analysis_lines)


def process_result(result):
    if isinstance(result, pd.DataFrame):
        print("dataframeが生成されたよ")
        return result.to_html(index=False, classes=['table', 'table-striped', 'table-hover'])

    elif isinstance(result, str) and result.startswith('<img'):
        # 既に<img>タグの場合はそのまま返す
        print("既に<img>タグの場合はそのまま返す")
        return result
    elif plt.get_fignums():
        print("図が描画されたよ")
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()  # 明示的にグラフをクローズ
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f'<img src="data:image/png;base64,{image_base64}" />'

    elif isinstance(result, str) and (result.endswith('.png') or result.endswith('.jpg') or result.endswith('.jpeg')):
        print("画像パスが返されたよ")
        try:
            with open(result, 'rb') as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            return f'<img src="data:image/png;base64,{image_base64}" />'
        except FileNotFoundError:
            return f'<div class="result-text text-sm text-gray-700">画像ファイルが見つかりません: {result}</div>'
    else:
        print("図が描画されなかったよ")
        return f'<div class="result-text text-sm text-gray-700">{result}</div>'
    
    
@ensure_csrf_cookie
def index(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        uploaded_file = request.FILES.get('file')
        output_type = request.POST.get('output_type')  # 新しく追加
        
        if uploaded_file:
            try:
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                if file_extension == 'csv':
                    # CSVファイルの処理（既存のコード）
                    try:
                        csv_content = uploaded_file.read().decode('utf-8')
                    except UnicodeDecodeError:
                        uploaded_file.seek(0)
                        csv_content = uploaded_file.read().decode('shift_jis')
                    
                    df = pd.read_csv(StringIO(csv_content))
                    print("csv:", df.head())
                    # 各列のデータ型を表示
                    print("\nColumn data types:")
                    print(df.dtypes)

                elif file_extension in ['xlsx', 'xls']:
                    # Excelファイルの処理
                    wb = load_workbook(filename=uploaded_file, read_only=True)
                    ws = wb.active
                    data = ws.values
                    columns = next(data)[0:]
                    df = pd.DataFrame(data, columns=columns)
                    print("excel:", df.head())
                
                else:
                    return JsonResponse({'error': '未対応のファイル形式です。CSVまたはExcelファイルをアップロードしてください。'}, status=400)
               
                media_path = settings.MEDIA_ROOT
                
                # Get the active model provider
                active_provider = AIModelProvider.objects.filter(is_active=True).first()
                if not active_provider:
                    return JsonResponse({'error': 'No active AI model provider found'}, status=400)

                # Get the active model for the active provider
                active_model = AIModel.objects.filter(provider=active_provider).first()
                if not active_model:
                    return JsonResponse({'error': 'No AI model found for the active provider'}, status=400)

                if active_provider.name == 'OpenAI':
                    llm = OpenAI(api_token=active_model.api_key, 
                                 model_name=active_model.model_name.name,
                                 temperature=0)
                elif active_provider.name == 'AzureOpenAI':
                    llm = AzureOpenAI(
                        api_token=active_model.api_key,
                        azure_endpoint=active_model.endpoint,
                        api_version=active_model.api_version,
                        deployment_name=active_model.model_name.name,
                        temperature=0
                    )
                else:
                    return JsonResponse({'error': 'Unsupported AI model provider'}, status=400)

                pandas_ai = SmartDataframe(df, 
                config={
                    "llm": llm,
                    "enable_cache": False,
                    "open_charts": False,
                    "save_charts": False,
                    "save_charts_path": media_path,
                    "verbose": False
                })

                try:
                    print("question=", question)
                    print("output_type=", output_type)
                    response = pandas_ai.chat(question, output_type=output_type)
                    print("response!!!!=", response)
                    
                    if output_type == 'string':
                        # stringの場合は直接responseを使用
                        result_html = f'<div class="result-text text-sm text-gray-700">{response}</div>'
                        explanation = "データなし"
                        executed_code = "データなし"
                        code_explanation = "データなし"
                        analysis_code = "データなし"
                    else:
                        # それ以外の場合は従来通りprocess_resultを使用
                        result_html = process_result(response)
                        
                        try:
                            explanation = pandas_ai._agent.explain()
                            japanese_explanation = translate_to_japanese(explanation, llm)
                        except Exception as e:
                            logger.error(f"Error in generating explanation: {str(e)}")
                            japanese_explanation = "説明を生成できませんでした。"

                        try:
                            executed_code = pandas_ai._agent.last_code_executed
                            print("executed_code1=", executed_code)
                            code_explanation, analysis_code = generate_code_explanation(executed_code, llm)
                        except Exception as e:
                            logger.error(f"Error in processing executed code: {str(e)}")
                            executed_code = "実行されたコードを取得できませんでした。"
                            code_explanation = "コードの説明を生成できませんでした。"
                            analysis_code = ""
                    
                    print("=====result_html=======-")
                    #print("result_html=", result_html)
                    
                    return JsonResponse({
                        'result': result_html,
                        'explanation': japanese_explanation if output_type != 'string' else explanation,
                        'executed_code': executed_code,
                        'code_explanation': code_explanation,
                        'analysis_code': analysis_code
                    })

                except NoResultFoundError:
                    if plt.get_fignums():
                        print("=====result_html2=======-")
                        result_html = process_result(None)  # This will handle the case where a plot was created
                    else:
                        result_html = '<div class="result-text text-sm text-gray-700">解析結果を表示できません。図が生成されたか確認してください。</div>'
                    return JsonResponse({
                        'result': result_html,
                        'explanation': "データなし",
                        'executed_code': "データなし",
                        'code_explanation': "データなし",
                        'analysis_code': "データなし"
                    })
                except Exception as e:
                    logger.error(f"Error in pandas_ai.chat: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': '予期せぬエラーが発生しました。指示文を修正して再実行してください。'}, status=500)

            except Exception as e:
                logger.error(f"Error processing CSV file: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({'error': '予期せぬエラーが発生しました。指示文を修正して再実行してください。'}, status=500)
        else:
            return JsonResponse({'error': 'CSVファイルがアップロードされていません。'}, status=400)
    
    return render(request, 'index.html')

@csrf_exempt
def save_model_settings(request):
    provider_name = request.POST.get('provider')
    is_active = request.POST.get('is_active') == 'true'
    
    try:
        provider, _ = AIModelProvider.objects.get_or_create(name=provider_name)
        provider.is_active = is_active
        provider.save()  # これにより他のプロバイダーが非アクティブになります

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
    print("get_model_settingsが呼ばれました")
    print(f"Request method: {request.method}")
    print(f"GET parameters: {request.GET}")
    
    if request.method == 'GET':
        provider_name = request.GET.get('model_type')
        print(f"Provider name: {provider_name}")
        
        try:
            provider = AIModelProvider.objects.get(name=provider_name)
            print(f"Provider found: {provider}")
            
            model = AIModel.objects.filter(provider=provider).first()
            print(f"Model found: {model}")
            
            if model:
                response_data = {
                    'id': model.id,  # この行を追加
                    'name': model.model_name.name,
                    'api_key': model.api_key,
                    'api_version': model.api_version,
                    'endpoint': model.endpoint,
                    'is_active': provider.is_active  # プロバイダーのis_activeを使用
                }
            else:
                response_data = {
                    'name': '',
                    'api_key': '',
                    'api_version': '',
                    'endpoint': '',
                    'is_active': provider.is_active  # プロバイダーのis_activeを使用
                }
            
            print(f"Returning data: {response_data}")
            return JsonResponse(response_data)
        except AIModelProvider.DoesNotExist:
            print(f"Provider not found: {provider_name}")
            return JsonResponse({'error': f'Provider not found: {provider_name}'}, status=404)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    print("Invalid request method")
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

def get_model_names(request):
    if request.method == 'GET':
        try:
            # プロバイダーに関係なく、すべてのモデル名を取得
            model_names = AIModelName.objects.values_list('name', flat=True)
            return JsonResponse({'model_names': list(model_names)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)