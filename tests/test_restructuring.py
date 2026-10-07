from copy import deepcopy
from datetime import date,timedelta
import time
import pytest
from src.restructuring.schema import Actor,validate_record
from src.restructuring.demo import example_record,demo_context,create_demo
from src.restructuring.calculations import calculate,classify
from src.restructuring.repository import Repository,FileStore
from src.contract_registry import load

ADMIN=Actor('admin','ADMIN',True,time.time())
DIRECTOR=Actor('diretoria','GESTOR',True,time.time())

@pytest.fixture
def repo(tmp_path):
    repository=Repository(FileStore(tmp_path/'durable.json'))
    repository.initialize(ADMIN)
    return repository


def real_record(number,entity='op-exemplo'):
    record=example_record(number,entity)
    record['source']='Inventário institucional de teste';record['evidence']='evidencia-operacional'
    return record


def context():
    value=demo_context();value.update(source='Fonte operacional de teste',validation_evidence='ref-validacao',data_origin='INSTITUCIONAL')
    return value


@pytest.mark.parametrize('number',range(1,15))
def test_fourteen_formulas(number):
    records=[real_record(number)]
    scope={'protocol':'Protocolo exemplo'} if number in (9,10) else {}
    if number==13:
        records=[]
        for i in range(1,11):
            r=real_record(13,'leito-'+str(i));r['bed_number']=i;records.append(r)
    result=calculate(number,records,'2026-04-01','2026-04-30',context(),scope)
    assert result['value_raw']==(0 if number==7 else 100)
    assert result['denominator']==(10 if number==13 else 1)
    assert result['included']


@pytest.mark.parametrize('number',range(1,15))
def test_missing_universe_never_zero(number):
    ctx=context();ctx['universe_confirmed']=False
    result=calculate(number,[],'2026-04-01','2026-04-30',ctx,{'protocol':'Exemplo'} if number in (9,10) else {})
    assert result['value_raw'] is None and result['status_data']=='Não aferível'


def test_empty_confirmed_universe_is_not_applicable():
    result=calculate(5,[],'2026-04-01','2026-04-30',context())
    assert result['status_data']=='Não aplicável no período' and result['value_raw'] is None


def test_counts_duplicate_and_dates():
    for aggregate in [dict(numerator=-1,denominator=2),dict(numerator=1.5,denominator=2),dict(numerator=3,denominator=2),dict(numerator=True,denominator=2)]:
        with pytest.raises(ValueError):calculate(5,[],'2026-04-01','2026-04-30',context(),aggregate=aggregate)
    with pytest.raises(ValueError):calculate(13,[],'2026-04-01','2026-04-30',context(),aggregate={'numerator':8,'denominator':9})
    r=real_record(5)
    with pytest.raises(ValueError):calculate(5,[r,r],'2026-04-01','2026-04-30',context())
    r=real_record(11);r['investigated_date']='2026-03-01'
    with pytest.raises(ValueError):validate_record(11,r)
    r=real_record(1);r['cpf']='123.456.789-00'
    with pytest.raises(ValueError):validate_record(1,r)


def test_original_due_cohort_and_late_effectiveness():
    a=real_record(6,'nc-a');a['current_due']='2026-06-20';a['validated_date']='2026-04-21'
    b=real_record(6,'nc-b');b['original_due']='2026-05-01'
    result=calculate(6,[a,b],'2026-04-01','2026-04-30',context())
    assert result['denominator']==1 and result['value_raw']==0
    assert result['excluded'][0]['id']=='nc-b'
    a['efficacy']=False
    result=calculate(6,[a],'2026-04-01','2026-04-30',context())
    assert result['complementary']['pendencias_vencidas']==1


def test_partial_observations_and_critical_loss():
    a=real_record(4,'obs-a');b=real_record(4,'obs-b');b['observed_complete']=False;b['critical']=True
    result=calculate(4,[a,b],'2026-04-01','2026-04-30',context())
    assert result['denominator']==1 and result['coverage']['perdas_parciais']==1
    assert result['critical']


def test_recurrence_window_and_same_requirement():
    mature=real_record(7,'nc-closed');mature.update(recurred=True,recurrence_date='2026-02-01',recurrence_requirement_key=mature['requirement_key'],recurrence_sector=mature['sector'],critical=True)
    immature=real_record(7,'nc-new');immature['closed_date']='2026-04-01';immature['rechecked_date']=None
    unrechecked=real_record(7,'nc-notchecked');unrechecked['rechecked_date']=None
    result=calculate(7,[mature,immature,unrechecked],'2026-04-01','2026-04-30',context())
    assert result['value_raw']==100 and result['denominator']==1 and result['critical']
    assert result['coverage']['casos_com_janela_completa']==2
    assert result['coverage']['reavaliados_ate_corte']==1
    mature['recurrence_sector']='Outro'
    assert calculate(7,[mature],'2026-04-01','2026-04-30',context())['value_raw']==0


def test_shared_bed_failure_and_unknown_dimensions():
    beds=[]
    for i in range(1,11):
        bed=real_record(13,'leito-'+str(i));bed['bed_number']=i;bed['dependencies']=['recurso-comum'];beds.append(bed)
    resource={'entity_id':'recurso-op','record_kind':'requisito_compartilhado','shared_group':'recurso-comum','shared_conform':False,'source':'Engenharia','evidence':'ref'}
    result=calculate(13,beds+[resource],'2026-04-01','2026-04-30',context())
    assert result['denominator']==10 and result['numerator']==0 and result['critical']
    assert all(row['seguranca'] is False for row in result['bed_dimensions'])
    resource['shared_conform']=True;beds[0]['dimensions']['documentacao']=None
    result=calculate(13,beds+[resource],'2026-04-01','2026-04-30',context())
    assert result['numerator']==9 and result['coverage']['leitos_com_avaliacao_completa']==9


def test_director_cannot_mutate_any_backend(repo):
    assert len(repo.definitions(DIRECTOR))==14
    for operation in [lambda:repo.initialize(DIRECTOR),lambda:repo.save_record(DIRECTOR,5,real_record(5),'2026-04-01','Teste'),lambda:repo.save_definition(DIRECTOR,1,{},'Teste'),lambda:repo.assess(DIRECTOR,5,'2026-04-01','2026-04-30',context()),lambda:repo.save_action(DIRECTOR,5,{},'Teste')]:
        with pytest.raises(PermissionError):operation()
    expired=Actor('admin','ADMIN',True,time.time()-3601)
    with pytest.raises(PermissionError):repo.initialize(expired)


def test_persistence_corrections_and_original_deadline(repo):
    record=real_record(6)
    repo.save_record(ADMIN,6,record,'2026-04-01','Cadastro')
    another=Repository(FileStore(repo.store.path))
    assert another.records(DIRECTOR,6)[0]['entity_id']==record['entity_id']
    record['efficacy']=False
    another.save_record(ADMIN,6,record,'2026-04-02','Correção documentada',1)
    assert len(repo.history(DIRECTOR,'record',6))==2
    record['original_due']='2026-05-01'
    with pytest.raises(ValueError):repo.save_record(ADMIN,6,record,'2026-04-03','Tentativa de alterar original',2)


def test_incident_action_link(repo):
    action=real_record(12)
    with pytest.raises(ValueError):repo.save_record(ADMIN,12,action,'2026-04-01','Cadastro')
    repo.save_record(ADMIN,11,real_record(11,'incidente-exemplo'),'2026-04-01','Cadastro')
    repo.save_record(ADMIN,12,action,'2026-04-01','Cadastro')
    assert repo.records(DIRECTOR,12)


def test_pactuation_history_and_period_specific_target(repo):
    d=repo.definition_for(ADMIN,5,'2026-04-01','2026-04-30')
    assert d['pact_status'].startswith('Proposta')
    d.update(target=90,pact_status='Pactuada',effective_from='2026-05-01',approved_plan_start='2026-01-01',approval={'approver':'Direção','date':'2026-05-01','evidence':'Ata-teste'})
    repo.save_definition(ADMIN,5,d,'Pactuação documental',1)
    repo.assess(ADMIN,5,'2026-04-01','2026-04-30',context(),aggregate={'numerator':8,'denominator':10})
    first=repo.assessments(DIRECTOR,5)[0]
    assert first['target']==100 and first['classification']=='Meta ainda não pactuada'
    repo.assess(ADMIN,5,'2026-05-01','2026-05-31',context(),aggregate={'numerator':9,'denominator':10})
    assert next(row for row in repo.assessments(DIRECTOR,5) if row['start']=='2026-05-01')['classification']=='Meta atingida no período'
    with pytest.raises(ValueError):repo.assess(ADMIN,5,'2026-04-20','2026-05-05',context(),aggregate={'numerator':9,'denominator':10})
    d['target']=80;d['effective_from']='2026-06-01';d['scope']='Novo escopo';repo.save_definition(ADMIN,5,d,'Repactuação documental',2)
    assert repo.assessments(DIRECTOR,5)[0]['target']==100
    assert repo.definition_for(DIRECTOR,5,'2026-06-01','2026-06-30')['comparability_break']


def test_demo_separation_and_aggregate_traceability(repo):
    with pytest.raises(ValueError):repo.save_record(ADMIN,5,example_record(5),'2026-04-01','Teste',data_origin='DEMONSTRACAO')
    with pytest.raises(ValueError):repo.save_record(ADMIN,5,example_record(5),'2026-04-01','Teste')
    demo=create_demo();assert len(demo.assessments(DIRECTOR))==42
    assert repo.assessments(DIRECTOR)==[]
    repo.assess(ADMIN,5,'2026-04-01','2026-04-30',context(),aggregate={'numerator':8,'denominator':10})
    result=repo.assessments(DIRECTOR,5)[0]
    assert result['calculation_type']=='Agregada' and not result['included']
    assert 'não existe rastreabilidade individual' in result['limitations']
    with pytest.raises(ValueError):repo.assess(ADMIN,5,'2026-04-01','2026-04-30',context(),aggregate={'numerator':9,'denominator':10})


def test_remaining_rule_specifics():
    record=real_record(1);record['granted']=False
    assert calculate(1,[record],'2026-04-01','2026-04-30',context())['value_raw']==0
    record=real_record(2);record['evaluated']=False;record['conform']=None
    result=calculate(2,[record],'2026-04-01','2026-04-30',context())
    assert result['coverage']['nao_avaliados']==1 and result['denominator']==1
    record=real_record(3);record['timely']=False
    assert calculate(3,[record],'2026-04-01','2026-04-30',context())['value_raw']==0
    record=real_record(8);record['training_done']=False
    assert calculate(8,[record],'2026-04-01','2026-04-30',context())['value_raw']==0
    record=real_record(14);record['triaged_date']=None
    result=calculate(14,[record],'2026-04-01','2026-04-30',context())
    assert result['complementary']['notificacoes_pendentes']==1 and result['value_raw']==0
    a=real_record(10,'p-a');b=real_record(10,'p-b');b['person_token']=a['person_token']
    with pytest.raises(ValueError):calculate(10,[a,b],'2026-04-01','2026-04-30',context(),{'protocol':'Protocolo exemplo'})


def test_milestones_and_reduction_classification():
    d=deepcopy(load('restructuring_indicators.yaml')['indicators'][6])
    d.update(pact_status='Pactuada',approved_plan_start='2026-01-01')
    result=calculate(7,[],'2026-04-01','2026-04-30',context(),aggregate={'numerator':2,'denominator':10})
    assert classify(result,d)[0]=='Prazo ainda em curso'
    result['cutoff']='2026-08-01'
    assert classify(result,d)[0]=='Abaixo da meta'
    result['value_raw']=10
    assert classify(result,d)[0]=='Meta atingida no período'


def test_definition_revision_conflict_and_baseline_evidence(repo):
    definition=repo.definition_for(ADMIN,1,'2026-04-01','2026-04-30')
    definition['effective_from']='2026-05-01'
    definition['baseline']['value']=80
    with pytest.raises(ValueError):repo.save_definition(ADMIN,1,definition,'Linha de base sem evidência',1)
    definition['baseline'].update(period='2026-04',coverage='Inventário integral',evidence='relatorio-baseline')
    repo.save_definition(ADMIN,1,definition,'Diagnóstico documentado',1)
    with pytest.raises(ValueError):repo.save_definition(ADMIN,1,definition,'Versão desatualizada',1)


def test_json_backup_restore_permissions_and_origin(repo,tmp_path):
    repo.save_record(ADMIN,5,real_record(5),'2026-04-01','Registro inicial')
    repo.assess(ADMIN,5,'2026-04-01','2026-04-30',context())
    backup=repo.backup(ADMIN)
    restored=Repository(FileStore(tmp_path/'restored.json'))
    count=restored.restore(ADMIN,backup,'Recuperação após reinicialização')
    assert count==16 and restored.assessments(DIRECTOR,5)[0]['value_raw']==100
    assert restored.restore(ADMIN,backup,'Conferência idempotente')==0
    assert len(restored.history(DIRECTOR,'restore'))==1
    for operation in [lambda:repo.backup(DIRECTOR),lambda:repo.restore(DIRECTOR,backup,'Teste')]:
        with pytest.raises(PermissionError):operation()
    with pytest.raises(ValueError):restored.restore(ADMIN,create_demo().backup(ADMIN),'Origem incompatível')


def test_restore_conflicts_and_corruption_never_overwrite(repo):
    import json
    backup=json.loads(repo.backup(ADMIN));before=repo.history(DIRECTOR)
    backup['entries'][0]['payload']['target']=99
    with pytest.raises(ValueError):repo.restore(ADMIN,json.dumps(backup).encode(),'Conflito')
    assert repo.history(DIRECTOR)==before
    with pytest.raises(ValueError):repo.restore(ADMIN,b'not json','Arquivo inválido')
    backup=json.loads(repo.backup(ADMIN));backup['entries'].pop()
    with pytest.raises(ValueError):Repository(FileStore()).restore(ADMIN,json.dumps(backup).encode(),'Histórico incompleto')
    repo.store.path.write_text('{incomplete',encoding='utf-8')
    with pytest.raises(ValueError):repo.initialize(ADMIN)
    assert repo.store.path.read_text()=='{incomplete'


def test_simultaneous_json_writers_preserve_all_versions(repo):
    from concurrent.futures import ThreadPoolExecutor
    def save(index):
        other=Repository(FileStore(repo.store.path))
        return other.save_record(ADMIN,5,real_record(5,'audit-'+str(index)),'2026-04-01','Gravação concorrente')
    with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(save,range(12)))
    assert len(repo.records(DIRECTOR,5))==12
    assert len(repo.history(DIRECTOR,'definition'))==14
