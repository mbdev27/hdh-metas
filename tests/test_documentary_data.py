import hashlib
import pandas as pd
from src.contract_registry import inventory,ROOT,duplicates
from src.contract_engine import ContractEngine
from src.historical import real_data,aggregate
from src.exports import workbook
from io import BytesIO

def test_corpus_identity_hash_and_exclusions():
    docs=inventory();assert len(docs)==67
    excluded={d['document_id'] for d in docs if d['excluido']}
    assert excluded=={'DOC021','DOC022','DOC052'}
    assert len(duplicates(docs))==3
    for d in docs:
        if d['excluido']:assert d['arquivo_biblioteca'] is None
        elif d['arquivo_biblioteca']:
            assert hashlib.sha256((ROOT/d['arquivo_biblioteca']).read_bytes()).hexdigest()==d['hash_sha256']
    assert len(list((ROOT/'documents').glob('*.pdf')))==60
    d=next(d for d in docs if d['document_id']=='DOC033');assert d['tipo_documento']=='Termo de Rerratificação'
    assert next(d for d in docs if d['document_id']=='DOC035')['periodo_avaliado']=='2019Q4'
    assert next(d for d in docs if d['document_id']=='DOC047')['duplicate_of']=='DOC046'

def test_targets_by_instrument_and_midmonth_change():
    e=ContractEngine()
    assert e.resolve('Q03','2024-06')['valor']==4286
    assert e.resolve('Q03','2024-07-01')['documento_fonte']=='DOC019'
    assert e.resolve('Q03','2024-07-15')['documento_fonte']=='DOC017'
    assert e.resolve('Q03','2026-01')['valor']==2520
    assert e.resolve('Q03','2022-06') is None
    assert e.validate_weights('CG018_ORIGINAL')==(20,10)
    assert e.validate_weights('TA08')==(20,10)
    assert e.validate_weights('RERR08')==(20,10)
    assert e.resolve('Q_TOTAL','2023-01')['valor']==688
    assert e.resolve('Q05','2023-01') is None
    assert e.resolve('M05','2026-01') is None

def test_actual_data_and_missing_values():
    p,q=real_data();assert p.competencia.nunique()==75
    assert not p.duplicated(['competencia','indicator_id']).any()
    assert not q.duplicated(['competencia','indicator_id']).any()
    r=p[(p.competencia=='2024-11')&(p.indicator_id=='Q04')].iloc[0]
    assert r.meta_reported==2520 and r.meta_contratual==4730 and r.divergencia_meta
    r=p[(p.competencia=='2026-01')&(p.indicator_id=='Q03')].iloc[0]
    assert r.realizado==1225 and r.meta_contratual==2520 and r.documento_fonte=='DOC065'
    r=p[(p.competencia=='2021-06')&(p.indicator_id=='Q01')].iloc[0];assert r.realizado==741
    assert p[p.indicator_id=='Q08'].realizado.isna().all()
    assert q[(q.competencia=='2026-01')&(q.indicator_id=='QL01')].iloc[0].status_dado=='INCONSISTÊNCIA NA FONTE'
    assert q[q.indicator_id=='QL02'].pontuacao.isna().all()
    assert q[(q.competencia=='2026-01')&(q.indicator_id=='QL10')].iloc[0].valor==.54
    assert q[(q.competencia=='2026-01')&(q.indicator_id=='QL11')].iloc[0].valor==10

def test_quarter_annual_coverage_no_extrapolation():
    p,_=real_data();t=aggregate(p)
    r=t[(t.periodo=='2026Q1')&(t.indicator_id=='Q01')].iloc[0]
    assert r.meta_acumulada==2568 and r.realizado==2586 and r.pontuacao==3
    assert pd.isna(t[(t.periodo=='2026Q1')&(t.indicator_id=='Q08')].iloc[0].realizado)
    a=aggregate(p,'Y');r=a[(a.periodo=='2026')&(a.indicator_id=='Q01')].iloc[0]
    assert r.meses_presentes==3 and 'PARCIAL' in r.cobertura and r.meta_acumulada==2568
    assert set(a[(a.periodo=='2022')&(a.indicator_id=='Q01')].contrato)=={'006/2010','018/2022'}

def test_workbook_real_data():
    p,q=real_data();tables={'Resumo':p,'Produção':p,'Qualidade':q,'Trimestre':aggregate(p),'Monitoramento':q,'Qualidade dos Dados':q,'Regras Contratuais':pd.DataFrame(ContractEngine().rules).astype(str)}
    result=pd.ExcelFile(BytesIO(workbook(tables)))
    assert result.sheet_names==list(tables)
