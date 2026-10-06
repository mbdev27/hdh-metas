from io import BytesIO
import pandas as pd
def csv_bytes(df):return df.to_csv(index=False).encode('utf-8-sig')
def workbook(tables):
    output=BytesIO()
    with pd.ExcelWriter(output,engine='openpyxl') as writer:
        for name,df in tables.items():
            safe=df.copy()
            for col in safe.columns:
                safe[col]=safe[col].map(lambda v: "'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v)
            safe.to_excel(writer,sheet_name=name,index=False)
    return output.getvalue()
