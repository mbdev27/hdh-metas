import pandas as pd
from src.indicators import indicators
PRODUCTION=['competencia']+[i['campo'] for i in indicators() if i['campo'] and i['grupo']=='quantitativo']+['sadt_producao','sad_emad','sad_emap','sadt_envio_data','sad_envio_data']
QUALITY=['competencia','pacientes_urgencia','pacientes_classificados','atendimentos_total','pesquisas_respondidas','pesquisas_positivas','queixas_total','queixas_resolvidas','glosas_cnes_percent','glosas_sia_percent','glosas_sih_percent','prestacao_contas_data','transparencia_nivel','obitos_total','obitos_revisados','infeccoes_hospitalares','plantao_restrito_qtd','educacao_previstas','educacao_realizadas','ocupacao_geral','prontuarios_vermelho_amarelo_total','prontuarios_vermelho_amarelo_revisados']
def validate(frame,kind):
    df=frame.copy();issues=[];bad=set();required=PRODUCTION if kind=='producao' else QUALITY
    def add(idx,col,msg,severity='ERRO'):
        issues.append(dict(linha=idx,campo=col,nivel=severity,mensagem=msg))
        if severity=='ERRO' and idx is not None:bad.add(idx)
    for c in required:
        if c not in df: add(None,c,'Campo obrigatório ausente');df[c]=None;bad.update(df.index)
    for idx,row in df.iterrows():
        try:
            val=str(row['competencia']);normalized=str(pd.Period(val,freq='M'))
            if val!=normalized:raise ValueError()
        except (ValueError,TypeError):add(idx,'competencia','Competência inválida: usar AAAA-MM')
        for c in required:
            if pd.isna(row[c]):add(idx,c,'Dado ausente','ALERTA');continue
            if c.endswith('_data'):
                if pd.isna(pd.to_datetime(row[c],errors='coerce')):add(idx,c,'Data inválida')
            elif c not in ('competencia','transparencia_nivel'):
                v=pd.to_numeric(row[c],errors='coerce')
                if pd.isna(v) or v<0:add(idx,c,'Valor não numérico ou negativo')
                elif ('percent' in c or c=='ocupacao_geral') and v>100:add(idx,c,'Percentual fora de 0–100')
                elif 'percent' not in c and c!='ocupacao_geral' and v%1:add(idx,c,'Contagem deve ser inteira')
        if kind=='qualidade':
            if pd.notna(row['transparencia_nivel']) and row['transparencia_nivel'] not in ('Desejado','Moderado','Intermediário','Insuficiente','Crítico'):add(idx,'transparencia_nivel','Nível inválido')
            for a,b,severity in [('pesquisas_positivas','pesquisas_respondidas','ERRO'),('pesquisas_respondidas','atendimentos_total','ALERTA'),('queixas_resolvidas','queixas_total','ERRO'),('obitos_revisados','obitos_total','ERRO'),('educacao_realizadas','educacao_previstas','ALERTA'),('pacientes_classificados','pacientes_urgencia','ERRO'),('prontuarios_vermelho_amarelo_revisados','prontuarios_vermelho_amarelo_total','ERRO')]:
                va=pd.to_numeric(row[a],errors='coerce');vb=pd.to_numeric(row[b],errors='coerce')
                if pd.notna(va) and pd.notna(vb) and va>vb:add(idx,a,f'{a} > {b}',severity)
    for idx in df.index[df.competencia.duplicated(keep=False)]:add(idx,'competencia','Competência duplicada')
    for c in required:
        if c not in ('competencia','transparencia_nivel') and not c.endswith('_data'):df[c]=pd.to_numeric(df[c],errors='coerce')
    report=pd.DataFrame(issues,columns=['linha','campo','nivel','mensagem'])
    return df.drop(index=list(bad)),report,{'linhas_carregadas':len(df),'linhas_validas':len(df)-len(bad),'linhas_rejeitadas':len(bad),'duplicidades':int(df.competencia.duplicated(keep=False).sum()),'campos_faltantes':int(df[required].isna().sum().sum())}
