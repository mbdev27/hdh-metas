from pathlib import Path
import hashlib
from src.cache import file_version,yaml_versioned
ROOT = Path(__file__).resolve().parents[1]
def load(name):
    return yaml_versioned(file_version(ROOT/'config'/name))
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
