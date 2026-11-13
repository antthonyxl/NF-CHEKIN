"""Associa custo líquido e quantidade da NF por código da loja + número da NF.

A base Auto NF não informa série. Uma nota com séries/valores diferentes no
mesmo estabelecimento fica pendente, sem atribuição financeira arbitrária.
A base original da Auto NF é preservada linha a linha.
"""
from __future__ import annotations

import pandas as pd
from conciliacao import CHAVE, normalizar_numero_nf, validar_colunas

COLUNAS_CUSTO = ["COD_EMPRESA", "NF", "SERIE", "Quantidade", "Custo Liquido"]


def _numerico(series: pd.Series) -> pd.Series:
    """Aceita NUMERIC BigQuery, texto decimal com ponto e padrão BR com vírgula."""
    s = series.astype("string").str.strip().str.replace(r"\s+", "", regex=True)
    # 1.234,56 -> 1234.56; 1234,56 -> 1234.56; 1234.56 permanece.
    ambos = s.str.contains(",", regex=False, na=False) & s.str.contains(".", regex=False, na=False)
    s = s.where(~ambos, s.str.replace(".", "", regex=False))
    s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def associar_custos(dados_auto: pd.DataFrame, custos: pd.DataFrame) -> pd.DataFrame:
    """Retorna uma linha de resultado para cada linha Auto; evita duplicar soma."""
    validar_colunas(dados_auto, CHAVE, "Resultado conciliação")
    validar_colunas(custos, COLUNAS_CUSTO, "BigQuery.custo_nf_entrada")

    origem = custos.copy()
    origem["COD_LOJA"] = pd.to_numeric(origem["COD_EMPRESA"], errors="coerce").astype("Int64")
    origem["NF_NORMALIZADA"] = normalizar_numero_nf(origem["NF"], retirar_serie=False)
    origem["SERIE_CUSTO"] = normalizar_numero_nf(origem["SERIE"], retirar_serie=False)
    origem["QUANTIDADE_CUSTO"] = _numerico(origem["Quantidade"])
    origem["CUSTO_LIQUIDO"] = _numerico(origem["Custo Liquido"])

    base_valida = origem.loc[
        origem["COD_LOJA"].notna() &
        origem["NF_NORMALIZADA"].str.fullmatch(r"\d+").fillna(False) &
        origem["SERIE_CUSTO"].str.fullmatch(r"\d+").fillna(False)
    ].copy()

    # Duplicata IDÊNTICA não cria novo custo; mesmo loja + NF com série,
    # quantidade ou custo diferente permanece ambíguo e não é somado.
    chave_versao = CHAVE + ["SERIE_CUSTO", "QUANTIDADE_CUSTO", "CUSTO_LIQUIDO"]
    versoes = base_valida.drop_duplicates(chave_versao)
    totais = versoes.groupby(CHAVE, dropna=False).size().rename("QTD_VERSOES_CUSTO")
    primeira = versoes.drop_duplicates(CHAVE).set_index(CHAVE)
    tab = primeira[["SERIE_CUSTO", "QUANTIDADE_CUSTO", "CUSTO_LIQUIDO"]].join(totais).reset_index()

    resultado = dados_auto.merge(tab, how="left", on=CHAVE, sort=False, validate="many_to_one")
    resultado["QTD_VERSOES_CUSTO"] = resultado["QTD_VERSOES_CUSTO"].fillna(0).astype(int)
    resultado["SITUACAO_CUSTO"] = "Não localizado"
    unica = resultado["QTD_VERSOES_CUSTO"].eq(1)
    incompleto = unica & (resultado["QUANTIDADE_CUSTO"].isna() | resultado["CUSTO_LIQUIDO"].isna())
    resultado.loc[unica, "SITUACAO_CUSTO"] = "Localizado"
    resultado.loc[incompleto, "SITUACAO_CUSTO"] = "Valor ou quantidade inválida"
    ambiguo = resultado["QTD_VERSOES_CUSTO"].gt(1)
    resultado.loc[ambiguo, "SITUACAO_CUSTO"] = "Múltiplos custos"
    invalidas = resultado["COD_LOJA"].isna() | ~resultado["NF_NORMALIZADA"].astype("string").str.fullmatch(r"\d+").fillna(False)
    resultado.loc[invalidas, "SITUACAO_CUSTO"] = "Chave inválida"
    # Nunca atribuir quantidade e valor de uma linha arbitrária.
    resultado.loc[ambiguo | incompleto, ["SERIE_CUSTO", "QUANTIDADE_CUSTO", "CUSTO_LIQUIDO"]] = pd.NA
    if len(resultado) != len(dados_auto):
        raise AssertionError("A vinculação de custos alterou a cardinalidade da Auto NF")
    return resultado


def somar_custo_sem_checkin(dados_sem_checkin: pd.DataFrame) -> float:
    """Soma custo líquido das NFs pendentes, contando cada loja + NF uma vez.

    Só entram notas com correspondência única e valores válidos na base de custos.
    """
    validar_colunas(
        dados_sem_checkin,
        CHAVE + ["SITUACAO_CUSTO", "CUSTO_LIQUIDO"],
        "Notas sem check-in",
    )
    localizados = dados_sem_checkin.loc[
        dados_sem_checkin["SITUACAO_CUSTO"].eq("Localizado")
    ].drop_duplicates(CHAVE)
    total = pd.to_numeric(localizados["CUSTO_LIQUIDO"], errors="coerce").sum(min_count=1)
    return 0.0 if pd.isna(total) else float(total)
