# Atualização NF × CHECK-IN — desempenho, KPI e ordenação

Esta atualização foi construída sobre o pacote de integração de custos de 13/11/2026 (app.py de 14:29), que já contém a associação com a tabela `custo_nf_entrada`.

## Arquivos para substituir no projeto

Substitua estes cinco arquivos na raiz do projeto:

- `app.py`
- `matriz.py`
- `custo_nf.py`
- `fonte_bigquery.py`
- `consultas_bigquery.py`

Os dois arquivos de teste em `tests/` são opcionais para execução do dashboard, mas foram incluídos para validação.

## O que mudou

1. **Cache do processamento:** conciliação Auto NF × CHECK-IN, associação dos custos e classificação das unidades passam a ser armazenadas em cache por 10 minutos. Interações com filtros, abas e tabelas deixam de repetir esse processamento.
2. **Atualização manual:** o botão `Atualizar dados agora` limpa tanto o cache das consultas BigQuery quanto o cache do processamento completo.
3. **Menos dados transferidos:** a consulta de custos retorna somente as combinações de loja + NF presentes na tabela `entrada_auto_nf`, mantendo as séries e conflitos para validação no Python.
4. **KPI da apresentação:** somente no link `?visao=sem-checkin`, o último KPI passa a exibir a soma do `CUSTO_LIQUIDO` das notas sem check-in com custo localizado. Cada combinação `COD_LOJA + NF_NORMALIZADA` é contada uma única vez. O dashboard completo mantém o KPI `Valor localizado` baseado no CHECK-IN.
5. **Ordenação inicial:** a matriz da visão compartilhável abre pela coluna `Custo líquido`, do menor para o maior. Custos não localizados ficam no final. Os cabeçalhos continuam clicáveis para alternar a ordenação.

## Publicação

No PowerShell, na pasta do projeto:

```powershell
git add app.py matriz.py custo_nf.py fonte_bigquery.py consultas_bigquery.py
git commit -m "Otimiza carga e ajusta KPI e ranking de custos"
git push origin main
```

Não há alteração de schema nem necessidade de reenviar o CSV de custos ao BigQuery.

## Testes executados

```powershell
python -m unittest discover -s tests -v
```

Resultado nesta atualização: 20 testes aprovados.

## Sobre o tempo de inicialização

O cache melhora principalmente as reexecuções do Streamlit durante o uso, dentro da janela de 10 minutos. A consulta de custos também retorna menos linhas para o Python. O primeiro carregamento após iniciar o processo ainda depende da latência do BigQuery e da inicialização do Streamlit; por isso, não é possível garantir que o primeiro acesso no Community Cloud seja mais rápido que no localhost.
