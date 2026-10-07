# Indicadores de reestruturação

Implementação local, sem publicação ou alteração do aplicativo remoto. Esta página é independente dos indicadores do contrato. As 14 fichas são propostas de gestão; baseline inicial **A levantar no diagnóstico inicial**. Nenhuma evidência fictícia constitui resultado atual do HDH. A pactuação documental é registrada pelo ADMIN; o perfil diretoria/GESTOR consulta e exporta, sem aprovar eletronicamente.

## Primeiro acesso

1. Instale `requirements.txt` e mantenha os Secrets de autenticação existentes.
2. Execute `python -m streamlit run app.py`.
3. Após login, abra **Indicadores de reestruturação**.
4. **Institucional** permite consultar as 14 fichas propostas antes da inicialização. O ADMIN pode inicializá-las para registrar dados no arquivo JSON, sem banco. Ausência de apurações não vira zero.
5. **Demonstração fictícia** cria, exclusivamente na sessão, 42 apurações ilustrativas de abril a junho/2026. Dados e pactuações deste modo são fictícios, identificados nas telas e exportações; não são copiados para o banco institucional. Encerrar/reiniciar a sessão pode eliminar a demonstração.

## Armazenamento sem SQL

Não há PostgreSQL, SQLite, SQLAlchemy ou driver SQL nesta implementação. Os registros são gravados em **JSON versionado**, por padrão em `data/private/reestruturacao.json`. Nenhuma configuração adicional de banco é necessária. Os Secrets de autenticação continuam obrigatórios.

O ADMIN clica **Inicializar fichas propostas**. Essa operação cria as 14 fichas propostas, sem inventar resultados ou aprovar metas. Diretoria/GESTOR permanece apenas em consulta.

Opcionalmente, altere o caminho no arquivo local `.streamlit/secrets.toml` ou nos Secrets do aplicativo:

```toml
[restructuring]
storage_path = "data/private/reestruturacao.json"
```

Também é possível usar `RESTRUCTURING_STORAGE_PATH`. Configurações antigas `database_url`/`RESTRUCTURING_DATABASE_URL` não são utilizadas e podem ser removidas dos Secrets. Credenciais de autenticação devem ser preservadas. Arquivos de bancos da implementação anterior não são convertidos automaticamente: esta versão inicia seu próprio arquivo JSON.

### Durabilidade e uso no Streamlit Cloud

No computador local, o arquivo persiste entre sessões e reinicializações enquanto o disco for preservado. A pasta `data/private/` continua ignorada pelo Git e excluída dos pacotes de entrega. Faça backup em local protegido e controle acesso ao computador.

**No Streamlit Community Cloud, o disco local não tem persistência garantida.** Os registros são compartilhados entre sessões atendidas pela mesma instância, mas podem desaparecer em reinicializações, reconstruções ou troca de servidor. Esta versão sem serviço externo atende ao protótipo e permite backup/restauração; não oferece armazenamento institucional durável na nuvem. Não há sincronização automática com GitHub nem gravação de dados institucionais no repositório. Para durabilidade automática em produção, seria preciso integrar posteriormente um armazenamento externo persistente, que pode ser de objetos/arquivos e não precisa usar SQL.

### Backup e restauração

Na seção **Administração → Backup e restauração dos registros**, o ADMIN pode:

1. Baixar o backup JSON completo, incluindo versões anteriores, autoria, justificativas e memórias. Faça isso após alterações importantes e antes de reiniciar/atualizar o aplicativo.
2. Guardar o arquivo em local protegido. O backup contém códigos operacionais opacos e referências de evidência; não deve conter dados de pacientes ou senhas.
3. Selecionar um backup confiável, informar justificativa, confirmar a origem e clicar **Restaurar backup**. Essa opção também está disponível antes da inicialização, permitindo recuperação após perda do arquivo.

A restauração aceita até 20 MB, valida estrutura, origem, sequência de versões e vínculos. Importa versões ausentes e preserva as existentes; divergências/conflitos, lacunas e mistura entre demonstração e institucional são rejeitados sem alteração parcial. Recuperações são registradas com o administrador atual, sem apagar a autoria histórica. Reimportar um backup já recuperado não duplica os registros. Backups não possuem assinatura criptográfica de autenticidade; o administrador deve conferir sua procedência.

### Integridade da gravação

A biblioteca padrão do Python controla acesso concorrente com bloqueio de arquivo (Linux/Windows) e bloqueio em memória para a demonstração. O arquivo é preparado em temporário, sincronizado e substituído atomicamente. Falhas anteriores à substituição preservam o arquivo existente. Arquivo JSON corrompido gera erro e não é sobrescrito automaticamente. Conflitos de revisão são rejeitados. Não há garantia de operação distribuída entre múltiplos servidores; o protótipo usa uma instância e arquivo local.

## Fluxo administrativo

**Administração** executa apenas a subseção selecionada:

- **Registros operacionais:** código opaco, fonte, referência de evidência, campos específicos do indicador e data da versão. Não inserir nomes, CPF, CNS ou prontuários. Campos não autorizados e padrões numéricos de identificadores são rejeitados; isso não substitui revisão humana do texto livre.
- **Pactuação e ficha:** editar descrição, numerador, denominador, fonte, método, periodicidade, responsabilidades, elegibilidade, resposta ao desvio, recursos, meta e baseline. Pactuação exige início aprovado do plano, aprovador identificado, data e referência documental. Não é assinatura eletrônica. Meta proposta não recebe classificação de meta pactuada.
- **Apurações:** definir período/corte, escopo, fonte, método, coleta, validação e evidência; confirmar universo e elegibilidade. Preferir registros unitários. Entrada agregada exige numerador/denominador e permanece identificada como sem rastreabilidade individual. Numerador e denominador são contagens inteiras; numerador maior que denominador é rejeitado.
- **Ações para desvios:** vincular à apuração, responsável, prazo original e atual, situação e evidência. Conclusão exige evidência.

Editar textos de fórmula ou elegibilidade NÃO reprograma o algoritmo. As 14 implementações operacionais estão em `calculations.py`, identificadas como `restructuring_v1`; mudanças substantivas exigem revisão técnica do motor e dos testes. Alterações de definição/escopo sinalizam quebra de comparabilidade. Não usar uma descrição repactuada incompatível com o algoritmo sem essa revisão.

## Regras verificáveis

| Nº | Indicador | Meta proposta | Principal cuidado |
|---|---|---|---|
| 1 | Documentos obrigatórios válidos | 100% | Protocolo não é concessão; validade, escopo e trilhas separadas |
| 2 | Conformidade dos requisitos | 100% | Não avaliado permanece no universo; cobertura separada |
| 3 | Completude do checklist cirúrgico | 100% | Três momentos e registro tempestivo; cirurgia sem checklist permanece |
| 4 | Execução observada da cirurgia segura | 95% / 60 dias | Observação integral; perdas e amostra explicitadas |
| 5 | Auditorias planejadas concluídas | 100% | Calendário original; auditorias extras separadas |
| 6 | Não conformidades tratadas no prazo | 90% / 90 dias | Prazo original e eficácia validada tempestivamente |
| 7 | Reincidência das não conformidades | Até 10% / 180 dias | Janela de 90 dias completa, mesmo requisito/setor, reavaliação e cobertura |
| 8 | Protocolos prioritários implementados | 100% / 90 dias | Aprovação, recursos, capacitação e uso demonstrado |
| 9 | Adesão observada aos protocolos | 95% / 90 dias | Por protocolo; etapas e observação integral |
| 10 | Equipe capacitada e avaliada | 100% / 60 dias | Pessoas únicas por competência no universo aprovado |
| 11 | Incidentes investigados no prazo | 100% | Vencimento original; não substitui notificação externa |
| 12 | Ações dos incidentes concluídas | 90% / 90 dias | Vínculo com incidente e eficácia; separado do indicador 6 |
| 13 | Adequação dos dez novos leitos UTI | 100% | Denominador fixo 10; seis dimensões e dependências compartilhadas |
| 14 | Notificações triadas no prazo | 100% | Recebidas, triadas e pendentes; não há meta de reduzir notificações |

Os marcos 60/90/180 dias são contados do início aprovado do plano e não substituem prazos originais dos casos. Denominador comprovadamente vazio gera **Não aplicável no período**; universo/fonte desconhecidos geram **Não aferível**, ambos sem percentual. Falhas críticas são sinalizadas mesmo com percentual favorável. No indicador 13, uma falha compartilhada afeta todos os leitos dependentes; dimensão desconhecida bloqueia conclusão de adequação.

## História, gráficos e exportações

Apuração mantém cópia da ficha, meta, classificação e memória usada. Mudança no meio do período exige dividir a apuração. Correção exige justificativa e nova versão; não substitui silenciosamente o histórico. Novas versões aparecem em séries distintas por escopo; gráficos não ligam lacunas e não produzem uma nota média de conformidade hospitalar.

As memórias exibem incluídos, excluídos e motivos, pendências, perdas, cobertura, datas, resultado original e arredondado, fonte, método, responsáveis e evidência. O XLSX contém síntese, memórias, fichas, ações e detalhes de inclusão/exclusão/pendências. CSV e XLSX são gerados sob demanda, com origem institucional ou fictícia explícita. Códigos opacos exportados não devem permitir identificação de pacientes; referências não contêm documentos clínicos.

## Fundamentação e limites

`restructuring_references.yaml` registra fontes oficiais, dispositivo pertinente, data de consulta e distinção entre texto original consultado e conferência de vigência/consolidação. Referências conservam **Pendente de conferência** onde a validade consolidada e aplicabilidade local não foram comprovadas. A RDC 509/2021 revoga a RDC 2/2010 na gestão de tecnologias; RDC 7/2010 deve ser considerada com alterações posteriores. Não se afirma que as normas prescrevem estas fórmulas e metas gerenciais.

A estrutura não constitui certificação sanitária, decisão jurídica, assinatura eletrônica ou homologação FGH. Segurança em produção exige avaliação institucional, validação dos universos, controle dos responsáveis, backup, retenção e revisão das referências aplicáveis. Não houve publicação nesta etapa.

## Manutenção

- `schema.py`: campos minimizados, validação e autorização.
- `calculations.py`: regras dos 14 indicadores e classificação.
- `repository.py`: regras de persistência, permissões, versionamento e backup/restauração.
- `file_store.py`: JSON, substituição atômica e bloqueios de gravação.
- `settings.py`: caminho do arquivo JSON, sem Secrets de banco.
- `demo.py`: exemplos fictícios isolados.
- `ui.py`: filtros, formulários, gráficos, fichas e exportações protegidos.
- `config/restructuring_*.yaml`: catálogo e fontes normativas, separados do contrato.

A persistência utiliza somente a biblioteca padrão do Python. As dependências SQLAlchemy, psycopg e psycopg-binary foram removidas dos arquivos de instalação; as demais versões continuam fixadas.

Execute `python -m pytest`, `python -m compileall app.py src pages scripts tests` e `python -m pip check` antes de atualizar. Testes novos cobrem motor, persistência, permissões, transições, formulários reais, exportação e navegação. A validação local não equivale a homologação de armazenamento institucional ou revisão jurídica.
