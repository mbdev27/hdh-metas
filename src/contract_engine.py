"""Scoped rules: replacement closes an interval, it never deletes historical evidence."""
from datetime import date
from src.contract_registry import load

class ContractEngine:
    def __init__(self, rules=None):
        self.rules = rules if rules is not None else load('contract_rules.yaml')['rules']

    def resolve(self, indicator, competence, demo=False):
        day = date.fromisoformat(str(competence) if len(str(competence)) == 10 else str(competence)[:7]+'-01')
        candidates = [r for r in self.rules if r['indicator_id']==indicator
            and r['tipo_alteracao'] not in ('REVOGADA','SUBSTITUÍDA')
            and r.get('status_validacao')=='VALIDADA' and r.get('inicio_vigencia')
            and date.fromisoformat(r['inicio_vigencia'])<=day
            and (not r.get('fim_vigencia') or day<=date.fromisoformat(r['fim_vigencia']))]
        if len(candidates)>1:
            raise ValueError('Regras sobrepostas: validar escopo e vigência')
        if candidates:
            return candidates[0]
        if demo:
            return next((r for r in load('demo_rules.yaml')['rules'] if r['indicator_id']==indicator),None)
        return None

    def validate_weights(self, ruleset='RERR08'):
        selected=[r for r in self.rules if r.get('ruleset',ruleset)==ruleset and r['tipo_alteracao'] not in ('REVOGADA','SUBSTITUÍDA')]
        q=sum(r['peso'] or 0 for r in selected if r['indicator_id'].startswith('Q') and not r['indicator_id'].startswith('QL'))
        l=sum(r['peso'] or 0 for r in selected if r['indicator_id'].startswith(('QL','OQL')))
        if abs(q-20)>1e-8 or abs(l-10)>1e-8:
            raise ValueError('Erro de configuração: pesos devem totalizar 20 + 10 = 30 p.p.')
        return q,l

    def monthly_value(self, competence):
        day=date.fromisoformat(str(competence)[:7]+'-01')
        periods=load('contract_documents.yaml')['contract_financial_periods']
        return next((p['valor_mensal'] for p in periods if p.get('status_validacao')=='REFERÊNCIA EXPRESSA COM VIGÊNCIA DELIMITADA'
            and date.fromisoformat(p['inicio'])<=day and p.get('fim') and day<=date.fromisoformat(p['fim'])),None)

    def history(self, indicator):
        return sorted([r for r in self.rules if r['indicator_id']==indicator],key=lambda r:r.get('inicio_vigencia') or '')
