from pathlib import Path
from io import BytesIO
import tempfile,unicodedata
import pandas as pd
from dbfread import DBF
from src.contract_registry import ROOT
ALIASES={'comp':'competencia','mes_ref':'competencia','dt_comp':'competencia'}
def normalize(df,mapping=None):
    original=list(df.columns);names=[]
    for c in original:
        n=unicodedata.normalize('NFKD',str(c)).encode('ascii','ignore').decode().lower().strip().replace(' ','_')
        names.append((mapping or {}).get(c,ALIASES.get(n,n)))
    if len(names)!=len(set(names)):raise ValueError('Mapeamento gerou colunas duplicadas')
    df=df.copy();df.columns=names
    return df,dict(zip(original,names))
def read_upload(data,name,encoding='utf-8'):
    ext=Path(name).suffix.lower()
    if ext=='.csv':return pd.read_csv(BytesIO(data),encoding=encoding,sep=None,engine='python')
    if ext=='.xlsx':return pd.read_excel(BytesIO(data))
    if ext=='.parquet':return pd.read_parquet(BytesIO(data))
    if ext=='.dbf':
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.dbf';path.write_bytes(data)
            return pd.DataFrame(iter(DBF(str(path),encoding=encoding,char_decode_errors='strict',load=True)))
    raise ValueError('Formato não suportado')
def mocks():
    return tuple(pd.read_csv(ROOT/'data/mock'/name) for name in ('producao.csv','qualidade.csv'))
