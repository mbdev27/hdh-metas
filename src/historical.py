"""Public CMA aggregates. Original observations and normative rules remain separate."""
import pandas as pd
from src.contract_registry import ROOT,load
from src.contract_engine import ContractEngine
from src.scoring import score

def real_data():
    p=pd.read_csv(ROOT/'data/real/producao.csv',dtype={'competencia':str})
    q=pd.read_csv(ROOT/'data/real/qualidade.csv',dtype={'competencia':str})
    return enrich(p),enrich_quality(q)

def names():return {i['indicator_id']:i['nome'] for i in load('indicators.yaml')['indicators']}

def enrich(data):
    engine=ContractEngine();engine.validate_weights();engine.validate_weights('CG018_ORIGINAL');output=[];lookup=names()
    for row in data.to_dict('records'):
        id_=row['indicator_id'];comp=row['competencia'];day=str((pd.Timestamp(comp)+pd.offsets.MonthEnd(0)).date())
        r=engine.resolve(id_,day) if row['contrato']=='018/2022' else None
        target=r['valor'] if r else row['meta_reported']
        actual=row['realizado'];missing=pd.isna(actual)
        row['observacao']='' if pd.isna(row.get('observacao')) else row['observacao']
        rate=None if missing or not target else actual/target*100
        row.update(nome=lookup.get(id_,id_),meta_contratual=target,atingimento=rate,
            diferenca=None if missing else actual-target,pontuacao=None if not r else score(rate,r),
            peso=None if not r else r['peso'],regra=None if not r else r['rule_id'],
            instrumento_meta=r['documento_fonte'] if r else 'Contrato 006/2010 não fornecido — meta referida pela CMA',
            pagina_meta=r['pagina_fonte'] if r else None,
            situacao='SEM DADOS' if missing else 'META ATINGIDA' if rate>=100 else 'CRÍTICO' if rate<55 else 'ATENÇÃO',
            divergencia_meta=target!=row['meta_reported'])
        if comp=='2024-07':row['observacao']+=' Transição TA08 → RERR08 dentro do mês; meta quantitativa coincidente; eficácia retroativa não presumida.'
        output.append(row)
    return pd.DataFrame(output)

def enrich_quality(data):
    engine=ContractEngine();out=[];lookup=names()
    for row in data.to_dict('records'):
        comp=row['competencia'];id_=row['indicator_id'];r=engine.resolve(id_,str((pd.Timestamp(comp)+pd.offsets.MonthEnd(0)).date()))
        row['nome']=lookup.get(id_,row['indicador_fonte']);row['pontuacao']=None;row['instrumento_meta']=r['documento_fonte'] if r else 'Definição histórica — consultar meta do parecer';row['regra']=r['rule_id'] if r else None
        row['meta_aplicada']=r['valor'] if r else row['meta_texto_fonte'];row['peso']=r['peso'] if r else None
        row['observacao']='' if pd.isna(row.get('observacao')) else row['observacao']
        if r and r.get('faixas') is not None and row['status_dado'] in ('INFORMADO','ALERTA'):
            value=row['valor'];text=str(row['resultado_texto'])
            if id_=='QL07':value=0 if 'fora' in text.lower() else 1 if 'no prazo' in text.lower() else None
            if id_=='QL08':value=next((v for v in r['faixas'] if v.lower() in text.lower()),None)
            # Public matrix lacks the survey conversion denominator: no contractual score.
            if id_=='QL02':row['observacao']=str(row.get('observacao',''))+' Conversão mínima de 10% não aferível: denominadores não publicados nesta matriz.'
            else:row['pontuacao']=score(value,r)
        out.append(row)
    return pd.DataFrame(out)

def aggregate(data,freq='Q'):
    work=data.copy();work['periodo']=pd.PeriodIndex(work.competencia,freq='M').asfreq(freq).astype(str);out=[]
    for (period,contract,id_),group in work.groupby(['periodo','contrato','indicator_id'],sort=True):
        expected=3 if freq=='Q' else 12
        missing=group.realizado.isna().any();actual=None if missing else group.realizado.sum()
        target=group.meta_contratual.sum();rate=None if actual is None or target<=0 else actual/target*100
        rule_ids=group.regra.dropna().unique();r=next((r for r in ContractEngine().rules if len(rule_ids)==1 and r['rule_id']==rule_ids[0]),None)
        out.append(dict(periodo=period,contrato=contract,indicator_id=id_,nome=group.iloc[0]['nome'],meses_presentes=group.competencia.nunique(),meses_esperados=expected,meta_acumulada=target,realizado=actual,atingimento=rate,pontuacao=score(rate,r) if r and freq=='Q' and len(group)==3 else None,cobertura='COMPLETA' if len(group)==expected else 'PARCIAL — SOMENTE MESES DOCUMENTADOS',situacao='SEM DADOS' if missing else 'META ATINGIDA' if rate>=100 else 'ATENÇÃO',documentos=', '.join(sorted(group.documento_fonte.unique()))))
    return pd.DataFrame(out)

def evidence(document_id,page=None):
    import json
    rows=json.loads((ROOT/'data/real/evidencias.json').read_text())
    return '\n\n'.join(f"PÁGINA {r['pagina']}\n{r['texto']}" for r in rows if r['document_id']==document_id and (page is None or r['pagina']==page))
