from pathlib import Path

import pandas as pd

from dados import gerar_dados
from processamento import executar_pipeline


def test_pipeline_atende_as_regras_principais(tmp_path: Path) -> None:
    transacoes_csv, cotacoes_csv = gerar_dados(pasta_saida=tmp_path)
    resultado = executar_pipeline(transacoes_csv, cotacoes_csv)
    transacoes = resultado["transacoes"]

    assert resultado["linhas_brutas"] == 1015
    assert resultado["duplicatas_removidas"] == 15
    assert transacoes["valor"].isna().sum() == 0
    assert transacoes["plataforma"].eq("Mobile").all()
    assert str(transacoes["data_transacao"].dt.tz) == "America/Sao_Paulo"
    assert {"dia_semana", "mes", "nivel_risco", "z_score"}.issubset(
        transacoes.columns
    )


def test_filtro_bitwise_respeita_todas_as_condicoes(tmp_path: Path) -> None:
    transacoes_csv, cotacoes_csv = gerar_dados(pasta_saida=tmp_path)
    filtradas = executar_pipeline(transacoes_csv, cotacoes_csv)["filtro_setembro"]

    assert filtradas["mes"].eq(9).all()
    assert filtradas["estado_cliente"].isin(["SP", "RJ"]).all()
    assert filtradas["valor"].gt(5_000).all()


def test_pivot_e_anomalias(tmp_path: Path) -> None:
    transacoes_csv, cotacoes_csv = gerar_dados(pasta_saida=tmp_path)
    resultado = executar_pipeline(transacoes_csv, cotacoes_csv)
    pivot = resultado["pivot_risco"]
    anomalias = resultado["anomalias"]

    assert "Total Geral" in pivot.index
    assert "Total Geral" in pivot.columns
    assert anomalias["z_score"].gt(2.5).all()
    assert pd.notna(resultado["cotacoes"]["cotacao_usd"]).all()
