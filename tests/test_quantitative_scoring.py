import pytest
from src.contract_engine import ContractEngine
from src.scoring import score
@pytest.mark.parametrize('id,maximum,expected',[('Q01',3,[0,1,1,1.5,1.5,2,2,3,3]),('Q04',1,[0,.25,.25,.5,.5,.75,.75,1,1]),('Q05',2,[0,.5,.5,1,1,1.5,1.5,2,2])])
def test_boundaries(id,maximum,expected):
    r=ContractEngine().resolve(id,'2026-07',True)
    assert [score(x,r) for x in [29.99,30,54.99,55,69.99,70,84.99,85,130]]==expected
    assert score(None,r) is None
