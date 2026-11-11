"""Camada visual Áquila: modo claro/escuro, tabelas executivas e cartões HTML.

Somente HTML gerado pelo servidor, com escape em todos os campos de origem externa.
"""
from __future__ import annotations

import html
from typing import Sequence

import streamlit as st

TEMAS = {
    "light": {
        "bg": "#F2F5F6", "surface": "#FFFFFF", "surface_alt": "#EAF0F2",
        "text": "#10343D", "muted": "#657B84", "line": "#D8E3E6",
        "head": "#10343D", "head_text": "#FFFFFF", "orange": "#EB963E",
        "teal": "#1E7D90", "blue": "#2388F7", "positive": "#13847A",
        "danger": "#CB5438", "grid": "#DCE6E9", "shadow": "rgba(16,52,61,.045)",
        "sidebar_start": "#153F50", "sidebar_end": "#0B2633", "hover": "#F5F8F9",
        "input_bg": "#FFFFFF", "input_text": "#10343D", "input_muted": "#657B84",
    },
    "dark": {
        "bg": "#0B1720", "surface": "#132633", "surface_alt": "#1E3845",
        "text": "#E9F2F4", "muted": "#AAC0C8", "line": "#31505D",
        "head": "#0B3945", "head_text": "#F9FFFF", "orange": "#F5AA5E",
        "teal": "#62C6D3", "blue": "#66AFFF", "positive": "#70D5B4",
        "danger": "#FF967E", "grid": "#34515E", "shadow": "rgba(0,0,0,.15)",
        "sidebar_start": "#124F9C", "sidebar_end": "#072845", "hover": "#1B3441",
        # Contraste garantido mesmo com o tema nativo Streamlit configurado como light:
        # campos claros usam SEMPRE texto escuro. Isso também cobre o estado de fallback
        # no qual BaseWeb mantém a superfície branca por causa de estilos internos.
        "input_bg": "#EDF4F8", "input_text": "#10343D", "input_muted": "#536F7B",
    },
}


def paleta(escuro: bool) -> dict[str, str]:
    return TEMAS["dark" if escuro else "light"]


def texto_seguro(valor: object) -> str:
    return html.escape("" if valor is None else str(valor), quote=True)


def aplicar_tema(escuro: bool) -> None:
    t = paleta(escuro)
    variaveis = "\n".join(f"--aq-{chave.replace('_','-')}: {valor};" for chave, valor in t.items())
    css = '''
    <style>
    :root {__VARS__}
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
      background: var(--aq-bg) !important; color:var(--aq-text) !important;
    }
    .block-container {max-width:1440px; padding:2.5rem 2.25rem 3.5rem;}
    .st-key-login_layout {max-width:1080px;margin:clamp(24px,8vh,100px) auto;}
    .st-key-login_card {background:var(--aq-surface);border-radius:22px;padding:28px;box-shadow:0 16px 60px var(--aq-shadow);}
    .aq-login-brand {font-size:2rem;font-weight:850;letter-spacing:-.06em;color:var(--aq-text);margin-bottom:32px;}
    .aq-login-brand span {color:var(--aq-teal);}
    .aq-login-title {font-size:clamp(2rem,3.5vw,3.25rem)!important;line-height:1.12!important;letter-spacing:-.045em;margin:18px 0!important;}
    .aq-login-features {color:var(--aq-muted);font-size:.8rem;line-height:1.8;border-top:1px solid var(--aq-line);padding-top:20px;margin-top:32px;}
    .st-key-login_card button {min-height:48px;margin-top:12px;}
    [data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3, [data-testid="stAppViewContainer"] h4,
    [data-testid="stAppViewContainer"] li {color:var(--aq-text); font-family:'Segoe UI',Arial,sans-serif;}
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] p,
    [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] p {color:var(--aq-muted) !important;}
    [data-testid="stVerticalBlockBorderWrapper"] {border-color:var(--aq-line) !important; background:var(--aq-surface) !important; border-radius:16px !important;}
    [data-testid="stVerticalBlockBorderWrapper"] > div {border-radius:16px !important;}
    /* Inputs e seletores: contraste suficiente em ambos os modos. O tema do
       config.toml é estático; por isso, os controles BaseWeb são estilizados
       também em seus elementos internos (que antes ficavam brancos no dark). */
    [data-testid="stAppViewContainer"] [data-baseweb="select"] > div,
    [data-testid="stAppViewContainer"] [data-baseweb="select"] [role="combobox"],
    [data-testid="stAppViewContainer"] [data-baseweb="input"] > div,
    [data-testid="stAppViewContainer"] [data-baseweb="textarea"] > div,
    [data-testid="stAppViewContainer"] [data-testid="stDateInput"] > div > div,
    [data-testid="stAppViewContainer"] [data-testid="stNumberInput"] > div > div {
      background-color:var(--aq-input-bg) !important;
      color:var(--aq-input-text) !important;
      border-color:var(--aq-line) !important;
      -webkit-text-fill-color:var(--aq-input-text) !important;
    }
    [data-testid="stAppViewContainer"] [data-baseweb="select"] > div > div,
    [data-testid="stAppViewContainer"] [data-baseweb="select"] [role="combobox"] > div,
    [data-testid="stAppViewContainer"] [data-baseweb="select"] span,
    [data-testid="stAppViewContainer"] [data-baseweb="select"] input,
    [data-testid="stAppViewContainer"] [data-baseweb="input"] input,
    [data-testid="stAppViewContainer"] input,
    [data-testid="stAppViewContainer"] textarea {
      color:var(--aq-input-text) !important;
      caret-color:var(--aq-input-text) !important;
      -webkit-text-fill-color:var(--aq-input-text) !important;
    }
    [data-testid="stAppViewContainer"] input::placeholder,
    [data-testid="stAppViewContainer"] textarea::placeholder,
    [data-testid="stAppViewContainer"] [data-baseweb="select"] input::placeholder {
      color:var(--aq-input-muted) !important;
      opacity:1 !important;
      -webkit-text-fill-color:var(--aq-input-muted) !important;
    }
    [data-testid="stAppViewContainer"] [data-baseweb="select"] svg {
      fill:var(--aq-input-muted) !important;
      color:var(--aq-input-muted) !important;
    }
    [data-testid="stAppViewContainer"] [data-baseweb="select"] [aria-disabled="true"] {
      opacity:.8 !important;
    }
    /* Selectbox / multiselect podem montar a área visual em diferentes níveis
       do DOM conforme a versão do Streamlit. Defina fundo E texto coerentes;
       jamais use texto branco em controles que possam continuar claros. */
    [data-testid="stAppViewContainer"] [data-baseweb="select"],
    [data-testid="stAppViewContainer"] [data-baseweb="select"] > div,
    [data-testid="stAppViewContainer"] [data-baseweb="select"] > div > div,
    [data-testid="stAppViewContainer"] [data-baseweb="select"] [role="combobox"],
    [data-testid="stAppViewContainer"] [data-baseweb="base-input"],
    [data-testid="stAppViewContainer"] [data-baseweb="base-input"] > div,
    [data-testid="stAppViewContainer"] [data-baseweb="input"] > div,
    [data-testid="stAppViewContainer"] [data-baseweb="textarea"] > div {
      background-color:var(--aq-input-bg) !important;
      color:var(--aq-input-text) !important;
      border-color:var(--aq-line) !important;
    }
    [data-testid="stAppViewContainer"] [data-baseweb="select"] *,
    [data-testid="stAppViewContainer"] [data-baseweb="input"] *,
    [data-testid="stAppViewContainer"] [data-baseweb="textarea"] *,
    [data-testid="stAppViewContainer"] [role="combobox"] * {
      color:var(--aq-input-text) !important;
      -webkit-text-fill-color:var(--aq-input-text) !important;
    }
    /* Chips do multiselect, sem apagar os textos e o botão remover. */
    [data-testid="stAppViewContainer"] [data-baseweb="tag"] {
      background:var(--aq-surface-alt) !important;
      border:1px solid var(--aq-line) !important;
    }
    [data-testid="stAppViewContainer"] [data-baseweb="tag"] *,
    [data-testid="stAppViewContainer"] [data-baseweb="tag"] span {
      color:var(--aq-text) !important;
      -webkit-text-fill-color:var(--aq-text) !important;
    }
    /* Dropdown: menu é um portal fora do container principal. */
    [data-baseweb="popover"] [role="option"],
    [data-baseweb="menu"] [role="option"],
    [data-baseweb="menu"] li {
      color:var(--aq-text) !important;
      -webkit-text-fill-color:var(--aq-text) !important;
    }
    [data-baseweb="popover"] [role="option"]:hover,
    [data-baseweb="menu"] [role="option"]:hover {
      background:var(--aq-surface-alt) !important;
    }
    /* Botões da ordenação: ativo e inativo com contraste definido pelo tema. */
    [data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="secondary"]:not(:disabled) {
      color:var(--aq-text) !important;
      -webkit-text-fill-color:var(--aq-text) !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="primary"] {
      color:#FFFFFF !important;
      -webkit-text-fill-color:#FFFFFF !important;
    }
    /* Painéis da comparação: ambos começam na mesma linha e têm altura mínima
       igual, mas aumentam naturalmente conforme mais colunas forem exibidas. */
    .st-key-aq_ranking_panel, .st-key-aq_historico_panel {
      min-height:755px;
      background:var(--aq-surface);
      border-radius:16px;
      border:1px solid var(--aq-line);
      box-shadow:0 4px 18px var(--aq-shadow);
    }
    /* Os dois cards de desempenho e o gráfico de ROB começam na mesma
       linha e ocupam painéis com altura equivalente nos dois temas. */
    .st-key-aq_rob_chart_panel,
    .st-key-aq_rob_reference_panel {
      min-height:500px;
      box-sizing:border-box;
    }
    .st-key-aq_rob_reference_panel .aq-card {
      min-height:185px;
      display:flex;
      flex-direction:column;
      justify-content:center;
    }
    .aq-comparison-title {
      min-height:2.65rem;
      display:flex;
      align-items:center;
      line-height:1.3;
      margin:0;
      overflow-wrap:anywhere;
    }
    .st-key-aq_comparison_controls,
    .st-key-aq_comparison_history_info {
      min-height:3.1rem;
      display:flex;
      align-items:center;
    }
    .aq-chart-helper {
      color:var(--aq-muted);
      font-size:.83rem;
      padding:7px 0;
    }
    .aq-filter-label {
      font-size:.85rem;
      color:var(--aq-muted);
      margin:4px 0 9px;
      font-weight:600;
    }
    /* Ranking com todas as lojas em altura fixa; outros quadros nao mudam. */
    .st-key-aq_ranking_panel .aq-table-wrap {
      width:100%;
      height:520px;
      min-height:520px;
      max-height:520px;
      overflow-x:auto;
      overflow-y:auto;
      margin-top:4px;
      scrollbar-width:thin;
      scrollbar-color:var(--aq-line) transparent;
    }
    .st-key-aq_ranking_panel .aq-table tfoot td {
      position:sticky;
      bottom:0;
      z-index:2;
      background:var(--aq-head);
      color:var(--aq-head-text) !important;
    }
    .st-key-aq_ranking_panel table.aq-table {
      font-size:.8rem;
    }
    .st-key-aq_ranking_panel .aq-table th,
    .st-key-aq_ranking_panel .aq-table td {
      padding:12px 12px;
    }
    /* O popover "Exibir mais colunas" mantém contraste com mouse e teclado. */
    [data-testid="stAppViewContainer"] [data-testid="stPopover"] button[kind="secondary"] {
      background:var(--aq-surface-alt) !important;
      color:var(--aq-text) !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="primary"] p,
    [data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="primary"] span {
      color:#FFFFFF !important;
      -webkit-text-fill-color:#FFFFFF !important;
    }
    @media(max-width:1000px) {
      .st-key-aq_ranking_panel, .st-key-aq_historico_panel {min-height:auto;}
    }

    /* Rankings de fiscais e produtos lado a lado: cabeçalhos na mesma
       altura, superfície idêntica e rolagem interna sem cortes de colunas. */
    .st-key-aq_fiscais_panel,
    .st-key-aq_produtos_panel {
      min-width:0;
      /* As duas caixas precisam comportar os 10 registros e os rodapés. */
      min-height:600px;
      width:100%;
      max-width:100%;
      height:auto !important;
      box-sizing:border-box;
      /* Folga interna real: não apenas um div HTML ao fim da tabela. */
      padding-bottom:20px !important;
      background:var(--aq-surface) !important;
      border:1px solid var(--aq-line) !important;
      border-radius:16px;
    }
    /* A reserva inferior participa do fluxo do Streamlit: ambos os contêineres
       crescem com o conteúdo, sem corte do rodapé ou altura gigante fixa. */
    .st-key-aq_fiscais_panel .aq-dual-footer-clearance,
    .st-key-aq_produtos_panel .aq-dual-footer-clearance {
      display:block;
      height:18px;
      min-height:18px;
      width:100%;
      pointer-events:none;
    }
    .aq-dual-title {
      /* Mesma área de título nos dois cards, inclusive ao quebrar linha. */
      min-height:3.15rem;
      box-sizing:border-box;
      padding-bottom:8px;
      display:flex;
      align-items:flex-start;
      font-size:1.23rem;
      line-height:1.3;
      font-weight:820;
      color:var(--aq-text);
      letter-spacing:-.02em;
    }
    .aq-dual-subtitle {
      min-height:4.2rem;
      font-size:.83rem;
      line-height:1.45;
      color:var(--aq-muted);
    }
    /* Painéis gêmeos: título + grade + rodapé no mesmo nível. */
    .st-key-aq_fiscais_panel [data-testid="stVerticalBlock"],
    .st-key-aq_produtos_panel [data-testid="stVerticalBlock"] {
      gap:0 !important;
    }
    .st-key-aq_fiscais_panel .aq-table-wrap {
      margin-top:0 !important;
      margin-bottom:0 !important;
    }
    /* Cabeçalho e 10 linhas da tabela de fiscais seguem a mesma medida da grade interativa. */
    .st-key-aq_fiscais_panel .aq-table thead th {
      height:48px;
      box-sizing:border-box;
      padding:8px 9px;
      vertical-align:middle;
    }
    .st-key-aq_fiscais_panel .aq-table tbody td {
      height:39px;
      box-sizing:border-box;
      padding:7px 9px;
      vertical-align:middle;
    }
    .st-key-aq_fiscais_panel .aq-table tfoot td {
      height:45px;
      box-sizing:border-box;
      padding:8px 9px;
    }
    .st-key-aq_produtos_panel .aq-total-interativo {
      border-radius:0 0 10px 10px;
      min-height:45px;
      box-sizing:border-box;
      align-items:center;
      margin:0 !important;
      /* O st.dataframe deixa um intervalo antes do rodapé HTML. O ajuste
         alinha o rodapé de produtos ao rodapé dos fiscais, sem modificar dados. */
      position:relative;
      top:-12px;
    }
    .st-key-aq_fiscais_panel .aq-table-wrap,
    .st-key-aq_produtos_panel .aq-table-wrap {
      width:100%;
      max-width:100%;
      min-width:0;
      box-sizing:border-box;
      max-height:530px;
      overflow-x:auto;
      overflow-y:auto;
      margin-top:0;
      margin-bottom:12px;
      box-shadow:none;
      scrollbar-width:thin;
    }
    .st-key-aq_fiscais_panel table.aq-table {
      min-width:765px;
      font-size:.77rem;
    }
    .st-key-aq_produtos_panel table.aq-table {
      min-width:670px;
      font-size:.77rem;
    }
    .st-key-aq_fiscais_panel .aq-table th,
    .st-key-aq_fiscais_panel .aq-table td,
    .st-key-aq_produtos_panel .aq-table th,
    .st-key-aq_produtos_panel .aq-table td {
      padding:10px 10px;
    }
    .st-key-aq_fiscais_panel .aq-table th:nth-child(2),
    .st-key-aq_fiscais_panel .aq-table td:nth-child(2) {
      min-width:190px;
      white-space:normal;
      overflow-wrap:break-word;
    }
    .st-key-aq_produtos_panel .aq-table th:nth-child(2),
    .st-key-aq_produtos_panel .aq-table td:nth-child(2) {
      min-width:195px;
      white-space:normal;
      overflow-wrap:break-word;
    }
    .aq-dual-footnote {
      color:var(--aq-muted);
      font-size:.79rem;
      line-height:1.5;
      padding:10px 2px 4px;
    }
    @media (max-width: 1050px) {
      .st-key-aq_fiscais_panel,
      .st-key-aq_produtos_panel { min-height:auto; }
      .aq-dual-title,.aq-dual-subtitle { min-height:unset; margin-bottom:.65rem; }
    }

    .st-key-aq_produtos_panel [data-testid="stCaptionContainer"],
    .st-key-aq_motivos_panel [data-testid="stCaptionContainer"],
    .st-key-aq_origem_panel [data-testid="stCaptionContainer"] {
      margin:0 0 7px;
    }
    .aq-total-interativo {
      background:var(--aq-head);
      color:var(--aq-head-text);
      border-radius:0 0 10px 10px;
      padding:13px 14px;
      display:flex;
      justify-content:space-between;
      gap:12px;
      flex-wrap:wrap;
      font-size:.81rem;
    }
    .aq-total-interativo strong,.aq-total-interativo span {color:var(--aq-head-text) !important;}

    /* Ranking de motivos e painel CSC x Loja: topos coincidentes e
       mesma altura visual. A lista de motivos rola internamente quando necessário. */
    .st-key-aq_motivos_panel,
    .st-key-aq_origem_panel {
      min-width:0;
      min-height:590px;
      box-sizing:border-box;
      background:var(--aq-surface) !important;
      border:1px solid var(--aq-line) !important;
      border-radius:16px;
    }
    .aq-motivos-title {
      display:flex;
      align-items:center;
      min-height:2.7rem;
      margin:0 0 4px;
    }
    .st-key-aq_motivos_panel .aq-table-wrap {
      width:100%;
      max-width:100%;
      max-height:466px;
      overflow-x:auto;
      overflow-y:auto;
      margin:4px 0 12px;
      box-shadow:none;
      scrollbar-width:thin;
    }
    .st-key-aq_motivos_panel table.aq-table {
      min-width:625px;
      font-size:.78rem;
    }
    .st-key-aq_motivos_panel .aq-table th,
    .st-key-aq_motivos_panel .aq-table td {
      padding:11px 10px;
    }
    .st-key-aq_motivos_panel .aq-table th:nth-child(2),
    .st-key-aq_motivos_panel .aq-table td:nth-child(2) {
      min-width:175px;
      white-space:normal;
      overflow-wrap:break-word;
    }
    .st-key-aq_origem_panel .aq-table-wrap {
      max-height:none;
      width:100%;
      box-shadow:none;
      margin:4px 0 12px;
    }
    @media(max-width:1020px) {
      .st-key-aq_motivos_panel,
      .st-key-aq_origem_panel {min-height:auto;}
    }

    /* V18: UMA tabela HTML por categoria. Não dividir linhas em st.columns.
       Os checkboxes nativos ficam sobre a primeira coluna e não participam do
       fluxo de layout: os espaçamentos Streamlit nunca separam as linhas. */
    .st-key-aq_grade_produto,
    .st-key-aq_grade_motivo,
    .st-key-aq_grade_origem {
      position:relative !important;
      display:block;
      box-sizing:border-box;
      min-width:0;max-width:100%;width:100%;
      border:1px solid var(--aq-line);
      border-radius:11px;
      background:var(--aq-surface);
      overflow-x:auto;
      overflow-y:hidden;
      scrollbar-width:thin;
    }
    .st-key-aq_grade_produto [data-testid="stVerticalBlock"],
    .st-key-aq_grade_motivo [data-testid="stVerticalBlock"],
    .st-key-aq_grade_origem [data-testid="stVerticalBlock"] {
      gap:0 !important;
      padding:0 !important;
      row-gap:0 !important;
    }
    .aq-unified-table {
      border-collapse:collapse;
      border-spacing:0;
      width:100%;
      table-layout:fixed;
      font-family:'Segoe UI',Arial,sans-serif;
      color:var(--aq-text);
      font-size:.78rem;
      margin:0;
    }
    .aq-unified-table th,
    .aq-unified-table td {
      box-sizing:border-box;
      height:39px;
      max-height:39px;
      padding:7px 9px;
      border-bottom:1px solid var(--aq-line);
      border-right:1px solid var(--aq-line);
      overflow:hidden;
      white-space:nowrap;
      text-overflow:ellipsis;
      vertical-align:middle;
      color:var(--aq-text) !important;
    }
    .aq-unified-table thead th {
      height:48px;
      max-height:48px;
      color:var(--aq-head-text) !important;
      background:var(--aq-head);
      border-right:1px solid rgba(255,255,255,.20);
      font-weight:750;
    }
    .aq-unified-table th:last-child,.aq-unified-table td:last-child {border-right:0;}
    .aq-unified-table tbody tr:nth-child(odd) {background:var(--aq-surface);}
    .aq-unified-table tbody tr:nth-child(even) {background:var(--aq-surface-alt);}
    .aq-unified-table tbody tr.aq-unified-selected {background:var(--aq-hover);}
    .aq-unified-table .num {text-align:right;}
    .aq-unified-table .rank {font-weight:800;color:var(--aq-orange) !important;}
    .aq-unified-table .strong {font-weight:750;}
    .aq-unified-table .aq-checkbox-space {width:40px;padding:0;}
    .aq-unified-table td[title] {cursor:default;}
    /* Checkboxes ficam exatamente no espaço da primeira coluna da tabela. */
    .st-key-aq_checks_produto,
    .st-key-aq_checks_motivo,
    .st-key-aq_checks_origem {
      position:absolute !important;
      top:48px;
      left:0;
      width:40px;
      max-width:40px;
      padding:0 !important;
      margin:0 !important;
      z-index:3;
      background:transparent !important;
      pointer-events:none;
    }
    .st-key-aq_checks_produto [data-testid="stCheckbox"],
    .st-key-aq_checks_motivo [data-testid="stCheckbox"],
    .st-key-aq_checks_origem [data-testid="stCheckbox"] {
      display:flex;
      align-items:center;
      justify-content:center;
      height:39px !important;
      min-height:39px !important;
      margin:0 !important;
      padding:0 !important;
      pointer-events:auto;
    }
    .st-key-aq_checks_produto [data-testid="stCheckbox"] label,
    .st-key-aq_checks_motivo [data-testid="stCheckbox"] label,
    .st-key-aq_checks_origem [data-testid="stCheckbox"] label {
      padding:0 !important;
      margin:0 !important;
      min-height:0 !important;
      line-height:1 !important;
    }
    .st-key-aq_checks_produto [data-testid="stCheckbox"] input,
    .st-key-aq_checks_motivo [data-testid="stCheckbox"] input,
    .st-key-aq_checks_origem [data-testid="stCheckbox"] input {
      accent-color:var(--aq-teal);
    }
    /* V19: checkbox centrado dentro dos 40px da primeira coluna.
       A posição horizontal é explícita: centralização por flex na camada
       interna do Streamlit não era suficiente para este componente. */
    .st-key-aq_checks_produto [data-testid="stCheckbox"] > label,
    .st-key-aq_checks_motivo [data-testid="stCheckbox"] > label,
    .st-key-aq_checks_origem [data-testid="stCheckbox"] > label {
      display:flex !important;
      align-items:center !important;
      justify-content:center !important;
      width:18px !important;
      height:39px !important;
    }
    /* O totalizador agora integra a mesma tabela HTML dos produtos,
       tal como o total dos fiscais. Evita diferenças entre blocos. */
    .aq-unified-table tfoot td {
      height:45px;
      max-height:45px;
      background:var(--aq-head) !important;
      color:var(--aq-head-text) !important;
      padding:8px 9px;
      font-size:.78rem;
      font-weight:800;
      vertical-align:middle;
      border-bottom:0;
      white-space:nowrap;
    }
    .aq-unified-table tfoot td:first-child {text-align:left;}
    .aq-unified-table tfoot td.num {text-align:right;}
    /* Equaliza a altura da tabela interativa e da tabela HTML de fiscais. */
    .st-key-aq_produtos_panel .aq-unified-table tbody tr,
    .st-key-aq_produtos_panel .aq-unified-table tbody td {
      height:39px !important;
      max-height:39px !important;
    }
    .st-key-aq_produtos_panel .aq-unified-table thead th {height:48px !important;}
    .st-key-aq_produtos_panel .aq-unified-table tfoot td {height:45px !important;}

    /* A grade possui no máximo as linhas reais; sem wrappers por célula. */
    .st-key-aq_produtos_panel .aq-total-interativo {
      position:static !important;top:auto !important;margin-top:4px !important;
    }

    /* O segmented_control da ordenação também era branco no tema escuro. */
    [data-testid="stAppViewContainer"] [data-testid="stSegmentedControl"] button,
    [data-testid="stAppViewContainer"] [data-testid="stSegmentedControl"] label {
      color:var(--aq-text) !important;
      background:var(--aq-surface-alt) !important;
      border-color:var(--aq-line) !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stSegmentedControl"] button[aria-checked="true"],
    [data-testid="stAppViewContainer"] [data-testid="stSegmentedControl"] button[aria-pressed="true"],
    [data-testid="stAppViewContainer"] [data-testid="stSegmentedControl"] [data-state="checked"] {
      background:var(--aq-blue) !important;
      color:#FFFFFF !important;
      -webkit-text-fill-color:#FFFFFF !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stSegmentedControl"] button p,
    [data-testid="stAppViewContainer"] [data-testid="stSegmentedControl"] label p {
      color:inherit !important;
    }
    /* Menus flutuantes e popovers podem ser montados fora de stAppViewContainer. */
    [data-baseweb="popover"], [data-baseweb="popover"] > div,
    [data-baseweb="menu"], [role="listbox"] {
      background:var(--aq-surface) !important;
      border-color:var(--aq-line) !important;
      color:var(--aq-text) !important;
    }
    [role="option"], [data-baseweb="menu"] li, [data-baseweb="popover"] li {
      color:var(--aq-text) !important;
    }
    [role="option"]:hover, [data-baseweb="menu"] li:hover {
      background:var(--aq-surface-alt) !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] section {
      background:var(--aq-surface-alt) !important; border-color:var(--aq-line) !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] section button {
      color:var(--aq-text) !important; background:var(--aq-surface) !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stTabs"] button p {color:var(--aq-muted) !important;}
    [data-testid="stAppViewContainer"] [data-testid="stTabs"] button[aria-selected="true"] p {color:var(--aq-blue) !important;}
    [data-testid="stAppViewContainer"] [data-testid="stButton"] button,
    [data-testid="stAppViewContainer"] [data-testid="stDownloadButton"] button {
      border-radius:10px; border-color:var(--aq-line);
    }
    [data-testid="stAppViewContainer"] button[kind="primary"] {
      background:#217DE1 !important; border-color:#217DE1 !important; color:#FFFFFF !important;
    }
    [data-testid="stAppViewContainer"] button[kind="secondary"] {
      background:var(--aq-surface) !important; color:var(--aq-text) !important;
    }
    [data-testid="stSidebar"] {
      background:linear-gradient(170deg,var(--aq-sidebar-start) 0%,var(--aq-sidebar-end) 100%) !important;
      border-right:0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
    [data-testid="stSidebar"] label {color:#EDF7FF !important;}
    [data-testid="stSidebar"] hr {border-color:rgba(255,255,255,.25);}
    [data-testid="stSidebar"] [data-testid="stButton"] button {
      min-height:48px; width:100%; text-align:left !important;
      justify-content:flex-start !important; border:1px solid transparent !important;
      border-radius:12px; padding-left:18px; font-size:.92rem; font-weight:650;
      transition:background .15s ease, transform .15s ease;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] {
      color:#F9FCFF !important; background:transparent !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"]:hover {
      background:rgba(255,255,255,.16) !important; transform:translateX(2px);
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
      color:#124B87 !important; background:#F2F9FF !important;
      box-shadow:0 5px 14px rgba(0,42,90,.12); border-left:4px solid #F5A24A !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] p {color:#124B87 !important;}
    [data-testid="stSidebar"] [data-testid="stToggle"] p {color:#F9FCFF !important;}
    .aq-brand {margin:20px 0 3px;color:white;font-size:2.3rem;line-height:1.04;font-weight:900;letter-spacing:-.045em;}
    .aq-brand small {color:#E3F6FF;font-size:.7rem;letter-spacing:.22em;display:block;margin-top:12px;font-weight:600;}
    .aq-user {background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.22);border-radius:14px;padding:15px;margin:21px 0 20px;color:white;}
    .aq-user-name {font-weight:750;font-size:.92rem;color:white;}
    .aq-user-sub {font-size:.78rem;color:#E1EFFD;margin-top:4px;}
    .aq-sidebar-label {color:#D0E9FC;font-size:.73rem;letter-spacing:.15em;text-transform:uppercase;margin:8px 0 11px;}
    .aq-sidebar-footer {color:#E3F1FF;font-size:.81rem;line-height:1.55;}
    .aq-title {color:var(--aq-text);font-size:clamp(1.65rem,2.5vw,2.45rem);font-weight:850;letter-spacing:-.045em;line-height:1.16;margin:3px 0 8px;}
    .aq-overline {color:var(--aq-teal);font-size:.73rem;letter-spacing:.16em;font-weight:750;text-transform:uppercase;}
    .aq-subtitle {color:var(--aq-muted);font-size:.97rem;line-height:1.5;margin:0 0 1.25rem;}
    .aq-section-title {color:var(--aq-text);font-size:1.4rem;font-weight:820;letter-spacing:-.02em;margin:12px 0 4px;}
    .aq-section-sub {color:var(--aq-muted);font-size:.88rem;margin:0 0 18px;}
    .aq-card {background:var(--aq-surface);border:1px solid var(--aq-line);border-radius:16px;padding:20px 22px;min-height:150px;box-sizing:border-box;box-shadow:0 6px 22px var(--aq-shadow);}
    .aq-card-label {font-size:.78rem;color:var(--aq-muted);font-weight:600;}
    .aq-card-value {font-size:clamp(1.3rem,1.9vw,1.85rem);font-variant-numeric:tabular-nums;overflow-wrap:anywhere;font-weight:840;color:var(--aq-text);line-height:1.25;margin:10px 0 5px;letter-spacing:-.03em;}
    .aq-card-note {font-size:.76rem;color:var(--aq-muted);}
    .aq-kpi-accent {border-top:4px solid var(--aq-teal);}
    .aq-kpi-orange {border-top-color:var(--aq-orange);}
    .aq-kpi-blue {border-top-color:var(--aq-blue);}
    .aq-table-wrap {overflow:auto;max-height:580px;background:var(--aq-surface);border:1px solid var(--aq-line);border-radius:14px;box-shadow:0 4px 18px var(--aq-shadow);margin:10px 0 17px;}
    .aq-table thead th {position:sticky;top:0;z-index:1;}
    table.aq-table {border-collapse:collapse;width:100%;font-family:'Segoe UI',Arial,sans-serif;font-size:.85rem;table-layout:auto;}
    .aq-table th {background:var(--aq-head);color:var(--aq-head-text);font-weight:730;text-align:left;padding:12px 14px;white-space:nowrap;border-right:1px solid rgba(255,255,255,.19);}
    .aq-table th.num,.aq-table td.num {text-align:right;white-space:nowrap;}
    .aq-table td {padding:11px 14px;border-right:1px solid var(--aq-line);border-bottom:1px solid var(--aq-line);color:var(--aq-text);vertical-align:middle;}
    .aq-table tbody tr:nth-child(even) {background:var(--aq-surface-alt);}
    .aq-table tbody tr:hover {background:var(--aq-hover);}
    .aq-table td.rank {color:var(--aq-orange);font-weight:850;}
    .aq-table td.strong {font-weight:730;}
    .aq-table td.emphasis {font-weight:800;color:var(--aq-danger);}
    .aq-table tfoot td {background:var(--aq-head);color:var(--aq-head-text) !important;font-weight:850;border-color:var(--aq-head);padding:13px 14px;}
    .aq-footnote {color:var(--aq-muted);font-size:.8rem;line-height:1.55;margin:10px 0 18px;}
    .aq-panel-title {font-size:1.04rem;font-weight:780;color:var(--aq-text);padding:2px 0 6px;}
    .aq-pill {display:inline-block;background:var(--aq-surface-alt);border:1px solid var(--aq-line);padding:6px 10px;border-radius:7px;color:var(--aq-text);font-weight:650;font-size:.8rem;}
    .aq-empty {border:1px dashed var(--aq-line);border-radius:15px;background:var(--aq-surface-alt);padding:28px 24px;margin:10px 0 18px;}
    .aq-empty-title {font-size:1.1rem;font-weight:780;color:var(--aq-text);margin-bottom:9px;}
    .aq-empty-text {color:var(--aq-muted);font-size:.9rem;line-height:1.55;}
    .aq-note {background:var(--aq-surface-alt);padding:13px 17px;border-radius:10px;color:var(--aq-muted);font-size:.85rem;border-left:4px solid var(--aq-teal);margin:8px 0 12px;}
    .aq-hero {background:linear-gradient(115deg,#123747,#245568);border-radius:17px;padding:23px 28px;margin-bottom:20px;color:#F8FFFF;}
    .aq-hero strong {color:#FFF;font-size:1.15rem;letter-spacing:-.01em;}
    .aq-hero span {display:block;color:#D1EBED;font-size:.85rem;margin-top:6px;}

    [data-baseweb="popover"] > div, [role="listbox"] {
      background:var(--aq-surface) !important; color:var(--aq-text) !important;
      border-color:var(--aq-line) !important;
    }
    [role="option"], [data-baseweb="popover"] li {color:var(--aq-text) !important;}
    [role="option"]:hover {background:var(--aq-surface-alt) !important;}
    [data-testid="stExpander"] details {border-color:var(--aq-line) !important; background:var(--aq-surface) !important;}
    [data-testid="stExpander"] summary p {color:var(--aq-text) !important;}
    [data-testid="stWidgetLabel"] p {color:var(--aq-muted) !important;}

    [data-testid="stPlotlyChart"] {border-radius:12px;overflow:hidden;}
    @media(max-width:900px) {
      .block-container {padding:1rem .85rem 2rem;}
      table.aq-table {font-size:.78rem;}
      .aq-table td, .aq-table th {padding:10px 10px;}
      .aq-card {padding:16px;}
      .st-key-login_layout {margin:20px auto;}
      .st-key-login_card {padding:18px;}
    }
    /* MENU LATERAL ISOLADO: regras gerais do dashboard nao mudam. */
    [data-testid="stSidebar"] :is(.st-key-nav_geral, .st-key-nav_mensal, .st-key-nav_administracao) [data-testid="stButton"] button[kind="secondary"] {
      background:transparent !important;
      color:#F5FBFF !important;
      -webkit-text-fill-color:#F5FBFF !important;
      border:1px solid transparent !important;
      box-shadow:none !important;
    }
    [data-testid="stSidebar"] :is(.st-key-nav_geral, .st-key-nav_mensal, .st-key-nav_administracao) [data-testid="stButton"] button[kind="secondary"]:hover {
      background:rgba(255,255,255,.15) !important;
    }
    [data-testid="stSidebar"] :is(.st-key-nav_geral, .st-key-nav_mensal, .st-key-nav_administracao) [data-testid="stButton"] button[kind="primary"] {
      background:#EFF7FF !important;
      border:1px solid #D8E9F9 !important;
      border-left:4px solid #F5A24A !important;
      color:#123F58 !important;
      -webkit-text-fill-color:#123F58 !important;
      box-shadow:0 5px 14px rgba(0,42,90,.12) !important;
    }
    [data-testid="stSidebar"] :is(.st-key-nav_geral, .st-key-nav_mensal, .st-key-nav_administracao) [data-testid="stButton"] button :is(p,span,svg) {
      color:inherit !important;
      -webkit-text-fill-color:currentColor !important;
    }
    [data-testid="stSidebar"] :is(.st-key-nav_geral, .st-key-nav_mensal, .st-key-nav_administracao) [data-testid="stButton"] button svg {
      fill:currentColor !important;
      stroke:currentColor !important;
    }
    [data-testid="stSidebar"] :is(.st-key-nav_geral, .st-key-nav_mensal, .st-key-nav_administracao) [data-testid="stButton"] button:focus-visible {
      outline:2px solid #FFBA64 !important;
      outline-offset:2px;
    }
    </style>
    '''.replace("__VARS__", variaveis)
    st.markdown(css, unsafe_allow_html=True)


def cabecalho(titulo: str, subtitulo: str, etiqueta: str = "ÁQUILA / DESCONTOS PDV") -> None:
    st.markdown(
        f'<div class="aq-overline">{texto_seguro(etiqueta)}</div>'
        f'<div class="aq-title">{texto_seguro(titulo)}</div>'
        f'<div class="aq-subtitle">{texto_seguro(subtitulo)}</div>',
        unsafe_allow_html=True,
    )


def kpi(label: str, valor: str, legenda: str, cor: str = "teal") -> None:
    css_cor = "aq-kpi-orange" if cor == "orange" else "aq-kpi-blue" if cor == "blue" else ""
    st.markdown(
        f'<div class="aq-card aq-kpi-accent {css_cor}">'
        f'<div class="aq-card-label">{texto_seguro(label)}</div>'
        f'<div class="aq-card-value">{texto_seguro(valor)}</div>'
        f'<div class="aq-card-note">{texto_seguro(legenda)}</div></div>',
        unsafe_allow_html=True,
    )


def secao(titulo: str, descricao: str = "") -> None:
    st.markdown(
        f'<div class="aq-section-title">{texto_seguro(titulo)}</div>'
        f'<div class="aq-section-sub">{texto_seguro(descricao)}</div>',
        unsafe_allow_html=True,
    )


def nota(mensagem: str) -> None:
    st.markdown(f'<div class="aq-note">{texto_seguro(mensagem)}</div>', unsafe_allow_html=True)


def vazio(titulo: str, descricao: str) -> None:
    st.markdown(
        f'<div class="aq-empty"><div class="aq-empty-title">{texto_seguro(titulo)}</div>'
        f'<div class="aq-empty-text">{texto_seguro(descricao)}</div></div>',
        unsafe_allow_html=True,
    )


def tabela(
    colunas: Sequence[tuple[str, str]],
    linhas: Sequence[Sequence[object]],
    total: Sequence[object] | None = None,
    numeros: Sequence[int] = (),
    fortes: Sequence[int] = (),
    enfases: Sequence[int] = (),
) -> None:
    """Tabelas com listras e rodapé, como os slides. Todos os dados são escapados."""
    def cell(val: object, idx: int, heading: bool = False, foot: bool = False) -> str:
        tags = []
        if idx in numeros:
            tags.append("num")
        if idx in fortes:
            tags.append("strong")
        if idx in enfases and not foot:
            tags.append("emphasis")
        if idx == 0 and not foot:
            tags.append("rank")
        tag = "th" if heading else "td"
        return f'<{tag} class="{" ".join(tags)}">{texto_seguro(val)}</{tag}>'

    if not linhas:
        vazio("Nenhum registro disponível", "Os filtros selecionados não retornaram resultados.")
        return
    header = "".join(f'<th class="{"num" if i in numeros else ""}">{texto_seguro(titulo)}</th>' for i, (_, titulo) in enumerate(colunas))
    corpo = "".join("<tr>" + "".join(cell(v, i) for i, v in enumerate(row)) + "</tr>" for row in linhas)
    rodape = "<tfoot><tr>" + "".join(cell(v, i, foot=True) for i, v in enumerate(total)) + "</tr></tfoot>" if total else ""
    st.markdown(
        f'<div class="aq-table-wrap"><table class="aq-table"><thead><tr>{header}</tr></thead>'
        f'<tbody>{corpo}</tbody>{rodape}</table></div>', unsafe_allow_html=True,
    )


def tabela_selecionavel(colunas, linhas, key: str, opcoes, ativo, ao_mudar, totalizador=None) -> None:
    """Grade HTML única e checkboxes nativos sobrepostos, sem lacunas entre linhas.

    Mantém a seleção controlada pela sessão e escapa todo dado externo. Não
    insere widgets entre as linhas da tabela: Streamlit não altera sua altura.
    """
    import hashlib

    if not linhas:
        vazio("Nenhum registro", "Não há dados para os filtros selecionados.")
        return
    if len(linhas) != len(opcoes):
        raise ValueError("Quantidade de linhas e opções de seleção diferente")

    categoria = key.split("_")[2] if key.startswith("aq_seletor_") else key
    # Primeira coluna é reservada à caixa de seleção nativa (40 px).
    larguras = {
        "produto": ("670px", ("40px", "45px", "37%", "16%", "19%", "auto")),
        "motivo": ("660px", ("40px", "42px", "39%", "14%", "20%", "auto")),
        "origem": ("350px", ("40px", "120px", "110px", "80px")),
    }
    if categoria not in larguras:
        raise ValueError(f"Tabela interativa desconhecida: {categoria}")
    largura_min, larguras_colunas = larguras[categoria]
    numericos = {
        "produto": {0, 2, 3, 4},
        "motivo": {0, 2, 3, 4},
        "origem": {1, 2},
    }[categoria]
    fortes = {"produto": {1, 3}, "motivo": {1, 3}, "origem": {0, 1}}[categoria]

    # Valores definidos ANTES de registrar as caixas na árvore de widgets.
    checks = []
    linhas_html = []
    for i, (linha, opcao) in enumerate(zip(linhas, opcoes, strict=True)):
        if len(linha) != len(colunas):
            raise ValueError("Quantidade de células e cabeçalhos diferente")
        assinatura = hashlib.sha256(repr(opcao).encode("utf-8")).hexdigest()[:16]
        chave = f"aq_check_{categoria}_{assinatura}"
        marcado = bool(ativo(opcao))
        if st.session_state.get(chave) != marcado:
            st.session_state[chave] = marcado
        checks.append((i, chave, opcao))

        celulas = []
        for j, valor in enumerate(linha):
            classes = " ".join(filter(None, [
                "num" if j in numericos else "",
                "strong" if j in fortes else "",
                "rank" if j == 0 and categoria != "origem" else "",
            ]))
            protegido = texto_seguro(valor)
            celulas.append(f'<td class="{classes}" title="{protegido}">{protegido}</td>')
        classe_linha = ' class="aq-unified-selected"' if marcado else ''
        linhas_html.append(
            f'<tr{classe_linha}><td class="aq-checkbox-space"></td>'
            + "".join(celulas) + "</tr>"
        )

    cabecalho = "".join(
        f'<th class="{"num" if j in numericos else ""}">{texto_seguro(titulo)}</th>'
        for j, (_, titulo) in enumerate(colunas)
    )
    colgroup = "".join(f'<col style="width:{w}">' for w in larguras_colunas)
    # Para produtos, rodapé na MESMA tabela que o cabeçalho e as linhas,
    # igual à tabela de fiscais; evita o segundo bloco com altura distinta.
    rodape_html = ""
    if totalizador is not None:
        if categoria != "produto" or len(totalizador) != 3:
            raise ValueError("Totalizador integrado permitido apenas para produtos: (rótulo, valor, percentual)")
        rotulo, valor_total, percentual_total = [texto_seguro(x) for x in totalizador]
        rodape_html = (
            '<tfoot><tr>'
            f'<td colspan="4">{rotulo}</td>'
            f'<td class="num">{valor_total}</td>'
            f'<td class="num">{percentual_total}</td>'
            '</tr></tfoot>'
        )
    tabela_html = (
        f'<table class="aq-unified-table" style="min-width:{largura_min}">'
        f'<colgroup>{colgroup}</colgroup>'
        f'<thead><tr><th class="aq-checkbox-space"></th>{cabecalho}</tr></thead>'
        f'<tbody>{"".join(linhas_html)}</tbody>{rodape_html}</table>'
    )

    # Posicionamento absoluto por linha. O CSS numérico não depende do espaço
    # entre widgets que o Streamlit muda conforme sua versão ou o tema ativo.
    regras = "\n".join(
        f'.st-key-aq_checkrow_{categoria}_{i}'
        f'{{position:absolute!important;top:{i * 39}px!important;left:11px!important;'
        f'width:18px!important;height:39px!important;min-height:39px!important;'
        f'padding:0!important;margin:0!important;pointer-events:auto!important;'
        f'box-sizing:border-box!important;}}'
        for i, _, _ in checks
    )

    with st.container(key=f"aq_grade_{categoria}"):
        st.markdown(f'<style>{regras}</style>{tabela_html}', unsafe_allow_html=True)
        with st.container(key=f"aq_checks_{categoria}"):
            for i, chave, opcao in checks:
                with st.container(key=f"aq_checkrow_{categoria}_{i}"):
                    st.checkbox(
                        f"Filtrar por {opcao}",
                        key=chave,
                        label_visibility="collapsed",
                        on_change=ao_mudar,
                        args=(opcao, chave),
                    )
