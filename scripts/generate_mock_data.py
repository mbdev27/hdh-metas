from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import random,pandas as pd
from src.indicators import indicators
from src.contract_engine import ContractEngine
ROOT=Path(__file__).resolve().parents[1]
def generate():
    rng=random.Random(202610);prod=[];quality=[]
    for i,m in enumerate(pd.period_range('2024-10',periods=24,freq='M')):
        p={'competencia':str(m)}
        for ind in indicators():
            if ind['grupo']=='quantitativo':p[ind['campo']]=round(ContractEngine().resolve(ind['indicator_id'],str(m),True)['valor']*rng.choice([.25,.54,.69,.84,.92,1.05,1.18]))
        p.update(sadt_producao=rng.randint(5000,9000),sad_emad=rng.randint(50,100),sad_emap=rng.randint(20,70),sadt_envio_data=str((m+1).start_time.date()+pd.Timedelta(days=23)),sad_envio_data=str((m+1).start_time.date()+pd.Timedelta(days=26)))
        if i==3:p['consultas_medicas']=None
        if i==8:p['cirurgias_genericas']=-2
        prod.append(p)
        q=dict(competencia=str(m),pacientes_urgencia=p['urgencia_emergencia'],pacientes_classificados=round(p['urgencia_emergencia']*.93),atendimentos_total=5000,pesquisas_respondidas=200 if i%5==0 else 600,pesquisas_positivas=180 if i%5==0 else 550,queixas_total=20,queixas_resolvidas=15,glosas_cnes_percent=rng.choice([0,1,5]),glosas_sia_percent=rng.choice([8,12,28]),glosas_sih_percent=rng.choice([7,17,32]),prestacao_contas_data=str((m+1).start_time.date()+pd.Timedelta(days=27 if i%4==0 else 23)),transparencia_nivel=rng.choice(['Desejado','Moderado','Intermediário']),obitos_total=30,obitos_revisados=28,infeccoes_hospitalares=round(p['saidas_hospitalares']*rng.choice([.04,.08,.16])),plantao_restrito_qtd=int(i%6==0),educacao_previstas=10,educacao_realizadas=rng.choice([7,9,10,11]),ocupacao_geral=rng.uniform(75,97),prontuarios_vermelho_amarelo_total=100,prontuarios_vermelho_amarelo_revisados=12)
        if i==7:q['obitos_revisados']=31
        quality.append(q)
    out=ROOT/'data/mock';out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(prod).to_csv(out/'producao.csv',index=False);pd.DataFrame(quality).to_csv(out/'qualidade.csv',index=False)
if __name__=='__main__':generate()
