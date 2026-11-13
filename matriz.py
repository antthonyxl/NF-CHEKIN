"""Matrizes expansíveis loja → notas, com paginação e ordenação no navegador.

Sem bibliotecas JavaScript externas, sem executar dados vindos do Excel.
Ordenação atua apenas sobre a apresentação, preservando a conciliação original.
"""
from __future__ import annotations

import json
from datetime import datetime

import pandas as pd


def numero_br(n: object, casas: int = 0) -> str:
    if n is None or pd.isna(n):
        return "—"
    try:
        txt = f"{float(n):,.{casas}f}"
        return txt.replace(",", "_").replace(".", ",").replace("_", ".")
    except (TypeError, ValueError):
        return "—"


def moeda(n: object) -> str:
    return "—" if n is None or pd.isna(n) else f"R$ {numero_br(n, 2)}"


def celula(valor: object) -> str:
    if valor is None or pd.isna(valor):
        return "—"
    if isinstance(valor, (pd.Timestamp, datetime)):
        return valor.strftime("%d/%m/%Y")
    text = str(valor).strip()
    return text if text else "—"


def contar_multiplos(grupo: pd.DataFrame) -> int:
    return grupo.loc[grupo["SITUACAO"].eq("Múltiplos check-ins"), "NF_NORMALIZADA"].nunique()


def montar_matriz(df: pd.DataFrame, *, com_checkin: bool, paleta: dict[str, str], ordenar_por_registros: bool = False) -> str:
    """HTML para components.html; colunas clicáveis, detalhes expansíveis e paginação de 75."""
    if com_checkin:
        colunas = [
            "NF Auto", "Origem", "Entrada Auto", "Valor Check-in",
            "Nº Check-in", "Status Check-in", "Fornecedor", "Situação",
        ]
        tipos_detalhe = ["identificador", "identificador", "data", "numero", "identificador", "texto", "texto", "texto"]
        headings = ["Loja / unidade", "Registros", "NFs únicas", "Valor localizado", "Múltiplos"]
    else:
        colunas = [
            "NF Auto", "Origem", "Emissão Auto", "Entrada Auto",
            "Dias", "Operação", "Situação",
        ]
        tipos_detalhe = ["identificador", "identificador", "data", "data", "numero", "identificador", "texto"]
        headings = ["Loja / unidade", "Registros", "NFs únicas"]

    grupos = []
    for loja, grupo in df.groupby("EMPRESA", sort=True, dropna=False):
        total_registros = len(grupo)
        total_nfs = int(grupo["NF_NORMALIZADA"].nunique())
        if com_checkin:
            linhas = [
                [
                    celula(r.NUMERONF), celula(r.NROEMP_ORIGEM), celula(r.DTAENTRADA),
                    moeda(r.VALOR_CHECKIN), celula(r.NUMERO_CHECKIN),
                    celula(r.STATUS_CHECKIN), celula(r.FORNECEDOR_CHECKIN),
                    celula(r.SITUACAO),
                ] for r in grupo.itertuples(index=False)
            ]
            valor_unico = grupo.loc[grupo["SITUACAO"].eq("Localizado")].drop_duplicates(
                ["COD_LOJA", "NF_NORMALIZADA"]
            )["VALOR_CHECKIN"].sum(min_count=1)
            valor_numerico = None if pd.isna(valor_unico) else float(valor_unico)
            quantidade_multiplos = int(contar_multiplos(grupo))
            extras = [moeda(valor_unico), numero_br(quantidade_multiplos)]
            ordenacao = [celula(loja), total_registros, total_nfs, valor_numerico, quantidade_multiplos]
        else:
            linhas = [
                [
                    celula(r.NUMERONF), celula(r.NROEMP_ORIGEM), celula(r.DTAEMISSAO),
                    celula(r.DTAENTRADA), celula(r.NRO_DIAS), celula(r.CODGERALOPER),
                    celula(r.SITUACAO),
                ] for r in grupo.itertuples(index=False)
            ]
            extras = []
            ordenacao = [celula(loja), total_registros, total_nfs]
        grupos.append({
            "loja": celula(loja),
            "registros": numero_br(total_registros),
            "notas": numero_br(total_nfs),
            "extras": extras,
            "sortKeys": ordenacao,
            "rows": linhas,
        })

    # Apenas na visão compartilhada: iniciar o ranking por maior quantidade de
    # registros sem check-in. As demais matrizes continuam na ordem original.
    if ordenar_por_registros:
        grupos.sort(key=lambda g: (-g["sortKeys"][1], str(g["sortKeys"][0])))

    # Escapa o JSON para impedir que texto da planilha encerre o <script> de dados.
    payload = json.dumps({
        "groups": grupos,
        "columns": colunas,
        "detailTypes": tipos_detalhe,
    }, ensure_ascii=False, default=str, allow_nan=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    grid_css = (
        "minmax(210px,1.5fr) minmax(100px,.48fr) minmax(95px,.48fr) minmax(150px,.9fr) minmax(105px,.5fr)"
        if com_checkin else
        "minmax(210px,1.5fr) minmax(100px,.5fr) minmax(95px,.5fr)"
    )
    css_vars = ";".join([
        f"--bg:{paleta['bg']}", f"--surface:{paleta['surface']}",
        f"--alt:{paleta['surface_alt']}", f"--text:{paleta['text']}",
        f"--muted:{paleta['muted']}", f"--line:{paleta['line']}",
        f"--head:{paleta['head']}", f"--head-text:{paleta['head_text']}",
        f"--blue:{paleta['blue']}", f"--orange:{paleta['orange']}",
        f"--grid:{grid_css}",
    ])
    html = r'''<!doctype html>
<html lang="pt-BR"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
:root {__THEME__}
* {box-sizing:border-box;}
body {font:14px/1.45 'Segoe UI',Arial,sans-serif;color:var(--text);background:var(--bg);margin:0;padding:0;}
.matrix {background:var(--surface);border:1px solid var(--line);border-radius:14px;overflow:hidden;}
.scroll {height:520px;overflow:auto;scrollbar-color:var(--line) transparent;}
.grid {display:grid;grid-template-columns:var(--grid);min-width:760px;align-items:center;gap:8px;padding:0 16px;}
.header {position:sticky;top:0;z-index:5;min-height:47px;background:var(--head);color:var(--head-text);font-size:12px;font-weight:750;}
.head-cell {min-width:0;}
.sort-button {width:100%;display:inline-flex;align-items:center;gap:6px;border:0;border-radius:4px;cursor:pointer;font-family:inherit;font-weight:750;text-align:left;white-space:nowrap;}
.head-sort {padding:12px 0;background:transparent;color:var(--head-text);font-size:12px;justify-content:flex-end;}
.head-cell:first-child .head-sort {justify-content:flex-start;}
.sort-button:hover {text-decoration:underline;text-underline-offset:3px;}
.sort-button:focus-visible {outline:2px solid var(--blue);outline-offset:2px;}
.sort-icon {font-size:11px;opacity:.7;flex:none;min-width:10px;}
.sort-button[data-active="true"] .sort-icon {opacity:1;color:var(--orange);}
details {border-bottom:1px solid var(--line);}
details:nth-child(even) {background:var(--alt);}
summary {list-style:none;cursor:pointer;min-height:50px;outline-offset:-2px;}
summary::-webkit-details-marker {display:none;}
summary:hover {background:rgba(111,166,186,.09);}
summary:focus-visible {outline:2px solid var(--blue);}
.summary>span {text-align:right;}
.label {display:flex;gap:12px;align-items:center;min-width:0;font-weight:730;}
.label .arrow {display:inline-flex;align-items:center;justify-content:center;flex:0 0 23px;height:23px;border:1px solid var(--line);border-radius:6px;color:var(--blue);font-size:19px;transform:rotate(0deg);transition:transform .12s;}
details[open] .arrow {transform:rotate(90deg);}
.label .name {white-space:nowrap;text-overflow:ellipsis;overflow:hidden;}
.ambiguous {color:var(--orange);font-weight:780;}
.content {background:var(--surface);padding:14px 16px 20px 20px;border-top:1px solid var(--line);}
.table-scroll {max-height:380px;overflow:auto;border:1px solid var(--line);border-radius:9px;}
table {width:100%;border-collapse:collapse;min-width:950px;font-size:12px;}
th {position:sticky;top:0;background:var(--head);color:var(--head-text);text-align:left;z-index:2;padding:0 12px;white-space:nowrap;}
.detail-sort {width:auto;max-width:100%;min-height:40px;padding:8px 0;background:transparent;color:var(--head-text);font-size:12px;}
td {padding:10px 12px;border-bottom:1px solid var(--line);color:var(--text);}
tr:nth-child(even) td {background:var(--alt);}
th:nth-child(4),td:nth-child(4) {white-space:nowrap;}
.pager {margin-top:10px;display:flex;justify-content:flex-end;align-items:center;gap:11px;color:var(--muted);font-size:12px;}
.pager button {border:1px solid var(--line);background:var(--alt);color:var(--text);padding:6px 11px;border-radius:7px;cursor:pointer;}
.pager button:disabled {opacity:.4;cursor:default;}
.foot {color:var(--muted);font-size:12px;padding:10px 3px;}
.empty {color:var(--muted);padding:24px;}
@media(max-width:780px) {.grid{min-width:760px}.scroll{height:500px}}
</style></head><body>
<div class="matrix"><div class="scroll" id="scroller"><div class="grid header" id="heading" role="row"></div><div id="groups"></div></div></div>
<div class="foot">Clique nos títulos para ordenar (▲ crescente / ▼ decrescente). Clique na seta de uma unidade para visualizar as notas, até 75 registros por página.</div>
<script id="payload" type="application/json">__DATA__</script>
<script>
'use strict';
const payload=JSON.parse(document.getElementById('payload').textContent);
const headings=__HEADINGS__;
const collator=new Intl.Collator('pt-BR',{numeric:true,sensitivity:'base'});
const root=document.getElementById('groups');
const head=document.getElementById('heading');
const scroller=document.getElementById('scroller');
const groupSort=__INITIAL_SORT__;
const detailState=new Map();
const detailsNodes=[];
const PAGE=75;
function esc(v){return String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');}
function empty(v){return v===null||v===undefined||String(v).trim()===''||String(v).trim()==='—';}
function parsed(v,type){
 if(empty(v))return null;
 if(type==='numero'){
  if(typeof v==='number')return Number.isFinite(v)?v:null;
  const s=String(v).replace(/\s|R\$/g,'').replace(/\./g,'').replace(',','.');
  const n=Number(s);return s && Number.isFinite(n)?n:null;
 }
 if(type==='data'){
  const m=String(v).match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  return m?Number(m[3]+m[2]+m[1]):null;
 }
 return String(v);
}
function compare(a,b,type,dir){
 const x=parsed(a,type),y=parsed(b,type);
 if(x===null||y===null)return x===null&&y===null?0:x===null?1:-1; // vazios sempre no fim
 let n;
 if(typeof x==='number'&&typeof y==='number') n=x===y?0:x<y?-1:1;
 else n=collator.compare(String(x),String(y));
 return n*dir;
}
function icon(ativo,direcao){return ativo?(direcao===1?'▲':'▼'):'↕';}
function renderHeading(){
 head.innerHTML=headings.map((label,j)=>{
  const ativo=groupSort.active&&groupSort.col===j;
  const sentido=ativo?(groupSort.direction===1?'crescente':'decrescente'):'não ordenado';
  return `<div class="head-cell" role="columnheader" aria-sort="${ativo?(groupSort.direction===1?'ascending':'descending'):'none'}"><button type="button" class="sort-button head-sort" data-col="${j}" data-active="${ativo}" title="Ordenar ${esc(label)} (${esc(sentido)})">${esc(label)}<span class="sort-icon" aria-hidden="true">${icon(ativo,groupSort.direction)}</span></button></div>`;
 }).join('');
 head.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>sortGroups(Number(b.dataset.col))));
}
function sortGroups(col){
 if(groupSort.active&&groupSort.col===col)groupSort.direction*=-1;
 else {groupSort.col=col;groupSort.direction=col===0?1:-1;groupSort.active=true;}
 renderHeading();
 const indices=payload.groups.map((_,i)=>i);
 const kind=col===0?'texto':'numero';
 indices.sort((a,b)=>compare(payload.groups[a].sortKeys[col],payload.groups[b].sortKeys[col],kind,groupSort.direction)||a-b);
 // Mover o mesmo <details> preserva os painéis já abertos e os eventos.
 const fragment=document.createDocumentFragment();
 indices.forEach(i=>fragment.appendChild(detailsNodes[i]));
 root.replaceChildren(fragment);
 scroller.scrollTop=0;
}
if(!payload.groups.length)root.innerHTML='<div class="empty">Nenhum registro para os filtros selecionados.</div>';
payload.groups.forEach((group,i)=>{
 const d=document.createElement('details');d.dataset.index=i;
 const s=document.createElement('summary');s.className='grid summary';
 s.innerHTML=`<div class="label"><span class="arrow">›</span><span class="name" title="${esc(group.loja)}">${esc(group.loja)}</span></div>`+
 `<span>${esc(group.registros)}</span><span>${esc(group.notas)}</span>`+
 group.extras.map((v,k)=>`<span class="${k===group.extras.length-1?'ambiguous':''}">${esc(v)}</span>`).join('');
 d.appendChild(s);
 const content=document.createElement('div');content.className='content';d.appendChild(content);
 d.addEventListener('toggle',()=>{if(d.open)renderPage(i,0);});
 detailsNodes.push(d);
 root.appendChild(d);
});
renderHeading();
function sortDetails(index,col){
 const g=payload.groups[index];
 let state=detailState.get(index);
 if(!state){state={col:null,direction:1,order:null};detailState.set(index,state);}
 if(state.col===col)state.direction*=-1;
 else {state.col=col;state.direction=payload.detailTypes[col]==='texto'?1:-1;}
 state.order=g.rows.map((_,i)=>i);
 const type=payload.detailTypes[col];
 state.order.sort((a,b)=>compare(g.rows[a][col],g.rows[b][col],type,state.direction)||a-b);
 renderPage(index,0);
}
function renderPage(index,page){
 // Índice estável mesmo quando as unidades mudam de posição ao ordenar.
 const d=detailsNodes[index];const g=payload.groups[index];const total=g.rows.length;
 const state=detailState.get(index);
 const pages=Math.max(1,Math.ceil(total/PAGE));page=Math.max(0,Math.min(pages-1,page));
 const start=page*PAGE;
 const activeCol=state?.col;
 const table=`<div class="table-scroll"><table><thead><tr>${payload.columns.map((v,j)=>{
  const ativo=activeCol===j;
  return `<th aria-sort="${ativo?(state.direction===1?'ascending':'descending'):'none'}"><button type="button" class="sort-button detail-sort" data-col="${j}" data-active="${ativo}" title="Ordenar ${esc(v)}">${esc(v)}<span class="sort-icon" aria-hidden="true">${icon(ativo,state?.direction)}</span></button></th>`;
 }).join('')}</tr></thead><tbody>`+
 (state?.order?state.order.slice(start,start+PAGE).map(i=>g.rows[i]):g.rows.slice(start,start+PAGE))
 .map(r=>`<tr>${r.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')+
 '</tbody></table></div>';
 d.querySelector('.content').innerHTML=table+`<div class="pager"><span>${start+1}–${Math.min(start+PAGE,total)} de ${total} registros</span><button data-dir="prev" ${page===0?'disabled':''}>Anterior</button><span>${page+1}/${pages}</span><button data-dir="next" ${page>=pages-1?'disabled':''}>Próxima</button></div>`;
 d.querySelectorAll('.detail-sort').forEach(b=>b.addEventListener('click',()=>sortDetails(index,Number(b.dataset.col))));
 d.querySelectorAll('.pager button').forEach(b=>b.addEventListener('click',e=>{
  e.preventDefault();renderPage(index,page+(b.dataset.dir==='next'?1:-1));
 }));
}
</script></body></html>'''
    ordenacao_inicial = (
        {"col": 1, "direction": -1, "active": True}
        if ordenar_por_registros else {"col": 0, "direction": 1, "active": False}
    )
    return html.replace("__THEME__", css_vars).replace("__DATA__", payload).replace(
        "__HEADINGS__", json.dumps(headings, ensure_ascii=False)
    ).replace("__INITIAL_SORT__", json.dumps(ordenacao_inicial))
