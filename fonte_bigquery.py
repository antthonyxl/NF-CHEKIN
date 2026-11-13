"""Leitura somente de BigQuery mantendo o contrato da conciliação existente.

A conta de serviço precisa de bigquery.jobs.create (BigQuery Job User no projeto)
e bigquery.tables.getData (BigQuery Data Viewer no dataset). Não cria/modifica tabelas.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

from conciliacao import COLUNAS_AUTO, COLUNAS_CHECKIN, validar_colunas

from consultas_bigquery import _AUTO_SQL, _CHECKIN_SQL, _CUSTO_SQL, consulta_custos_relevantes, consulta_tabela


def configuracao_disponivel() -> bool:
    """Detecta configuração ausente sem quebrar o dashboard antes do setup."""
    try:
        return "bigquery" in st.secrets
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _cliente_bigquery():
    cfg = st.secrets["bigquery"]
    project_id = str(cfg["project_id"])
    # Localmente também permite credenciais padrão do gcloud, sem guardar JSON.
    if "gcp_service_account" in st.secrets:
        cred = service_account.Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]))
        return bigquery.Client(project=project_id, credentials=cred)
    return bigquery.Client(project=project_id)


@st.cache_data(show_spinner=False, ttl=600, max_entries=3)
def _consultar(sql: str, location: str, _cliente) -> pd.DataFrame:
    # Evita uma consulta inesperadamente grande por erro no identificador de tabela.
    config = bigquery.QueryJobConfig(maximum_bytes_billed=2 * 1024**3)
    job = _cliente.query(sql, location=location, job_config=config)
    linhas = (dict(linha.items()) for linha in job.result(page_size=10000))
    return pd.DataFrame.from_records(linhas)


def carregar_bases() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Entrega DataFrames com os mesmos nomes dos arquivos XLSX já suportados."""
    cfg = st.secrets["bigquery"]
    projeto = str(cfg["project_id"])
    dataset = str(cfg.get("dataset", "controle_recebimento"))
    local = str(cfg.get("location", "southamerica-east1"))
    cliente = _cliente_bigquery()

    sql_auto = consulta_tabela(projeto, dataset, "entrada_auto_nf", _AUTO_SQL)
    sql_checkin = consulta_tabela(projeto, dataset, "checkin", _CHECKIN_SQL)
    auto = _consultar(sql_auto, local, cliente)
    checkin = _consultar(sql_checkin, local, cliente)
    # Uma tabela recém-criada sem linhas não deveria provocar KeyError na conciliação.
    if auto.empty:
        auto = pd.DataFrame(columns=COLUNAS_AUTO)
    if checkin.empty:
        checkin = pd.DataFrame(columns=COLUNAS_CHECKIN)
    validar_colunas(auto, COLUNAS_AUTO, "BigQuery.entrada_auto_nf")
    validar_colunas(checkin, COLUNAS_CHECKIN, "BigQuery.checkin")
    return auto, checkin


def limpar_cache():
    _consultar.clear()


def carregar_custos() -> pd.DataFrame:
    """Terceira tabela do BigQuery: custo e quantidade por loja, NF e série."""
    cfg = st.secrets["bigquery"]
    projeto = str(cfg["project_id"])
    dataset = str(cfg.get("dataset", "controle_recebimento"))
    local = str(cfg.get("location", "southamerica-east1"))
    sql = consulta_custos_relevantes(projeto, dataset)
    custo = _consultar(sql, local, _cliente_bigquery())
    if custo.empty:
        custo = pd.DataFrame(columns=list(_CUSTO_SQL.values()))
    return custo
