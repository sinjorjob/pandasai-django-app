import pandas as pd
from io import StringIO
from openpyxl import load_workbook

def process_uploaded_file(uploaded_file):
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension == 'csv':
        try:
            csv_content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            csv_content = uploaded_file.read().decode('shift_jis')
        
        df = pd.read_csv(StringIO(csv_content))

    elif file_extension in ['xlsx', 'xls']:
        wb = load_workbook(filename=uploaded_file, read_only=True)
        ws = wb.active
        data = ws.values
        columns = next(data)[0:]
        df = pd.DataFrame(data, columns=columns)
    
    else:
        raise ValueError('未対応のファイル形式です。CSVまたはExcelファイルをアップロードしてください。')
    
    return df