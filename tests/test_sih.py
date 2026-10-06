from pathlib import Path
import pandas as pd
import pytest
from src.sih import load_sih,monthly_series,parse_tabnet
from src.sih_ui import annual_for_selection
from src.contract_registry import ROOT

def test_sih_sources_identity_and_duplicates():
    data,meta=load_sih();assert len(meta)==12
    assert len({m['hash_sha256'] for m in meta})==11
    assert all(m['cnes']=='6559379' and m['data_extracao']=='2026-10-06' for m in meta)
    assert sum(bool(m['duplicate_of']) for m in meta)==1
    assert not data.duplicated(['medida','dimensao','tipo_linha','competencia','ano','categoria']).any()
    for m in meta:
        _,parsed=parse_tabnet((ROOT/m['arquivo_original']).read_bytes())
        assert parsed['hash_sha256']==m['hash_sha256']

def test_sih_period_and_symbol_preservation():
    data,_=load_sih();m=monthly_series(data)
    assert m.competencia.nunique()==79
    assert m.competencia.min()=='2020-01' and m.competencia.max()=='2026-07'
    assert '2019-12' in set(data.competencia.dropna())
    assert data[data.valor_original.isin(['-','...'])].valor.isna().all()
    r=m[(m.medida=='AIH aprovadas')&(m.dimensao=='Caráter atendimento')&(m.categoria=='Total')&(m.competencia=='2026-07')].iloc[0]
    assert r.valor==726
    r=m[(m.medida=='Valor total')&(m.categoria=='Total')&(m.competencia=='2020-01')].iloc[0]
    assert r.valor==1775727.40

def test_annual_rates_are_not_summed_or_averaged():
    data,_=load_sih();selected=monthly_series(data,'2020-01','2020-12')
    result=annual_for_selection(data,selected,'Taxa mortalidade','Caráter atendimento')
    assert result.iloc[0].valor==13.62
    partial=annual_for_selection(data,monthly_series(data,'2020-01','2020-02'),'Taxa mortalidade','Caráter atendimento')
    assert pd.isna(partial.iloc[0].valor)
    annual=annual_for_selection(data,monthly_series(data,'2026-01','2026-07'),'AIH aprovadas','Caráter atendimento')
    assert annual.iloc[0].valor==4812 and annual.iloc[0].cobertura=='ANO PARCIAL'

def test_other_cnes_rejected():
    _,meta=load_sih();raw=(ROOT/meta[0]['arquivo_original']).read_bytes().replace(b'6559379',b'1234567')
    with pytest.raises(ValueError,match='CNES'):parse_tabnet(raw)
