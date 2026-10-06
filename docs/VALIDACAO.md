# Validação da atualização documental e SIH

- Python local 3.12.14: **53 testes passaram** (`pytest`), incluindo faixas financeiras, versões, 20/10/30 por conjunto, inventário e hashes, exclusão de documentos de outras unidades, ausência de dados e divergências reais.
- AppTest: login, logout, configuração ausente, limitação de tentativas e **cinco áreas** renderizadas; todas bloqueadas sem sessão autenticada.
- CSV, XLSX, Parquet e DBF em UTF-8, Latin-1 e CP1252 exercitados pelos testes de leitura/validação.
- SIH: identidade CNES, 12 arquivos/11 conteúdos únicos, 79 competências no recorte, dezembro/2019 separado, decimais brasileiros, símbolos preservados e taxas anuais não aditivas testados.
- XLSX documental com sete abas validado por leitura posterior.
- `python -m compileall` nos arquivos do projeto: aprovado.
- `streamlit run app.py --server.headless true --server.port 8502`: iniciou e informou URL local, sem erro de inicialização.

Python 3.13 é executado pelo GitHub Actions. A criação/configuração do aplicativo no Streamlit Community Cloud é realizada pelo proprietário da conta. Upload via navegador não automatizado; leitores, validação e interface foram exercitados. Conferência visual no navegador e homologação institucional permanecem recomendadas. Validação do software não equivale a validação jurídica definitiva das regras ou de todas as células OCR.
