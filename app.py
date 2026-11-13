"""Dashboard simples de conciliação de notas fiscais — Streamlit.

Instalação: pip install -r requirements.txt
Execução: streamlit run app.py
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import aquila_visual as visual
from conciliacao import conciliar
from fonte_bigquery import carregar_bases, limpar_cache, configuracao_disponivel
from classificacao import classificar_unidades, filtrar_hierarquia, ler_classificacao
from matriz import moeda, montar_matriz, numero_br

st.set_page_config(
    page_title="AUTO NF",
    page_icon="imagem/image.png",
    layout="wide",
)


def gerar_csv(df: pd.DataFrame, colunas: list[str]) -> bytes:
    recorte = df.loc[:, colunas].copy()
    for coluna in ("DTAENTRADA", "DTAEMISSAO", "ENTRADA_CHECKIN"):
        if coluna in recorte:
            recorte[coluna] = pd.to_datetime(recorte[coluna], errors="coerce").dt.strftime("%d/%m/%Y")
    return recorte.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig").encode("utf-8-sig")


def painel(nome: str, dados: pd.DataFrame, *, com_checkin: bool, tema: dict[str, str], arquivo_csv: str):
    visual.secao(nome, "Clique nos títulos para ordenar as lojas e na seta para abrir as notas. Nos detalhes, os títulos também ordenam as NFs.")
    if dados.empty:
        visual.vazio("Nenhuma nota encontrada", "Nenhum registro corresponde aos filtros selecionados.")
        return
    components.html(montar_matriz(dados, com_checkin=com_checkin, paleta=tema), height=590, scrolling=False)
    if com_checkin:
        cols = [
            "EMPRESA", "NUMERONF", "NROEMP_ORIGEM", "DTAEMISSAO", "DTAENTRADA",
            "NUMERO_CHECKIN", "STATUS_CHECKIN", "STATUS_NF_CHECKIN", "VALOR_CHECKIN",
            "FORNECEDOR_CHECKIN", "SITUACAO", "QTD_CHECKINS", "LINHA_AUTO",
        ]
    else:
        cols = [
            "EMPRESA", "NUMERONF", "NROEMP_ORIGEM", "DTAEMISSAO", "DTAENTRADA",
            "NRO_DIAS", "CODGERALOPER", "SITUACAO", "LINHA_AUTO",
        ]
    st.download_button(
        "Exportar registros em CSV", data=gerar_csv(dados, cols),
        file_name=arquivo_csv, mime="text/csv", key=f"download_{arquivo_csv}",
    )


with st.sidebar:
    st.markdown('<div class="aq-brand">NF <span style="color:#F5A24A">/</span> CHECK-IN'
                '<small>CONCILIAÇÃO OPERACIONAL</small></div>', unsafe_allow_html=True)
    st.divider()
    escuro = st.toggle("Modo escuro", value=False)
    st.markdown('<div class="aq-sidebar-label">DADOS DO BIGQUERY</div>', unsafe_allow_html=True)
    st.caption("Atualização automática a cada 10 minutos.")
    if st.button("Atualizar dados agora", use_container_width=True):
        limpar_cache()

visual.aplicar_tema(escuro)
tema = visual.paleta(escuro)
visual.cabecalho(
    "Conciliação de notas fiscais",
    "Esses dados são de uso interno e não devem ser compartilhados fora da empresa.",
    etiqueta="CONTROLE OPERACIONAL / ENTRADA DE NF",
)

try:
    with st.spinner("Consultando e conciliando as bases..."):
        if not configuracao_disponivel():
            st.error("Configure a seção [bigquery] em .streamlit/secrets.toml ou nos Secrets do Streamlit Cloud.")
            st.stop()
        auto, checkin = carregar_bases()
        dados, candidatos, indicadores = conciliar(auto, checkin)
        cadastro = ler_classificacao(Path(__file__).with_name("classificacao_unidades.csv"))
        dados = classificar_unidades(dados, cadastro)
except Exception as e:
    st.error(f"Não foi possível obter ou conciliar as bases: {e}")
    st.info("Confira as permissões de leitura, o projeto/dataset, a região e o esquema das tabelas no BigQuery.")
    st.stop()

with st.container(border=True):
    filtros_regional, filtros_distrital = st.columns(2)
    with filtros_regional:
        opcoes_regionais = sorted(dados["REGIONAL"].dropna().unique().tolist())
        regionais = st.multiselect("Filtrar por Regional", opcoes_regionais, placeholder="Todas as regionais")
    # Lista distrital acompanha a(s) regional(is) escolhida(s).
    base_distritais = dados.loc[dados["REGIONAL"].isin(regionais)] if regionais else dados
    opcoes_distritais = sorted(base_distritais["DISTRITAL"].dropna().unique().tolist())
    chave_distrital = "filtro_distritais"
    if chave_distrital in st.session_state:
        st.session_state[chave_distrital] = [
            nome for nome in st.session_state[chave_distrital] if nome in opcoes_distritais
        ]
    with filtros_distrital:
        distritais = st.multiselect(
            "Filtrar por Distrital", opcoes_distritais,
            placeholder="Todos os distritais", key=chave_distrital,
        )
    filtros_col1, filtros_col2 = st.columns([3, 2])
    with filtros_col1:
        todas_lojas = sorted(dados["EMPRESA"].dropna().astype(str).unique().tolist())
        unidades = st.multiselect("Filtrar por loja / CD", todas_lojas, placeholder="Todas as unidades")
    with filtros_col2:
        consulta = st.text_input("Pesquisar número da NF", placeholder="Digite o número da nota")

filtrados = filtrar_hierarquia(dados, regionais, distritais)
if unidades:
    filtrados = filtrados.loc[filtrados["EMPRESA"].isin(unidades)]
if consulta.strip():
    termo = re.escape(consulta.strip())
    filtrados = filtrados.loc[
        filtrados["NF_NORMALIZADA"].astype(str).str.contains(termo, regex=True, na=False)
    ]

localizados = filtrados[filtrados["SITUACAO"].isin(["Localizado", "Múltiplos check-ins"])]
sem_checkin = filtrados[filtrados["SITUACAO"].isin(["Sem check-in", "Chave inválida"])]
multiplos = localizados[localizados["SITUACAO"].eq("Múltiplos check-ins")]
valor_unico = localizados.loc[localizados["SITUACAO"].eq("Localizado")].drop_duplicates(
    ["COD_LOJA", "NF_NORMALIZADA"]
)["VALOR_CHECKIN"].sum(min_count=1)

k1, k2, k3, k4 = st.columns(4)
with k1:
    visual.kpi("Registros Auto NF", numero_br(len(filtrados)), "Quantidade de linhas na base", "blue")
with k2:
    visual.kpi("Com check-in", numero_br(len(localizados)), "Inclui ocorrências múltiplas", "teal")
with k3:
    visual.kpi("Sem check-in", numero_br(len(sem_checkin)), "Sem correspondência na base recebida", "orange")
with k4:
    visual.kpi("Valor localizado", moeda(valor_unico), "Notas únicas sem ambiguidade", "teal")

st.caption(
    f"{numero_br(len(multiplos))} registro(s) com múltiplos check-ins | "
    f"{filtrados['EMPRESA'].nunique()} unidade(s) no filtro"
)

tab_com, tab_sem, tab_rev = st.tabs(["Com check-in", "Sem check-in", "Revisar múltiplos check-ins"])
with tab_com:
    painel("Notas com check-in", localizados, com_checkin=True, tema=tema, arquivo_csv="notas_com_checkin.csv")
with tab_sem:
    painel("Notas sem check-in", sem_checkin, com_checkin=False, tema=tema, arquivo_csv="notas_sem_checkin.csv")
with tab_rev:
    visual.secao("Notas com múltiplos registros", "Os candidatos reais do CHECKIN são apresentados sem escolher automaticamente um valor.")
    if multiplos.empty:
        visual.vazio("Nenhuma ambiguidade no filtro", "Não há notas com múltiplos check-ins para os filtros selecionados.")
    else:
        chaves = multiplos[["COD_LOJA", "NF_NORMALIZADA"]].drop_duplicates()
        revisao = chaves.merge(candidatos, on=["COD_LOJA", "NF_NORMALIZADA"], how="left")
        vis = revisao[[
            "Loja", "Nota", "Fornecedor", "Entrada", "Valor", "Check-In",
            "Status Check-In", "Status NF", "LINHA_CHECKIN",
        ]].copy()
        vis["Entrada"] = pd.to_datetime(vis["Entrada"], errors="coerce").dt.strftime("%d/%m/%Y")
        st.dataframe(vis, width="stretch", hide_index=True, height=420)
        st.download_button("Exportar candidatos para conferência (CSV)",
                           data=gerar_csv(revisao, ["Loja", "Nota", "Fornecedor", "Entrada", "Valor", "Check-In", "Status Check-In", "Status NF", "LINHA_CHECKIN"]),
                           file_name="checkins_multiplos.csv", mime="text/csv")

with st.expander("ATENÇÃO!", expanded=False):
    st.markdown("""
    **Dados Restritos:** Não compartilhe dados internos fora da empresa. As informações apresentadas são `confidenciais` e de uso `exclusivo` para fins operacionais.

    **Atualizações:** Atualizações e a analise dos dados deste painel, é feita pela equipe de `Proteção de Ativos`.
    """)
