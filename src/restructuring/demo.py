"""Synthetic operational examples. Never written to the institutional database."""
from copy import deepcopy
from datetime import date
from src.restructuring.repository import Repository,FileStore
from src.restructuring.schema import Actor
import time


def example_record(number,entity='registro-exemplo'):
    r=dict(entity_id=entity,sector='Setor demonstrativo',protocol='Protocolo exemplo',shift='Diurno',specialty='Exemplo',source='DEMONSTRAÇÃO — fonte fictícia',evidence='DEMONSTRAÇÃO — evidência fictícia',applicable=True,exclusion_approved=False,exclusion_justification='',critical=False)
    specific={
      1:dict(granted=True,scope_sufficient=True,valid_from='2026-01-01',valid_until='2027-01-01',track='Sanitária'),
      2:dict(evaluated=True,conform=True),
      3:dict(event_date='2026-04-10',moments=[True,True,True],timely=True),
      4:dict(event_date='2026-04-10',moments=[True,True,True],observed_complete=True,sample_method='Conveniente — fictícia'),
      5:dict(planned_date='2026-04-10',completed_date='2026-04-10',report_valid=True,extra=False,original_calendar='DEMO calendário v1'),
      6:dict(original_due='2026-04-20',closed_date='2026-04-18',validated_date='2026-04-19',efficacy=True),
      7:dict(closed_date='2026-01-01',rechecked_date='2026-04-10',recurred=False,requirement_key='requisito-exemplo'),
      8:dict(approved=True,resources_ready=True,training_done=True,use_verified=True,priority=True,priority_list_version='DEMO-v1'),
      9:dict(event_date='2026-04-10',observed_complete=True,all_steps_correct=True,sample_method='Conveniente — fictícia'),
      10:dict(person_token='pessoa-opaca-'+entity,competency='Protocolo exemplo',eligible=True,completed_date='2026-04-10',assessment_satisfactory=True,function='Função demonstrativa'),
      11:dict(received_date='2026-04-01',original_due='2026-04-20',investigated_date='2026-04-18',gravity='Classificação fictícia'),
      12:dict(incident_id='incidente-exemplo',original_due='2026-04-20',completed_date='2026-04-18',validated_date='2026-04-19',efficacy=True),
      13:dict(record_kind='leito',bed_number=1,dimensions={key:True for key in ('estrutura','equipamentos','profissionais','processos','seguranca','documentacao')},dependencies=[]),
      14:dict(received_date='2026-04-01',original_due='2026-04-05',triaged_date='2026-04-02',gravity='Classificação fictícia'),
    }
    return {**r,**specific[number]}


def demo_context():
    return dict(source='DEMONSTRAÇÃO — fonte fictícia',method='Exemplo sintético operacional',eligibility_confirmed=True,universe_confirmed=True,collector='Equipe fictícia',validator='Validador fictício',validation_evidence='DEMO-EVIDENCIA',limitations='Dados inteiramente fictícios, sem representação de resultados atuais.',data_origin='DEMONSTRACAO')


def create_demo():
    actor=Actor('demo-system','ADMIN',True,time.time())
    repo=Repository(FileStore(),'DEMONSTRACAO');repo.initialize(actor)
    # Clearly synthetic, documented pactuation examples, isolated from real definitions.
    for number in range(1,15):
        d=repo.definition_for(actor,number,'2026-01-01','2026-01-01')
        d.update(pact_status='Pactuada',effective_from='2026-01-01',approved_plan_start='2026-01-01',approval={'approver':'Diretoria fictícia','date':'2026-01-01','evidence':'DEMONSTRAÇÃO — aprovação fictícia'})
        repo.save_definition(actor,number,d,'DEMONSTRAÇÃO: pactuação fictícia',1)
    repo.save_record(actor,11,example_record(11,'incidente-exemplo'),'2026-01-01','Exemplo fictício')
    for month in (4,5,6):
        for number in range(1,15):
            records=10 if number==13 else 2
            if number==11:records=0
            for index in range(records):
                record=example_record(number,f'exemplo-{month}-{number}-{index}')
                for field in ('event_date','planned_date','completed_date','original_due','closed_date','validated_date','investigated_date','received_date','triaged_date','rechecked_date'):
                    if field in record and not (number==7 and field=='closed_date'):
                        record[field]=record[field].replace('2026-04',f'2026-{month:02}')
                if number==13:
                    record['entity_id']=f'leito-{index+1}';record['bed_number']=index+1
                    if month==4 and index>=8:record['dimensions']['documentacao']=None
                if index==1 and month==4:
                    if number==2:record['evaluated']=False;record['conform']=None
                    elif number in (3,4):record['moments']=[True,False,True]
                    elif number in (6,12):record['efficacy']=False
                    elif number==9:record['observed_complete']=False
                old=repo._latest(actor,'record',number).get(f'{number}:{record["entity_id"]}')
                repo.save_record(actor,number,record,f'2026-{month:02}-01','DEMONSTRAÇÃO — exemplo operacional',old['revision'] if old else None)
            end=date(2026,month,30).isoformat() if month in (4,6) else '2026-05-31'
            scope={'protocol':'Protocolo exemplo'} if number in (9,10) else {}
            repo.assess(actor,number,f'2026-{month:02}-01',end,demo_context(),scope)
    return repo
