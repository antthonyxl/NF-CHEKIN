# Integração NF × CHECK-IN com BigQuery

Este pacote mantém a aparência e a conciliação da versão aprovada, incluindo as duas matrizes, ordenação, paginação e filtros Regional/Distrital. A mudança é somente a origem dos dados: BigQuery, com opção de carregar Excel para validação local.

## 1. Antes de mexer nas tabelas existentes: verificação obrigatória

Você já carregou `checkin` e `entrada_auto_nf` DIRETAMENTE no dataset `controle_recebimento`. Isso pode ter criado tabelas com apenas as colunas do CSV. Os SQLs anteriores, por outro lado, esperam campos adicionais `id_registro`, `criado_em` e `atualizado_em` nas tabelas permanentes.

**Colocar arquivos `.sql` na pasta `sql/` do VS Code não os executa no BigQuery.**

1. Abra `sql/04_diagnostico_apos_upload_direto.sql`.
2. Substitua `SEU-PROJETO-REAL` pelo ID real do projeto em todas as ocorrências.
3. Cole e execute no editor SQL do BigQuery.
4. Confirme nomes e tipos de colunas; conte as linhas e verifique a existência dos três campos técnicos.

**Não execute `03_acumular_sem_duplicar.sql` enquanto os campos técnicos não estiverem presentes.** Também não execute `CREATE OR REPLACE TABLE`, `DROP TABLE` ou cargas em modo sobrescrever nas tabelas principais para tentar consertar o esquema sem backup.

Se as tabelas foram criadas diretamente pelo upload, será necessária uma migração única e cuidadosa para permitir o MERGE sem perder a carga já existente. A leitura pelo Streamlit **não depende** desses três campos técnicos, então pode ser configurada desde já.

## 2. Ativar APIs e configurar conta de serviço para leitura

No Google Cloud, com projeto selecionado:

- Ative a **BigQuery API** se ainda não estiver ativa.
- Crie uma conta de serviço, exemplo `streamlit-nf-leitura`.
- Conceda **BigQuery Job User** no projeto (permissão para executar consultas) e **BigQuery Data Viewer** no dataset `controle_recebimento` (leitura da base).
- Não conceda permissão de editor/administrador à identidade que serve o BI.

Se usar autenticação local do Google Cloud CLI:

```powershell
gcloud auth application-default login
```

Se sua organização permitir chaves JSON de serviço, armazene-as **somente** em Secrets, nunca em arquivo versionado. Contas corporativas podem proibir a criação de chaves; siga a política da equipe de segurança.

## 3. Configuração no VS Code

Na pasta raiz do projeto, crie `.streamlit/secrets.toml` a partir do exemplo `.streamlit/secrets.toml.example`:

```toml
[bigquery]
project_id = "ID-REAL-DO-PROJETO"
dataset = "controle_recebimento"
location = "southamerica-east1"
```

- Para **Windows com gcloud/ADC** previamente configurado: essas linhas bastam; a biblioteca usará as credenciais da sua sessão.
- Para **Streamlit Community Cloud**: além dessas linhas, adicione a seção `[gcp_service_account]` com o conteúdo de cada campo do JSON da conta de serviço, mantendo a formatação TOML (modelo comentado no `.example`). Cole o mesmo conteúdo nos **Secrets** do aplicativo Streamlit Cloud. Não compartilhe a chave em prints, chat ou repositório Git.

**A localização deve coincidir com a região real do dataset.** Se o dataset não foi criado em São Paulo, altere esse campo.

## 4. Dependências e execução

No PowerShell do VS Code, com seu `.venv` ativado:

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

Na lateral, selecione **BigQuery** em *Fonte de dados*. A leitura usa as colunas existentes em cada tabela, converte os tipos para texto e entrega o mesmo contrato de dados à conciliação original. Os dados são atualizados automaticamente após 10 minutos ou com o botão **Atualizar dados agora**.

Se quiser comparar com Excel local sem modificar o banco, selecione *Arquivos Excel*.

## 5. Como serão as próximas cargas

**Atenção: não use `APPEND` diretamente nas tabelas `entrada_auto_nf` e `checkin`, pois isso pode duplicar linhas e inflar a aba de múltiplos check-ins.**

Depois da migração para o modelo com `id_registro`, o ciclo padrão será:

1. Converter os XLSX para CSV com `preparar_csv.py` do pacote inicial;
2. Fazer upload dos CSVs nas tabelas `stg_entrada_auto_nf` e `stg_checkin` usando **sobrescrever**, ignorando o cabeçalho;
3. Executar `03_acumular_sem_duplicar.sql` (projeto real no SQL), que faz MERGE das staging para as permanentes;
4. Abrir o Streamlit e clicar em **Atualizar dados agora**.

Se precisar **zerar o histórico**, faça antes backup e substitua as tabelas permanentes em carga controlada, preservando o esquema exigido pelo MERGE; a substituição direta por CSV pode remover os campos técnicos.

## 6. Validação local

- Testes de código: `python -m unittest discover -s tests -v`.
- Teste da leitura com CSV equivalente aos arquivos originais: Auto NF 16.106 registros; CHECKIN 184.977; total de 2.167 localizações contando 59 linhas ambíguas; valor único não ambíguo R$ 24.520.649,14.

Esses números referem-se **aos CSVs fornecidos**, não à leitura real do seu projeto Google Cloud, que depende de suas credenciais/permissões e do esquema efetivo após o upload.
