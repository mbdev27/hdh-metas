from pathlib import Path
import yaml, hashlib
ROOT = Path(__file__).resolve().parents[1]
def load(name):
    return yaml.safe_load((ROOT/'config'/name).read_text(encoding='utf8'))
def inventory(): return load('contract_documents.yaml')['documents']
def verify_document(path, contract_number, unit):
    return {'accepted': contract_number == '018/2022' and unit == load('organizational_units.yaml')['units'][0]['nome'], 'hash_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}
def duplicates(documents):
    seen={}; result=[]
    for d in documents:
        h=d.get('hash_sha256')
        if h and h in seen: result.append((seen[h],d['document_id']))
        elif h: seen[h]=d['document_id']
    return result
