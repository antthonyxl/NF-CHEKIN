# NF × CHECK-IN — terceira base de custos (BigQuery)

Esta atualização **mantém** as duas tabelas existentes, os KPIs atuais e o link `?visao=sem-checkin` somente com as lojas. O `app.py` é baseado no arquivo atualizado que você enviou em 13/11/2026, e não numa revisão anterior.

## Base recebida

`CUSTO-NF-ENTRADA.xlsx` possui as colunas: Empresa, COD_EMPRESA, NF, SERIE, Quantidade e Custo Liquido. A primeira carga contém **135.866 linhas**. O arquivo CSV entregue preserva todas as linhas e utiliza cabeçalhos padronizados:

`empresa,cod_empresa,nf,serie,quantidade,custo_liquido`

O valor e a quantidade vêm da própria nota fiscal, não do valor do CHECKIN. A quantidade **pode ser fracionária**.

Na carga original, uma chave `63 + 7369 + 1` tem duas linhas com custo e quantidade diferentes. Como a base é de totais por NF e não há informação para escolher uma versão, o MERGE **não importa essa chave**, e o SQL 07 permite revisar a divergência. As demais 135.864 chaves são importadas para a tabela principal.

## Criação e primeira carga no Google BigQuery

1. No BigQuery Studio, substitua `SEU-PROJETO-REAL` pelo ID do seu projeto e execute `sql/05_criar_tabelas_custos.sql` (só uma vez). O dataset `controle_recebimento` já deve existir.
2. Na tabela **`stg_custo_nf_entrada`**, use **Criar tabela → Fazer upload**, selecione **`carga_custo_nf_entrada.csv`**, formato CSV, delimitador `,`, **1 linha de cabeçalho ignorada**, codificação UTF-8, com esquema **de seis campos STRING** na mesma ordem do arquivo. Se a tabela já existir, escolha **Sobrescrever tabela** **apenas para stg**. Se o console não permitir ajustar esquema de tabela criada, use *criar tabela* com mesmo nome e esquema manual; não use detecção automática.
3. Execute `sql/06_acumular_custos_sem_duplicar.sql` no BigQuery Studio. É um MERGE por **código de loja + NF + série**, que atualiza custos de chaves existentes e insere novas, sem replicar reenvios.
4. Execute `sql/07_conferir_custos.sql`. Resultado previsto na primeira carga: **135.866** registros na stg e **135.864** na tabela principal (1 chave com duas versões conflitantes, ambas retidas na stg para conferência).
5. Atualize o app conforme o capítulo abaixo e faça o push dos arquivos de código (não do CSV operacional).

**Permissões:** a conta de serviço do Streamlit necessita de BigQuery Data Viewer para a nova tabela dentro do dataset. Se já é Data Viewer do dataset, não precisa criar outra conta de serviço. O Streamlit continua somente de leitura.

## Regra de conciliação

- Chave de busca: `COD_LOJA` da base Auto NF + `NUMERONF` normalizada, associadas a `COD_EMPRESA` + `NF` da base de custos.
- Não se usa o nome da loja para relacionar bases. A série está disponível na base de custo, mas não na Auto NF; se uma combinação **loja + NF** tiver duas séries diferentes, a nota terá custo **pendente**, sem atribuir valor arbitrário.
- Repetições idênticas são consolidadas; duplicações conflitantes são sinalizadas como **Múltiplos custos** (sem quantidade nem valor).
- Não são somados valores de notas repetidas da Auto NF mais de uma vez nos totais por loja.
- Notas sem correspondência de custo permanecem na matriz, com quantidade e custo `—`.
- A tabela **Sem check-in** recebe **Quantidade** e **Custo líquido** no resumo da loja e nas linhas das notas, com ordenação nos cabeçalhos e exportação CSV.
- O link compartilhável continua exibindo só as lojas de código `001` a `068` e começa com a ordenação por **Registros** decrescente. Os quatro KPIs atuais continuam com sua função e não foram modificados.

## Atualizar no VS Code

Substitua **`app.py`**, **`matriz.py`**, **`fonte_bigquery.py`**, **`consultas_bigquery.py`** e adicione **`custo_nf.py`**, além dos SQLs novos em `sql/`. Os arquivos antigos de conciliação, cadastro e `aquila_visual.py` ficam inalterados.

Dentro da pasta do projeto, com `.venv` ativado:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

Após validar e carregar a terceira tabela no BigQuery:

```powershell
git add app.py matriz.py fonte_bigquery.py consultas_bigquery.py custo_nf.py sql/05_criar_tabelas_custos.sql sql/06_acumular_custos_sem_duplicar.sql sql/07_conferir_custos.sql sql/08_reiniciar_custos_opcional.sql
git commit -m "Adiciona custo liquido e quantidade de NF sem checkin"
git push origin main
```

Não coloque `carga_custo_nf_entrada.csv`, XLSX, JSON de credenciais nem `.streamlit/secrets.toml` no GitHub; o arquivo CSV é fornecido separadamente para importar no BigQuery. A pasta compactada de atualização exclui o CSV e todos os segredos.

## Reiniciar histórico manualmente

Na emergência, para recomeçar a tabela de custos sem mudar o esquema, rode o comando **TRUNCATE** comentado em `sql/08_reiniciar_custos_opcional.sql` e, depois, faça o upload na stg e execute novamente 06. Isso exclui os custos históricos na tabela principal e exige operação intencional; não é parte do fluxo normal.

## Limitações

- A Auto NF não possui a série da nota, então séries coincidentes em uma mesma loja + NF sempre exigirão conferência.
- O arquivo de custos não informa data da nota. Se a mesma NF e série forem reutilizadas em outro período com valor diferente, o MERGE atualizará a chave antiga em vez de guardar as duas versões. Para um histórico de múltiplas emissões idênticas, precisaremos de um identificador adicional (por exemplo chave de acesso ou data de emissão).
- As credenciais e projeto real são necessários para testar a integração publicada; os testes feitos localmente não executam consultas na conta BigQuery.
