# Histórico de acesso — exclusivo do admin

A página **Administração**, no menu lateral, aparece somente após login com o usuário **admin** e perfil **ADMIN**. Diretoria/GESTOR não vê a página. A permissão também é verificada pelo leitor do histórico e ao abrir a página diretamente; ocultar o menu não é o único controle.

## O que é registrado

- Login confirmado pelo verificador bcrypt.
- Saída pelo botão **Sair**.
- Expiração detectada quando uma sessão com mais de uma hora volta a interagir com o aplicativo.

Campos: identificador aleatório do evento, data/hora UTC, usuário, perfil, tipo de evento e intervalo da sessão em segundos nas saídas/expirações. Na tela, datas são convertidas para Recife (UTC−3). A duração é o intervalo da sessão, não uma medida de tempo ativo no painel.

Nenhuma senha, hash de senha, IP, informação do navegador ou dado de paciente é gravado. Tentativas inválidas não entram neste histórico; não se grava o nome digitado por pessoas não autenticadas. Não há rastreamento automático de páginas. Fechar navegador ou perder conexão não comprova logout: o aplicativo não inventa esse evento. A expiração só é registrada quando detectada, não no instante em que o navegador foi fechado.

O registro começa nesta atualização; acessos antigos não são reconstruídos. Login é registrado uma vez na autenticação, e atualizações de tela não geram novos eventos de login. Se houver falha na gravação, o acesso/saída não fica bloqueado: a falha é registrada sem credenciais no log técnico, e o login exibe aviso ao usuário quando possível. O histórico não é uma trilha de segurança completa nem um registro inviolável.

## Consulta

Abra **Administração → Histórico de acessos**. Filtre período, usuário e tipo de evento. A tela apresenta totais, tabela e download CSV do recorte. **Baixar histórico completo JSON** permite guardar uma cópia de todos os eventos, também restrita ao admin.

## Armazenamento sem SQL

O arquivo padrão é `data/private/access_history.json`. Gravação usa bloqueio entre operações e substituição atômica do JSON, mantendo o mesmo mecanismo sem SQL da reestruturação. O histórico de acesso fica em arquivo separado, não entra no backup da reestruturação nem nos pacotes distribuídos, e não é versionado no Git.

Opcionalmente configure nos Secrets:

```toml
[access_history]
storage_path = "data/private/access_history.json"
```

Ou defina `ACCESS_HISTORY_PATH`. Nenhuma dependência nova foi adicionada. Preserve os Secrets de autenticação existentes.

No computador local, o arquivo persiste enquanto o disco for preservado. **No Streamlit Community Cloud, reinicializações/reconstruções podem apagar arquivos locais.** Baixe cópias periodicamente. A exportação JSON desta página é para preservação/consulta externa; não há importação do histórico de acesso pela interface nesta etapa. Não há gravação automática no GitHub nem promessa de armazenamento durável na nuvem.

Retenção e proteção das cópias devem ser definidas pelo responsável pela implantação. Esta versão não apaga eventos automaticamente. Não houve publicação nem alteração de serviços externos.
