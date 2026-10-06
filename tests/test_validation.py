import pandas as pd
from src.data_loader import mocks,normalize,read_upload
from src.data_validation import validate
from src.exports import workbook
from io import BytesIO
import struct,datetime
import pytest

def test_validation():
    p,q=mocks();clean,report,stats=validate(p,'producao');assert stats['linhas_rejeitadas']==1
    assert clean.loc[3,'consultas_medicas']!=clean.loc[3,'consultas_medicas']
    clean,report,stats=validate(q,'qualidade');assert stats['linhas_rejeitadas']==1
    assert (report.nivel=='ALERTA').any()
    p.loc[0,'competencia']='invalid';p.loc[1,'competencia']=p.loc[2,'competencia']
    assert validate(p,'producao')[2]['duplicidades']==2
    q.loc[0,'glosas_sia_percent']=101;q.loc[1,'prestacao_contas_data']='wrong'
    assert validate(q,'qualidade')[2]['linhas_rejeitadas']>=3

def test_formats():
    df=pd.DataFrame({'COMP':['2026-07'],'VALUE':[10]})
    csv=df.to_csv(index=False).encode();assert normalize(read_upload(csv,'x.csv'))[0].columns[0]=='competencia'
    excel=BytesIO();df.to_excel(excel,index=False);assert read_upload(excel.getvalue(),'x.xlsx').equals(df)
    parquet=BytesIO();df.to_parquet(parquet);assert read_upload(parquet.getvalue(),'x.parquet').equals(df)
    xlsx=workbook({n:df for n in ['Resumo','Produção','Qualidade','Trimestre','Monitoramento','Qualidade dos Dados','Regras Contratuais']})
    assert len(pd.ExcelFile(BytesIO(xlsx)).sheet_names)==7

@pytest.mark.parametrize('encoding',['utf-8','latin-1','cp1252'])
def test_dbf(encoding):
    # Minimal dBase III file, one C(7) field and one record.
    header=bytearray(32);header[0]=3;header[1:4]=bytes([126,7,1]);struct.pack_into('<IHH',header,4,1,65,8)
    field=bytearray(32);field[:4]=b'COMP';field[11]=ord('C');field[16]=7
    payload=bytes(header)+bytes(field)+b'\r'+b' '+b'2026-07'+b'\x1a'
    df=read_upload(payload,'x.dbf',encoding);assert df.iloc[0,0]=='2026-07'
