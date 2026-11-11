"""Classificação Regional/Distrital por nome de unidade da base Auto NF.

A planilha de referência é a única fonte de gestores. Unidades que não aparecem
nela continuam visíveis como NÃO CLASSIFICADO, sem atribuições presumidas.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

NAO_CLASSIFICADO = "NÃO CLASSIFICADO"
COLUNAS_CSV = ("Unidade", "Regional", "Distrital")


def chave_unidade(nome: object) -> str:
    """Ex.: '002-VIT.SA' e 'Vit.Sa' -> 'VITSA'."""
    if pd.isna(nome):
        return ""
    texto = re.sub(r"^\s*\d+\s*-\s*", "", str(nome).strip())
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]", "", texto.upper())


def ler_classificacao(caminho: str | Path) -> pd.DataFrame:
    """Carrega o cadastro CSV preservando exatamente a classificação informada."""
    cadastro = pd.read_csv(caminho, sep=";", encoding="utf-8-sig", dtype="string")
    cadastro.columns = cadastro.columns.str.strip()
    ausentes = set(COLUNAS_CSV) - set(cadastro.columns)
    if ausentes:
        raise ValueError("classificacao_unidades.csv sem coluna(s): " + ", ".join(sorted(ausentes)))
    cadastro = cadastro.loc[:, COLUNAS_CSV].copy()
    for coluna in COLUNAS_CSV:
        cadastro[coluna] = cadastro[coluna].str.strip()
    cadastro["CHAVE_UNIDADE"] = cadastro["Unidade"].map(chave_unidade)
    if (cadastro["CHAVE_UNIDADE"] == "").any() or cadastro["CHAVE_UNIDADE"].duplicated().any():
        raise ValueError("classificacao_unidades.csv contém unidade vazia ou repetida após normalização")
    return cadastro


def classificar_unidades(dados: pd.DataFrame, cadastro: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta duas colunas sem alterar linhas, valores nem resultados de conciliação."""
    resultado = dados.copy()
    chaves = resultado["EMPRESA"].map(chave_unidade)
    mapa = cadastro.set_index("CHAVE_UNIDADE")
    if not mapa.index.is_unique:
        raise ValueError("Cadastro com unidades duplicadas")
    resultado["REGIONAL"] = chaves.map(mapa["Regional"]).fillna(NAO_CLASSIFICADO)
    resultado["DISTRITAL"] = chaves.map(mapa["Distrital"]).fillna(NAO_CLASSIFICADO)
    return resultado


def filtrar_hierarquia(
    dados: pd.DataFrame,
    regionais: list[str] | None = None,
    distritais: list[str] | None = None,
) -> pd.DataFrame:
    """Aplica seleção combinada (E), sem interferir nos outros filtros."""
    resultado = dados
    if regionais:
        resultado = resultado.loc[resultado["REGIONAL"].isin(regionais)]
    if distritais:
        resultado = resultado.loc[resultado["DISTRITAL"].isin(distritais)]
    return resultado
