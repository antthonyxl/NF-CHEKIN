-- Execute SOMENTE DEPOIS de carregar os dois CSVs nas respectivas tabelas stg_.
-- Os arquivos stg_ devem receber sobrescrita (WRITE_TRUNCATE), nunca APPEND.
-- Substitua bi-conciliacao-nf pelo ID real do projeto.
-- NFs repetidas da mesma loja mas de ORIGENS diferentes NÃO são unificadas.

-- AUTO NF: identidade = codigo de loja + empresa origem + numero NF + data emissao.
-- Não utilizar nfechaveacesso na identidade: o Excel original já traz esse valor
-- em notação científica, com precisão insuficiente para recuperar os 44 dígitos.
MERGE `bi-conciliacao-nf.controle_recebimento.entrada_auto_nf` AS T
USING (
  SELECT * EXCEPT(ordem)
  FROM (
    SELECT r.*,
           ROW_NUMBER() OVER (
             PARTITION BY r.id_registro
             ORDER BY r.dtaentrada DESC, r.nro_dias DESC
           ) AS ordem
    FROM (
      SELECT
        TO_HEX(SHA256(TO_JSON_STRING(STRUCT(
          COALESCE(
            CAST(SAFE_CAST(REGEXP_EXTRACT(empresa, r'^\s*(\d{1,3})\s*-') AS INT64) AS STRING),
            UPPER(TRIM(empresa))
          ) AS loja,
          TRIM(nroemp_origem) AS origem,
          COALESCE(NULLIF(REGEXP_REPLACE(REGEXP_REPLACE(TRIM(numeronf), r'\.0+$', ''), r'^0+', ''), ''), '0') AS nf,
          TRIM(dtaemissao) AS emissao
        )))) AS id_registro,
        empresa, nroemp_origem, numeronf, nfechaveacesso, codgeraloper,
        dtaemissao, dtaentrada, nro_dias
      FROM `bi-conciliacao-nf.controle_recebimento.stg_entrada_auto_nf`
      WHERE NULLIF(TRIM(empresa), '') IS NOT NULL
        AND NULLIF(TRIM(nroemp_origem), '') IS NOT NULL
        AND NULLIF(TRIM(numeronf), '') IS NOT NULL
        AND NULLIF(TRIM(dtaemissao), '') IS NOT NULL
    ) AS r
  )
  WHERE ordem = 1
) AS S
ON T.id_registro = S.id_registro
WHEN MATCHED THEN UPDATE SET
  empresa = S.empresa,
  nroemp_origem = S.nroemp_origem,
  numeronf = S.numeronf,
  nfechaveacesso = S.nfechaveacesso,
  codgeraloper = S.codgeraloper,
  dtaemissao = S.dtaemissao,
  dtaentrada = S.dtaentrada,
  nro_dias = S.nro_dias,
  atualizado_em = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (
  id_registro, empresa, nroemp_origem, numeronf, nfechaveacesso,
  codgeraloper, dtaemissao, dtaentrada, nro_dias, criado_em, atualizado_em
) VALUES (
  S.id_registro, S.empresa, S.nroemp_origem, S.numeronf, S.nfechaveacesso,
  S.codgeraloper, S.dtaemissao, S.dtaentrada, S.nro_dias,
  CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
);

-- CHECKIN: identidade = chave de acesso NF-e (44 digitos) + numero check-in.
-- O campo Check-In sozinho NÃO identifica uma NF: um recebimento pode ter
-- diversas notas. A Chave isolada também não basta: pode haver recheck-in.
MERGE `bi-conciliacao-nf.controle_recebimento.checkin` AS T
USING (
  SELECT * EXCEPT(ordem)
  FROM (
    SELECT r.*,
           ROW_NUMBER() OVER (
             PARTITION BY r.id_registro
             ORDER BY r.data DESC, r.entrada DESC
           ) AS ordem
    FROM (
      SELECT
        TO_HEX(SHA256(TO_JSON_STRING(STRUCT(
          TRIM(chave) AS chave,
          TRIM(check_in) AS check_in
        )))) AS id_registro,
        data, entrada, loja, nota, fornecedor, valor,
        status_nf, check_in, status_check_in, chave
      FROM `bi-conciliacao-nf.controle_recebimento.stg_checkin`
      WHERE REGEXP_CONTAINS(TRIM(chave), r'^\d{44}$')
        AND NULLIF(TRIM(check_in), '') IS NOT NULL
    ) AS r
  )
  WHERE ordem = 1
) AS S
ON T.id_registro = S.id_registro
WHEN MATCHED THEN UPDATE SET
  data = S.data,
  entrada = S.entrada,
  loja = S.loja,
  nota = S.nota,
  fornecedor = S.fornecedor,
  valor = S.valor,
  status_nf = S.status_nf,
  check_in = S.check_in,
  status_check_in = S.status_check_in,
  chave = S.chave,
  atualizado_em = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (
  id_registro, data, entrada, loja, nota, fornecedor, valor,
  status_nf, check_in, status_check_in, chave, criado_em, atualizado_em
) VALUES (
  S.id_registro, S.data, S.entrada, S.loja, S.nota, S.fornecedor, S.valor,
  S.status_nf, S.check_in, S.status_check_in, S.chave,
  CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
);

-- Consulta de conferência. Na primeira execução com os arquivos enviados,
-- espera-se 16.106 registros Auto e 184.977 registros CHECKIN.
SELECT 'entrada_auto_nf' AS tabela, COUNT(*) AS registros,
       COUNT(DISTINCT id_registro) AS ids_distintos
FROM `bi-conciliacao-nf.controle_recebimento.entrada_auto_nf`
UNION ALL
SELECT 'checkin' AS tabela, COUNT(*) AS registros,
       COUNT(DISTINCT id_registro) AS ids_distintos
FROM `bi-conciliacao-nf.controle_recebimento.checkin`;
