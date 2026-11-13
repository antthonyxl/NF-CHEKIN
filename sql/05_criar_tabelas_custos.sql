-- NOVA BASE CUSTO-NF-ENTRADA — executar no BigQuery Studio UMA vez.
-- Substitua SEU-PROJETO-REAL pelo ID exato do projeto que já contém
-- controle_recebimento. Não altera entrada_auto_nf ou checkin.

-- Tabela de carregamento temporário lógico (persistente, recriada por sobrescrita de CSV).
-- Os seis campos são STRING para receber o CSV sem inferência de tipos.
CREATE TABLE IF NOT EXISTS `SEU-PROJETO-REAL.controle_recebimento.stg_custo_nf_entrada` (
  empresa STRING,
  cod_empresa STRING,
  nf STRING,
  serie STRING,
  quantidade STRING,
  custo_liquido STRING
);

-- Tabela definitiva, consolidada por código da loja + NF + série.
-- A quantidade pode ser fracionária; por isso usamos NUMERIC, não INT64.
CREATE TABLE IF NOT EXISTS `SEU-PROJETO-REAL.controle_recebimento.custo_nf_entrada` (
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
CLUSTER BY cod_empresa, nf;
