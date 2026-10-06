import pytest
from src.contract_engine import ContractEngine
from src.scoring import score
from src.calculations import monthly,safe_ratio
from src.data_loader import mocks
@pytest.mark.parametrize('id,values,expected',[('QL10',[7.5,7.51,10,10.01],[1,.8,.8,.6]),('QL05',[10,10.01,30,30.01],[1,.8,.2,0]),('QL02',[89.99,90],[.8,1]),('QL04',[0,.001,1,1.01,4,4.01],[.5,.4,.4,.3,.1,0]),('QL01',[99.99,100],[.4,.5]),('QL11',[0,1],[1,0])])
def test_bounds(id,values,expected):
    r=ContractEngine().resolve(id,'2026-07',True)
    assert [score(x,r) for x in values]==expected
@pytest.mark.parametrize('id',['QL01','QL02','QL03','QL04','QL05','QL06','QL09','QL10','QL12'])
def test_all_thresholds(id):
    r=ContractEngine().resolve(id,'2026-07',True)
    for boundary,points in r['faixas']:assert score(boundary,r)==points

def test_insufficient_sample_and_zero_denominator():
    p,q=mocks();t=monthly(p,q,'2024-10');row=t[t.indicador=='QL02'].iloc[0]
    assert row.situacao=='AMOSTRA INSUFICIENTE PARA AFERIÇÃO CONTRATUAL'
    assert row.pontuacao!=row.pontuacao
    assert safe_ratio(0,0) is None
