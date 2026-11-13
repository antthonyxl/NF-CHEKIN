import json
import re
import unittest

import pandas as pd

from custo_nf import associar_custos, somar_custo_sem_checkin
from matriz import montar_matriz

PALETA = {
    "bg": "#f4f5f6", "surface": "#fff", "surface_alt": "#eef3f6",
    "text": "#111", "muted": "#777", "line": "#ccc", "head": "#10343d",
    "head_text": "#fff", "blue": "#2388f7", "orange": "#eb963e",
}


def auto_base():
    return pd.DataFrame([
        {"COD_LOJA": 1, "NF_NORMALIZADA": "33713", "EMPRESA": "001-CARPINA", "NUMERONF": "33713", "NROEMP_ORIGEM": "21", "DTAEMISSAO": pd.Timestamp('2026-10-03'), "DTAENTRADA": pd.Timestamp('2026-10-04'), "NRO_DIAS": "1", "CODGERALOPER": "50", "SITUACAO": "Sem check-in"},
        {"COD_LOJA": 1, "NF_NORMALIZADA": "33713", "EMPRESA": "001-CARPINA", "NUMERONF": "33713", "NROEMP_ORIGEM": "21", "DTAEMISSAO": pd.Timestamp('2026-10-03'), "DTAENTRADA": pd.Timestamp('2026-10-04'), "NRO_DIAS": "1", "CODGERALOPER": "50", "SITUACAO": "Sem check-in"},
        {"COD_LOJA": 2, "NF_NORMALIZADA": "33713", "EMPRESA": "002-LOJA", "NUMERONF": "33713", "NROEMP_ORIGEM": "998", "DTAEMISSAO": pd.Timestamp('2026-10-03'), "DTAENTRADA": pd.Timestamp('2026-10-04'), "NRO_DIAS": "1", "CODGERALOPER": "50", "SITUACAO": "Sem check-in"},
        {"COD_LOJA": 3, "NF_NORMALIZADA": "22", "EMPRESA": "003-LOJA", "NUMERONF": "22", "NROEMP_ORIGEM": "998", "DTAEMISSAO": pd.Timestamp('2026-10-03'), "DTAENTRADA": pd.Timestamp('2026-10-04'), "NRO_DIAS": "1", "CODGERALOPER": "50", "SITUACAO": "Sem check-in"},
    ])


def custos_base():
    return pd.DataFrame([
        {"COD_EMPRESA": "1", "NF": "033713", "SERIE": "1", "Quantidade": "2", "Custo Liquido": "368.49"},
        {"COD_EMPRESA": "1", "NF": "033713", "SERIE": "1", "Quantidade": "2", "Custo Liquido": "368.49"},  # idêntica
        {"COD_EMPRESA": "2", "NF": "33713", "SERIE": "1", "Quantidade": "6.5", "Custo Liquido": "100.5"},
        {"COD_EMPRESA": "2", "NF": "33713", "SERIE": "2", "Quantidade": "8", "Custo Liquido": "125.0"},  # séries diferentes
    ])


class TestCusto(unittest.TestCase):
    def test_mesma_nf_em_lojas_diferentes_e_conflito(self):
        dados = associar_custos(auto_base(), custos_base())
        self.assertEqual(len(dados), 4)
        self.assertEqual(dados.loc[0, "CUSTO_LIQUIDO"], 368.49)
        self.assertEqual(dados.loc[1, "CUSTO_LIQUIDO"], 368.49)
        self.assertEqual(dados.loc[0, "SITUACAO_CUSTO"], "Localizado")
        self.assertEqual(dados.loc[2, "SITUACAO_CUSTO"], "Múltiplos custos")
        self.assertTrue(pd.isna(dados.loc[2, "CUSTO_LIQUIDO"]))
        self.assertEqual(dados.loc[3, "SITUACAO_CUSTO"], "Não localizado")
        self.assertTrue(pd.isna(dados.loc[3, "QUANTIDADE_CUSTO"]))

    def test_valor_divergente_mesma_serie_nao_soma(self):
        custos = custos_base().iloc[:1].copy()
        custos.loc[1] = ["1", "33713", "1", "17", "999.00"]
        dados = associar_custos(auto_base(), custos)
        self.assertEqual(dados.loc[0, "SITUACAO_CUSTO"], "Múltiplos custos")
        self.assertTrue(pd.isna(dados.loc[0, "QUANTIDADE_CUSTO"]))

    def test_ordenacao_matriz_e_totais_nao_duplicam_nf(self):
        dados = associar_custos(auto_base(), custos_base())
        html = montar_matriz(dados, com_checkin=False, paleta=PALETA, ordenar_por_registros=True)
        payload = json.loads(re.search(r'<script id="payload" type="application/json">(.*?)</script>', html, re.S).group(1))
        self.assertEqual(payload["columns"][7:9], ["Quantidade", "Custo líquido"])
        self.assertEqual(payload["detailTypes"][7:9], ["numero", "numero"])
        self.assertEqual(payload["groups"][0]["loja"], "001-CARPINA")
        self.assertEqual(payload["groups"][0]["extras"], ["2", "R$ 368,49"])
        self.assertEqual(payload["groups"][0]["sortKeys"], ["001-CARPINA", 2, 1, 2.0, 368.49])
        self.assertIn('"direction": -1', html)


    def test_kpi_soma_custo_sem_checkin_sem_duplicar_loja_nf(self):
        dados = associar_custos(auto_base(), custos_base())
        pendentes = dados.loc[dados["SITUACAO"].isin(["Sem check-in", "Chave inválida"])]
        self.assertEqual(somar_custo_sem_checkin(pendentes), 368.49)

    def test_visao_apresentacao_inicia_por_custo_crescente(self):
        dados = associar_custos(auto_base(), custos_base())
        html = montar_matriz(
            dados, com_checkin=False, paleta=PALETA, ordenar_por_custo_ascendente=True
        )
        raw = re.search(r'<script id="payload" type="application/json">(.*?)</script>', html, re.S)
        payload = json.loads(raw.group(1))
        self.assertEqual(
            [g["loja"] for g in payload["groups"]],
            ["001-CARPINA", "002-LOJA", "003-LOJA"],
        )
        self.assertIn('"col": 4, "direction": 1, "active": true', html)

    def test_quantidade_fracionaria_e_localidade(self):
        c = pd.DataFrame([{"COD_EMPRESA": "1", "NF": "33713", "SERIE": "001", "Quantidade": "6,25", "Custo Liquido": "1.234,56"}])
        d = associar_custos(auto_base(), c)
        self.assertEqual(d.loc[0, "QUANTIDADE_CUSTO"], 6.25)
        self.assertEqual(d.loc[0, "CUSTO_LIQUIDO"], 1234.56)


if __name__ == "__main__":
    unittest.main()
