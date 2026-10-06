import pytest
from src.contract_engine import ContractEngine
from src.contract_registry import inventory,verify_document,duplicates

def test_weights():assert ContractEngine().validate_weights()==(20,10)
def test_bad_weights():
    e=ContractEngine();e.rules[0]['peso']=4
    with pytest.raises(ValueError):e.validate_weights()
def test_missing_document():assert next(d for d in inventory() if d['document_id']=='TA10')['status']=='DOCUMENTO NÃO DISPONÍVEL'
def test_contract_exclusion(tmp_path):
    p=tmp_path/'file';p.write_bytes(b'example')
    assert not verify_document(p,'019/2022','Outra unidade')['accepted']
    assert duplicates([{'document_id':'1','hash_sha256':'a'},{'document_id':'2','hash_sha256':'a'}])==[('1','2')]
