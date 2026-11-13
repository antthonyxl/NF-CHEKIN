-- NF x CHECK-IN | SQL 06 V3 - compatível com BigQuery Sandbox
-- Consolida o CSV já importado em stg_custo_nf_entrada, sem MERGE/DML.
-- Corrige: TRIM em campos numéricos e agregação dentro de agregação no HAVING.
-- IMPORTANTE: substitua SEU-PROJETO-REAL em TODAS as referências.
-- Execute o SCRIPT INTEIRO (não selecione linhas isoladas).
-- A primeira instrução prepara a consolidação antes de substituir a tabela final.
-- Registros já presentes na tabela definitiva são preservados quando não
-- aparecem na nova carga; para chaves válidas da carga, o custo novo prevalece.

CREATE TEMP TABLE custos_consolidados AS
WITH normalizados AS (
  SELECT
    TRIM(CAST(empresa AS STRING)) AS empresa,
    CAST(SAFE_CAST(TRIM(CAST(cod_empresa AS STRING)) AS INT64) AS STRING) AS cod_empresa,
    COALESCE(NULLIF(LTRIM(REGEXP_REPLACE(TRIM(CAST(nf AS STRING)), r'\.0+$', ''), '0'), ''), '0') AS nf,
    COALESCE(NULLIF(LTRIM(REGEXP_REPLACE(TRIM(CAST(serie AS STRING)), r'\.0+$', ''), '0'), ''), '0') AS serie,
    SAFE_CAST(REPLACE(TRIM(CAST(quantidade AS STRING)), ',', '.') AS NUMERIC) AS quantidade,
    SAFE_CAST(REPLACE(TRIM(CAST(custo_liquido AS STRING)), ',', '.') AS NUMERIC) AS custo_liquido
  FROM `SEU-PROJETO-REAL.controle_recebimento.stg_custo_nf_entrada`
),
validos AS (
  SELECT *
  FROM normalizados
  WHERE cod_empresa IS NOT NULL
    AND REGEXP_CONTAINS(nf, r'^\d+$')
    AND REGEXP_CONTAINS(serie, r'^\d+$')
    AND quantidade IS NOT NULL
    AND custo_liquido IS NOT NULL
),
-- Primeiro calculamos a quantidade de versoes distintas de cada NF.
-- Fazemos isso em CTE separada, sem referenciar aliases de MIN() em HAVING.
variacoes AS (
  SELECT
    cod_empresa, nf, serie,
    COUNT(DISTINCT TO_JSON_STRING(STRUCT(quantidade, custo_liquido))) AS qtd_versoes
  FROM validos
  GROUP BY cod_empresa, nf, serie
),
-- Importamos somente NFs com UMA versao de quantidade e custo.
-- Repeticoes identicas viram um unico registro.
consistentes AS (
  SELECT
    MIN(v.empresa) AS empresa,
    v.cod_empresa, v.nf, v.serie,
    MIN(v.quantidade) AS quantidade,
    MIN(v.custo_liquido) AS custo_liquido
  FROM validos AS v
  JOIN variacoes AS vr
    ON vr.cod_empresa = v.cod_empresa AND vr.nf = v.nf AND vr.serie = v.serie
  WHERE vr.qtd_versoes = 1
  GROUP BY v.cod_empresa, v.nf, v.serie
),
novos AS (
  SELECT
    TO_HEX(SHA256(TO_JSON_STRING(STRUCT(cod_empresa, nf, serie)))) AS id_registro,
    empresa, cod_empresa, nf, serie, quantidade, custo_liquido
  FROM consistentes
),
versoes AS (
  SELECT
    1 AS prioridade,
    n.id_registro, n.empresa, n.cod_empresa, n.nf, n.serie,
    n.quantidade, n.custo_liquido,
    COALESCE(a.criado_em, CURRENT_TIMESTAMP()) AS criado_em,
    CASE
      WHEN a.id_registro IS NULL
        OR a.empresa IS DISTINCT FROM n.empresa
        OR a.quantidade IS DISTINCT FROM n.quantidade
        OR a.custo_liquido IS DISTINCT FROM n.custo_liquido
      THEN CURRENT_TIMESTAMP()
      ELSE a.atualizado_em
    END AS atualizado_em
  FROM novos AS n
  LEFT JOIN `SEU-PROJETO-REAL.controle_recebimento.custo_nf_entrada` AS a
    ON a.id_registro = n.id_registro

  UNION ALL

  SELECT
    2 AS prioridade,
    id_registro, empresa, cod_empresa, nf, serie,
    quantidade, custo_liquido, criado_em, atualizado_em
  FROM `SEU-PROJETO-REAL.controle_recebimento.custo_nf_entrada`
)
SELECT * EXCEPT(prioridade)
FROM versoes
QUALIFY ROW_NUMBER() OVER (PARTITION BY id_registro ORDER BY prioridade) = 1;

-- A tabela definitiva só é substituída depois que o preparo acima funciona.
CREATE OR REPLACE TABLE `SEU-PROJETO-REAL.controle_recebimento.custo_nf_entrada` (
  id_registro STRING NOT NULL,
  empresa STRING,
  cod_empresa STRING,
  nf STRING,
  serie STRING,
  quantidade NUMERIC,
  custo_liquido NUMERIC,
  criado_em TIMESTAMP,
  atualizado_em TIMESTAMP
)
CLUSTER BY cod_empresa, nf
AS SELECT
  id_registro, empresa, cod_empresa, nf, serie,
  quantidade, custo_liquido, criado_em, atualizado_em
FROM custos_consolidados;

SELECT
  COUNT(*) AS linhas_tabela_final,
  COUNT(DISTINCT id_registro) AS chaves_unicas
FROM `SEU-PROJETO-REAL.controle_recebimento.custo_nf_entrada`;
