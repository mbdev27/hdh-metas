"""Managerial summaries: physical achievement and data completeness, no pooled production."""
import pandas as pd
from src.contract_engine import ContractEngine

STATUS={'META ATINGIDA':'Atingida','ATENÇÃO':'Não atingida','CRÍTICO':'Crítico','SEM DADOS':'Sem dados'}


def production_summary(data,contract,competence):
    rows=data[(data.contrato==contract)&(data.competencia==competence)].copy()
    rows['situacao']=rows.situacao.replace(STATUS)
    previous=str(pd.Period(competence,freq='M')-1)
    before=data[(data.contrato==contract)&(data.competencia==previous)]
    comparisons=before.set_index('indicator_id')
    changes=[]
    for row in rows.itertuples():
        change=None
        if row.indicator_id in comparisons.index:
            old=comparisons.loc[row.indicator_id]
            # Compare only adjacent documented months with the same rule/definition.
            if pd.notna(row.atingimento) and pd.notna(old.atingimento) and row.regra==old.regra:
                change=row.atingimento-old.atingimento
        changes.append(change)
    rows['variacao_pp']=changes
    rows['deficit_percentual']=(100-rows.atingimento).clip(lower=0)
    return rows


def quality_summary(data,contract,competence):
    rows=data[(data.contrato==contract)&(data.competencia==competence)].copy()
    rules={r['rule_id']:r for r in ContractEngine().rules}
    statuses=[]
    for row in rows.itertuples():
        if row.status_dado=='SEM DADOS':status='Sem dados'
        elif row.status_dado=='INCONSISTÊNCIA NA FONTE':status='Inconsistência'
        else:
            rule=rules.get(row.regra)
            status='Não aferível'
            if rule and isinstance(rule['valor'],(int,float)) and pd.notna(row.valor):
                ok=row.valor<=rule['valor'] if rule['operador']=='<=' else row.valor>=rule['valor']
                status='Atingida' if ok else 'Não atingida'
            elif rule and isinstance(rule['valor'],str):
                # A published category can be compared without inventing a numeric score.
                if str(row.resultado_texto).strip().casefold()==rule['valor'].casefold():status='Atingida'
        statuses.append(status)
    rows['situacao']=statuses
    return rows


def comparable_annual(data,same_months=False):
    if data.empty or not same_months:return data.copy()
    latest=data.competencia.str[:4].max()
    # A month must be represented by all selected contracts/indicators in the latest year.
    selected=data[data.competencia.str.startswith(latest)]
    groups=selected.groupby(['contrato','indicator_id'])
    sets=[set(group.competencia.str[5:7]) for _,group in groups]
    months=set.intersection(*sets) if sets else set()
    return data[data.competencia.str[5:7].isin(months)].copy()
