"""Protected proposed-indicator page with minimized inputs and calculation memories."""
from copy import deepcopy
from datetime import date
import json
import logging
import pandas as pd
import plotly.express as px
import streamlit as st
from src.auth import require_login
from src.theme import apply_theme,header,footer,sidebar_notice
from src.contract_registry import load
from src.exports import csv_bytes,workbook
from src.presentation import chart,section
from src.restructuring.schema import current_actor,COMMON,FIELDS,DIMENSIONS
from src.restructuring.settings import storage_path,persistent_repository
from src.restructuring.demo import create_demo

LABELS={
 'entity_id':'Código operacional opaco','sector':'Setor','protocol':'Protocolo/competência','shift':'Turno','specialty':'Especialidade',
 'source':'Fonte de coleta','evidence':'Referência da evidência (sem dados pessoais)','applicable':'Aplicável/elegível',
 'exclusion_approved':'Não aplicabilidade validada','exclusion_justification':'Justificativa da exclusão','critical':'Falha de risco crítico',
 'valid_from':'Início da validade/aplicabilidade','valid_until':'Fim da validade','granted':'Documento concedido e verificável',
 'scope_sufficient':'Escopo suficiente','track':'Trilha documental','evaluated':'Avaliação realizada','conform':'Conformidade demonstrada',
 'event_date':'Data da cirurgia/oportunidade','moments':'Três momentos','timely':'Registro tempestivo','observed_complete':'Observação integral',
 'sample_method':'Método de seleção da amostra','planned_date':'Data originalmente programada','completed_date':'Data de conclusão',
 'report_valid':'Relatório válido com escopo, critérios, evidências e encaminhamentos','extra':'Auditoria extra','original_calendar':'Referência do calendário original',
 'original_due':'Prazo original','current_due':'Prazo atual (não substitui o original)','closed_date':'Data de encerramento',
 'validated_date':'Data de validação da eficácia','efficacy':'Eficácia comprovada','rechecked_date':'Data de reavaliação após a janela',
 'recurrence_date':'Data do reaparecimento','requirement_key':'Código do requisito','recurrence_requirement_key':'Requisito que reapareceu',
 'recurrence_sector':'Setor do reaparecimento','recurred':'Reapareceu na janela de 90 dias',
 'approved':'Protocolo aprovado','resources_ready':'Recursos disponíveis','training_done':'Capacitação concluída','use_verified':'Uso demonstrado em campo',
 'priority':'Integra prioridades pactuadas','priority_list_version':'Versão da lista prioritária','all_steps_correct':'Todas as etapas aplicáveis executadas',
 'person_token':'Código opaco do profissional (sem matrícula/CPF/CNS)','competency':'Competência de capacitação','eligible':'Profissional elegível',
 'assessment_satisfactory':'Avaliação satisfatória','function':'Função','received_date':'Data de recebimento','investigated_date':'Investigação concluída em',
 'gravity':'Gravidade conforme critério interno','incident_id':'Código do incidente vinculado','bed_number':'Número do novo leito',
 'shared_group':'Código do recurso/requisito compartilhado','shared_conform':'Conformidade compartilhada','record_kind':'Tipo de registro UTI',
 'triaged_date':'Triagem concluída em','dependencies':'Grupos compartilhados de que o leito depende','dimensions':'Dimensões do leito',
}
COLORS={'Meta atingida no período':'#24956a','Abaixo da meta':'#d29520','Falha crítica identificada':'#d35a64','Prazo ainda em curso':'#146bb0','Meta ainda não pactuada':'#93a3b4','Não aferível':'#93a3b4','Não aplicável no período':'#93a3b4'}


def message_error(error):
    if isinstance(error,(ValueError,PermissionError)):st.error(str(error))
    else:
        logging.getLogger(__name__).error('Operação de reestruturação indisponível (%s)',type(error).__name__)
        st.error('Não foi possível concluir a operação. Verifique o armazenamento e tente novamente; nenhum sucesso de gravação foi confirmado.')


def definitions(repo,actor):
    return repo.definitions(actor) if repo and repo.initialized(actor) else deepcopy(load('restructuring_indicators.yaml')['indicators'])


def summary_table(assessments):
    columns={'number':'Indicador','start':'Início','end':'Fim','value_rounded':'Resultado (%)','target':'Meta (%)','classification':'Situação','pact_status':'Pactuação','definition_version':'Versão da ficha'}
    frame=pd.DataFrame(assessments)
    return frame[[key for key in columns if key in frame]].rename(columns=columns) if not frame.empty else pd.DataFrame(columns=list(columns.values()))


def overview(repo,actor,catalog):
    assessments=repo.assessments(actor) if repo else []
    period=st.date_input('Período do resumo',value=(date(2026,1,1),date.today()),key='restructure_overview_dates')
    if len(period)!=2:st.info('Selecione início e fim do período.');return
    start,end=period
    selected=[row for row in assessments if row['start']>=str(start) and row['end']<=str(end)]
    latest={}
    for row in sorted(selected,key=lambda row:row['end']):latest[(row['number'],json.dumps(row['scope'],sort_keys=True))]=row
    cards=st.columns(4)
    cards[0].metric('Indicadores propostos',14)
    cards[1].metric('Fichas pactuadas',sum(d['pact_status']=='Pactuada' for d in catalog))
    cards[2].metric('Apurações no recorte',len(selected))
    cards[3].metric('Falhas críticas registradas',sum(bool(row['critical']) for row in latest.values()))
    if not selected:
        st.info('Ainda não há apurações para este período. Linhas de base e resultados não são preenchidos com zero.')
    else:
        st.dataframe(summary_table(list(latest.values())),hide_index=True,width='stretch')
        st.caption('Não existe nota média de adequação do hospital. Cada escopo mantém sua apuração; metas atingidas não equivalem a conformidade legal.')
    st.write('**Fichas disponíveis**')
    st.dataframe(pd.DataFrame([{'Nº':d['number'],'Indicador':d['name'],'Meta proposta/vigente (%)':d['target'],'Pactuação':d['pact_status'],'Linha de base':d['baseline']['status']} for d in catalog]),hide_index=True,width='stretch')


def show_definition(definition):
    st.write('**Finalidade:** '+definition['purpose'])
    st.write('**Ação acompanhada:** '+definition['action'])
    st.write('**Fórmula:** '+definition['formula'])
    st.write('**Numerador:** '+definition['numerator_definition'])
    st.write('**Denominador:** '+definition['denominator_definition'])
    st.write(f"**Meta:** {definition['target']}% · sentido: {definition['improvement']}")
    st.write('**Pactuação:** '+definition['pact_status'])
    start=definition.get('approved_plan_start')
    st.write('**Início aprovado do plano:** '+(start or 'Não registrado'))
    if definition['milestone_days'] is not None:st.caption(f"Marco gerencial: {definition['milestone_days']} dias após início aprovado. Não substitui prazos individuais nem autoriza condição insegura.")
    baseline=definition['baseline']
    st.write('**Linha de base:** '+(baseline['status'] if baseline['value'] is None else f"{baseline['value']}% · {baseline['period']} · {baseline['coverage']} · {baseline['evidence']}"))
    st.write('**Coleta:** '+definition['collector']+' · **Validação:** '+definition['validator'])
    st.write('**Fonte:** '+definition['source']+' · **Método:** '+definition['collection_method'])
    st.write('**Periodicidade:** '+definition['frequency'])
    with st.expander('Inclusões, exclusões e critérios de conclusão'):
        for rule in definition['eligibility_rules']:st.write('• '+rule)
        st.write('**Conclusão:** '+definition['conclusion_criteria'])
    st.write('**Resposta prevista ao desvio:** '+definition['deviation_response'])
    st.caption('Sentido de melhoria: '+definition['improvement']+' · Unidade: '+definition['unit']+' · Ficha v'+str(definition['version']))


def memory(row):
    with st.expander('Memória de cálculo',expanded=True):
        st.write(row['definition_snapshot']['formula'])
        st.write(f"Período: {row['start']} a {row['end']} · Corte: {row['cutoff']} · Ficha v{row['definition_version']} · {row['calculation_type']}")
        n=row['numerator'];d=row['denominator']
        if row['value_raw'] is not None:
            st.write(f"**{n} ÷ {d} × 100 = {row['value_raw']:.10g}%** · apresentado: {row['value_rounded']:.2f}%")
        else:st.info(row['status_data']+' — não representa 0% ou 100%.')
        st.write('**Fonte:** '+row['source']+' · **Método:** '+row['method'])
        st.write('**Limitações:** '+(row['limitations'] or 'Sem limitação adicional registrada; conferir cobertura e método.'))
        for title,key in [('Incluídos','included'),('Excluídos e justificativas','excluded'),('Pendências','pending')]:
            if row[key]:
                st.write('**'+title+'**');st.dataframe(pd.DataFrame(row[key]).rename(columns={'id':'Código operacional','reason':'Justificativa','contributes':'Contribui ao numerador','original_due':'Prazo original'}),hide_index=True,width='stretch')
        if row['coverage']:st.write('**Cobertura:**');st.dataframe(pd.DataFrame([{'Critério':key,'Informação':str(value)} for key,value in row['coverage'].items()]),hide_index=True)
        context=row['context']
        st.write('**Coleta:** '+context['collector']+' · **Validação:** '+context['validator']+' · **Evidência:** '+context['validation_evidence'])
        st.caption('Registrado por '+row['author']+' · Atualizado em '+row['updated_at'])


def followup(repo,actor,catalog):
    lookup={d['number']:d for d in catalog}
    number=st.selectbox('Indicador de reestruturação',list(lookup),format_func=lambda n:f'{n}. '+lookup[n]['name'],key='restructure_indicator')
    definition=lookup[number];show_definition(definition)
    all_rows=repo.assessments(actor,number) if repo else []
    period=st.date_input('Período de acompanhamento',value=(date(2026,1,1),date.today()),key=f'restructure_period_{number}')
    if len(period)!=2:st.info('Selecione início e fim do período.');return number
    start,end=period
    rows=[r for r in all_rows if r['start']>=str(start) and r['end']<=str(end)]
    for field,label in [('sector','Setor'),('protocol','Protocolo/competência')]:
        choices=['Todos']+sorted({r['scope'].get(field,'') for r in rows if r['scope'].get(field)})
        chosen=st.selectbox(label,choices,key=f'restruct_filter_{field}_{number}')
        if chosen!='Todos':rows=[r for r in rows if r['scope'].get(field)==chosen]
    statuses=['Todas']+sorted({r['classification'] for r in rows})
    chosen=st.selectbox('Situação das apurações',statuses,key=f'restruct_status_{number}')
    if chosen!='Todas':rows=[r for r in rows if r['classification']==chosen]
    rows=sorted(rows,key=lambda r:r['end'])
    if not rows:
        st.info('Sem apuração neste recorte. Não há gráfico de desempenho nem série inventada.')
    else:
        # Scope/definition groups stay separate, including before/after repactuation.
        latest=rows[-1]
        c=st.columns(3)
        c[0].metric('Resultado do último período','Não aferível' if latest['value_raw'] is None else f"{latest['value_rounded']:.2f}%")
        c[1].metric('Numerador','Não informado' if latest['numerator'] is None else latest['numerator'])
        c[2].metric('Denominador','Não informado' if latest['denominator'] is None else latest['denominator'])
        st.write('**'+latest['classification']+'**')
        for flag in latest['flags']:st.caption(flag)
        if any(r['value_raw'] is not None for r in rows):
            series=pd.DataFrame([{'Período':r['end'],'Resultado (%)':r['value_raw'],'Meta (%)':r['target'],'Série':json.dumps(r['scope'],ensure_ascii=False,sort_keys=True)+' · ficha v'+str(r['definition_version']),'Pactuação':r['pact_status']} for r in rows])
            figure=px.line(series,x='Período',y='Resultado (%)',color='Série',markers=True,hover_data=['Pactuação'],title='Evolução por escopo e versão da ficha')
            figure.update_traces(connectgaps=False)
            for label,group in series.groupby('Série'):
                figure.add_scatter(x=group['Período'],y=group['Meta (%)'],mode='lines+markers',line={'dash':'dot'},name='Meta — '+label)
            chart(figure)
            st.caption('Versões e escopos não são conectados. Metas propostas permanecem identificadas; a série não constitui uma conclusão de conformidade legal.')
        selected=st.selectbox('Apuração para conferir',range(len(rows)),format_func=lambda i:rows[i]['start']+' a '+rows[i]['end']+' · '+rows[i]['classification'],key=f'restructure_memory_{number}')
        row=rows[selected];memory(row)
        if number==7:st.info('Quanto menor a reincidência, melhor. Verifique janela completa e cobertura da reavaliação.')
        if number==13:
            if row['bed_dimensions']:
                st.write('**Dez novos leitos: avaliação por dimensão**')
                bedframe=pd.DataFrame(row['bed_dimensions'])
                data=bedframe.melt(id_vars=['leito'],value_vars=list(DIMENSIONS),var_name='Dimensão',value_name='Valor')
                data['Situação']=data.Valor.map(lambda value:'Não avaliado' if pd.isna(value) else 'Conforme' if bool(value) else 'Não conforme')
                chart(px.scatter(data,x='leito',y='Dimensão',color='Situação',symbol='Situação',color_discrete_map={'Conforme':'#24956a','Não conforme':'#d35a64','Não avaliado':'#93a3b4'},title='Situação dos dez leitos por dimensão'),hovermode='closest')
            else:st.caption('Apuração agregada: não existe avaliação por leito registrada para exibir.')
        if number==14 and row['complementary']:
            frame=pd.DataFrame([{'Contagem':key,'Quantidade':value} for key,value in row['complementary'].items()])
            chart(px.bar(frame,x='Contagem',y='Quantidade',title='Contagens complementares — notificações e pendências'))
            st.caption('Sem meta de redução dos relatos. Quantidade de notificações não representa incidência de dano.')
        elif row['complementary']:
            st.write('**Contagens complementares:**');st.dataframe(pd.DataFrame([{'Medida':key,'Valor':value} for key,value in row['complementary'].items()]),hide_index=True)
    with st.expander('Fundamentação normativa e técnica'):
        references={r['reference_id']:r for r in load('restructuring_references.yaml')['references']}
        for ref_id in definition['normative_refs']:
            ref=references[ref_id];st.write('**'+ref['title']+'**')
            st.write(ref['organ']+' · '+ref['relevant_device'])
            if ref['official_url']:st.markdown('[Consultar fonte oficial]('+ref['official_url']+')')
            st.caption(ref['verification_status']+' · '+ref['verification_note'])
            st.caption('Consulta: '+(ref['consulted_on'] or 'Ainda não registrada')+' · '+ref['formula_prescription'])
        st.info('Indicadores propostos não substituem indicadores específicos obrigatórios dos serviços e protocolos aplicáveis.')
    if repo:
        with st.expander('Histórico de pactuação, fichas e alterações'):
            history=repo.history(actor,'definition',number)
            for entry in history:
                d=entry['payload'];approval=d.get('approval') or {}
                st.write(f"**Ficha v{d['version']} · vigência {entry['effective_from']} · meta {d['target']}% · {d['pact_status']}**")
                st.write('Justificativa: '+entry['reason']+' · Registro: '+entry['author'])
                if approval:st.write('Aprovador informado: '+approval['approver']+' · '+approval['date']+' · evidência: '+approval['evidence'])
                if d['comparability_break']:st.warning('Mudança de definição/escopo: quebra de comparabilidade sinalizada.')
            actions=repo.actions(actor,number)
            if actions:st.write('**Ações registradas para desvios**');st.dataframe(pd.DataFrame(actions).drop(columns=['assessment_entity'],errors='ignore'),hide_index=True,width='stretch')
    return number


def read_field(key,kind,value,prefix):
    label=LABELS.get(key,key);widget=prefix+'_'+key
    if kind=='date':return _date_field(label,value,widget)
    if kind=='bool':return st.checkbox(label,value=bool(value),key=widget)
    if kind=='tri':
        choices=['Não avaliado','Conforme','Não conforme'];index=1 if value is True else 2 if value is False else 0
        selected=st.selectbox(label,choices,index=index,key=widget)
        return {'Não avaliado':None,'Conforme':True,'Não conforme':False}[selected]
    if kind=='moments':
        result=[]
        for i,name in enumerate(['Antes da indução','Antes da incisão','Antes da saída']):
            current=value[i] if value and len(value)==3 else None
            selected=st.selectbox(name,['Não avaliado','Correto','Falha'],index=1 if current is True else 2 if current is False else 0,key=widget+str(i))
            result.append({'Não avaliado':None,'Correto':True,'Falha':False}[selected])
        return result
    if kind=='bed':return int(st.number_input(label,min_value=1,max_value=10,value=value or 1,step=1,key=widget))
    if kind=='dimensions':return {dimension:read_field(dimension,'tri',(value or {}).get(dimension),widget) for dimension in DIMENSIONS}
    if kind=='dependencies':return [s.strip() for s in st.text_input(label,value=', '.join(value or []),key=widget).split(',') if s.strip()]
    if kind=='kind':return st.selectbox(label,['leito','requisito_compartilhado'],index=1 if value=='requisito_compartilhado' else 0,key=widget)
    if key=='track':return st.selectbox(label,['Sanitária','Bombeiros','Conselho profissional'],index=['Sanitária','Bombeiros','Conselho profissional'].index(value) if value else 0,key=widget)
    return st.text_input(label,value=value or '',key=widget)


def _date_field(label,value,key):
    selected=st.date_input(label,value=date.fromisoformat(value) if value else None,key=key)
    return str(selected) if selected else None


def record_form(repo,actor,number):
    history=repo._latest(actor,'record',number)
    choices=['Novo registro']+list(history)
    chosen=st.selectbox('Registro operacional',choices,key=f'restruct_record_pick_{number}')
    old=history.get(chosen);initial=old['payload']['record'] if old else {}
    st.caption('Registros opacos, sem nomes de pacientes, CPF, CNS ou prontuário. Evidências ficam no repositório autorizado da unidade; registre somente a referência minimizada.')
    if number==13:st.caption('Para recurso compartilhado, selecione requisito_compartilhado e informe o grupo. O mesmo grupo deve constar nas dependências de todos os leitos afetados.')
    with st.form(f'restruct_record_form_{number}_{chosen}'):
        payload={}
        for key,kind in {**COMMON,**FIELDS[number]}.items():
            if key=='applicable':value=initial.get(key,True)
            else:value=initial.get(key)
            payload[key]=read_field(key,kind,value,f'rec_{number}_{chosen}')
        effective=st.date_input('Vigência deste registro/snapshot',value=date.today(),key=f'record_effective_{number}_{chosen}')
        reason=st.text_input('Justificativa do cadastro/correção',key=f'record_reason_{number}_{chosen}')
        confirmed=st.checkbox('Confirmo fonte, evidência e ausência de dados pessoais identificáveis.')
        submit=st.form_submit_button('Salvar registro operacional')
    if submit:
        if not confirmed:st.error('Confirme a verificação antes de gravar.');return
        try:
            # Fields optional for a shared-resource record are not forced into a bed assessment.
            if number==13 and payload['record_kind']=='requisito_compartilhado':
                for key in ('bed_number','dimensions','dependencies'):payload.pop(key,None)
            repo.save_record(actor,number,payload,str(effective),reason,old['revision'] if old else None)
            st.success('Registro persistido; versão anterior preservada.');st.rerun()
        except Exception as error:message_error(error)


def definition_form(repo,actor,number):
    current=repo._latest(actor,'definition',number)[str(number)];initial=current['payload']
    with st.form(f'restruct_definition_{number}_{current["revision"]}'):
        name=st.text_input('Nome completo',initial['name']);purpose=st.text_area('Finalidade e ação acompanhada',initial['purpose'])
        formula=st.text_area('Fórmula por extenso',initial['formula'])
        numerator_definition=st.text_area('Definição do numerador',initial['numerator_definition'])
        denominator_definition=st.text_area('Definição do denominador',initial['denominator_definition'])
        conclusion_criteria=st.text_area('Critérios de conclusão',initial['conclusion_criteria'])
        st.caption('O algoritmo dos 14 indicadores é fixo e versionado no código. Alteração substantiva de fórmula exige revisão técnica do motor; editar a descrição não muda o cálculo automaticamente.')
        source=st.text_input('Fonte da ficha',initial['source']);method=st.text_input('Método de coleta',initial['collection_method'])
        frequency=st.text_input('Periodicidade',initial['frequency']);collector=st.text_input('Responsável pela coleta',initial['collector']);validator=st.text_input('Responsável pela validação',initial['validator'])
        scope=st.text_input('Escopo e critérios de elegibilidade',initial['scope']);rules=st.text_area('Regras de inclusão/exclusão (uma por linha)','\n'.join(initial['eligibility_rules']))
        response=st.text_area('Resposta prevista ao desvio',initial['deviation_response']);resources=st.text_input('Recursos e dependências',initial['resources'])
        target=st.number_input('Meta percentual',min_value=0.0,max_value=100.0,value=float(initial['target']))
        milestone=st.number_input('Marco após início aprovado (dias; zero = sem marco gerencial)',min_value=0,value=initial['milestone_days'] or 0,step=1)
        pact=st.selectbox('Situação da pactuação',['Proposta — aguardando pactuação','Pactuada'],index=1 if initial['pact_status']=='Pactuada' else 0)
        plan_start=st.date_input('Início aprovado do plano',value=date.fromisoformat(initial['approved_plan_start']) if initial['approved_plan_start'] else None)
        effective=st.date_input('Início da vigência da nova ficha',value=date.today())
        approval=initial.get('approval') or {}
        approver=st.text_input('Aprovador identificado documentalmente',approval.get('approver',''))
        approved_date=st.date_input('Data da aprovação documental',value=date.fromisoformat(approval['date']) if approval.get('date') else None)
        approved_evidence=st.text_input('Referência da evidência de aprovação',approval.get('evidence',''))
        baseline_known=st.checkbox('Linha de base efetivamente levantada',value=initial['baseline']['value'] is not None)
        baseline_value=st.number_input('Linha de base (%)',min_value=0.0,max_value=100.0,value=float(initial['baseline']['value'] or 0))
        baseline_period=st.text_input('Período da linha de base',initial['baseline'].get('period') or '')
        baseline_coverage=st.text_input('Cobertura da linha de base',initial['baseline'].get('coverage') or '')
        baseline_evidence=st.text_input('Referência da evidência da linha de base',initial['baseline'].get('evidence') or '')
        reason=st.text_input('Justificativa da pactuação/repactuação/alteração')
        submit=st.form_submit_button('Registrar nova versão da ficha')
    if submit:
        updated=deepcopy(initial)
        updated.update(name=name,purpose=purpose,action=purpose,formula=formula,numerator_definition=numerator_definition,denominator_definition=denominator_definition,conclusion_criteria=conclusion_criteria,source=source,collection_method=method,frequency=frequency,collector=collector,validator=validator,scope=scope,eligibility_rules=[r for r in rules.splitlines() if r.strip()],deviation_response=response,resources=resources,target=target,milestone_days=milestone or None,pact_status=pact,approved_plan_start=str(plan_start) if plan_start else None,effective_from=str(effective),approval={'approver':approver,'date':str(approved_date) if approved_date else None,'evidence':approved_evidence} if pact=='Pactuada' else None,baseline={'value':baseline_value if baseline_known else None,'period':baseline_period or None,'coverage':baseline_coverage or None,'evidence':baseline_evidence or None,'status':initial['baseline']['status']})
        try:repo.save_definition(actor,number,updated,reason,current['revision']);st.success('Versão registrada; apurações anteriores permanecem preservadas.');st.rerun()
        except Exception as error:message_error(error)


def assessment_form(repo,actor,number):
    previous=repo._latest(actor,'assessment',number)
    choices=['Nova apuração']+list(previous)
    chosen=st.selectbox('Apuração para inserir/corrigir',choices,format_func=lambda value:value if value=='Nova apuração' else previous[value]['payload']['start']+' a '+previous[value]['payload']['end']+' · v'+str(previous[value]['revision']),key=f'assessment_pick_{number}')
    old=previous.get(chosen);payload=old['payload'] if old else {};ctx=payload.get('context',{})
    with st.form(f'assessment_form_{number}_{chosen}'):
        start=st.date_input('Início do período apurado',value=date.fromisoformat(payload['start']) if payload else date.today().replace(day=1))
        end=st.date_input('Fim do período/data de corte',value=date.fromisoformat(payload['end']) if payload else date.today())
        mode=st.selectbox('Tipo de apuração',['Registros operacionais','Agregada'],index=1 if payload.get('calculation_type')=='Agregada' else 0)
        st.caption('Entrada agregada exige confirmação e fonte; não cria rastreabilidade individual inexistente. Para registros por prazo, o motor usa vencimento ORIGINAL no período.')
        numerator=int(st.number_input('Numerador (somente na entrada agregada)',min_value=0,value=payload.get('numerator') or 0,step=1))
        denominator=int(st.number_input('Denominador (somente na entrada agregada)',min_value=0,value=payload.get('denominator') or 0,step=1))
        source=st.text_input('Fonte desta apuração',ctx.get('source',''));method=st.text_input('Método desta apuração',ctx.get('method',''))
        sector=st.text_input('Setor do escopo (vazio = todos)',payload.get('scope',{}).get('sector',''))
        protocol=st.text_input('Protocolo/competência do escopo (obrigatório em 9 e 10)',payload.get('scope',{}).get('protocol',''))
        collector=st.text_input('Responsável pela coleta da apuração',ctx.get('collector',''));validator=st.text_input('Responsável pela validação da apuração',ctx.get('validator',''))
        evidence=st.text_input('Referência da evidência da validação',ctx.get('validation_evidence',''))
        limitations=st.text_area('Cobertura e limitações',ctx.get('limitations',''))
        coverage=st.text_input('Descrição da cobertura (entrada agregada)',str(ctx.get('coverage',{}).get('descricao','')))
        universe=st.checkbox('Universo elegível confirmado (inclusive quando comprovadamente vazio)',value=bool(ctx.get('universe_confirmed')))
        eligibility=st.checkbox('Critérios de elegibilidade conferidos',value=bool(ctx.get('eligibility_confirmed')))
        critical=st.checkbox('Falha crítica identificada na apuração',value=bool(ctx.get('critical')))
        reason=st.text_input('Justificativa da apuração/correção',value='Nova apuração' if not old else '')
        submit=st.form_submit_button('Calcular e registrar apuração')
    if submit:
        context=dict(source=source,method=method,collector=collector,validator=validator,validation_evidence=evidence,limitations=limitations,coverage={'descricao':coverage} if coverage else {},universe_confirmed=universe,eligibility_confirmed=eligibility,critical=critical,data_origin=repo.origin)
        scope={key:value for key,value in [('sector',sector),('protocol',protocol)] if value}
        try:
            repo.assess(actor,number,str(start),str(end),context,scope,{'numerator':numerator,'denominator':denominator} if mode=='Agregada' else None,reason,chosen if old else None,old['revision'] if old else None)
            st.success('Apuração calculada e persistida, com ficha e meta históricas.');st.rerun()
        except Exception as error:message_error(error)


def actions_form(repo,actor,number):
    assessments=repo.assessments(actor,number)
    if not assessments:st.info('Registre uma apuração antes de vincular uma ação.');return
    actions=repo._latest(actor,'action',number)
    choice=st.selectbox('Ação de tratamento',['Nova ação']+list(actions),key=f'action_pick_{number}')
    old=actions.get(choice);value=old['payload'] if old else {}
    with st.form(f'action_form_{number}_{choice}'):
        id_=st.text_input('Código da ação',value.get('action_id',''))
        assessment=st.selectbox('Apuração vinculada',assessments,format_func=lambda a:a['start']+' a '+a['end']+' · '+a['classification'])
        description=st.text_area('Ação necessária',value.get('description',''));responsible=st.text_input('Responsável pela ação',value.get('responsible',''))
        due=st.date_input('Prazo original da ação',value=date.fromisoformat(value['original_due']) if value.get('original_due') else date.today())
        current=st.date_input('Prazo atual (se alterado)',value=date.fromisoformat(value['current_due']) if value.get('current_due') else None)
        status=st.selectbox('Situação da ação',['Aberta','Em execução','Concluída com evidência'])
        evidence=st.text_input('Evidência da ação',value.get('evidence',''));reason=st.text_input('Justificativa do registro/alteração da ação')
        submit=st.form_submit_button('Registrar ação de tratamento')
    if submit:
        try:
            repo.save_action(actor,number,dict(action_id=id_,assessment_entity=assessment['assessment_entity'],description=description,responsible=responsible,original_due=str(due),current_due=str(current) if current else None,status=status,evidence=evidence),reason,old['revision'] if old else None)
            st.success('Ação registrada com histórico.');st.rerun()
        except Exception as error:message_error(error)


def admin(repo,actor,catalog):
    actor.require(write=True)
    if not repo:st.info('Inicialize as fichas propostas antes de registrar dados institucionais. Consulte o manual de configuração.');return
    lookup={d['number']:d for d in catalog}
    number=st.selectbox('Ficha para administrar',list(lookup),format_func=lambda n:f'{n}. '+lookup[n]['name'],key='restructure_admin_indicator')
    action=section(['Registros operacionais','Apurações','Pactuação e ficha','Ações para desvios'],'restruct_admin_section')
    if action=='Registros operacionais':record_form(repo,actor,number)
    elif action=='Apurações':assessment_form(repo,actor,number)
    elif action=='Pactuação e ficha':definition_form(repo,actor,number)
    else:actions_form(repo,actor,number)
    backup_controls(repo,actor)
    with st.expander('Histórico de autoria e alterações'):
        history=repo.history(actor,indicator=number)
        st.dataframe(pd.DataFrame([{'Tipo':r['kind'],'Código':r['entity'],'Versão':r['revision'],'Autor':r['author'],'Data':r['created_at'],'Justificativa':r['reason']} for r in history]),hide_index=True,width='stretch')


def backup_controls(repo,actor):
    actor.require(write=True)
    with st.expander('Backup e restauração dos registros'):
        st.caption('Backup completo com histórico. Guarde em local protegido. Restauração aceita apenas o mesmo modo, preserva versões existentes e registra autoria; não é uma assinatura de autenticidade.')
        st.download_button('Baixar backup JSON',repo.backup(actor),'backup_reestruturacao_'+repo.origin+'.json',mime='application/json')
        upload=st.file_uploader('Selecionar backup JSON confiável',type=['json'],key='restruct_backup_upload')
        reason=st.text_input('Justificativa da restauração',key='restruct_restore_reason')
        confirm=st.checkbox('Conferi a origem e a confiabilidade do backup',key='restruct_restore_confirm')
        if st.button('Restaurar backup',disabled=not upload or not confirm):
            try:
                count=repo.restore(actor,upload.getvalue(),reason)
                st.success(f'{count} versões recuperadas; histórico existente preservado.')
            except Exception as error:message_error(error)


def exports(repo,actor):
    if not repo:return
    with st.expander('Exportar síntese e memórias autorizadas'):
        if not st.checkbox('Preparar exportação da reestruturação',key='restruct_exports'):return
        rows=repo.assessments(actor)
        summary=summary_table(rows)
        origin='DEMONSTRAÇÃO — FICTÍCIO' if repo.origin=='DEMONSTRACAO' else 'INSTITUCIONAL — REGISTRADO'
        summary['Origem']=origin
        memories=pd.DataFrame([{'Indicador':r['number'],'Início':r['start'],'Fim':r['end'],'Ficha':r['definition_version'],'Fórmula':r['definition_snapshot']['formula'],'Numerador':r['numerator'],'Denominador':r['denominator'],'Resultado original':r['value_raw'],'Resultado arredondado':r['value_rounded'],'Fonte':r['source'],'Método':r['method'],'Cobertura':json.dumps(r['coverage'],ensure_ascii=False),'Limitações':r['limitations'],'Tipo':r['calculation_type'],'Coleta':r['context']['collector'],'Validação':r['context']['validator'],'Evidência da validação':r['context']['validation_evidence'],'Autor':r['author'],'Atualização':r['updated_at'],'Origem':origin} for r in rows])
        mode='DEMO_FICTICIO' if repo.origin=='DEMONSTRACAO' else 'INSTITUCIONAL'
        st.download_button('Baixar síntese CSV',csv_bytes(summary),'reestruturacao_'+mode+'.csv')
        details={title:pd.DataFrame([{'Indicador':r['number'],'Início':r['start'],'Fim':r['end'],'Versão da apuração':r['revision'],'Origem':origin,**item} for r in rows for item in r[key]]) for title,key in [('Incluídos','included'),('Excluídos','excluded'),('Pendências','pending')]}
        st.download_button('Baixar relatório XLSX',workbook({**details,'Síntese':summary,'Memórias':memories,'Fichas':pd.DataFrame([{'Nº':d['number'],'Nome':d['name'],'Meta':d['target'],'Pactuação':d['pact_status'],'Versão':d['version'],'Origem':origin} for d in repo.definitions(actor)]),'Ações':pd.DataFrame(repo.actions(actor)).drop(columns=['assessment_entity'],errors='ignore')}),'reestruturacao_'+mode+'.xlsx')


def render_restructuring():
    require_login(show_logout=False);apply_theme();header();sidebar_notice()
    actor=current_actor(st.session_state);actor.require()
    st.title('Indicadores de reestruturação')
    config=load('restructuring_indicators.yaml')
    st.info(config['notice']);st.caption(config['disclaimer'])
    st.write('**Monitoramento contratual:** metas assistenciais e qualitativas dos instrumentos de gestão. **Monitoramento da reestruturação:** execução e sustentação das adequações propostas nesta página. Produção contratual não é denominador automático destes indicadores.')
    mode=st.radio('Modo de acompanhamento',['Institucional','Demonstração fictícia'],horizontal=True,key='restructure_mode')
    repo=None
    if mode=='Demonstração fictícia':
        st.warning('DEMONSTRAÇÃO — DADOS FICTÍCIOS. Não representam resultados atuais do hospital e não são transferidos ao banco institucional.')
        if 'restructure_demo_repo' not in st.session_state:st.session_state['restructure_demo_repo']=create_demo()
        repo=st.session_state['restructure_demo_repo']
    else:
        try:
            repo=persistent_repository(storage_path())
            if not repo.initialized(actor):
                st.info('Arquivo institucional pronto; fichas ainda não inicializadas.')
                if actor.role=='ADMIN' and st.button('Inicializar fichas propostas'):
                    repo.initialize(actor);st.rerun()
                if actor.role=='ADMIN':backup_controls(repo,actor)
                repo=None
        except Exception as error:message_error(error);repo=None
    if mode=='Institucional':st.warning('Registros salvos em arquivo JSON, sem SQL. No Streamlit Cloud, reinicializações podem apagar arquivos locais. Baixe backups após alterações; o administrador pode restaurá-los.')
    catalog=definitions(repo,actor)
    options=['Resumo','Acompanhamento e fichas']+(['Administração'] if actor.role=='ADMIN' else [])
    active=section(options,'restruct_section')
    if active=='Resumo':overview(repo,actor,catalog)
    elif active=='Acompanhamento e fichas':followup(repo,actor,catalog)
    else:admin(repo,actor,catalog)
    exports(repo,actor);footer()
