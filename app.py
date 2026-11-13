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

# Visão compartilhável: use ?visao=sem-checkin ao final do endereço do app.
# O link muda somente a apresentação; o controle de acesso continua sendo do Streamlit Cloud.
visao_compartilhada = st.query_params.get("visao") == "sem-checkin"
icone_local = Path(__file__).parent / "imagem" / "image.png"
st.set_page_config(
    page_title="NF | Check-in", page_icon=str(icone_local) if icone_local.is_file() else "📊",
    layout="wide", initial_sidebar_state="collapsed" if visao_compartilhada else "expanded",
)



def filtrar_lojas_do_link(dados: pd.DataFrame) -> pd.DataFrame:
    """No link compartilhável, manter somente as lojas 001–068 da base atual.

    COD_LOJA vem de EMPRESA, e não do nome exibido pelo CHECKIN.
    Assim são excluídos os CDs (988, 989, 993, 995, 996, 998, 999),
    a unidade CSC (552) e a darkstore (700), sem excluir lojas ainda
    não classificadas no cadastro Regional/Distrital (ex.: 025-TAMBAU).
    """
    codigo = pd.to_numeric(dados["COD_LOJA"], errors="coerce")
    return dados.loc[codigo.between(1, 68).fillna(False)].copy()

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


if not visao_compartilhada:
    with st.sidebar:
        st.markdown('<div class="aq-brand">NF <span style="color:#F5A24A">/</span> CHECK-IN'
                    '<small>CONCILIAÇÃO OPERACIONAL</small></div>', unsafe_allow_html=True)
        st.divider()
        escuro = st.toggle("Modo escuro", value=False)
        st.markdown('<div class="aq-sidebar-label">DADOS DO BIGQUERY</div>', unsafe_allow_html=True)
        st.caption("Fonte: BigQuery · Dataset controle_recebimento. Atualização automática a cada 10 minutos.")
        if st.button("Atualizar dados agora", use_container_width=True):
            limpar_cache()
else:
    escuro = False  # Layout claro no link compartilhado, sem controles laterais.

visual.aplicar_tema(escuro)
tema = visual.paleta(escuro)
if not visao_compartilhada:
    visual.cabecalho(
        "Conciliação de notas fiscais",
        "Notas da ENTRADA AUTO NF localizadas na base CHECKIN, com análise de pendências por unidade.",
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

if not visao_compartilhada:
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
else:
    # Restringe apenas a VISÃO COMPARTILHADA a lojas; KPIs e matriz usam o mesmo recorte.
    # No dashboard completo, os CDs e as demais unidades permanecem acessíveis.
    filtrados = filtrar_lojas_do_link(dados)

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
    f"{filtrados['EMPRESA'].nunique()} unidade(s) no filtro | "
    "a conciliação usa código da unidade + NF normalizada."
)

if visao_compartilhada:
    st.caption("VISÃO COMPARTILHADA / NOTAS SEM CHECK-IN · SOMENTE LOJAS (SEM CDs)")
    painel("Notas sem check-in", sem_checkin, com_checkin=False, tema=tema, arquivo_csv="notas_sem_checkin.csv")
    st.caption("'Sem check-in' significa ausência de correspondência nas bases disponíveis, não prova de que o recebimento nunca ocorreu.")
    if st.button("Voltar ao dashboard completo", key="voltar_dashboard_completo"):
        st.query_params.pop("visao", None)
        st.rerun()
else:
    tab_com, tab_sem, tab_rev = st.tabs(["Com check-in", "Sem check-in", "Revisar múltiplos check-ins"])
    with tab_com:
        painel("Notas com check-in", localizados, com_checkin=True, tema=tema, arquivo_csv="notas_com_checkin.csv")
        if not multiplos.empty:
            st.warning("Algumas notas possuem mais de um check-in para a mesma unidade e NF. O valor dessas notas não foi atribuído automaticamente.")
    with tab_sem:
        if st.button("Abrir visão para apresentação", key="compartilhar_sem_checkin"):
            st.query_params["visao"] = "sem-checkin"
            st.rerun()
        painel("Notas sem check-in", sem_checkin, com_checkin=False, tema=tema, arquivo_csv="notas_sem_checkin.csv")
        st.caption("'Sem check-in' significa ausência de correspondência nos arquivos carregados, não prova de que o recebimento nunca ocorreu.")
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

    with st.expander("Como funciona a conciliação", expanded=False):
        st.markdown("""
        **Chave de busca:** código da unidade + número da nota. Por exemplo,
        `001-CARPINA` corresponde à unidade `NOVO - 01 - Carpina Centro`.

        **Tratamento da série:** `75137-1` → `75137` e `1776754-001` → `1776754`.
        O sufixo numérico é retirado somente da coluna **Nota** do CHECKIN.

        **Valor e check-in:** quando existe uma única correspondência, apresenta Valor,
        número e status do check-in. Se houver dois ou mais registros do CHECKIN para a
        mesma loja + nota, a nota permanece localizada, mas seu valor fica pendente
        de análise na guia **Revisar múltiplos check-ins**.

        **Preservação das linhas:** a saída mantém todas as linhas da ENTRADA AUTO NF,
        incluindo registros repetidos. O indicador financeiro não soma a mesma
        combinação de loja + NF mais de uma vez.
        """)
