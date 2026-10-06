import pandas as pd
from src.indicators import indicators
from src.contract_engine import ContractEngine
from src.scoring import score
def safe_ratio(n,d):
    return None if n is None or d is None or pd.isna(n) or pd.isna(d) or d<=0 else float(n)/float(d)*100
def monthly(production,quality,competence):
    engine=ContractEngine();engine.validate_weights()
    p=production[production.competencia==competence];q=quality[quality.competencia==competence]
    data={}
    if not p.empty: data.update(p.iloc[0].to_dict())
    if not q.empty: data.update(q.iloc[0].to_dict())
    rows=[]
    for ind in indicators():
        r=engine.resolve(ind['indicator_id'],competence,demo=True);v=data.get(ind['campo'])
        if ind['formula']=='ratio': v=safe_ratio(v,data.get(ind['denominador']))
        if ind['formula']=='deadline':
            deadline=pd.Timestamp(competence)+pd.offsets.MonthBegin(1)+pd.Timedelta(days=24)
            v=None if v is None or pd.isna(v) else int(pd.Timestamp(v)<=deadline)
        achieved=safe_ratio(v,r['valor']) if ind['grupo']=='quantitativo' else None
        points=score(achieved if ind['grupo']=='quantitativo' else v,r)
        missing=v is None or pd.isna(v)
        ok=False if missing else (v==r['valor'] if isinstance(r['valor'],str) else ((v<=r['valor'] if r['operador']=='<=' else v>=r['valor']) if r['valor'] is not None else True))
        status='SEM DADOS' if missing else ('META ATINGIDA' if ok else 'META NÃO ATINGIDA')
        if ind['indicator_id']=='QL02':
            conversion=safe_ratio(data.get('pesquisas_respondidas'),data.get('atendimentos_total'))
            if conversion is None or conversion<10: points=None;status='AMOSTRA INSUFICIENTE PARA AFERIÇÃO CONTRATUAL'
        rows.append(dict(indicador=ind['indicator_id'],nome=ind['nome'],grupo=ind['grupo'],meta=r['valor'],realizado=v,atingimento=achieved,diferenca=None if missing or not isinstance(r['valor'],(float,int)) else v-r['valor'],pontuacao=points,peso=r['peso'],situacao=status,regra=r['rule_id']))
    return pd.DataFrame(rows)
def quarter(production,quality,period):
    months=[str(x) for x in pd.period_range(period.start_time,period.end_time,freq='M')]
    tables=[monthly(production,quality,m) for m in months];rows=[];engine=ContractEngine()
    for ind in indicators():
        if ind['grupo']!='quantitativo': continue
        rs=[t[t.indicador==ind['indicator_id']].iloc[0] for t in tables]
        target=sum(x['meta'] for x in rs)
        actual=None if any(pd.isna(x['realizado']) for x in rs) else sum(x['realizado'] for x in rs)
        rate=safe_ratio(actual,target);r=engine.resolve(ind['indicator_id'],months[0],True)
        rows.append(dict(indicador=ind['indicator_id'],nome=ind['nome'],**{m:rs[i]['realizado'] for i,m in enumerate(months)},meta=target,realizado=actual,atingimento=rate,pontuacao=score(rate,r),situacao='SEM DADOS' if rate is None else ('Desempenho trimestral inferior a 85%. Verificar regra de compensação e providências contratuais.' if rate<85 else 'FAIXA FINANCEIRA MÁXIMA')))
    return pd.DataFrame(rows),tables
