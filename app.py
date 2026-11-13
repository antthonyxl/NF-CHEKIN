"""Dashboard simples de conciliação de notas fiscais — Streamlit.

Instalação: pip install -r requirements.txt
Execução: streamlit run app.py
"""
from __future__ import annotations

import re
from datetime import datetime, time, timedelta
from pathlib import Path
from threading import Lock
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import aquila_visual as visual
from conciliacao import conciliar
from custo_nf import associar_custos, somar_custo_sem_checkin
from fonte_bigquery import carregar_bases, carregar_custos, limpar_cache, configuracao_disponivel
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


# Atualizações programadas no horário de Brasília.
# A sessão ativa agenda somente o próximo horário, sem polling a cada minuto.
FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")
HORARIOS_ATUALIZACAO = ((8, 0), (12, 0), (17, 0))


def _horario_no_dia(data, horario: tuple[int, int]) -> datetime:
    return datetime.combine(data, time(*horario), tzinfo=FUSO_HORARIO)


def _ultima_janela_atualizacao(agora: datetime) -> datetime:
    for horario in reversed(HORARIOS_ATUALIZACAO):
        alvo = _horario_no_dia(agora.date(), horario)
        if agora >= alvo:
            return alvo
    return _horario_no_dia(agora.date() - timedelta(days=1), HORARIOS_ATUALIZACAO[-1])


def _proxima_atualizacao(agora: datetime) -> datetime:
    for horario in HORARIOS_ATUALIZACAO:
        alvo = _horario_no_dia(agora.date(), horario)
        if alvo > agora:
            return alvo
    return _horario_no_dia(agora.date() + timedelta(days=1), HORARIOS_ATUALIZACAO[0])


_agora = datetime.now(FUSO_HORARIO)
_janela_atualizacao = _ultima_janela_atualizacao(_agora).strftime("%Y-%m-%d %H:%M")
_proxima_atualizacao_em = _proxima_atualizacao(_agora)
_segundos_ate_atualizacao = max(
    1.0, (_proxima_atualizacao_em - _agora).total_seconds() + 2.0
)


@st.fragment(run_every=_segundos_ate_atualizacao)
def _gatilho_atualizacao_programada() -> None:
    # O fragmento fica quieto até o próximo horário; então solicita um único
    # rerun completo, que carrega a nova janela de dados e agenda a seguinte.
    if datetime.now(FUSO_HORARIO) >= _proxima_atualizacao_em:
        st.rerun()


_gatilho_atualizacao_programada()


@st.cache_resource(show_spinner=False)
def _estado_atualizacao_programada() -> dict:
    # Compartilhado entre sessões: evita que cada usuário invalide o cache
    # separadamente no mesmo horário de atualização.
    return {"lock": Lock(), "janela": None}


def _invalidar_cache_nova_janela(janela: str) -> None:
    estado = _estado_atualizacao_programada()
    with estado["lock"]:
        if estado["janela"] != janela:
            limpar_cache()
            estado["janela"] = janela


def filtrar_lojas_do_link(dados: pd.DataFrame) -> pd.DataFrame:
    """No link compartilhável, manter somente as lojas 001–068 da base atual.

    COD_LOJA vem de EMPRESA, e não do nome exibido pelo CHECKIN.
    Assim são excluídos os CDs (988, 989, 993, 995, 996, 998, 999),
    a unidade CSC (552) e a darkstore (700), sem excluir lojas ainda
    não classificadas no cadastro Regional/Distrital (ex.: 025-TAMBAU).
    """
    codigo = pd.to_numeric(dados["COD_LOJA"], errors="coerce")
    return dados.loc[codigo.between(1, 68).fillna(False)].copy()

@st.cache_data(show_spinner=False, ttl=None, max_entries=2)
def carregar_dados_conciliados(janela_atualizacao: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Carrega as três bases uma vez por janela programada (08h, 12h ou 17h).

    A chave da janela mantém os dados em cache entre interações e só permite
    nova leitura do BigQuery nos três horários definidos ou por atualização manual.
    """
    auto, checkin = carregar_bases()
    custos = carregar_custos()
    dados, candidatos, indicadores = conciliar(auto, checkin)
    dados = associar_custos(dados, custos)
    cadastro = ler_classificacao(Path(__file__).with_name("classificacao_unidades.csv"))
    dados = classificar_unidades(dados, cadastro)
    return dados, candidatos, indicadores


def gerar_csv(df: pd.DataFrame, colunas: list[str]) -> bytes:
    recorte = df.loc[:, colunas].copy()
    for coluna in ("DTAENTRADA", "DTAEMISSAO", "ENTRADA_CHECKIN"):
        if coluna in recorte:
            recorte[coluna] = pd.to_datetime(recorte[coluna], errors="coerce").dt.strftime("%d/%m/%Y")
    return recorte.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig").encode("utf-8-sig")


def painel(nome: str, dados: pd.DataFrame, *, com_checkin: bool, tema: dict[str, str], arquivo_csv: str, ordenar_por_registros: bool = False, ordenar_por_custo_descendente: bool = False):
    visual.secao(nome, "Clique nos títulos para ordenar as lojas e na seta para abrir as notas. Nos detalhes, os títulos também ordenam as NFs.")
    if dados.empty:
        visual.vazio("Nenhuma nota encontrada", "Nenhum registro corresponde aos filtros selecionados.")
        return
    components.html(montar_matriz(dados, com_checkin=com_checkin, paleta=tema, ordenar_por_registros=ordenar_por_registros, ordenar_por_custo_descendente=ordenar_por_custo_descendente), height=590, scrolling=False)
    if com_checkin:
        cols = [
            "EMPRESA", "NUMERONF", "NROEMP_ORIGEM", "DTAEMISSAO", "DTAENTRADA",
            "NUMERO_CHECKIN", "STATUS_CHECKIN", "STATUS_NF_CHECKIN", "VALOR_CHECKIN",
            "FORNECEDOR_CHECKIN", "SITUACAO", "QTD_CHECKINS", "LINHA_AUTO",
        ]
    else:
        cols = [
            "EMPRESA", "NUMERONF", "NROEMP_ORIGEM", "DTAEMISSAO", "DTAENTRADA",
            "NRO_DIAS", "CODGERALOPER", "QUANTIDADE_CUSTO", "CUSTO_LIQUIDO",
            "SERIE_CUSTO", "SITUACAO_CUSTO", "SITUACAO", "LINHA_AUTO",
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
        st.caption("Atualização automática às 08h, 12h e 17h (horário de Brasília).")
        if st.button("Atualizar dados agora", use_container_width=True):
            limpar_cache()
            carregar_dados_conciliados.clear()
else:
    escuro = False  # Layout claro no link compartilhado, sem controles laterais.

# Invalida a leitura interna do BigQuery uma única vez quando a janela muda.
# O cache do processamento completo usa a própria janela como chave.
_invalidar_cache_nova_janela(_janela_atualizacao)

visual.aplicar_tema(escuro)
# Somente no link compartilhavel: respiro entre o topo da pagina e os KPIs.
# Nao modifica o espacamento do dashboard completo.
if visao_compartilhada:
    st.markdown("""
        <style>
        .block-container { padding-top: 6.5rem !important; }
        @media (max-width: 900px) {
            .block-container { padding-top: 5.5rem !important; }
        }
        </style>
    """, unsafe_allow_html=True)
tema = visual.paleta(escuro)
if not visao_compartilhada:
    visual.cabecalho(
        "Conciliação de notas fiscais",
        "Acompanhamento das Notas com entradas automaticas.",
        etiqueta="CONTROLE OPERACIONAL / ENTRADA DE NF",
    )

try:
    with st.spinner("Consultando e conciliando as bases..."):
        if not configuracao_disponivel():
            st.error("Configure a seção [bigquery] em .streamlit/secrets.toml ou nos Secrets do Streamlit Cloud.")
            st.stop()
        dados, candidatos, indicadores = carregar_dados_conciliados(_janela_atualizacao)
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

def exibir_kpis(titulo_valor: str, valor: float, descricao_valor: str) -> None:
    """Renderiza os quatro indicadores usando o valor da aba atualmente aberta."""
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        visual.kpi("Entradas Automaticas", numero_br(len(filtrados)), "Quantidade de Notas", "blue")
    with k2:
        visual.kpi("Com check-in", numero_br(len(localizados)), "Notas com Check-in", "teal")
    with k3:
        visual.kpi("Sem check-in", numero_br(len(sem_checkin)), "Notas Sem Check-in", "orange")
    with k4:
        visual.kpi(titulo_valor, moeda(valor), descricao_valor, "teal")


# Reserva a posição dos KPIs antes da legenda e das abas, preservando o layout original.
area_kpis = st.container()

st.caption(
    f"{numero_br(len(multiplos))} registro(s) com múltiplos check-ins | "
    f"{filtrados['EMPRESA'].nunique()} unidade(s) no filtro"
)

if visao_compartilhada:
    # O link compartilhável representa exclusivamente a visão Sem check-in.
    custo_pendente = somar_custo_sem_checkin(sem_checkin)
    with area_kpis:
        exibir_kpis(
            "Custo líquido sem check-in", custo_pendente,
            "Soma das notas únicas com custo localizado",
        )
    painel("Notas sem check-in", sem_checkin, com_checkin=False, tema=tema, arquivo_csv="notas_sem_checkin.csv", ordenar_por_custo_descendente=True)
    
    if st.button("Voltar ao dashboard completo", key="voltar_dashboard_completo"):
        st.query_params.pop("visao", None)
        st.rerun()
else:
    # O placeholder mantém os KPIs visualmente acima das abas, embora o valor
    # do último indicador dependa da aba selecionada pelo usuário.
    tab_com, tab_sem, tab_rev = st.tabs(
        ["Com check-in", "Sem check-in", "Revisar múltiplos check-ins"],
        key="aba_conciliacao",
        on_change="rerun",
    )

    if tab_sem.open:
        titulo_kpi_valor = "Custo líquido sem check-in"
        valor_kpi_valor = somar_custo_sem_checkin(sem_checkin)
        descricao_kpi_valor = "Soma das notas únicas com custo localizado"
    else:
        # Com check-in e Revisar múltiplos mantêm o indicador financeiro original.
        titulo_kpi_valor = "Valor localizado"
        valor_kpi_valor = valor_unico
        descricao_kpi_valor = "Notas únicas sem ambiguidade"

    with area_kpis:
        exibir_kpis(titulo_kpi_valor, valor_kpi_valor, descricao_kpi_valor)

    # Renderiza somente o conteúdo da aba ativa. Além de atualizar o KPI ao
    # trocar de aba, evita montar matrizes ocultas em cada rerun do Streamlit.
    if tab_com.open:
        with tab_com:
            painel("Notas com check-in", localizados, com_checkin=True, tema=tema, arquivo_csv="notas_com_checkin.csv")

    if tab_sem.open:
        with tab_sem:
            if st.button("Abrir para apresentação", key="compartilhar_sem_checkin"):
                st.query_params["visao"] = "sem-checkin"
                st.rerun()
            painel("Notas sem check-in", sem_checkin, com_checkin=False, tema=tema, arquivo_csv="notas_sem_checkin.csv")

    if tab_rev.open:
        with tab_rev:
            visual.secao("Notas com múltiplos registros",)
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

    with st.expander("ATENÇÃO !", expanded=False):
        st.markdown("""
        **Dados Privados:** Não compartilhe este link com pessoas externas à empresa. Ele contém informações financeiras e operacionais sensíveis.

        **Atualizações automáticas:** O dashboard consulta as bases às 08h, 12h e 17h (horário de Brasília). Também é possível usar o botão "Atualizar dados agora" para uma atualização extraordinária.

        **Responsabilidade:** As atualizações e análises operacionais desses dados são feitas pela equipe de `Proteção de Ativos`.
        """)
