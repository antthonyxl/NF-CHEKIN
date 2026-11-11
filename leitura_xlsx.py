"""Leitor XLSX incremental: extrai somente as colunas pedidas sem openpyxl.

Projetado para planilhas de check-in grandes: não constrói milhões de objetos
Cell, como acontece na leitura tradicional por engines de planilha.
"""
from __future__ import annotations

import posixpath
import re
import xml.etree.ElementTree as ET
from io import BytesIO
from zipfile import ZipFile, BadZipFile

import pandas as pd

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL_DOC = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_REL_PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _indice_coluna(ref: str) -> int:
    p = re.match(r"[A-Z]+", ref or "")
    if p is None:
        return -1
    idx = 0
    for ch in p.group():
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def _valores_compartilhados(zipf: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zipf.namelist():
        return []
    strings = []
    with zipf.open("xl/sharedStrings.xml") as f:
        parser = ET.iterparse(f, events=("start", "end"))
        _, root = next(parser)
        for evento, el in parser:
            if evento == "end" and el.tag == NS + "si":
                strings.append("".join((t.text or "") for t in el.iter(NS + "t")))
                el.clear()
                root.clear()
    return strings


def _primeira_aba(zipf: ZipFile) -> str:
    livro = ET.fromstring(zipf.read("xl/workbook.xml"))
    aba = livro.find(NS + "sheets/" + NS + "sheet")
    if aba is None:
        raise ValueError("Arquivo Excel sem planilha")
    rel_id = aba.get(NS_REL_DOC + "id")
    rels = ET.fromstring(zipf.read("xl/_rels/workbook.xml.rels"))
    for rel in rels.findall(NS_REL_PKG + "Relationship"):
        if rel.get("Id") == rel_id:
            target = rel.get("Target") or ""
            if target.startswith("/"):
                return target.lstrip("/")
            return posixpath.normpath(posixpath.join("xl", target))
    raise ValueError("A primeira aba não pôde ser localizada no arquivo XLSX")


def ler_colunas_xlsx(conteudo: bytes, colunas: list[str]) -> pd.DataFrame:
    """Lê o primeiro sheet, preservando o valor literal e a ordem das linhas.

    Valores de data/valor chegam como texto ou números seriais e são convertidos
    posteriormente na etapa de conciliação. Campos não pedidos não são armazenados.
    """
    linhas: list[list[str | None]] = []
    try:
        with ZipFile(BytesIO(conteudo)) as zipf:
            strings = _valores_compartilhados(zipf)
            arquivo = _primeira_aba(zipf)
            with zipf.open(arquivo) as f:
                parser = ET.iterparse(f, events=("start", "end"))
                _, root = next(parser)
                indices: dict[int, int] = {}
                colunas_atuais: dict[int, str] = {}
                header_visto = False
                for evt, elem in parser:
                    if evt != "end" or elem.tag != NS + "row":
                        continue
                    if not header_visto:
                        for cell in elem.findall(NS + "c"):
                            pos = _indice_coluna(cell.get("r", ""))
                            colunas_atuais[pos] = _ler_celula(cell, strings) or ""
                        ausentes = set(colunas) - set(colunas_atuais.values())
                        if ausentes:
                            raise ValueError("Colunas ausentes: " + ", ".join(sorted(ausentes)))
                        mapa = {nome: pos for pos, nome in colunas_atuais.items()}
                        indices = {mapa[nome]: i for i, nome in enumerate(colunas)}
                        header_visto = True
                    else:
                        vals: list[str | None] = [None] * len(colunas)
                        for cell in elem.findall(NS + "c"):
                            pos = _indice_coluna(cell.get("r", ""))
                            j = indices.get(pos)
                            if j is not None:
                                vals[j] = _ler_celula(cell, strings)
                        linhas.append(vals)
                    elem.clear()
                    root.clear()
    except BadZipFile as e:
        raise ValueError("O arquivo carregado não é um XLSX válido") from e
    return pd.DataFrame(linhas, columns=colunas)


def _ler_celula(celula: ET.Element, strings: list[str]) -> str | None:
    t = celula.get("t")
    if t == "inlineStr":
        return "".join(x.text or "" for x in celula.iter(NS + "t"))
    v = celula.find(NS + "v")
    if v is None or v.text is None:
        return None
    if t == "s":
        return strings[int(v.text)]
    if t == "e":
        return None
    return v.text
