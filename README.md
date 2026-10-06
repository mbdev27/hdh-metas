# HDH Metas

Painel de Monitoramento do Contrato de Gestão — Hospital Metropolitano Sul Dom Helder Câmara.
Protótipo de Monitoramento Contratual e Gestão de Indicadores Hospitalares para estudo de caso profissional de Sanitarista. Sem vínculo oficial com FGH, SES/PE ou Governo de Pernambuco.

## Situação documental

**Nenhum documento foi anexado ou localizado no ambiente de execução.** Não houve análise de PDFs, validação do conteúdo, identificação de duplicatas reais ou comprovação de vigências dos indicadores. Consulte [auditoria](docs/AUDITORIA.md). As configurações reproduzem exclusivamente informações do prompt, explicitamente pendentes. O 10º TA é DOCUMENTO NÃO DISPONÍVEL. Os outros instrumentos são NÃO FORNECIDO PARA AUDITORIA, sem inventar datas, páginas, arquivos ou hashes.

O motor não aplica regras pendentes no modo normal. A interface usa um cenário demonstrativo explícito para 24 competências (outubro/2024 a setembro/2026). Isso **não comprova que as metas eram juridicamente aplicáveis naquelas competências**. Valores financeiros do 18º TA são limitados a julho/2026–junho/2028, conforme informação do prompt, também não auditada. Nenhum cálculo é valor definitivo a pagar.

## Instalação do zero

1. Instale Python 3.13 em https://www.python.org/downloads/ (no Windows marque Add Python to PATH). Python 3.12 também é aceito.
2. Instale Git em https://git-scm.com/downloads/ e crie uma conta em https://github.com/.
3. Extraia o projeto e abra um terminal na pasta `hdh-metas`.

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Se a política impedir a ativação, execute diretamente `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` e use esse executável nos comandos seguintes, sem alterar a política do computador.

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Credenciais obrigatórias

A senha inicial foi fornecida separadamente pelo solicitante e não é armazenada neste projeto. Gere o hash bcrypt interativamente (entrada oculta):

```bash
python scripts/generate_password_hash.py
```

Digite a senha fornecida e confirme. Copie somente o hash gerado para `.streamlit/secrets.toml`, criado a partir do exemplo:

```toml
[auth]
admin_username = "adm"
admin_password_hash = "COLE_O_HASH_BCRYPT_GERADO"
```

Esse arquivo é ignorado pelo Git. Alternativamente configure `ADMIN_USERNAME` e `ADMIN_PASSWORD_HASH` no ambiente. Nunca use senha em comandos, arquivos versionados ou logs. Sem hash válido, o aplicativo bloqueia acesso. Login dura uma hora; cinco falhas geram bloqueio de 30 segundos por sessão. ADMIN é o único perfil ativo; futuras permissões GESTOR/LEITURA devem ser definidas antes de criar usuários. O bloqueio por sessão é básico e não impede novas sessões: produção necessita identidade institucional e controles de rede.

## Executar e testar

```bash
streamlit run app.py
pytest
python -m compileall app.py src pages scripts tests
python scripts/generate_mock_data.py
```

O último comando recria os CSV com seed fixa; não é necessário para iniciar. Abra a URL local indicada pelo Streamlit e entre com `adm` e a senha configurada. Use Sair para apagar a sessão. Os dados inválidos intencionais são rejeitados no carregamento e exibidos no relatório, não corrigidos silenciosamente.

## Utilização

- Visão Geral: competência, pontuações e projeção quando existe valor conhecido.
- Produção: nove metas físicas de 100%, faixa financeira máxima a partir de 85%, diferença, tendência anual, acumulado e trimestre.
- Qualidade: doze indicadores mensais; amostra de satisfação abaixo de 10% impede aferição e não vira pontuação zero.
- Trimestre: soma metas e produção dos três meses; faltas impedem consolidação completa. Qualitativos mostram pontuação mensal e média analítica rotulada.
- Monitoramento: SADT/SAD, prazos do dia 25, ocupação e revisão de prontuários sem peso inventado.
- Governança: inventário, relações, lacunas, regras e períodos financeiros.
- Gestão de Dados: validação, upload, mapeamento, prévia, confirmação e justificativas de demanda.

Upload aceita CSV, XLSX (primeira aba), Parquet e DBF autocontido sem campos memo. Escolha UTF-8, Latin-1 ou CP1252 para arquivos textuais/DBF. COMP, COMPETENCIA, MES_REF e DT_COMP são normalizados para competencia; preserve AAAA-MM. Colunas DBF truncadas podem ser mapeadas manualmente. Campos extras são bloqueados para evitar importação de identificadores; remova-os antes de enviar. O esquema completo está em `src/data_validation.py` e nos CSV de exemplo. Não envie bases individualizadas de pacientes.

Fluxo: upload → leitura → normalização → mapeamento → validação → prévia → confirmação → consolidação. Qualquer erro bloqueia o arquivo inteiro; alertas ficam visíveis. Na confirmação, competências coincidentes são substituídas explicitamente no conjunto selecionado. Metadados mantêm nomes originais e novos. Dados e auditoria de upload vivem apenas na sessão e são perdidos ao sair/reiniciar. Exporte resultados para preservá-los; este protótipo não tem banco persistente.

XLSX possui Resumo, Produção, Qualidade, Trimestre, Monitoramento, Qualidade dos Dados e Regras Contratuais. CSV exporta o resultado da competência. Valores ausentes permanecem vazios. XLSX neutraliza fórmulas textuais.

Justificativas não modificam a pontuação nem dispensam descontos automaticamente. O status informado no protótipo não equivale a aprovação institucional. Regras contratuais são alteradas em YAML com revisão de Git, escopo, vigências e testes. Filtros e mapeamentos são configurações não sensíveis disponíveis ao ADMIN.

## Arquitetura

`app.py` autentica antes de criar a navegação; cada página repete a proteção. `src/contract_registry.py` mantém inventário e verificação exata de contrato/unidade com SHA-256. A identidade extraída precisa de revisão humana; hash não verifica autenticidade jurídica. `contract_engine.py` seleciona por competência e escopo explicitamente representado, exclui regras substituídas/revogadas e rejeita sobreposição. Não usa data mais recente para revogar regras. Configurações separadas contêm indicadores, documentos, unidades e regras. `calculations.py` não embute metas. Importação e validação são independentes da interface.

A soma 20/10/30 é validada para o único ruleset demonstrativo. Ao inserir histórico validado, deve-se criar conjuntos por vigência e validar pesos do conjunto resolvido, sem somar múltiplas versões históricas. O protótipo não possui interface para ratificação documental nem persistência de alterações. Veja a árvore completa em [ARVORE.md](docs/ARVORE.md).

## GitHub e Streamlit Community Cloud

```bash
git init
git add .
git status
git commit -m "Implementa protótipo HDH Metas"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/hdh-metas.git
git push -u origin main
```

Antes de adicionar arquivos, verifique que secrets, uploads e dados pessoais não aparecem no `git status`. Crie o repositório vazio pelo site do GitHub. O workflow testa Python 3.12 e 3.13 em cada push/PR. Nenhum repositório remoto foi criado nesta entrega.

Em https://share.streamlit.io/, conecte sua conta GitHub, escolha o repositório, branch `main` e arquivo `app.py`. Nas configurações avançadas selecione Python 3.13 se disponível (3.12 também funciona) e cole o bloco TOML de autenticação no campo Secrets, com seu hash. Publique. Não publique o secrets no repositório. Instalação é feita a partir de `requirements.txt`. Se faltar configuração, a tela será bloqueada. Nenhum site foi publicado automaticamente nesta entrega.

## Segurança, LGPD e evolução para bases reais

Somente dados sintéticos agregados e não identificáveis são permitidos nesta versão. Não há campos de nome, CPF, CNS, telefone, endereço ou prontuário individual. HTTPS, gestão de credenciais, autorização granular, trilha persistente, política de retenção, backup e revisão institucional são necessários antes de qualquer uso com bases reais. Dados hospitalares agregados também exigem controle de acesso e atenção a pequenos grupos identificáveis.

Para evolução: disponibilize e audite os documentos; valide contrato/unidade, hash, páginas, escopo e datas; insira regras históricas com início/fim e status VALIDADA; descarte apenas os anexos expressamente substituídos; esclareça o 10º TA; preencha valores por período. Implemente validação por ruleset resolvido, persistência autorizada, governança e testes de migração antes de remover o modo demonstrativo. Integrações SIMAS/SES, CNES, SIA e SIH não foram implementadas; nenhuma conexão ou fonte real é alegada. Ocupação por clínica e vigência histórica de 4.286 consultas dependem de documentação. Verifique o pitch em [PITCH.md](docs/PITCH.md).
