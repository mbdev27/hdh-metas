# HDH Metas

Painel de Monitoramento do Contrato de Gestão — Hospital Metropolitano Sul Dom Helder Câmara. **Protótipo demonstrativo para estudo de caso profissional de Sanitarista**, sem vínculo oficial com FGH, SES/PE ou Governo de Pernambuco.

O aplicativo reúne 60 PDFs únicos do HDH, metas por instrumento e dados assistenciais públicos agregados dos pareceres CMA. São 75 competências de produção, janeiro/2020–março/2026. Mantém separadamente o histórico do Contrato 006/2010 e as regras do Contrato 018/2022. A ausência do 10º TA e as demais inconsistências são visíveis. Consulte a [auditoria](docs/AUDITORIA.md) antes de interpretar os resultados.

## Testar diretamente na web

1. Abra https://share.streamlit.io/ e entre com sua conta GitHub.
2. Clique em **Create app / New app** e escolha implantação a partir do GitHub.
3. Repositório: `mbdev27/hdh-metas`; branch: `main`; arquivo principal: `app.py`.
4. Em **Advanced settings**, selecione Python 3.13, se disponível, ou 3.12.
5. Em **Secrets**, configure o bloco abaixo com o hash bcrypt gerado. Se o aplicativo já estiver publicado com credenciais, preserve seus Secrets: a atualização não exige alterar a senha.
6. Clique em **Deploy**. Abra a URL `.streamlit.app` informada pela plataforma e faça login.

```toml
[auth]
admin_username = "admin"
admin_password_hash = "COLE_AQUI_O_HASH_BCRYPT_GERADO"
```

Sem configuração válida, o acesso é bloqueado. A senha não fica no GitHub. Esta implantação é feita na conta do proprietário; atualizar o código do repositório não cria, por si só, um aplicativo no Streamlit Cloud.

## O que existe no painel

- **Tela inicial**: apresentação do hospital, especialidades, missão, visão, valores, endereço e contatos, com fontes SES/PE e FGH. Redação própria, identificação CNES e contatos institucionais.
- **Indicadores**: metas, realizado, diferença, alcance e pontuação quando aferível; séries mensais, trimestre, comparação anual e fundamentação. Aba de qualidade e monitoramento; metas por versão; gestão de uploads e cenário de simulação.
- **Instrumentos de gestão**: biblioteca com download dos PDFs originais, linha do tempo, mapa de alterações, metas instituídas por documento, inventário, lacunas e condições financeiras.
- **Produção Hospitalar**: dados SIH/SUS do CNES 6559379, janeiro/2020–julho/2026; AIHs por caráter, grupo e subgrupo, valores aprovados, permanência, óbitos e mortalidade; fonte TabNet e extração em 06/10/2026.
- **Pareceres CMA**: biblioteca por período, séries por mês e ano, tabelas, evidências e qualidade dos dados.

Login abre a Tela inicial. Todas as páginas são protegidas. Saída limpa a sessão. ADMIN administra os dados; GESTOR consulta e exporta resultados. O acesso GESTOR da diretoria é habilitado por Secrets; LEITURA permanece previsto para evolução. Cinco tentativas inválidas geram bloqueio de 30 segundos por sessão; sessão expira em uma hora. A proteção por sessão é básica: uso institucional necessita identidade e controles apropriados.

## Instalação local do zero — Windows

Instale [Python 3.13](https://www.python.org/downloads/) marcando **Add Python to PATH** e [Git](https://git-scm.com/downloads/). Abra PowerShell:

```powershell
git clone https://github.com/mbdev27/hdh-metas.git
cd hdh-metas
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/generate_password_hash.py
```

Se a ativação for bloqueada, use diretamente `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` e esse executável nos comandos seguintes. Não é necessário alterar a política do computador. Python 3.12 também funciona.

O script solicita a senha com entrada oculta e confirmação. Copie **somente o hash** para o Secrets do Streamlit Cloud ou, para teste local, crie `.streamlit/secrets.toml` a partir de `.streamlit/secrets.toml.example`. Nunca coloque a senha em comandos, commits, YAML ou logs. Também é possível definir `ADMIN_USERNAME` e `ADMIN_PASSWORD_HASH` como variáveis de ambiente. Não há fallback de senha.

```powershell
python -m streamlit run app.py
python -m pytest
python -m compileall .
```

Linux/macOS:

```bash
git clone https://github.com/mbdev27/hdh-metas.git
cd hdh-metas
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_password_hash.py
streamlit run app.py
pytest
```

## Origem e interpretação dos dados

O histórico documental é a fonte padrão. Cada observação conserva contrato, documento, página, resultado publicado e observações. Os PDFs são documentos recebidos do solicitante; dados assistenciais são agregados públicos. Os três arquivos de outras unidades não entram na biblioteca ou nos cálculos. Duplicidades são registradas por SHA-256 sem dupla contagem. Pareceres anuais de 2020–2025 são as fontes canônicas da produção; 2026 usa o 1º trimestre. Nem toda matriz digitalizada foi estruturada: o PDF continua disponível, e lacunas não viram números inventados.

As regras originais de 2022 e as do 8º TA são históricas. Os anexos rerratificados substituem expressamente os anexos do 8º TA e constituem a regra mais recente localizada no corpus, com validação da cadeia pendente pela ausência do 10º TA. Julho/2024 contém transição intramensal; não se presume retroatividade da assinatura de 15/07. A versão original tinha 4.286 consultas médicas; a rerratificada, 2.520. Cirurgia total e cirurgia genérica possuem definições distintas.

**Meta física = 100%. Faixa financeira máxima = a partir de 85%.** Cada versão possui 20 p.p. quantitativos e 10 p.p. qualitativos, sem somar versões históricas. O trimestre agrega metas e realizado por contrato e indicador; se faltar dado, o consolidado fica ausente. Ano parcial é identificado e não extrapolado. Taxas qualitativas anuais não são reconstruídas sem denominadores; satisfação não recebe pontuação contratual sem evidência da conversão mínima de 10%.

Valor mensal do 18º TA: R$ 10.904.885,46, somente julho/2026–junho/2028. Não utilizado retroativamente nos pareceres até março/2026. Valores anteriores são referências documentais com validação pendente. Pagamento 70%/30% do 16º TA é distinto da valoração 20%/10%. Cálculos financeiros sempre são **PROJEÇÃO FINANCEIRA**, nunca valor definitivo a pagar.

## Importação, validação e exportação

Em **Indicadores → Gestão de dados**, envie CSV, XLSX (primeira aba), Parquet ou DBF autocontido sem campos memo. Escolha UTF-8, Latin-1 ou CP1252. O fluxo apresenta leitura, normalização, mapeamento, validação, prévia e confirmação antes de consolidar. Aliases COMP, COMPETENCIA, MES_REF e DT_COMP são normalizados para `competencia`; use `AAAA-MM`. Nomes originais ficam nos metadados. Mapeie colunas DBF truncadas manualmente.

Campos extras são bloqueados. Arquivos com erro não são consolidados. Ausência é `NaN/None`, nunca zero. Negativos, contagens incompatíveis, percentuais inválidos, competências inválidas e duplicidades são registrados no relatório. Pesquisas maiores que atendimentos e educação acima do planejado são alertas; positivos maiores que respondidas ou óbitos revisados maiores que totais são erros.

Uploads e justificativas ficam **somente na sessão**, sem sobrescrever os dados documentais CMA. A substituição de competências na base da sessão exige confirmação explícita. Justificativa de ausência de demanda não altera pontuação nem dispensa desconto automaticamente. Exporte antes de sair para preservar o trabalho. Não há banco persistente.

CSV exporta séries e inventário. XLSX documental contém **Resumo, Produção, Qualidade, Trimestre, Monitoramento, Qualidade dos Dados e Regras Contratuais**. A base de simulação também pode ser exportada; ausências permanecem vazias. Textos que poderiam formar fórmulas são neutralizados no XLSX.

## Dados sintéticos

`data/mock/` mantém 24 competências, outubro/2024–setembro/2026, seed fixa. Cenários incluem falta de dados, baixo cumprimento, excesso de produção, atraso, glosas, amostra insuficiente e inconsistências. A área de gestão de dados mostra explicitamente **DADOS SIMULADOS / IMPORTADOS NA SESSÃO**; esses registros não são apresentados como históricos reais.

```bash
python scripts/generate_mock_data.py
```

## Arquitetura e manutenção

Veja a [árvore completa](docs/ARVORE.md). Documentos, definições de indicadores, regras e dados são separados. `src/contract_engine.py` resolve intervalos por data, preserva versões e valida pesos por ruleset; não presume que o documento mais novo revoga todos os escopos. `src/historical.py` mantém dados publicados e metas normativas separados, identifica divergências e consolida períodos sem extrapolação. `src/portal.py` apresenta as cinco áreas; autenticação antecede a navegação. Não há metas espalhadas nas funções de cálculo.

Para acrescentar documentos: conferir identidade e escopo, calcular SHA-256, registrar metadados, apontar páginas, identificar somente as substituições expressas e fechar intervalos quando houver fundamento. Antes de adicionar resultados, registrar a fonte e conferir células, sobretudo OCR. Revise regras e CSV com testes antes do commit. Dados `data/real/` são séries públicas transcritas, não acesso a sistemas hospitalares. OCR e extração foram procedimentos de auditoria offline; o Streamlit não exige Tesseract nem conexão externa para iniciar.

## GitHub e testes

No repositório do proprietário, atualize arquivos após revisar o status:

```bash
git status
git add app.py pages src config data/real documents docs tests README.md
git commit -m "Atualiza painel e corpus documental"
git push origin main
```

Nunca versione `.streamlit/secrets.toml`, `.env`, uploads ou dados pessoais. `.gitignore` inclui essas exclusões. O GitHub Actions testa Python 3.12 e 3.13, pytest e compileall. Os testes abrangem faixas, versões, pesos, hashes, exclusões, dados ausentes, consolidação, cinco áreas protegidas, login/logout, limitação de tentativas, formatos de importação e exportação. Consulte [validação](docs/VALIDACAO.md).

## Segurança e limites

Não inserir nomes, CPF, CNS, telefone ou prontuários individuais. Os dados reais incluídos são exclusivamente agregados públicos, com identificadores de pacientes ausentes. Uso institucional com bases internas depende de autorização, validação documental, avaliação LGPD, gestão de identidade, retenção, backups e trilha persistente. Pequenos grupos agregados também podem requerer proteção. Não há integração direta com SIMAS, CNES, SIA/SUS ou SIH/SUS; nenhuma sincronização automática é alegada.

O aplicativo apoia análise e não substitui decisão da Contratante, parecer jurídico ou conferência do documento original. O projeto mantém o [pitch profissional](docs/PITCH.md).

## Produção Hospitalar — SIH/SUS

12 CSVs recebidos, 11 conteúdos únicos. Dados do Ministério da Saúde — [DATASUS/TabNet](https://tabnet.datasus.gov.br/), extraídos pelo solicitante em **06/10/2026**. Os arquivos identificam **CNES 6559379 — HOSPITAL DOM HELDER CAMARA** e a dimensão **Ano/mês atendimento**, não mês de processamento. O recorte padrão tem **79 competências, janeiro/2020–julho/2026**.

As exportações trazem também dezembro/2019; esse mês é conservado nos originais, mas excluído do recorte padrão. Os totais originais podem incluí-lo. A exportação de mortalidade terminada em `181656` é cópia exata da terminada em `181645`: ambos os originais são preservados, uma série é utilizada. Totais e subtotais anuais não são somados aos meses. Taxas, médias de permanência e valores médios não são somados nem calculados por média simples; as comparações anuais usam valores anuais publicados quando o recorte corresponde ao ano disponível. 2026 é explicitamente parcial.

AIHs aprovadas não equivalem automaticamente a internações, saídas ou procedimentos contratuais. A taxa de mortalidade publicada não é recalculada usando AIHs como denominador presumido. Valores do SIH são distintos do valor mensal do contrato. Os símbolos `-`, `...` e campos vazios são conservados e não se tornam zero automaticamente. A nota da fonte informa que dados dos últimos seis meses estão sujeitos a atualização.

Originais: `data/sih/originais/`; observações normalizadas: `data/sih/observacoes.csv`; metadados e hashes: `config/sih_sources.json`. A página permite filtros, gráficos, tabelas e download dos originais e dos recortes em CSV/XLSX. Não existe consulta automática ao TabNet; a fonte é o conjunto de arquivos fornecido.

A interface utiliza resumos e tabelas gerenciais, sem blocos JSON, hashes ou estruturas internas. A fundamentação legal é referência interna e não aparece na biblioteca. PDFs são oferecidos para download, preservando sua apresentação original. Pareceres CMA também possuem visualização paginada dentro do painel, com preservação do layout original e alternativa de download se a prévia falhar. Erros técnicos ficam nos logs do servidor; mensagens do painel não mostram código nem traceback.

O usuário administrativo é `admin`. Configurações antigas com o nome `adm` são migradas automaticamente para `admin`, preservando o hash e a senha; o nome antigo não é aceito no login. A navegação lateral só fica visível após autenticação.

### Acesso da diretoria

O administrador continua usando `admin`. Para habilitar um segundo acesso com perfil GESTOR, gere outro hash com `python scripts/generate_password_hash.py`. No Streamlit Cloud, abra Settings → Secrets e acrescente `director_username = "diretoria"` e `director_password_hash = "HASH_GERADO"` ao bloco `[auth]` existente, preservando as chaves do administrador. Não crie outro bloco `[auth]`. O perfil GESTOR consulta painéis e documentos e exporta resultados; a gestão de dados permanece restrita ao ADMIN. Alternativamente, configure `DIRECTOR_USERNAME` e `DIRECTOR_PASSWORD_HASH` no ambiente. Sem essas chaves, apenas o administrador permanece habilitado.
