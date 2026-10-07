# Validação da atualização documental e SIH

- Python local 3.12.14: **57 testes passaram** (`pytest`), incluindo faixas financeiras, versões, 20/10/30 por conjunto, inventário e hashes, exclusão de documentos de outras unidades, ausência de dados e divergências reais.
- AppTest: login, logout, configuração ausente, limitação de tentativas e **cinco áreas** renderizadas; todas bloqueadas sem sessão autenticada.
- CSV, XLSX, Parquet e DBF em UTF-8, Latin-1 e CP1252 exercitados pelos testes de leitura/validação.
- SIH: identidade CNES, 12 arquivos/11 conteúdos únicos, 79 competências no recorte, dezembro/2019 separado, decimais brasileiros, símbolos preservados e taxas anuais não aditivas testados.
- XLSX documental com sete abas validado por leitura posterior.
- `python -m compileall` nos arquivos do projeto: aprovado.
- `streamlit run app.py --server.headless true --server.port 8502`: iniciou e informou URL local, sem erro de inicialização.

GitHub Actions confirmou pytest e compileall em Python 3.12 e 3.13 na integração inicial desta atualização (execução 37534635141). A criação/configuração do aplicativo no Streamlit Community Cloud é realizada pelo proprietário da conta. Upload via navegador não automatizado; leitores, validação e interface foram exercitados. Conferência visual no navegador e homologação institucional permanecem recomendadas. Validação do software não equivale a validação jurídica definitiva das regras ou de todas as células OCR.

Polimento: biblioteca sem fundamentação legal, sem exposição de metadados técnicos ou datas ausentes; PDFs com download; pareceres CMA possuem prévia paginada do layout original. Navegação lateral habilitada. Tratamento de falhas com mensagem pública genérica e logs internos.

Autenticação: cinco testes passaram após ajuste do usuário para admin, incluindo login, logout, bloqueio de tentativas, migração de configuração antiga sem alterar senha e ocultação da barra lateral no login.

Ajustes finais: **64 testes passaram** na suíte completa local, incluindo acesso diretoria/GESTOR, preservação do administrador quando a configuração opcional é inválida, contatos e resumo da Tela inicial, seleção de todos os grupos de procedimentos e restrição da gestão de dados ao ADMIN. Compileall aprovado; Streamlit iniciou na porta 8503 com configuração headless.

Gráficos de qualidade e visualizador CMA: **70 testes passaram** na suíte completa. Todos os PDFs CMA disponíveis renderizaram a primeira página; limites de página e alternativa de download para PDF inválido foram testados. A aba Histórico mensal foi removida da CMA, resultados numéricos mantêm lacunas e resultados textuais são exibidos por categoria, sem atribuição artificial de pontuação.

Evolução gerencial e desempenho: **85 testes passaram** na suíte completa local, sem avisos do pytest, após separação das telas, cache público por versão de arquivo e execução apenas da seção selecionada. Testes cobrem resumo/drilldown, seções e filtros, preservação das lacunas, comparação anual de meses correspondentes, referências de 85/100%, regras de transição, página/ano do PDF, geração de exportação sob demanda e fluxo de importação válido/inválido pela interface com arquivo injetado no upload. Configurações e dados em cache retornam cópias isoladas; uploads não usam cache compartilhado. `pip check` e compileall aprovados; Streamlit iniciou na porta 8504.

Medição local exploratória: carregamento e enriquecimento dos dados documentais, 0,1803 s na chamada fria e 0,0021 s com cache aquecido. Valores específicos desta execução, sem garantia de tempo de resposta no Streamlit Cloud. Dependências diretas e transitivas fixadas em requirements.txt e requirements-lock.txt.

## Reestruturação — validação local em 07/10/2026

**131 testes passaram** em Python 3.12.14. Os 46 testes novos cobrem 14 fórmulas, universos ausentes, contagens, duplicidades, observações parciais, janela de reincidência, recursos compartilhados da UTI, prazos originais, vínculo de incidentes, transição de metas, correção/histórico, baseline, origem fictícia, controle de acesso no backend, persistência em nova instância e novas sessões AppTest. Interface: 14 indicadores, quatro formulários administrativos, exportações e apuração agregada persistida, consulta diretoria e ausência de permissão de escrita. TLS obrigatório e bloqueio de SQLite Cloud testados.

`compileall` e `pip check` aprovados. Streamlit iniciou em 127.0.0.1:8507; `/_stcore/health` respondeu HTTP 200, corpo `ok`. Nenhuma publicação ou alteração de serviço externo foi feita. PostgreSQL externo não foi provisionado nem testado nesta sessão; SQLite local e driver importável foram validados. Esta entrega não afirma validação de infraestrutura institucional nem conferência jurídica conclusiva das normas. Python 3.13 não foi executado localmente nesta etapa; workflow existente permanece preparado para 3.12/3.13.

## Versão sem SQL — validação local em 07/10/2026

Esta seção substitui a arquitetura SQL descrita na etapa anterior. **134 testes passaram** em Python 3.12.14, incluindo os fluxos preservados e 49 testes do módulo de reestruturação. Persistência agora em JSON, sem SQLAlchemy/psycopg/SQLite/PostgreSQL. Testes exercitam reabertura do arquivo, 12 escritores concorrentes, conflitos de versões, restauração idempotente, separação institucional/demonstração, rejeição de backup incompatível, corrompido ou conflitante e manutenção de arquivo corrompido sem sobrescrita. AppTest confirmou restauração pela interface e consulta em nova sessão da diretoria.

`compileall` e `pip check` aprovados. Streamlit iniciou na porta 8511 e respondeu HTTP 200 em `/_stcore/health`. Nenhuma publicação foi realizada. O armazenamento local funciona entre sessões na mesma instância, mas não é durável no Streamlit Cloud; backup/restauração manual deve ser utilizado. Bloqueio Windows implementado com msvcrt, mas não executado neste ambiente Linux.

## Histórico de acessos — validação local em 07/10/2026

**143 testes passaram**. Nove testes novos verificam persistência/reabertura, ausência de credenciais nos eventos, proibição de consulta por diretoria, outro ADMIN e sessão não autenticada/expirada, evento único de login e expiração, logout, ausência de gravação de tentativas inválidas, filtros e exportações na página administrativa e visibilidade da navegação exclusivamente para admin. Os testes de autenticação usam arquivos temporários para não contaminar o histórico da aplicação. Compileall e pip check aprovados; Streamlit iniciou na porta 8514, com HTTP 200 e resposta ok no healthcheck. Nenhuma publicação foi realizada. Histórico em JSON separado, sujeito às limitações de persistência do Cloud; encerramento do navegador não é tratado como logout confirmado.
