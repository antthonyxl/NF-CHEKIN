import unittest
import pandas as pd

from conciliacao import COLUNAS_AUTO, COLUNAS_CHECKIN, conciliar, normalizar_numero_nf, extrair_codigo_loja, converter_data


class ConciliaNotasTest(unittest.TestCase):
    def setUp(self):
        self.auto = pd.DataFrame([
            ["001-CARPINA", 21, "75137", "chave", 50, 46295, 46296, -1],
            ["002-VIT.SA", 21, "75137", "chave", 50, 46295, 46296, -1],
            ["998-CD FLV", 3, "0009429", "chave", 50, 46331, 46332, -1],
            ["001-CARPINA", 21, "75137", "chave", 50, 46295, 46296, -1],
            ["001-CARPINA", 21, "999999", "chave", 50, 46295, 46296, -1],
        ], columns=COLUNAS_AUTO)
        self.ck = pd.DataFrame([
            [46296, 46296, "NOVO - 01 - Carpina Centro", "00075137-1", "Fornecedor A", 100.50, "Recebida", "123", "Finalizado", "k1"],
            [46331, 46331, "998 - CD FLV / PER", "9429-001", "Fornecedor B", 15.25, "Recebida", "456", "Finalizado", "k2"],
            [46332, 46332, "998 - CD FLV / PER", "9429-1", "Fornecedor C", 33.25, "Recebida", "457", "Em Conferência", "k3"],
            [46295, 46295, "MATEUS - 02 - Vitória", "333333-1", "Fornecedor D", 15, "Recebida", "456", "Finalizado", "k4"],
        ], columns=COLUNAS_CHECKIN)

    def test_normalizacao(self):
        s = normalizar_numero_nf(pd.Series(["00075137-001", "1776754-001", "55", "0012.0"]), retirar_serie=True)
        self.assertEqual(s.tolist(), ["75137", "1776754", "55", "12"])

    def test_codigos_loja(self):
        s = pd.Series(["NOVO - 01 - Carpina", "MATEUS - 02 - Vitória", "998 - CD FLV", "995-CD SECO PB"])
        self.assertEqual(extrair_codigo_loja(s, auto=False).tolist(), [1, 2, 998, 995])

    def test_dados_e_cardinalidade(self):
        out, candidatos, kpi = conciliar(self.auto, self.ck)
        self.assertEqual(len(out), len(self.auto))
        self.assertEqual(kpi["localizados"], 2)
        self.assertEqual(kpi["multiplos"], 1)
        self.assertEqual(kpi["sem_checkin"], 2)
        self.assertEqual(kpi["auto_repetidos"], 1)
        self.assertEqual(len(candidatos), 2)
        self.assertEqual(out.loc[0, "VALOR_CHECKIN"], 100.50)
        self.assertTrue(pd.isna(out.loc[2, "VALOR_CHECKIN"]))
        self.assertEqual(kpi["valor_localizado_unico"], 100.50)

    def test_datas_excel(self):
        serial = converter_data(pd.Series([46296, 46332]))
        self.assertEqual(str(serial.iloc[0].date()), "2026-10-01")
        self.assertEqual(str(serial.iloc[1].date()), "2026-11-06")
        dt = converter_data(pd.to_datetime(pd.Series(["2026-11-01", "2026-11-02"])))
        self.assertEqual(str(dt.iloc[0].date()), "2026-11-01")


if __name__ == "__main__":
    unittest.main()
