from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from pandasai import SmartDataframe
from pandasai.exceptions import NoResultFoundError
import matplotlib.pyplot as plt
import logging
import traceback
import matplotlib
matplotlib.use('Agg')  # バックエンドをAggに設定
import japanize_matplotlib

from ..services.data_processing import process_uploaded_file
from ..services.llm_service import initialize_llm
from ..services.result_processing import process_result
from .utils import translate_to_japanese, generate_code_explanation

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def index(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        uploaded_file = request.FILES.get('file')
        output_type = request.POST.get('output_type')

        if uploaded_file:
            try:
                df = process_uploaded_file(uploaded_file)
                llm = initialize_llm()

                pandas_ai = SmartDataframe(df, config={
                    "llm": llm,
                    "enable_cache": False,
                    "open_charts": False,
                    "save_charts": False,
                    "save_charts_path": settings.MEDIA_ROOT,
                    "verbose": False
                })

                try:
                    response = pandas_ai.chat(question, output_type=output_type)

                    if output_type == 'string':
                        formatted_response = response.replace('\n', '<br>')
                        formatted_response = '<p>' + formatted_response.replace('<br><br>', '</p><p>') + '</p>'
                        result_html = f'<div class="result-text text-sm text-gray-700">{formatted_response}</div>'
                        explanation = "データなし"
                        executed_code = "データなし"
                        code_explanation = "データなし"
                        analysis_code = "データなし"
                    else:
                        result_html = process_result(response)
                        
                        try:
                            explanation = pandas_ai._agent.explain()
                            japanese_explanation = translate_to_japanese(explanation, llm)
                        except Exception as e:
                            logger.error(f"Error in generating explanation: {str(e)}")
                            japanese_explanation = "説明を生成できませんでした。"

                        try:
                            executed_code = pandas_ai._agent.last_code_executed
                            code_explanation, analysis_code = generate_code_explanation(executed_code, llm)
                        except Exception as e:
                            logger.error(f"Error in processing executed code: {str(e)}")
                            executed_code = "実行されたコードを取得できませんでした。"
                            code_explanation = "コードの説明を生成できませんでした。"
                            analysis_code = ""
                    
                    return JsonResponse({
                        'result': result_html,
                        'explanation': japanese_explanation if output_type != 'string' else explanation,
                        'executed_code': executed_code,
                        'code_explanation': code_explanation,
                        'analysis_code': analysis_code
                    })

                except NoResultFoundError:
                    if plt.get_fignums():
                        result_html = process_result(None)
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
                logger.error(f"Error processing file: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({'error': '予期せぬエラーが発生しました。指示文を修正して再実行してください。'}, status=500)
        else:
            return JsonResponse({'error': 'ファイルがアップロードされていません。'}, status=400)
    
    return render(request, 'index.html')