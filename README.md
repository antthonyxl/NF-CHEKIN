# Conciliação NF × CHECKIN — Streamlit

Painel operacional com a identidade visual do módulo `aquila_visual.py` fornecido.

## Rodar localmente (PowerShell / Windows)

```powershell
cd "caminho\conciliacao_nf_streamlit"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Caso a política de execução do PowerShell impeça a ativação, utilize diretamente
` .\.venv\Scripts\python.exe -m streamlit run app.py ` (sem necessidade de ativar).

Na barra lateral, faça upload de **ENTRADA AUTO NF LOJAS.xlsx** e **CHECKIN.xlsx**.
Alternativamente, coloque ambos na pasta `data/` (não versionada) e reinicie o app.

## O que o painel faz

- Compara `ENTRADA AUTO NF.NUMERONF` com `CHECKIN.Nota`, removendo apenas o último
  hífen e os dígitos seguintes da nota no CHECKIN (`75137-1` → `75137`).
- Usa **código da unidade + NF** para evitar relacionar notas de lojas diferentes.
  Assim, `001-CARPINA` corresponde a `NOVO - 01 - Carpina Centro`; `998-CD` corresponde
  a `998 - CD FLV / PER`, independentemente das descrições.
- Exibe **duas matrizes expansíveis por loja**, com paginação de 75 notas dentro
  da unidade; usa JavaScript local leve para abrir/paginar/ordenar as linhas.
- **Ordenação por clique nos cabeçalhos** das matrizes: Loja/unidade, Registros,
  NFs únicas, Valor localizado e Múltiplos (na matriz com check-in). Os cabeçalhos
  das notas expandidas também podem ser ordenados. Cada clique alterna entre
  maior→menor e menor→maior; um indicador ▲/▼ mostra a direção ativa.
  A ordenação numérica e por data é real (não alfabética); células sem valor ficam
  por último. A paginação é aplicada **após** a ordenação, para contemplar todas
  as NFs da loja. Não altera cálculos, correspondências ou arquivos exportados.
- **Filtros Regional e Distrital:** usam o arquivo `classificacao_unidades.csv` do projeto.
  O distrital acompanha as regionais escolhidas; lojas e CDs ausentes no cadastro
  aparecem como `NÃO CLASSIFICADO`. Não afeta o cálculo das NFs ou dos KPIs.
- **Com check-in:** número do check-in, status, fornecedor e valor encontrado.
- **Sem check-in:** as linhas do Auto NF que não têm correspondência nos dados fornecidos.
- **Revisão:** casos com mais de um registro do CHECKIN na mesma loja + NF.
  Esses casos têm correspondência, mas **não recebem valor arbitrário**.
- Preserva a quantidade original de linhas da ENTRADA AUTO NF e oferece CSV para baixar.
- Os valores apresentados como total financeiro contabilizam uma única vez cada NF por loja,
  e deixam as notas ambíguas de fora para evitar dupla contagem.

## Estrutura

- `app.py`: interface, uploads, filtros, KPIs e downloads.
- `classificacao.py`: classificação por nome da unidade e filtro Regional/Distrital.
- `classificacao_unidades.csv`: cadastro fornecido para Regionais e Distritais.
- `conciliacao.py`: regra de normalização, análise de duplicidades e junção segura.
- `matriz.py`: visualização hierárquica expansível.
- `aquila_visual.py`: estilos da referência do usuário (claro/escuro).
- `leitura_xlsx.py`: leitura incremental do CHECKIN de grande porte (somente colunas necessárias).
- `VALIDACAO_DAS_BASES.md`: resultado da análise real dos arquivos enviados.
- `tests/test_conciliacao.py`: testes de conciliação.
- `tests/test_matriz.py`: testes de geração das matrizes ordenáveis.
- `tests/test_classificacao.py`: testes dos filtros e de preservação das linhas.

## Observações sobre os dados

**Sem check-in** significa sem correspondência na base CHECKIN carregada: não é prova
formal de que nenhuma etapa de recebimento tenha ocorrido em outro período ou sistema.

Quando a mesma loja tem duas linhas para a mesma NF no CHECKIN, a chave solicitada é
insuficiente para identificar qual registro representa a NF do Auto. Em vez de escolher
um valor financeiro errado, o painel sinaliza a situação como **Múltiplos check-ins**.

A coluna `NFECHAVEACESSO` da base Auto foi gravada pelo Excel em notação científica.
Isso pode acarretar perda de dígitos. Por esse motivo, **não é usada como chave** nesta
versão. O número da NF e o código da loja são a referência indicada na solicitação.

Arquivos `data/*.xlsx` estão no `.gitignore` para evitar publicar as bases em repositórios.

## Testes

```powershell
python -m unittest discover -s tests -v
```
