"""Exporta apenas campos que o dashboard NF x CHECK-IN utiliza.

Não modifica o Excel. Preserva identificadores como textos e datas seriais
originais, para evitar truncamento/erros de inferência de tipos pelo BigQuery.
Uso: python preparar_csv.py /caminho/ENTRADA...xlsx /caminho/CHECKIN.xlsx
"""
from __future__ import annotations
import csv
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
CAMPOS_AUTO = [('EMPRESA','empresa'),('NROEMP_ORIGEM','nroemp_origem'),('NUMERONF','numeronf'),('NFECHAVEACESSO','nfechaveacesso'),('CODGERALOPER','codgeraloper'),('DTAEMISSAO','dtaemissao'),('DTAENTRADA','dtaentrada'),('NRO_DIAS','nro_dias')]
CAMPOS_CHECKIN = [('Data','data'),('Entrada','entrada'),('Loja','loja'),('Nota','nota'),('Fornecedor','fornecedor'),('Valor','valor'),('Status NF','status_nf'),('Check-In','check_in'),('Status Check-In','status_check_in'),('Chave','chave')]


def shared_strings(arquivo):
    if 'xl/sharedStrings.xml' not in arquivo.namelist():
        return []
    strings=[]
    with arquivo.open('xl/sharedStrings.xml') as f:
        parser=ET.iterparse(f,events=('start','end'))
        _,root=next(parser)
        for evento,el in parser:
            if evento=='end' and el.tag==NS+'si':
                strings.append(''.join(t.text or '' for t in el.iter(NS+'t')))
                el.clear()
                root.clear()
    return strings


def celula(c,strings):
    t=c.attrib.get('t')
    if t=='inlineStr':
        return ''.join(x.text or '' for x in c.iter(NS+'t'))
    v=c.find(NS+'v')
    if v is None or v.text is None: return ''
    if t=='s': return strings[int(v.text)]
    if t=='e': return ''
    return v.text


def extrair(entrada: Path, saida: Path, campos):
    with zipfile.ZipFile(entrada) as z:
        strings=shared_strings(z)
        with z.open('xl/worksheets/sheet1.xml') as f, saida.open('w',encoding='utf-8',newline='') as fo:
            writer=csv.writer(fo)
            writer.writerow([s for _,s in campos])
            parser=ET.iterparse(f,events=('start','end'))
            _,root=next(parser)
            header=None
            posicoes=None
            total=0
            for event, row in parser:
                if event!='end' or row.tag!=NS+'row': continue
                values={}
                for c in row.findall(NS+'c'):
                    m=re.match(r'[A-Z]+',c.attrib.get('r',''))
                    if m:values[m.group()]=celula(c,strings)
                if header is None:
                    header={v:k for k,v in values.items()}
                    ausentes=[a for a,_ in campos if a not in header]
                    if ausentes: raise ValueError(f'Campos ausentes em {entrada.name}: {ausentes}')
                    posicoes=[header[a] for a,_ in campos]
                else:
                    vals=[values.get(p,'') for p in posicoes]
                    if any(v.strip() for v in vals):
                        if campos is CAMPOS_CHECKIN:
                            # O Excel contém 44 dígitos literais prefixados por apóstrofo.
                            vals[-1]=vals[-1].lstrip("'").strip()
                        writer.writerow(vals)
                        total+=1
                row.clear();root.clear()
    return total


def main():
    if len(sys.argv)!=3: raise SystemExit('Uso: python preparar_csv.py entrada_auto_nf.xlsx CHECKIN.xlsx')
    root=Path(__file__).resolve().parent
    for entrada,nome,campos in [(Path(sys.argv[1]),'carga_auto_nf.csv',CAMPOS_AUTO),(Path(sys.argv[2]),'carga_checkin.csv',CAMPOS_CHECKIN)]:
        total=extrair(entrada,root/nome,campos)
        print(f'{nome}: {total:,} registros')

if __name__=='__main__': main()
