"""Parse TabNet semicolon exports without adding totals or averaging published rates."""
from pathlib import Path
import csv,hashlib,re,json
import pandas as pd
from src.contract_registry import ROOT
from src.cache import file_version,json_versioned,csv_versioned
MONTHS={'Janeiro':1,'Fevereiro':2,'Março':3,'Abril':4,'Maio':5,'Junho':6,'Julho':7,'Agosto':8,'Setembro':9,'Outubro':10,'Novembro':11,'Dezembro':12}
NON_ADDITIVE={'Taxa mortalidade','Média permanência','Valor médio intern'}

def parse_tabnet(content):
    try:text=content.decode('utf-8-sig')
    except UnicodeDecodeError:text=content.decode('latin-1')
    lines=text.splitlines()
    if len(lines)<5:raise ValueError('Exportação TabNet incompleta')
    identity=next((l for l in lines if l.startswith('Estabelecimento:')),'')
    if not re.search(r'\b6559379\s+HOSPITAL DOM HELDER CAMARA\b',identity):raise ValueError('CNES ou unidade diferente do HDH')
    title=lines[1].strip();measure,dimension=title.split(' por Ano/mês atendimento e ',1)
    header_index=next(i for i,l in enumerate(lines) if l.startswith('"Ano/mês atendimento";'))
    columns=next(csv.reader([lines[header_index]],delimiter=';'));rows=[]
    for i,line in enumerate(lines[header_index+1:],header_index+2):
        if not line.startswith('"'):continue
        cells=next(csv.reader([line],delimiter=';'))
        if len(cells)!=len(columns):raise ValueError(f'Colunas incompatíveis na linha {i}')
        label=cells[0].strip().lstrip('.').strip();comp=None;year=None
        if label=='Total':kind='total_publicado'
        elif re.fullmatch(r'\d{4}',label):kind='ano_publicado';year=int(label)
        else:
            match=re.fullmatch(r'([A-Za-zçÇ]+)/([0-9]{4})',label)
            if not match or match[1] not in MONTHS:raise ValueError('Competência não reconhecida: '+label)
            kind='mensal';year=int(match[2]);comp=f'{year}-{MONTHS[match[1]]:02}'
        for category,raw in zip(columns[1:],cells[1:]):
            value=None if raw.strip() in ('-','...','..','') else float(raw.replace('.','').replace(',','.'))
            if value is not None and value<0:raise ValueError('Valor negativo na fonte')
            rows.append(dict(medida=measure,dimensao=dimension,tipo_linha=kind,competencia=comp,ano=year,categoria=category,valor=value,valor_original=raw,linha_fonte=i))
    return pd.DataFrame(rows),dict(titulo=title,medida=measure,dimensao=dimension,cnes='6559379',unidade='HOSPITAL DOM HELDER CAMARA',periodo_solicitado=lines[3].strip(),hash_sha256=hashlib.sha256(content).hexdigest(),fonte='Ministério da Saúde — SIH/SUS — DATASUS/TabNet',url='https://tabnet.datasus.gov.br/',data_extracao='2026-10-06',observacao='Dados dos últimos seis meses sujeitos a atualização, conforme nota da fonte. Símbolos originais preservados; não convertidos automaticamente em zero.')

def load_sih():
    meta=json_versioned(file_version(ROOT/'config/sih_sources.json'))
    data=csv_versioned(file_version(ROOT/'data/sih/observacoes.csv'))
    return data,meta

def monthly_series(data,start='2020-01',end='2026-07'):
    return data[(data.tipo_linha=='mensal')&data.competencia.between(start,end)].copy()

def published_annual(data):
    return data[data.tipo_linha=='ano_publicado'].copy()

def measure_unit(measure):
    if measure.startswith('Valor'):return 'R$'
    if measure=='Taxa mortalidade':return '%'
    if measure in ['Média permanência','Dias permanência']:return 'dias'
    return 'AIHs' if measure=='AIH aprovadas' else 'óbitos'
