-- LEITURA SOMENTE. NÃO MODIFICA NENHUM REGISTRO OU TABELA.
-- SUBSTITUA SEU-PROJETO-REAL pelo ID exato do Google Cloud.
-- Execute os blocos e confira campos, tipos e contagem de linhas.

-- 1) Todas as colunas reais das duas tabelas
SELECT table_name, ordinal_position, column_name, data_type
FROM `SEU-PROJETO-REAL.controle_recebimento.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN ('entrada_auto_nf', 'checkin')
ORDER BY table_name, ordinal_position;

-- 2) Quantidade de linhas já carregadas (a primeira carga deveria
-- ter 16.106 e 184.977, respectivamente, se não houve filtros no upload)
SELECT 'entrada_auto_nf' AS tabela, COUNT(*) AS linhas
FROM `SEU-PROJETO-REAL.controle_recebimento.entrada_auto_nf`
UNION ALL
SELECT 'checkin' AS tabela, COUNT(*) AS linhas
FROM `SEU-PROJETO-REAL.controle_recebimento.checkin`;

-- 3) Verificação dos campos de histórico necessários para o MERGE
-- Se aparecer FALTANDO, ainda NÃO execute 03_acumular_sem_duplicar.sql
SELECT table_name,
       COUNTIF(column_name = 'id_registro') > 0 AS tem_id_registro,
       COUNTIF(column_name = 'criado_em') > 0 AS tem_criado_em,
       COUNTIF(column_name = 'atualizado_em') > 0 AS tem_atualizado_em
FROM `SEU-PROJETO-REAL.controle_recebimento.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN ('entrada_auto_nf', 'checkin')
GROUP BY table_name
ORDER BY table_name;
