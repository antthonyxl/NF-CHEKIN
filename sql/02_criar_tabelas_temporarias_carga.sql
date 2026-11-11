-- Estas tabelas são áreas técnicas de carga. Não substituem as duas tabelas principais.
-- Todo novo CSV entra primeiro na tabela stg_ correspondente (sobrescrevendo a carga anterior).
-- Substitua bi-conciliacao-nf abaixo pelo ID REAL do seu projeto.

CREATE TABLE IF NOT EXISTS `bi-conciliacao-nf.controle_recebimento.stg_entrada_auto_nf` (
  empresa STRING,
  nroemp_origem STRING,
  numeronf STRING,
  nfechaveacesso STRING,
  codgeraloper STRING,
  dtaemissao STRING,
  dtaentrada STRING,
  nro_dias STRING
);

CREATE TABLE IF NOT EXISTS `bi-conciliacao-nf.controle_recebimento.stg_checkin` (
  data STRING,
  entrada STRING,
  loja STRING,
  nota STRING,
  fornecedor STRING,
  valor STRING,
  status_nf STRING,
  check_in STRING,
  status_check_in STRING,
  chave STRING
);
