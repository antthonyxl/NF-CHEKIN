"""SQL de leitura BigQuery, isolado para testes sem conexão."""
from __future__ import annotations
import re

_AUTO_SQL = {
    "empresa": "EMPRESA",
    "nroemp_origem": "NROEMP_ORIGEM",
    "numeronf": "NUMERONF",
    "nfechaveacesso": "NFECHAVEACESSO",
    "codgeraloper": "CODGERALOPER",
    "dtaemissao": "DTAEMISSAO",
    "dtaentrada": "DTAENTRADA",
    "nro_dias": "NRO_DIAS",
}
_CHECKIN_SQL = {
    "data": "Data",
    "entrada": "Entrada",
    "loja": "Loja",
    "nota": "Nota",
    "fornecedor": "Fornecedor",
    "valor": "Valor",
    "status_nf": "Status NF",
    "check_in": "Check-In",
    "status_check_in": "Status Check-In",
    "chave": "Chave",
}


_CUSTO_SQL = {
    "cod_empresa": "COD_EMPRESA",
    "nf": "NF",
    "serie": "SERIE",
    "quantidade": "Quantidade",
    "custo_liquido": "Custo Liquido",
}


def _identificador(valor: str, *, projeto: bool = False) -> str:
    padrao = r"[A-Za-z][A-Za-z0-9_.:-]*" if projeto else r"[A-Za-z_][A-Za-z0-9_]*"
    if not re.fullmatch(padrao, valor or ""):
        raise ValueError(f"Identificador BigQuery inválido: {valor!r}")
    return valor


def consulta_tabela(projeto: str, dataset: str, tabela: str, colunas: dict[str, str]) -> str:
    """Retorna apenas campos necessários, independentemente do tipo inferido no CSV."""
    p = _identificador(projeto, projeto=True)
    d = _identificador(dataset)
    t = _identificador(tabela)
    campos = ",\n  ".join(
        f"CAST(`{coluna}` AS STRING) AS `{saida}`" for coluna, saida in colunas.items()
    )
    return f"SELECT\n  {campos}\nFROM `{p}.{d}.{t}`"




def consulta_custos_relevantes(projeto: str, dataset: str) -> str:
    """Lê custos apenas das combinações loja + NF existentes na Auto NF.

    Reduz o volume transferido do BigQuery sem alterar a regra de conciliação
    Python: séries e divergências continuam sendo avaliadas por associar_custos.
    """
    p = _identificador(projeto, projeto=True)
    d = _identificador(dataset)
    campos = ",\n  ".join(
        f"CAST(c.`{coluna}` AS STRING) AS `{saida}`"
        for coluna, saida in _CUSTO_SQL.items()
    )
    auto = f"`{p}.{d}.entrada_auto_nf`"
    custos = f"`{p}.{d}.custo_nf_entrada`"
    return f"""SELECT
  {campos}
FROM {custos} AS c
WHERE EXISTS (
  SELECT 1
  FROM {auto} AS a
  WHERE SAFE_CAST(REGEXP_EXTRACT(CAST(a.`EMPRESA` AS STRING), r'^\\s*([0-9]+)\\s*-') AS INT64)
      = SAFE_CAST(REGEXP_REPLACE(TRIM(CAST(c.`COD_EMPRESA` AS STRING)), r'\\.0+$', '') AS INT64)
    AND SAFE_CAST(REGEXP_REPLACE(TRIM(CAST(a.`NUMERONF` AS STRING)), r'\\.0+$', '') AS INT64)
      = SAFE_CAST(REGEXP_REPLACE(TRIM(CAST(c.`NF` AS STRING)), r'\\.0+$', '') AS INT64)
)"""
