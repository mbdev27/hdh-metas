"""Append-only domain storage. ADMIN checks are enforced by every mutation."""
from copy import deepcopy
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import uuid
from src.contract_registry import load
from src.restructuring.schema import Actor,day,safe_text,validate_record
from src.restructuring.calculations import calculate,classify
from src.restructuring.file_store import FileStore


def _clean_payload(payload):
    """No arbitrary fields identifying patients; free text is still subject to human review."""
    forbidden={'cpf','cns','patient_name','nome_paciente','telefone','endereco_paciente','prontuario','password','senha','database_url'}
    def check(value):
        if isinstance(value,dict):
            if forbidden.intersection(str(k).lower() for k in value):raise ValueError('Campo pessoal ou segredo não permitido.')
            for item in value.values():check(item)
        elif isinstance(value,list):
            for item in value:check(item)
        elif isinstance(value,str):safe_text(value)
        elif isinstance(value,float) and not math.isfinite(value):raise ValueError('Número inválido.')
    check(payload)
    return deepcopy(payload)


class Repository:
    def __init__(self,store,origin='INSTITUCIONAL'):
        if origin not in ('INSTITUCIONAL','DEMONSTRACAO'):raise ValueError('Origem inválida.')
        self.store=store;self.origin=origin

    def initialized(self,actor):
        actor.require()
        return self.store.state()['initialized']

    def initialize(self,actor):
        actor.require(write=True)
        with self.store.transaction() as state:
            existing={row['indicator'] for row in state['entries'] if row['kind']=='definition' and row['origin']==self.origin}
            for definition in load('restructuring_indicators.yaml')['indicators']:
                if definition['number'] not in existing:
                    self._insert(state,actor,'definition',str(definition['number']),definition['number'],definition,'1900-01-01','Cadastro inicial proposto',None)
            state['initialized']=True

    def history(self,actor,kind=None,indicator=None,entity=None):
        actor.require()
        rows=self.store.state()['entries']
        return sorted([r for r in rows if r['origin']==self.origin and (not kind or r['kind']==kind) and (indicator is None or r['indicator']==indicator) and (entity is None or r['entity']==entity)],key=lambda r:(r['created_at'],r['revision']))

    def _latest(self,actor,kind,indicator=None,cutoff=None):
        result={}
        for row in self.history(actor,kind,indicator):
            if cutoff and row['effective_from']>cutoff:continue
            key=row['entity']
            if key not in result or (row['effective_from'],row['revision'])>(result[key]['effective_from'],result[key]['revision']):result[key]=row
        return result

    def _append(self,actor,kind,entity,indicator,payload,effective_from,reason,expected_revision):
        actor.require(write=True)
        payload=_clean_payload(payload)
        if payload.get('data_origin',self.origin)!=self.origin:
            raise ValueError('Dados de demonstração não podem ser gravados no armazenamento institucional.')
        day(effective_from,True)
        if not reason.strip():raise ValueError('Informe justificativa do registro/alteração.')
        safe_text(reason)
        with self.store.transaction() as state:
            return self._insert(state,actor,kind,entity,indicator,payload,effective_from,reason,expected_revision)

    def _insert(self,state,actor,kind,entity,indicator,payload,effective_from,reason,expected_revision):
        previous=max((row for row in state['entries'] if row['kind']==kind and row['entity']==entity and row['origin']==self.origin),key=lambda r:r['revision'],default=None)
        revision=previous['revision'] if previous else 0
        if previous and expected_revision!=revision:raise ValueError('Registro alterado por outra operação; recarregue antes de corrigir.')
        if not previous and expected_revision not in (None,0):raise ValueError('Versão anterior não encontrada.')
        if kind=='assessment':
            latest={}
            for row in state['entries']:
                if row['kind']=='assessment' and row['origin']==self.origin and row['indicator']==indicator:
                    if row['entity'] not in latest or row['revision']>latest[row['entity']]['revision']:latest[row['entity']]=row
            if any(key!=entity and row['payload']['start']==payload['start'] and row['payload']['end']==payload['end'] and row['payload']['scope']==payload['scope'] for key,row in latest.items()):raise ValueError('Apuração duplicada; registre correção da versão existente.')
        payload=_clean_payload(payload);payload['data_origin']=self.origin
        new=dict(id=str(uuid.uuid4()),kind=kind,entity=entity,revision=revision+1,indicator=indicator,
                 effective_from=effective_from,payload=payload,author=actor.username,
                 created_at=datetime.now(timezone.utc).isoformat(),reason=reason,
                 previous_id=previous['id'] if previous else None,origin=self.origin)
        state['entries'].append(new)
        return new['id']

    def definitions(self,actor):
        return [row['payload'] for row in self._latest(actor,'definition').values()]

    def definition_for(self,actor,number,start,end):
        day(start,True);day(end,True)
        history=self.history(actor,'definition',number)
        candidates=[row for row in history if row['effective_from']<=start]
        if not candidates:raise ValueError('Não há ficha aplicável ao período.')
        if any(start<row['effective_from']<=end for row in history):raise ValueError('O período atravessa mudança de ficha/meta. Divida a apuração na data de vigência.')
        return max(candidates,key=lambda row:(row['effective_from'],row['revision']))['payload']

    def save_definition(self,actor,number,definition,reason,expected_revision=None):
        actor.require(write=True)
        old=self._latest(actor,'definition',number).get(str(number))
        if old is None:raise ValueError('Ficha inicial não encontrada.')
        allowed=set(old['payload'])
        if set(definition)-allowed:raise ValueError('Campo de ficha não reconhecido.')
        definition=deepcopy(definition)
        for field in ('number','indicator_id','record_type','formula_code'):
            if definition.get(field)!=old['payload'][field]:raise ValueError('Identificação e algoritmo de cálculo não podem ser alterados por formulário.')
        target=definition.get('target')
        if isinstance(target,bool) or not isinstance(target,(int,float)) or not math.isfinite(target) or not 0<=target<=100:raise ValueError('Meta percentual deve estar entre zero e cem.')
        if definition.get('improvement') not in ('aumentar','reduzir','interpretar contexto'):raise ValueError('Sentido de melhoria inválido.')
        milestone=definition.get('milestone_days')
        if milestone is not None and (isinstance(milestone,bool) or not isinstance(milestone,int) or milestone<0):raise ValueError('Marco deve ser inteiro e não negativo.')
        effective=definition['effective_from'];day(effective,True)
        if effective<old['effective_from']:raise ValueError('Não alterar retrospectivamente a vigência; reprocessamento exige apuração corrigida, mantendo a anterior.')
        status=definition.get('pact_status')
        if status not in ('Proposta — aguardando pactuação','Pactuada'):raise ValueError('Situação de pactuação inválida.')
        if status=='Pactuada':
            approval=definition.get('approval') or {}
            if not all(approval.get(key) for key in ('approver','date','evidence')):raise ValueError('Pactuação exige aprovador, data e evidência documental.')
            if day(approval['date'],True)>day(effective,True):raise ValueError('Vigência não pode anteceder a aprovação registrada.')
            day(definition.get('approved_plan_start'),True)
        baseline=definition.get('baseline',{})
        if baseline.get('value') is not None:
            value=baseline['value']
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=100:raise ValueError('Linha de base percentual inválida.')
            if not all(baseline.get(key) for key in ('period','coverage','evidence')):raise ValueError('Linha de base exige período, cobertura e evidência.')
            baseline['status']='Levantada e documentada'
        else:baseline['status']='A levantar no diagnóstico inicial'
        structural=('formula','numerator_definition','denominator_definition','scope','eligibility_rules')
        changed=any(definition.get(key)!=old['payload'].get(key) for key in structural)
        definition['comparability_break']=bool(changed or definition.get('comparability_break'))
        definition['version']=old['revision']+1
        return self._append(actor,'definition',str(number),number,definition,effective,reason,expected_revision)

    def records(self,actor,number,cutoff=None):
        return [row['payload']['record'] for row in self._latest(actor,'record',number,cutoff).values()]

    def save_record(self,actor,number,record,effective_from,reason,expected_revision=None,data_origin=None):
        actor.require(write=True)
        if data_origin and data_origin!=self.origin:raise ValueError('Origem incompatível com o modo de armazenamento.')
        record=validate_record(number,record)
        if self.origin=='INSTITUCIONAL' and any('DEMONSTRA' in str(record.get(key,'')).upper() or 'FICT' in str(record.get(key,'')).upper() for key in ('source','evidence')):
            raise ValueError('Evidência fictícia não pode ser registrada como institucional.')
        entity=f'{number}:{record["entity_id"]}'
        old=self._latest(actor,'record',number).get(entity)
        if old:
            for field in ('original_due','original_calendar','person_token','competency','bed_number'):
                if old['payload']['record'].get(field)!=record.get(field):raise ValueError(f'{field} é preservado; registre alteração justificada em campo separado, sem apagar o original.')
        if number==12:
            incidents={r['entity_id'] for r in self.records(actor,11)}
            if record['incident_id'] not in incidents:raise ValueError('Incidente vinculado não encontrado.')
        return self._append(actor,'record',entity,number,{'record':record,'data_origin':data_origin or self.origin},effective_from,reason,expected_revision)

    def assess(self,actor,number,start,end,context,scope=None,aggregate=None,reason='Nova apuração',assessment_entity=None,expected_revision=None):
        actor.require(write=True)
        if context.get('data_origin',self.origin)!=self.origin:raise ValueError('Não misturar demonstração e resultados institucionais.')
        if not all(context.get(key) for key in ('collector','validator','validation_evidence')):raise ValueError('Apuração exige coleta, validação e referência da evidência.')
        if self.origin=='INSTITUCIONAL' and any('DEMONSTRA' in str(context.get(key,'')).upper() or 'FICT' in str(context.get(key,'')).upper() for key in ('source','validation_evidence')):
            raise ValueError('Apuração fictícia não pode ser registrada como institucional.')
        definition=self.definition_for(actor,number,start,end)
        result=calculate(number,self.records(actor,number,end),start,end,context,scope,aggregate)
        result['classification'],result['flags']=classify(result,definition)
        result.update(definition_version=definition['version'],definition_snapshot=definition,scope=scope or {},context=context,
                      target=definition['target'],pact_status=definition['pact_status'],data_origin=self.origin)
        entity=assessment_entity or str(uuid.uuid4())
        # Duplicate periods/scopes must be explicitly corrected, never silently overwritten.
        for key,old in self._latest(actor,'assessment',number).items():
            previous=old['payload']
            if key!=entity and previous['start']==start and previous['end']==end and previous['scope']==(scope or {}):raise ValueError('Apuração duplicada; selecione a existente e registre correção justificada.')
        return self._append(actor,'assessment',entity,number,result,end,reason,expected_revision)

    def assessments(self,actor,number=None):
        return [{'assessment_entity':key,'revision':row['revision'],'author':row['author'],'updated_at':row['created_at'],**row['payload']} for key,row in self._latest(actor,'assessment',number).items()]

    def save_action(self,actor,number,action,reason,expected_revision=None):
        actor.require(write=True)
        allowed={'action_id','assessment_entity','description','responsible','original_due','current_due','status','evidence'}
        if set(action)-allowed or not all(action.get(key) for key in ('action_id','assessment_entity','description','responsible','original_due')):raise ValueError('Ação incompleta ou com campo não autorizado.')
        day(action['original_due'],True);day(action.get('current_due'))
        if action.get('status') not in ('Aberta','Em execução','Concluída com evidência'):raise ValueError('Situação da ação inválida.')
        if action['status']=='Concluída com evidência' and not action.get('evidence'):raise ValueError('Conclusão exige evidência.')
        if not any(a['assessment_entity']==action['assessment_entity'] for a in self.assessments(actor,number)):raise ValueError('Apuração vinculada não encontrada.')
        old=self._latest(actor,'action',number).get(action['action_id'])
        if old and old['payload']['original_due']!=action['original_due']:raise ValueError('Prazo original da ação é preservado.')
        return self._append(actor,'action',action['action_id'],number,action,action['original_due'],reason,expected_revision)

    def actions(self,actor,number=None):
        return [row['payload'] for row in self._latest(actor,'action',number).values()]

    def backup(self,actor):
        actor.require(write=True)
        snapshot={'format_version':1,'origin':self.origin,'entries':self.history(actor)}
        return json.dumps(snapshot,ensure_ascii=False,allow_nan=False,indent=2).encode('utf-8')

    def restore(self,actor,content,reason):
        """Merge a trusted backup, never replacing existing versions or mixing origins."""
        actor.require(write=True)
        if not isinstance(content,bytes) or len(content)>20*1024*1024:raise ValueError('Backup deve ter até 20 MB.')
        if not reason.strip():raise ValueError('Informe justificativa da restauração.')
        safe_text(reason)
        try:snapshot=json.loads(content)
        except (ValueError,UnicodeError):raise ValueError('Backup JSON inválido.') from None
        if not isinstance(snapshot,dict) or snapshot.get('format_version')!=1 or snapshot.get('origin')!=self.origin or not isinstance(snapshot.get('entries'),list):raise ValueError('Formato ou origem do backup incompatível.')
        incoming=snapshot['entries']
        if not incoming:raise ValueError('Backup vazio; nenhuma restauração realizada.')
        required={'id','kind','entity','revision','indicator','effective_from','payload','author','created_at','reason','previous_id','origin'}
        catalog={d['number']:d for d in load('restructuring_indicators.yaml')['indicators']}
        seen=set()
        for row in incoming:
            if not isinstance(row,dict) or set(row)!=required:raise ValueError('Registro de backup incompleto ou inesperado.')
            if row['origin']!=self.origin or row['kind'] not in ('definition','record','assessment','action','restore'):raise ValueError('Registro de backup com origem/tipo incompatível.')
            if type(row['indicator']) is not int or row['indicator'] not in catalog:raise ValueError('Indicador inválido no backup.')
            if type(row['revision']) is not int or row['revision']<1:raise ValueError('Versão inválida no backup.')
            try:uuid.UUID(row['id']);datetime.fromisoformat(row['created_at'])
            except (ValueError,TypeError):raise ValueError('Identificação ou data de backup inválida.') from None
            for field in ('entity','author','reason'):safe_text(row[field])
            day(row['effective_from'],True)
            if row['id'] in seen:raise ValueError('Identificação duplicada no backup.')
            seen.add(row['id']);payload=_clean_payload(row['payload'])
            if not isinstance(payload,dict) or payload.get('data_origin')!=self.origin:raise ValueError('Conteúdo do backup com origem incompatível.')
            if row['kind']=='record':
                record=validate_record(row['indicator'],payload.get('record',{}))
                if row['entity']!=f'{row["indicator"]}:{record["entity_id"]}':raise ValueError('Código do registro incompatível.')
                if self.origin=='INSTITUCIONAL' and any('DEMONSTRA' in str(record.get(k,'')).upper() or 'FICT' in str(record.get(k,'')).upper() for k in ('source','evidence')):raise ValueError('Backup contém evidência fictícia.')
            elif row['kind']=='definition':
                base=catalog[row['indicator']]
                if set(payload)!=set(base)|{'data_origin'} or any(payload[k]!=base[k] for k in ('number','indicator_id','record_type','formula_code')):raise ValueError('Ficha do backup incompatível com o catálogo.')
                if payload['version']!=row['revision'] or payload['number']!=row['indicator']:raise ValueError('Versão da ficha incompatível.')
                if isinstance(payload['target'],bool) or not isinstance(payload['target'],(int,float)) or not 0<=payload['target']<=100:raise ValueError('Meta inválida no backup.')
                if not isinstance(payload['baseline'],dict) or not all(k in payload['baseline'] for k in ('value','period','coverage','evidence','status')):raise ValueError('Linha de base inválida no backup.')
                if not isinstance(payload['eligibility_rules'],list) or not all(isinstance(v,str) for v in payload['eligibility_rules']):raise ValueError('Critérios inválidos no backup.')
                if payload['pact_status'] not in ('Proposta — aguardando pactuação','Pactuada'):raise ValueError('Pactuação inválida no backup.')
                if payload['pact_status']=='Pactuada':
                    approval=payload.get('approval') or {}
                    if not all(approval.get(k) for k in ('approver','date','evidence')):raise ValueError('Aprovação incompleta no backup.')
                    day(approval['date'],True);day(payload['approved_plan_start'],True)
            elif row['kind']=='assessment':
                if not all(k in payload for k in ('start','end','scope','definition_snapshot','numerator','denominator','classification')):raise ValueError('Apuração incompleta no backup.')
                required_assessment={'number','start','end','cutoff','source','method','limitations','included','excluded','pending','coverage','complementary','bed_dimensions','numerator','denominator','value_raw','value_rounded','status_data','calculation_type','critical','classification','flags','definition_version','definition_snapshot','scope','context','target','pact_status','data_origin'}
                if set(payload)!=required_assessment:raise ValueError('Memória de cálculo incompleta ou inesperada.')
                if day(payload['start'],True)>day(payload['end'],True):raise ValueError('Período inválido no backup.')
                day(payload['cutoff'],True)
                if payload['number']!=row['indicator'] or not isinstance(payload['scope'],dict):raise ValueError('Escopo ou indicador inválido.')
                for key in ('included','excluded','pending','bed_dimensions','flags'):
                    if not isinstance(payload[key],list):raise ValueError('Detalhes da memória inválidos.')
                if not isinstance(payload['context'],dict) or not all(k in payload['context'] for k in ('collector','validator','validation_evidence')):raise ValueError('Validação da apuração incompleta.')
                if not isinstance(payload['definition_snapshot'],dict) or set(payload['definition_snapshot'])!=set(catalog[row['indicator']])|{'data_origin'}:raise ValueError('Ficha histórica incompleta.')
            elif row['kind']=='action':
                required_action={'action_id','assessment_entity','description','responsible','original_due','current_due','status','evidence','data_origin'}
                if set(payload)!=required_action or row['entity']!=payload['action_id']:raise ValueError('Ação inválida no backup.')
                day(payload['original_due'],True);day(payload.get('current_due'))
                if payload['status'] not in ('Aberta','Em execução','Concluída com evidência'):raise ValueError('Situação de ação inválida.')
                if payload['status']=='Concluída com evidência' and not payload['evidence']:raise ValueError('Conclusão sem evidência no backup.')
        with self.store.transaction() as state:
            existing={r['id']:r for r in state['entries']}
            combined=deepcopy(state['entries'])
            keys={(r['origin'],r['kind'],r['entity'],r['revision']):r['id'] for r in combined}
            count=0
            for row in incoming:
                if row['id'] in existing:
                    if row!=existing[row['id']]:raise ValueError('Backup diverge de uma versão já registrada; nenhuma alteração foi feita.')
                    continue
                key=(row['origin'],row['kind'],row['entity'],row['revision'])
                if key in keys:raise ValueError('Conflito de versões do backup; nenhuma alteração foi feita.')
                keys[key]=row['id'];combined.append(deepcopy(row));count+=1
            by_id={r['id']:r for r in combined}
            for row in combined:
                if row['revision']==1:
                    if row['previous_id'] is not None:raise ValueError('Histórico inicial inválido.')
                else:
                    previous=by_id.get(row['previous_id'])
                    if not previous or any(previous[k]!=row[k] for k in ('origin','kind','entity','indicator')) or previous['revision']!=row['revision']-1:raise ValueError('Backup tem lacuna no histórico; restauração cancelada.')
            incident_ids={r['payload']['record']['entity_id'] for r in combined if r['kind']=='record' and r['indicator']==11}
            assessment_ids={r['entity'] for r in combined if r['kind']=='assessment'}
            for row in combined:
                if row['kind']=='record' and row['indicator']==12 and row['payload']['record']['incident_id'] not in incident_ids:raise ValueError('Ação de incidente sem vínculo no backup.')
                if row['kind']=='action' and row['payload']['assessment_entity'] not in assessment_ids:raise ValueError('Ação sem apuração vinculada no backup.')
            definitions={r['indicator'] for r in combined if r['origin']==self.origin and r['kind']=='definition'}
            if definitions!=set(catalog):raise ValueError('Backup deve preservar as 14 fichas.')
            state['entries']=combined;state['initialized']=True
            if count:self._insert(state,actor,'restore',str(uuid.uuid4()),1,{'restored_versions':count,'data_origin':self.origin},date_today(),reason,None)
        return count


def date_today():
    return datetime.now(timezone.utc).date().isoformat()
