"""Gera os arquivos de entrada usados na Atividade de Fixacao 5."""

from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def gerar_dados(seed: int = 42, pasta_saida: Path = DATA_DIR) -> tuple[Path, Path]:
    """Gera transacoes.csv e cotacoes.csv de forma reprodutivel."""
    np.random.seed(seed)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    datas_transacoes = pd.date_range(
        start="2026-09-01", periods=1000, freq="h"
    )
    df_transacoes = pd.DataFrame(
        {
            "id_cliente": np.random.choice(
                ["C100", "C101", "C102", "C103", "C104"], size=1000
            ),
            "data_transacao": datas_transacoes,
            "valor": np.random.choice(
                [np.nan, 150.0, 3000.0, 7500.0, 12000.0, 50.0],
                size=1000,
                p=[0.05, 0.40, 0.30, 0.15, 0.05, 0.05],
            ),
            "estado_cliente": np.random.choice(
                ["SP", "RJ", "MG", "RS"], size=1000
            ),
            "origem": np.random.choice(
                ["web", "mobile_app", "atm"], size=1000
            ),
        }
    )

    # Insere 15 duplicatas de proposito para exercitar a etapa de limpeza.
    df_transacoes = pd.concat(
        [df_transacoes, df_transacoes.iloc[:15]], ignore_index=True
    )
    caminho_transacoes = pasta_saida / "transacoes.csv"
    df_transacoes.to_csv(caminho_transacoes, index=False, encoding="latin1")

    datas_cotacoes = pd.date_range(
        start="2026-09-01", end="2026-10-01", freq="D"
    )
    variacoes = np.random.normal(
        loc=0.001, scale=0.015, size=len(datas_cotacoes)
    )
    preco_inicial = 5.20
    precos = preco_inicial * np.exp(np.cumsum(variacoes))

    df_cotacoes = pd.DataFrame(
        {
            "data": datas_cotacoes,
            "cotacao_usd": np.round(precos, 4),
            "volume_negociado": np.random.randint(
                10_000, 500_000, size=len(datas_cotacoes)
            ),
        }
    )
    df_cotacoes.loc[5, "cotacao_usd"] = np.nan
    df_cotacoes.loc[18, "cotacao_usd"] = np.nan
    caminho_cotacoes = pasta_saida / "cotacoes.csv"
    df_cotacoes.to_csv(caminho_cotacoes, index=False, encoding="utf-8")

    return caminho_transacoes, caminho_cotacoes


if __name__ == "__main__":
    transacoes, cotacoes = gerar_dados()
    print("Arquivos gerados com sucesso:")
    print(f"- {transacoes}")
    print(f"- {cotacoes}")
