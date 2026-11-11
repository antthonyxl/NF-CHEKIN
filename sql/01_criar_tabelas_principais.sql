-- Executar no BigQuery Studio, APÓS criar o projeto e o dataset.
-- Substitua bi-conciliacao-nf abaixo pelo ID REAL do seu projeto Google Cloud.
-- Estas são as duas tabelas permanentes consultadas pelo dashboard.

CREATE TABLE IF NOT EXISTS `bi-conciliacao-nf.controle_recebimento.entrada_auto_nf` (
  id_registro STRING NOT NULL,
  empresa STRING,
  nroemp_origem STRING,
  numeronf STRING,
  nfechaveacesso STRING,
  codgeraloper STRING,
  dtaemissao STRING,
  dtaentrada STRING,
  nro_dias STRING,
  criado_em TIMESTAMP,
  atualizado_em TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `bi-conciliacao-nf.controle_recebimento.checkin` (
  id_registro STRING NOT NULL,
  data STRING,
  entrada STRING,
  loja STRING,
  nota STRING,
  fornecedor STRING,
  valor STRING,
  status_nf STRING,
  check_in STRING,
  status_check_in STRING,
  chave STRING,
  criado_em TIMESTAMP,
  atualizado_em TIMESTAMP
);
