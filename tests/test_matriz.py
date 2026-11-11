"""Valida criação de matrizes ordenáveis sem alterar os dados conciliados."""
import json
import re
import unittest

import pandas as pd

from matriz import montar_matriz


PALETA = {
    "bg": "#f5f5f5", "surface": "#ffffff", "surface_alt": "#eeeeee",
    "text": "#111111", "muted": "#888888", "line": "#dddddd",
    "head": "#10343d", "head_text": "#ffffff", "blue": "#2488ff",
    "orange": "#eb963e",
}


def dados_teste():
    return pd.DataFrame([
        {
            "EMPRESA": "001-LOJA A", "NUMERONF": "11", "NROEMP_ORIGEM": "1",
            "DTAEMISSAO": pd.Timestamp("2026-10-04"),
            "DTAENTRADA": pd.Timestamp("2026-11-02"), "NRO_DIAS": 29,
            "CODGERALOPER": "1", "SITUACAO": "Localizado", "NF_NORMALIZADA": "11",
            "COD_LOJA": 1, "VALOR_CHECKIN": 1234.50, "NUMERO_CHECKIN": "123",
            "STATUS_CHECKIN": "Recebido", "FORNECEDOR_CHECKIN": "Fornecedor <test>",
        },
        {
            "EMPRESA": "002-LOJA B", "NUMERONF": "30", "NROEMP_ORIGEM": "2",
            "DTAEMISSAO": pd.Timestamp("2026-09-01"),
            "DTAENTRADA": pd.Timestamp("2026-10-01"), "NRO_DIAS": 30,
            "CODGERALOPER": "2", "SITUACAO": "Localizado", "NF_NORMALIZADA": "30",
            "COD_LOJA": 2, "VALOR_CHECKIN": 5000.00, "NUMERO_CHECKIN": "456",
            "STATUS_CHECKIN": "Recebido", "FORNECEDOR_CHECKIN": "Fornecedor B",
        },
        {
            "EMPRESA": "002-LOJA B", "NUMERONF": "5", "NROEMP_ORIGEM": "2",
            "DTAEMISSAO": pd.Timestamp("2026-08-01"),
            "DTAENTRADA": pd.Timestamp("2026-09-01"), "NRO_DIAS": 31,
            "CODGERALOPER": "3", "SITUACAO": "Localizado", "NF_NORMALIZADA": "5",
            "COD_LOJA": 2, "VALOR_CHECKIN": 700.00, "NUMERO_CHECKIN": "789",
            "STATUS_CHECKIN": "Recebido", "FORNECEDOR_CHECKIN": "Fornecedor C",
        },
    ])


class MatrizTest(unittest.TestCase):
    def test_matriz_com_checkin_tem_chaves_numericas_para_ordenacao(self):
        html = montar_matriz(dados_teste(), com_checkin=True, paleta=PALETA)
        raw = re.search(r'<script id="payload" type="application/json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(raw)
        groups = json.loads(raw.group(1))["groups"]
        self.assertEqual([g["loja"] for g in groups], ["001-LOJA A", "002-LOJA B"])
        self.assertEqual(groups[0]["sortKeys"], ["001-LOJA A", 1, 1, 1234.5, 0])
        self.assertEqual(groups[1]["sortKeys"], ["002-LOJA B", 2, 2, 5700.0, 0])
        self.assertIn("function sortGroups(col)", html)
        self.assertIn("function sortDetails(index,col)", html)
        self.assertIn("aria-sort", html)

    def test_matriz_sem_checkin_tem_ordenacao_e_paginacao(self):
        html = montar_matriz(dados_teste(), com_checkin=False, paleta=PALETA)
        self.assertIn("const PAGE=75;", html)
        self.assertIn("function sortGroups(col)", html)
        self.assertIn('"detailTypes": ["identificador", "identificador", "data", "data", "numero"', html)

    def test_texto_externo_nao_fecha_script(self):
        df = dados_teste()
        df.loc[0, "FORNECEDOR_CHECKIN"] = "</script><script>alert(1)</script>"
        html = montar_matriz(df, com_checkin=True, paleta=PALETA)
        self.assertNotIn("</script><script>alert(1)</script>", html)
        self.assertIn("\\u003c/script\\u003e", html)


if __name__ == "__main__":
    unittest.main()
