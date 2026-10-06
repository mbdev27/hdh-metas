from src.contract_engine import ContractEngine
from src.calculations import quarter
from src.data_loader import mocks
import pandas as pd

def test_financial_period():
    e=ContractEngine();assert e.monthly_value('2026-06') is None
    assert e.monthly_value('2026-07')==10904885.46
    assert e.monthly_value('2028-07') is None

def test_rule_versions_and_replacement():
    base=dict(indicator_id='X',status_validacao='VALIDADA',tipo_alteracao='ALTERADA',inicio_vigencia='2025-01-01',fim_vigencia='2025-12-31',valor=10)
    newer=dict(base,inicio_vigencia='2026-01-01',fim_vigencia=None,valor=20)
    replaced=dict(newer,tipo_alteracao='SUBSTITUÍDA',valor=999)
    e=ContractEngine([base,newer,replaced]);assert e.resolve('X','2025-12')['valor']==10;assert e.resolve('X','2026-01')['valor']==20
    assert ContractEngine().resolve('Q03','2026-07')['valor']==2520
    assert ContractEngine().resolve('Q03','2026-07',True)['valor']==2520

def test_quarter_missing_is_not_zero():
    p,q=mocks();t,_=quarter(p,q,pd.Period('2025Q1'))
    assert pd.isna(t[t.indicador=='Q03'].iloc[0].realizado)
