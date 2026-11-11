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


