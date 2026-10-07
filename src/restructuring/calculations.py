"""Operational proposals. No pooled score, statistical inference or legal compliance verdict."""
from datetime import timedelta
from src.restructuring.schema import count,day,validate_record


def in_period(value,start,end):
    value=day(value)
    return bool(value and start<=value<=end)


def on_time(record,completion,validation=None):
    due=day(record.get('original_due'))
    done=day(record.get(completion))
    checked=day(record.get(validation)) if validation else done
    return bool(due and done and checked and done<=checked<=due and (not validation or record.get('efficacy') is True))


def calculate(number,records,start,end,context,scope=None,aggregate=None):
    start=day(start,True);end=day(end,True)
    if end<start:raise ValueError('Fim anterior ao início.')
    if not context.get('source') or not context.get('method') or not context.get('eligibility_confirmed'):
        raise ValueError('Informe fonte, método e confirmação de elegibilidade.')
    scope=scope or {}
    if number in (9,10) and not scope.get('protocol'):
        raise ValueError('Apure separadamente por protocolo ou competência; informe o filtro correspondente.')
    result=dict(number=number,start=start.isoformat(),end=end.isoformat(),cutoff=end.isoformat(),
                source=context['source'],method=context['method'],limitations=context.get('limitations',''),
                included=[],excluded=[],pending=[],coverage={},complementary={},bed_dimensions=[],
                numerator=None,denominator=None,value_raw=None,value_rounded=None,status_data='Não aferível',
                calculation_type='Agregada' if aggregate is not None else 'Registros operacionais',critical=False)
    if not context.get('universe_confirmed'):
        result['limitations']+=' Universo elegível desconhecido ou não confirmado.'
        return result
    if aggregate is not None:
        n=count(aggregate.get('numerator'));d=count(aggregate.get('denominator'))
        if n>d:raise ValueError('Numerador não pode exceder o denominador.')
        if number==13 and d!=10:raise ValueError('O denominador dos novos leitos deve ser dez.')
        result['limitations']+=' Apuração agregada: critérios confirmados pelo registrador; não existe rastreabilidade individual nesta entrada.'
        result['coverage']=dict(context.get('coverage',{}))
        result['critical']=bool(context.get('critical'))
        result['complementary']=dict(context.get('complementary',{}))
        result['numerator']=n;result['denominator']=d
    else:
        ids=set();work=[]
        for original in records:
            record=validate_record(number,original)
            if record['entity_id'] in ids:raise ValueError('Identificador operacional duplicado.')
            ids.add(record['entity_id'])
            if any(scope.get(key) and record.get(key)!=value for key,value in scope.items() if value):continue
            if record.get('applicable') is False:
                result['excluded'].append({'id':record['entity_id'],'reason':record['exclusion_justification']});continue
            work.append(record)
        selected=[];success=[];partial=[]
        for r in work:
            ok=False;include=True;reason='Fora do universo do período'
            if number==1:
                ok=r.get('granted') is True and r.get('scope_sufficient') is True and bool(r.get('evidence'))
                begin=day(r.get('valid_from'));expiry=day(r.get('valid_until'))
                ok=ok and bool(begin and begin<=end and expiry and expiry>=end)
            elif number==2:
                ok=r.get('evaluated') is True and r.get('conform') is True
                if not r.get('evaluated'):result['pending'].append({'id':r['entity_id'],'reason':'Requisito não avaliado; mantido no denominador'})
            elif number==3:
                include=in_period(r.get('event_date'),start,end)
                ok=r.get('moments')==[True,True,True] and r.get('timely') is True
            elif number==4:
                include=in_period(r.get('event_date'),start,end)
                if include and not r.get('observed_complete'):
                    partial.append(r);include=False;reason='Observação parcial: perda, fora do cálculo principal'
                ok=r.get('moments')==[True,True,True]
            elif number==5:
                include=in_period(r.get('planned_date'),start,end) and not r.get('extra',False)
                reason='Auditoria extra ou fora do calendário/período'
                ok=r.get('report_valid') is True and in_period(r.get('completed_date'),start,end)
            elif number in (6,11,12,14):
                include=in_period(r.get('original_due'),start,end)
                reason='Prazo original não vence no período'
                completion={6:'closed_date',11:'investigated_date',12:'completed_date',14:'triaged_date'}[number]
                ok=on_time(r,completion,'validated_date' if number in (6,12) else None)
            elif number==7:
                closed=day(r.get('closed_date'));recheck=day(r.get('rechecked_date'))
                mature=bool(closed and closed+timedelta(days=90)<=end)
                include=mature and bool(recheck and recheck>=closed+timedelta(days=90) and start<=recheck<=end)
                reason='Janela incompleta, caso aberto ou sem reavaliação integral no período'
                recurrence=day(r.get('recurrence_date'))
                ok=bool(include and r.get('recurred') and recurrence and closed<recurrence<=closed+timedelta(days=90) and r.get('recurrence_requirement_key')==r.get('requirement_key') and r.get('recurrence_sector')==r.get('sector'))
            elif number==8:
                include=r.get('priority',True)
                ok=all(r.get(field) is True for field in ('approved','resources_ready','training_done','use_verified'))
            elif number==9:
                include=in_period(r.get('event_date'),start,end)
                if include and not r.get('observed_complete'):
                    partial.append(r);include=False;reason='Oportunidade parcialmente observada: perda'
                ok=r.get('all_steps_correct') is True
            elif number==10:
                include=r.get('eligible',False) and r.get('competency')==scope['protocol']
                completed=day(r.get('completed_date'))
                ok=bool(r.get('assessment_satisfactory') and completed and completed<=end)
            elif number==13:continue
            if include:
                selected.append(r)
                if ok:success.append(r)
                result['included'].append({'id':r['entity_id'],'contributes':ok,'original_due':r.get('original_due')})
                if r.get('critical') and (ok if number==7 else not ok):result['critical']=True
            else:result['excluded'].append({'id':r['entity_id'],'reason':reason})
        if any(r.get('critical') for r in partial):result['critical']=True
        if number==10:
            keys=[(r['person_token'],r['competency']) for r in selected]
            if len(set(keys))!=len(keys):raise ValueError('Pessoa repetida para a mesma competência; use um registro consolidado por pessoa.')
        if number==13:
            beds={};shared={r['shared_group']:r.get('shared_conform') for r in work if r.get('record_kind')=='requisito_compartilhado'}
            for r in work:
                if r.get('record_kind','leito')!='leito':continue
                if r['bed_number'] in beds:raise ValueError('Leito duplicado.')
                beds[r['bed_number']]=r
            conform=0;evaluated=0
            for bed in range(1,11):
                record=beds.get(bed);dimensions={key:None for key in ('estrutura','equipamentos','profissionais','processos','seguranca','documentacao')}
                dependencies_complete=False
                if record:
                    dimensions=dict(record['dimensions'])
                    dependencies=record.get('dependencies',[])
                    dependencies_complete=all(key in shared and shared[key] is not None for key in dependencies)
                    if any(shared.get(key) is False for key in dependencies):
                        dimensions['seguranca']=False;result['critical']=True
                    if any(shared.get(key) is None for key in dependencies):dimensions['seguranca']=None
                full=all(value is not None for value in dimensions.values()) and dependencies_complete
                ok=full and all(value is True for value in dimensions.values())
                conform+=int(ok);evaluated+=int(full)
                result['bed_dimensions'].append({'leito':bed,**dimensions,'adequado':ok,'avaliacao_completa':full})
                if record:result['included'].append({'id':record['entity_id'],'contributes':ok})
                if record and record.get('critical') and not ok:result['critical']=True
            result['numerator']=conform;result['denominator']=10
            result['coverage']={'leitos_com_avaliacao_completa':evaluated,'leitos_inventariados':len(beds),'universo':10}
        else:
            result['numerator']=len(success);result['denominator']=len(selected)
        if number==2:
            evaluated=sum(r.get('evaluated') is True for r in selected)
            result['coverage']={'avaliados':evaluated,'aplicaveis':len(selected),'nao_avaliados':len(selected)-evaluated,'nao_conformes_comprovados':sum(r.get('evaluated') is True and r.get('conform') is False for r in selected)}
        if number in (4,9):
            result['coverage']={'observacoes_integrais':len(selected),'perdas_parciais':len(partial),'turnos':sorted({r.get('shift','Não informado') for r in selected}),'especialidades':sorted({r.get('specialty','Não informada') for r in selected})}
            population=context.get('population_count')
            if population is not None:
                count(population)
                if population<len(selected)+len(partial):raise ValueError('Amostra maior que a população informada.')
                result['coverage']['populacao_elegivel']=population
            result['limitations']+=' Amostra operacional; não constitui estimativa universal. Perdas excluídas do cálculo principal.'
        if number==5:result['complementary']['auditorias_extras']=sum(bool(r.get('extra')) and in_period(r.get('completed_date'),start,end) for r in work)
        if number==7:
            mature=[r for r in work if day(r.get('closed_date')) and day(r['closed_date'])+timedelta(days=90)<=end]
            result['coverage']={'casos_com_janela_completa':len(mature),'reavaliados_no_periodo':len(selected),'reavaliados_ate_corte':sum(bool(day(r.get('rechecked_date')) and day(r['rechecked_date'])+timedelta(0)>=day(r['closed_date'])+timedelta(days=90) and day(r['rechecked_date'])<=end) for r in mature)}
            result['limitations']+=' Janela de 90 dias; casos abertos e janelas incompletas não integram a taxa.'
        if number in (6,11,12,14):
            completion={6:'closed_date',11:'investigated_date',12:'completed_date',14:'triaged_date'}[number]
            overdue=[r for r in work if day(r.get('original_due')) and day(r['original_due'])<=end and (not day(r.get(completion)) or day(r[completion])>end or number in (6,12) and (not r.get('efficacy') or not day(r.get('validated_date')) or day(r['validated_date'])>end))]
            result['complementary']['pendencias_vencidas']=len(overdue)
            result['complementary']['maior_atraso_dias']=max(((end-day(r['original_due'])).days for r in overdue),default=0)
            result['pending'] += [{'id':r['entity_id'],'reason':'Prazo original vencido; conclusão/eficácia não demonstrada na data de corte'} for r in overdue]
        if number==14:
            result['complementary'].update(notificacoes_recebidas=sum(in_period(r.get('received_date'),start,end) for r in work),notificacoes_triadas=sum(in_period(r.get('triaged_date'),start,end) for r in work),notificacoes_pendentes=sum(bool(day(r.get('received_date')) and day(r['received_date'])<=end and (not day(r.get('triaged_date')) or day(r['triaged_date'])>end)) for r in work))
            result['limitations']+=' Quantidade de relatos não é incidência de dano; mais relatos podem indicar maior confiança/detecção.'
    denominator=result['denominator']
    if denominator==0:result['status_data']='Não aplicável no período'
    elif denominator is not None:
        result['value_raw']=result['numerator']/denominator*100
        result['value_rounded']=round(result['value_raw'],2)
        result['status_data']='Apuração válida'
    return result


def classify(result,definition):
    flags=[]
    if definition['baseline'].get('value') is None:flags.append('Linha de base pendente')
    if definition.get('pact_status')!='Pactuada':flags.append('Meta ainda não pactuada')
    if result.get('critical'):return 'Falha crítica identificada',flags
    if result['status_data']!='Apuração válida':return result['status_data'],flags
    if definition.get('pact_status')!='Pactuada':return 'Meta ainda não pactuada',flags
    start=day(definition.get('approved_plan_start'))
    if not start:return 'Início aprovado do plano pendente',flags
    elapsed=(day(result['cutoff'])-start).days
    target=definition['target'];value=result['value_raw']
    reached=value<=target if definition['improvement']=='reduzir' else value>=target
    if reached:return 'Meta atingida no período',flags
    milestone=definition.get('milestone_days')
    if elapsed<0 or milestone and elapsed<milestone:return 'Prazo ainda em curso',flags
    return 'Abaixo da meta',flags
