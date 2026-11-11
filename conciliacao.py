"""Conciliação conservadora: unidade + número da NF, com rastreabilidade.

A série da coluna Nota do CHECKIN é removida; colisões entre fornecedores
ou datas não são resolvidas silenciosamente. A cardinalidade da Auto NF é
preservada, inclusive quando há lançamentos repetidos.
"""
from __future__ import annotations

import re
from io import BytesIO

import pandas as pd
from leitura_xlsx import ler_colunas_xlsx

COLUNAS_AUTO = [
    "EMPRESA", "NROEMP_ORIGEM", "NUMERONF", "NFECHAVEACESSO",
    "CODGERALOPER", "DTAEMISSAO", "DTAENTRADA", "NRO_DIAS",
]
COLUNAS_CHECKIN = [
    "Data", "Entrada", "Loja", "Nota", "Fornecedor", "Valor",
    "Status NF", "Check-In", "Status Check-In", "Chave",
]
CHAVE = ["COD_LOJA", "NF_NORMALIZADA"]


def normalizar_numero_nf(serie: pd.Series, *, retirar_serie: bool) -> pd.Series:
    """Normaliza comparações numéricas sem transformar uma NF em float.

    Exemplos: '00075137-001' -> '75137'; '75137.0' -> '75137'.
    Só remove o sufixo -número da coluna CHECKIN.Nota.
    """
    s = serie.astype("string").fillna("").str.strip().str.replace(r"^'", "", regex=True)
    if retirar_serie:
        s = s.str.replace(r"-\d+$", "", regex=True)
    s = s.str.replace(r"\.0+$", "", regex=True)
    s = s.str.replace(r"^0+(?=\d)", "", regex=True)
    return s


def extrair_codigo_loja(serie: pd.Series, *, auto: bool) -> pd.Series:
    """Auto: 001-CARPINA; Check-in: NOVO - 01 - Carpina / 998 - CD."""
    padrao = (
        r"^\s*(\d{1,3})\s*-"
        if auto else
        r"^\s*(?:(?:NOVO|MATEUS|MIX)\s*-\s*)?(\d{1,3})\s*-"
    )
    s = serie.astype("string").str.extract(padrao, flags=re.IGNORECASE, expand=False)
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def converter_data(serie: pd.Series) -> pd.Series:
    """Reconhece datas Excel serializadas e datetimes sem confundir seriais com nanossegundos."""
    num = pd.to_numeric(serie, errors="coerce")
    e_serial = num.between(1, 110000)
    datas = pd.to_datetime(serie.where(~e_serial), errors="coerce", dayfirst=True)
    excel = pd.to_datetime(num.where(e_serial), unit="D", origin="1899-12-30", errors="coerce")
    return datas.fillna(excel)


def ler_auto(conteudo: bytes) -> pd.DataFrame:
    df = pd.read_excel(
        BytesIO(conteudo), sheet_name=0, usecols=COLUNAS_AUTO,
        dtype={"EMPRESA": "string", "NUMERONF": "string"},
        engine="openpyxl",
    )
    validar_colunas(df, COLUNAS_AUTO, "ENTRADA AUTO NF")
    return df


def ler_checkin(conteudo: bytes) -> pd.DataFrame:
    df = ler_colunas_xlsx(conteudo, COLUNAS_CHECKIN)
    validar_colunas(df, COLUNAS_CHECKIN, "CHECKIN")
    return df


def validar_colunas(df: pd.DataFrame, colunas: list[str], nome: str) -> None:
    ausentes = set(colunas) - set(df.columns)
    if ausentes:
        raise ValueError(f"Colunas ausentes em {nome}: {', '.join(sorted(ausentes))}")


def conciliar(auto: pd.DataFrame, checkin: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Retorna resultado (1 linha/linha Auto), check-ins ambíguos e indicadores."""
    validar_colunas(auto, COLUNAS_AUTO, "ENTRADA AUTO NF")
    validar_colunas(checkin, COLUNAS_CHECKIN, "CHECKIN")

    a = auto.copy().reset_index(drop=True)
    c = checkin.copy().reset_index(drop=True)
    a["LINHA_AUTO"] = a.index + 2
    c["LINHA_CHECKIN"] = c.index + 2
    a["COD_LOJA"] = extrair_codigo_loja(a["EMPRESA"], auto=True)
    c["COD_LOJA"] = extrair_codigo_loja(c["Loja"], auto=False)
    a["NF_NORMALIZADA"] = normalizar_numero_nf(a["NUMERONF"], retirar_serie=False)
    c["NF_NORMALIZADA"] = normalizar_numero_nf(c["Nota"], retirar_serie=True)
    a["DTAEMISSAO"] = converter_data(a["DTAEMISSAO"])
    a["DTAENTRADA"] = converter_data(a["DTAENTRADA"])
    c["Entrada"] = converter_data(c["Entrada"])
    c["Valor"] = pd.to_numeric(c["Valor"], errors="coerce")

    validos_c = c["COD_LOJA"].notna() & c["NF_NORMALIZADA"].str.fullmatch(r"\d+").fillna(False)
    validos_a = a["COD_LOJA"].notna() & a["NF_NORMALIZADA"].str.fullmatch(r"\d+").fillna(False)
    cv = c.loc[validos_c].copy()

    # Uma única linha do CHECKIN por chave evita explosão da cardinalidade.
    contagem = cv.groupby(CHAVE, sort=False, dropna=False).size().rename("QTD_CHECKINS")
    indices_primeiros = cv.drop_duplicates(CHAVE, keep="first").set_index(CHAVE)
    indice = indices_primeiros.join(contagem, how="left").reset_index()
    indice = indice.rename(columns={
        "Nota": "NOTA_ORIGINAL_CHECKIN",
        "Loja": "LOJA_CHECKIN",
        "Valor": "VALOR_CHECKIN",
        "Check-In": "NUMERO_CHECKIN",
        "Status Check-In": "STATUS_CHECKIN",
        "Status NF": "STATUS_NF_CHECKIN",
        "Fornecedor": "FORNECEDOR_CHECKIN",
        "Entrada": "ENTRADA_CHECKIN",
        "Chave": "CHAVE_CHECKIN",
    })
    manter = CHAVE + [
        "QTD_CHECKINS", "NOTA_ORIGINAL_CHECKIN", "LOJA_CHECKIN", "VALOR_CHECKIN",
        "NUMERO_CHECKIN", "STATUS_CHECKIN", "STATUS_NF_CHECKIN",
        "FORNECEDOR_CHECKIN", "ENTRADA_CHECKIN", "CHAVE_CHECKIN",
    ]
    resultado = a.merge(indice[manter], on=CHAVE, how="left", sort=False, validate="many_to_one")
    resultado["QTD_CHECKINS"] = resultado["QTD_CHECKINS"].fillna(0).astype("int32")
    resultado["SITUACAO"] = "Sem check-in"
    resultado.loc[resultado["QTD_CHECKINS"] == 1, "SITUACAO"] = "Localizado"
    multiplo = resultado["QTD_CHECKINS"] > 1
    resultado.loc[multiplo, "SITUACAO"] = "Múltiplos check-ins"
    resultado.loc[~validos_a.to_numpy(), "SITUACAO"] = "Chave inválida"
    # Não apresentar valores de uma linha arbitrária quando há mais de um candidato.
    resultado.loc[multiplo, "VALOR_CHECKIN"] = float("nan")
    for campo in ["NUMERO_CHECKIN", "STATUS_CHECKIN", "STATUS_NF_CHECKIN", "FORNECEDOR_CHECKIN", "CHAVE_CHECKIN"]:
        resultado.loc[multiplo, campo] = pd.NA
    resultado.loc[multiplo, "ENTRADA_CHECKIN"] = pd.NaT

    chaves_amb = resultado.loc[multiplo, CHAVE].drop_duplicates()
    candidatos = (
        chaves_amb.merge(cv, on=CHAVE, how="left", validate="one_to_many")
        if not chaves_amb.empty else cv.head(0).copy()
    )
    if not candidatos.empty:
        candidatos = candidatos.sort_values(CHAVE + ["LINHA_CHECKIN"], kind="stable")

    # Valores financeiros apenas de notas únicas e sem conflito no CHECKIN.
    validas_fin = resultado["SITUACAO"].eq("Localizado")
    total_valor = resultado.loc[validas_fin].drop_duplicates(CHAVE)["VALOR_CHECKIN"].sum(min_count=1)
    if pd.isna(total_valor):
        total_valor = 0.0
    dados = {
        "total_auto": len(a),
        "total_checkin": len(c),
        "localizados": int(resultado["SITUACAO"].eq("Localizado").sum()),
        "multiplos": int(multiplo.sum()),
        "sem_checkin": int(resultado["SITUACAO"].eq("Sem check-in").sum()),
        "invalidos": int(resultado["SITUACAO"].eq("Chave inválida").sum()),
        "nf_multiplas_unicas": len(chaves_amb),
        "auto_repetidos": int(a.duplicated(CHAVE).sum()),
        "valor_localizado_unico": float(total_valor),
        "lojas_auto": int(a["COD_LOJA"].nunique()),
    }
    if len(resultado) != len(a):
        raise AssertionError("A conciliação alterou o número de registros da ENTRADA AUTO NF")
    return resultado, candidatos, dados
