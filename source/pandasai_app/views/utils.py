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
    return explanation, analysis_code

def extract_analysis_code(code):
    lines = code.split('\n')
    analysis_lines = []
    exclude_keywords = [
        'savefig',
        'result =',
    ]
    
    for line in lines:
        if not any(keyword in line for keyword in exclude_keywords):
            analysis_lines.append(line)
    
    return '\n'.join(analysis_lines)