"""Minimized operational fields, validation and authorization helpers."""
from dataclasses import dataclass
from datetime import date
import re
import time


@dataclass(frozen=True)
class Actor:
    username: str
    role: str
    authenticated: bool
    login_time: float

    def require(self, write=False):
        if not self.authenticated or time.time()-self.login_time>3600:
            raise PermissionError('Sessão não autenticada ou expirada.')
        allowed={'ADMIN'} if write else {'ADMIN','GESTOR','LEITURA'}
        if self.role not in allowed or not self.username:
            raise PermissionError('Operação restrita ao administrador.' if write else 'Acesso não autorizado.')


def current_actor(state):
    return Actor(state.get('username',''),state.get('role',''),bool(state.get('authenticated')),state.get('login_time',0))


def day(value, required=False):
    if value in (None,''):
        if required:raise ValueError('Data obrigatória ausente.')
        return None
    if not isinstance(value,str):raise ValueError('Datas devem usar AAAA-MM-DD.')
    try:return date.fromisoformat(value)
    except ValueError:raise ValueError('Data inválida; use AAAA-MM-DD.') from None


def count(value):
    if isinstance(value,bool) or not isinstance(value,int) or value<0:
        raise ValueError('Contagens devem ser inteiras e não negativas.')
    return value


def safe_text(value):
    if not isinstance(value,str) or len(value)>4000:
        raise ValueError('Texto inválido ou excessivamente longo.')
    if re.search(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11,15}\b',value):
        raise ValueError('Não inserir CPF, CNS ou identificadores pessoais.')
    return value


COMMON={'entity_id':'id','sector':'text','protocol':'text','shift':'text','specialty':'text',
        'source':'text','evidence':'text','applicable':'bool','exclusion_approved':'bool',
        'exclusion_justification':'text','critical':'bool','valid_from':'date','valid_until':'date'}
FIELDS={
 1:{'granted':'bool','scope_sufficient':'bool','track':'text'},
 2:{'evaluated':'bool','conform':'tri'},
 3:{'event_date':'date','moments':'moments','timely':'bool'},
 4:{'event_date':'date','moments':'moments','observed_complete':'bool','sample_method':'text'},
 5:{'planned_date':'date','completed_date':'date','report_valid':'bool','extra':'bool','original_calendar':'text'},
 6:{'original_due':'date','current_due':'date','closed_date':'date','validated_date':'date','efficacy':'bool'},
 7:{'closed_date':'date','rechecked_date':'date','recurrence_date':'date','requirement_key':'text','recurrence_requirement_key':'text','recurrence_sector':'text','recurred':'bool'},
 8:{'approved':'bool','resources_ready':'bool','training_done':'bool','use_verified':'bool','priority':'bool','priority_list_version':'text'},
 9:{'event_date':'date','observed_complete':'bool','all_steps_correct':'bool','sample_method':'text'},
 10:{'person_token':'id','competency':'text','eligible':'bool','completed_date':'date','assessment_satisfactory':'bool','function':'text'},
 11:{'received_date':'date','original_due':'date','current_due':'date','investigated_date':'date','gravity':'text'},
 12:{'incident_id':'id','original_due':'date','current_due':'date','completed_date':'date','validated_date':'date','efficacy':'bool'},
 13:{'bed_number':'bed','dimensions':'dimensions','dependencies':'dependencies','shared_group':'text','shared_conform':'tri','record_kind':'kind'},
 14:{'received_date':'date','original_due':'date','current_due':'date','triaged_date':'date','gravity':'text'},
}
DIMENSIONS=('estrutura','equipamentos','profissionais','processos','seguranca','documentacao')
REQUIRED_DATES={3:['event_date'],4:['event_date'],5:['planned_date'],6:['original_due'],9:['event_date'],11:['received_date','original_due'],12:['original_due'],14:['received_date','original_due']}


def validate_record(number,record):
    if number not in FIELDS:raise ValueError('Indicador inexistente.')
    schema={**COMMON,**FIELDS[number]}
    if set(record)-set(schema):raise ValueError('Campos fora do esquema minimizado não são permitidos.')
    for key in ('entity_id','source','evidence'):
        if not record.get(key):raise ValueError(f'Campo obrigatório: {key}.')
    for key,value in record.items():
        kind=schema[key]
        if kind=='date':day(value,key in REQUIRED_DATES.get(number,[]))
        elif kind in ('bool','tri'):
            if value is not None and not isinstance(value,bool):raise ValueError(f'{key}: valor lógico inválido.')
            if value is None and kind=='bool':raise ValueError(f'{key}: informe verdadeiro ou falso.')
        elif kind=='id':
            if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.:-]{0,79}',value):
                raise ValueError('Use código operacional opaco começando por letra, sem identificação pessoal.')
            safe_text(value)
        elif kind=='text':safe_text(value)
        elif kind=='moments':
            if not isinstance(value,list) or len(value)!=3 or any(v not in (True,False,None) or isinstance(v,(str,int,float)) and not isinstance(v,bool) for v in value):
                raise ValueError('Informe os três momentos como verdadeiro, falso ou não avaliado.')
        elif kind=='bed':
            if isinstance(value,bool) or not isinstance(value,int) or not 1<=value<=10:raise ValueError('Leito deve estar entre 1 e 10.')
        elif kind=='dimensions':
            if not isinstance(value,dict) or set(value)!=set(DIMENSIONS) or any(v is not None and not isinstance(v,bool) for v in value.values()):
                raise ValueError('Informe as seis dimensões; não avaliado deve ser nulo.')
        elif kind=='dependencies':
            if not isinstance(value,list) or any(not isinstance(v,str) for v in value):raise ValueError('Dependências devem ser códigos de grupos compartilhados.')
            for item in value:safe_text(item)
        elif kind=='kind' and value not in ('leito','requisito_compartilhado'):raise ValueError('Tipo de registro de UTI inválido.')
    for key in REQUIRED_DATES.get(number,[]):day(record.get(key),True)
    if record.get('applicable') is False and not (record.get('exclusion_approved') and record.get('exclusion_justification')):
        raise ValueError('Não aplicabilidade exige justificativa e validação.')
    pairs=[('valid_from','valid_until'),('received_date','investigated_date'),('received_date','triaged_date'),('received_date','original_due'),('completed_date','validated_date'),('closed_date','validated_date'),('closed_date','recurrence_date'),('closed_date','rechecked_date')]
    for before,after in pairs:
        a=day(record.get(before));b=day(record.get(after))
        if a and b and b<a:raise ValueError(f'Datas incoerentes: {after} anterior a {before}.')
    if number==7 and record.get('recurred') and not record.get('recurrence_date'):
        raise ValueError('Reincidência exige data do reaparecimento.')
    if number==9 and not record.get('protocol'):raise ValueError('Oportunidade exige protocolo identificado.')
    if number==10 and not (record.get('person_token') and record.get('competency')):raise ValueError('Informe código opaco e competência de capacitação.')
    if number==12 and not record.get('incident_id'):raise ValueError('A ação deve referenciar um incidente existente.')
    if number==13:
        kind=record.get('record_kind','leito')
        if kind=='leito' and ('bed_number' not in record or 'dimensions' not in record):raise ValueError('Informe número do leito e avaliação por dimensão.')
        if kind=='requisito_compartilhado' and not record.get('shared_group'):raise ValueError('Informe o grupo compartilhado.')
    if record.get('efficacy') and not record.get('validated_date'):raise ValueError('Eficácia exige data de validação.')
    if record.get('track') and record['track'] not in ('Sanitária','Bombeiros','Conselho profissional'):raise ValueError('Trilha documental inválida.')
    return dict(record)
