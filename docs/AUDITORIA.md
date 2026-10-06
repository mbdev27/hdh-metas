# Auditoria documental — corpus recebido

Foram recebidos **65 PDFs**. O inventário contém 67 entradas: os 65 arquivos e os registros de ausência do 1º e do 10º Termos Aditivos. Há **60 PDFs únicos do HDH** na biblioteca: referências institucionais, instrumentos e pareceres. O hash identifica igualdade de arquivos; não certifica autenticidade jurídica.

## Método e limites

Leitura das páginas, extração textual, OCR dos documentos digitalizados e das tabelas incorporadas como imagens; conferência das linhas anuais de produção e das tabelas de janeiro–março/2026. Identificação pelo cabeçalho e pelo objeto, não pelo nome do arquivo. Datas de assinatura são distintas de datas de impressão SEI. Campos não comprovados permanecem nulos. O texto OCR é auxiliar: o PDF original prevalece.

O inventário completo está em `config/contract_documents.yaml`; documentos aceitos em `documents/`. Cada registro preserva nome original, contrato, unidade, número efetivamente identificado, objeto, escopo, assinatura, relação com outros instrumentos, processo SEI, observações, páginas e SHA-256. Os documentos de outra unidade são registrados na auditoria, mas seus PDFs e seus dados não são incorporados à biblioteca HDH.

## Identidade, duplicidades e divergências

| Arquivo / registro | Achado | Tratamento |
|---|---|---|
| DOC021 e DOC022, chamados rerratificação do 5º TA | Conteúdo: 8º TA da UPA Igarassu, CG002/2022; arquivos idênticos | Excluídos. Não constituem rerratificação HDH |
| DOC052, chamado 4º trimestre HDH/2023 | Conteúdo: UPA Imbiribeira, CG003/2021 | Excluído. Histórico do HDH/2023 obtido do anual |
| DOC011 e DOC012 | Apostilamentos idênticos por SHA-256 | Um PDF; duas entradas de auditoria |
| DOC046 e DOC047 | Mesmo parecer 3º tri/2022; segundo nome diz 4º tri | Um PDF; quarto trimestre obtido do anual/2022 |
| DOC035 | Nome diz 4º tri/2020; cabeçalho identifica 4º tri/2019 | Biblioteca classificada pelo período interno; série mensal começa em 2020 |
| DOC033 | Nome diz 12º TA; é rerratificação do 12º TA | Tipo corrigido pelo conteúdo |
| DOC034 | Nome genérico SEI | Identificado como 12º TA |
| DOC062 | Recorte sem cabeçalho e objeto, tabelas julho–setembro/2025 e referência final HDH/018 | Consulta disponível com validação pendente; não usado na série canônica |

Os pareceres de 2020, 2021 e janeiro–junho/2022 pertencem ao HDH sob o **Contrato 006/2010**. São referências históricas do hospital, separadas das regras do Contrato 018/2022. O contrato anterior não foi fornecido; suas metas são identificadas como referências secundárias da CMA.

## Lacunas

- **10º Termo Aditivo — DOCUMENTO NÃO DISPONÍVEL**, número 10, tipo Termo Aditivo. Conteúdo e eventual alteração de metas não presumidos.
- 1º TA não fornecido; nenhum conteúdo reconstruído.
- Rerratificação HDH do 5º TA não localizada: os arquivos com esse nome são de outra unidade. Isso não comprova existência ou inexistência de outro instrumento.
- Os pareceres trimestrais específicos de 4º tri/2020, 4º tri/2022 e 4º tri/2023 não foram obtidos como documentos próprios corretos. Os anuais fornecem os meses dessas séries.
- Denominadores de satisfação e outras evidências não constam das matrizes transcritas; não são inventados.
- Matrizes qualitativas anuais digitalizadas de 2021 permanecem consultáveis no PDF; seus resultados mensais não foram integralmente estruturados como série numérica.

## Mapa de alterações

Contrato original DOC003 → metas originais. Aditivos 2, 4, 6 e 9 alteram custeio/rateio/serviço. Aditivos 3, 5, 7, 11, 12 e 15 tratam de investimentos; apostilamentos têm seus próprios escopos. O 13º TA inclui dez leitos UTI; o 14º amplia recursos humanos da emergência. A rerratificação do 12º modifica prazos e comprovação do investimento, não as faixas dos indicadores. O 16º altera condições de pagamento e exige estudo de habilitações; o 17º trata de provisionamento e sua rerratificação corrige referência de cláusula. O 18º prorroga a vigência e informa valor mensal.

**8º TA DOC019 → Rerratificação DOC017 → anexos rerratificados**: substituição expressa na cláusula 1.1. Apenas o escopo dos anexos é substituído; as demais regras têm sua própria cadeia. A assinatura final da rerratificação é de 15/07/2024; não se presume retroatividade. Os valores quantitativos coincidem nos dois conjuntos. Julho/2024 é marcado como transição intramensal.

## Regras e vigências de referência

| Conjunto | Intervalo identificado | Produção valorada |
|---|---|---|
| Contrato original 018/2022 | 01/07/2022–30/06/2024 | Saídas 856; urgência 2.826; consultas médicas 4.286; cirurgia total 688. Quatro pesos de 5 p.p. |
| 8º TA — histórico | 01/07/2024–14/07/2024 | Nove metas, anexos posteriormente substituídos |
| Rerratificação do 8º TA | Referência a partir da última assinatura de 15/07/2024 | 856; 2.826; 2.520; 4.730; 120; 136; 260; 20; 152. Pesos 3/3/3/1/2/2/2/2/2 p.p. |

O motor mantém o original e o 8º TA para consulta histórica; a rerratificação é a **regra mais recente identificada no corpus disponível**. O campo VALIDADA registra conferência do conteúdo, não certeza jurídica definitiva. `status_cadeia` registra a necessidade de validar documentos ausentes. As versões original, TA08 e RERR08 totalizam 20 p.p. quantitativos e 10 p.p. qualitativos, separadamente. Metas históricas qualitativas mantêm significados próprios; não são rebatizadas como indicadores novos nem pontuadas pela tabela atual.

A regra física é 100%; 85% é faixa financeira. Cirurgia total original não é cirurgia genérica. Artroplastia não é presumida subconjunto matemático para valoração. Produções por grupos distintos não são somadas para medir pontuação.

## Séries reais e qualidade dos dados

`data/real/producao.csv`: **435 observações, 75 competências**, janeiro/2020–março/2026. Pareceres anuais são a fonte canônica de 2020–2025, evitando soma dos mesmos meses nos trimestrais; 2026 usa o parecer do primeiro trimestre. Contrato, documento e página acompanham cada observação. CSV qualitativo: **762 observações** de matrizes estruturáveis, mantendo resultado textual, valor, meta publicada e situação. Não há integração direta com SIMAS ou prontuários.

- Artroplastias: “Análise impossibilitada” permanece ausente, mesmo quando a tabela apresenta total zero.
- Annual/2024 DOC055: meta de consultas multiprofissionais de novembro/dezembro aparece como 2.520; anexo estabelece 4.730. Ambas são preservadas, divergência sinalizada; atingimento usa o anexo.
- Annual/2022 DOC045: soma tabular de urgências julho–dezembro = 18.485; texto narrativo cita 18.845. A série usa as linhas mensais, sem corrigir silenciosamente o texto.
- Classificação de risco com percentuais acima de 100% é conservada como inconsistência na fonte, sem pontuação automática. Execução da educação acima de 100% é alerta de produção superior ao planejado.
- Satisfação: índice publicado exibido; sem a conversão mínima comprovada, pontuação contratual não aferível.
- Ocupação por clínica é preservada em texto, sem fabricar média geral.
- Revisão de prontuários vermelho/amarelo: meta ≥10% na descrição rerratificada, sem peso próprio na súmula; **PENDENTE DE VALIDAÇÃO DOCUMENTAL**.

## Financeiro

O 18º TA DOC025 registra **01/07/2026–30/06/2028**, valor mensal **R$ 10.904.885,46**. Não se aplica aos resultados reais até março/2026. Valores anteriores publicados estão versionados como referências, com lacunas de término/composição; não são reconstruídos por inferência. O 16º TA DOC028 registra pagamento 70% até o quinto dia útil e 30% até dia 30, condicionado à prestação de informações. Isso é distinto dos pesos de avaliação 20%/10%.

Todos os resultados financeiros são projeções. Ausência de demanda e justificativas não suspendem descontos automaticamente. Esta auditoria técnica/documental não substitui validação jurídica e institucional.

## Corpus adicional SIH/SUS — 06/10/2026

Recebidos 12 CSVs TabNet, identidade CNES 6559379 HOSPITAL DOM HELDER CAMARA. A origem e a data de extração foram informadas pelo solicitante: Ministério da Saúde — DATASUS/TabNet, https://tabnet.datasus.gov.br/, 06/10/2026. Hashes e títulos preservados em `config/sih_sources.json`.

São 11 conteúdos únicos, 6.319 células normalizadas, incluindo meses, anos e totais originais. Há nove medidas em onze tabulações: AIHs aprovadas por três dimensões (caráter, grupo e subgrupo), valor total, serviços hospitalares, serviços profissionais, valor médio de internação, dias de permanência, média de permanência, óbitos e taxa de mortalidade. Nenhuma equivalência automática com indicadores pactuados foi aplicada.

- Os CSVs `181645` e `181656` de mortalidade são idênticos. Originais conservados, sem duplicar observações.
- Todos incluem dezembro/2019 apesar do período solicitado Jan/2020–Jul/2026. A página usa 79 meses no recorte solicitado; totais originais são distinguidos.
- Subtotais anuais e total geral são registros separados; nunca adicionados novamente aos meses.
- Taxas e médias anuais são as publicadas, quando correspondem ao ano disponível. Não se presume denominador de internações igual a AIHs.
- Símbolos de ausência e valores originais são mantidos; nenhum preenchimento automático com zero.
- O CSV informa que os dados dos últimos seis meses estão sujeitos a atualização.
