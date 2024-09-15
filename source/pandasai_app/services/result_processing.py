import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def process_result(result):
    if isinstance(result, pd.DataFrame):
        return result.to_html(index=False, classes=['table', 'table-striped', 'table-hover'])

    elif isinstance(result, str) and result.startswith('<img'):
        return result
    elif plt.get_fignums():
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f'<img src="data:image/png;base64,{image_base64}" />'

    elif isinstance(result, str) and (result.endswith('.png') or result.endswith('.jpg') or result.endswith('.jpeg')):
        try:
            with open(result, 'rb') as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            return f'<img src="data:image/png;base64,{image_base64}" />'
        except FileNotFoundError:
            return f'<div class="result-text text-sm text-gray-700">画像ファイルが見つかりません: {result}</div>'
    else:
        return f'<div class="result-text text-sm text-gray-700">{result}</div>'