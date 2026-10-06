"""Inventário de integridade; identidade jurídica exige leitura/revisão humana."""
import argparse,hashlib,json
from pathlib import Path

def audit(directory):
    records=[];seen={}
    for path in sorted(Path(directory).rglob('*')):
        if not path.is_file():continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        records.append({'nome_arquivo':str(path),'hash_sha256':digest,'duplicado_de':seen.get(digest),'status':'AGUARDANDO REVISÃO DE CONTRATO, UNIDADE E CONTEÚDO'})
        seen.setdefault(digest,str(path))
    return records
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory');parser.add_argument('--output',default='inventory_pending.json');args=parser.parse_args()
    Path(args.output).write_text(json.dumps(audit(args.directory),ensure_ascii=False,indent=2),encoding='utf8')
