"""Pipeline de limpeza, transformacao e analise da Atividade 5."""

from pathlib import Path
from typing import BinaryIO, TextIO

import numpy as np
import pandas as pd


FonteCSV = str | Path | BinaryIO | TextIO

COLUNAS_TRANSACOES = {
    "id_cliente",
    "data_transacao",
    "valor",
    "origem",
    "estado_cliente",
}
COLUNAS_COTACOES = {"data", "cotacao_usd", "volume_negociado"}

RISCO_DICT = {
    "C100": "Baixo",
    "C101": "Alto",
    "C102": "Médio",
    "C103": "Baixo",
    "C104": "Alto",
}

DIAS_SEMANA = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


def _validar_colunas(
    dataframe: pd.DataFrame, obrigatorias: set[str], nome_arquivo: str
) -> None:
    ausentes = obrigatorias.difference(dataframe.columns)
    if ausentes:
        lista = ", ".join(sorted(ausentes))
        raise ValueError(f"{nome_arquivo} não contém as colunas: {lista}")


def carregar_transacoes(fonte: FonteCSV) -> pd.DataFrame:
    """Le o CSV legado sem corromper caracteres acentuados."""
    dataframe = pd.read_csv(fonte, encoding="latin1")
    _validar_colunas(dataframe, COLUNAS_TRANSACOES, "transacoes.csv")
    return dataframe


def carregar_cotacoes(fonte: FonteCSV) -> pd.DataFrame:
    """Le e valida o arquivo de cotacoes."""
    dataframe = pd.read_csv(fonte, encoding="utf-8")
    _validar_colunas(dataframe, COLUNAS_COTACOES, "cotacoes.csv")
    return dataframe


def limpar_transacoes(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Limpa e enriquece as transacoes usando operacoes vetorizadas."""
    df = dataframe.copy()
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    # Imputacao pela mediana do proprio estado; a mediana global e um fallback
    # para um eventual estado que possua todos os valores ausentes.
    medianas_estado = df.groupby("estado_cliente")["valor"].transform("median")
    df["valor"] = df["valor"].fillna(medianas_estado)
    df["valor"] = df["valor"].fillna(df["valor"].median())
    df["plataforma"] = "Mobile"

    datas = pd.to_datetime(df["data_transacao"], errors="coerce")
    if datas.isna().any():
        quantidade = int(datas.isna().sum())
        raise ValueError(
            f"Foram encontradas {quantidade} datas de transação inválidas."
        )
    if datas.dt.tz is None:
        datas = datas.dt.tz_localize(
            "America/Sao_Paulo", ambiguous="NaT", nonexistent="shift_forward"
        )
    else:
        datas = datas.dt.tz_convert("America/Sao_Paulo")
    df["data_transacao"] = datas

    # As duas colunas abaixo sao derivadas obrigatoriamente pelo acessor .dt.
    df["dia_semana"] = df["data_transacao"].dt.dayofweek.map(DIAS_SEMANA)
    df["mes"] = df["data_transacao"].dt.month

    # Mantem a primeira ocorrencia, conforme solicitado no enunciado.
    return df.drop_duplicates(keep="first").reset_index(drop=True)


def filtrar_transacoes_setembro(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Aplica o filtro solicitado exclusivamente com & e | vetorizados."""
    filtro = (
        (dataframe["mes"] == 9)
        & (
            (dataframe["estado_cliente"] == "SP")
            | (dataframe["estado_cliente"] == "RJ")
        )
        & (dataframe["valor"] > 5_000)
    )
    return dataframe.loc[filtro].copy()


def mapear_risco(
    dataframe: pd.DataFrame, risco_dict: dict[str, str] = RISCO_DICT
) -> pd.DataFrame:
    """Associa a categoria de risco por cliente por meio de Series.map."""
    df = dataframe.copy()
    df["nivel_risco"] = df["id_cliente"].map(risco_dict)
    df["nivel_risco"] = df["nivel_risco"].fillna("Não mapeado")
    return df


def criar_tabela_dinamica(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Soma valores por mes e risco, incluindo totais nas margens."""
    return pd.pivot_table(
        dataframe,
        values="valor",
        index="mes",
        columns="nivel_risco",
        aggfunc="sum",
        fill_value=0.0,
        margins=True,
        margins_name="Total Geral",
    )


def calcular_z_score_por_estado(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calcula Z-Score por estado sem lacos for."""
    df = dataframe.copy()
    agrupado = df.groupby("estado_cliente")["valor"]
    medias = agrupado.transform("mean")
    desvios = agrupado.transform("std").replace(0, np.nan)
    df["z_score"] = ((df["valor"] - medias) / desvios).fillna(0.0)
    return df


def filtrar_anomalias(
    dataframe: pd.DataFrame, limite: float = 2.5
) -> pd.DataFrame:
    """Retorna apenas anomalias superiores ao limiar definido."""
    return dataframe.loc[dataframe["z_score"] > limite].copy()


def limpar_cotacoes(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Trata datas, tipos e lacunas das cotacoes para a consolidacao."""
    df = dataframe.copy()
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    if df["data"].isna().any():
        raise ValueError("cotacoes.csv contém datas inválidas.")
    df["cotacao_usd"] = pd.to_numeric(df["cotacao_usd"], errors="coerce")
    df["volume_negociado"] = pd.to_numeric(
        df["volume_negociado"], errors="coerce"
    )
    df = df.sort_values("data").drop_duplicates("data", keep="first")
    df["cotacao_ausente_original"] = df["cotacao_usd"].isna()
    df["cotacao_usd"] = df["cotacao_usd"].interpolate(
        method="linear", limit_direction="both"
    )
    return df.reset_index(drop=True)


def consolidar_por_dia(
    transacoes: pd.DataFrame, cotacoes: pd.DataFrame
) -> pd.DataFrame:
    """Agrega transacoes por dia e alinha as cotacoes pela data."""
    base = transacoes.copy()
    base["data"] = (
        base["data_transacao"].dt.tz_localize(None).dt.normalize()
    )
    diario = (
        base.groupby("data", as_index=False)
        .agg(
            total_transacoes=("valor", "sum"),
            quantidade_transacoes=("id_cliente", "size"),
        )
        .sort_values("data")
    )
    diario["media_movel_7d"] = diario["total_transacoes"].rolling(7).mean()
    return diario.merge(
        cotacoes[["data", "cotacao_usd", "volume_negociado"]],
        on="data",
        how="left",
        validate="one_to_one",
    )


def executar_pipeline(
    fonte_transacoes: FonteCSV, fonte_cotacoes: FonteCSV
) -> dict[str, object]:
    """Executa o pipeline completo e devolve bases e indicadores."""
    transacoes_brutas = carregar_transacoes(fonte_transacoes)
    cotacoes_brutas = carregar_cotacoes(fonte_cotacoes)
    transacoes = mapear_risco(limpar_transacoes(transacoes_brutas))
    transacoes_z = calcular_z_score_por_estado(transacoes)
    cotacoes = limpar_cotacoes(cotacoes_brutas)

    return {
        "transacoes": transacoes_z,
        "filtro_setembro": filtrar_transacoes_setembro(transacoes_z),
        "anomalias": filtrar_anomalias(transacoes_z),
        "pivot_risco": criar_tabela_dinamica(transacoes_z),
        "cotacoes": cotacoes,
        "consolidado_diario": consolidar_por_dia(transacoes_z, cotacoes),
        "linhas_brutas": len(transacoes_brutas),
        "duplicatas_removidas": len(transacoes_brutas) - len(transacoes_z),
        "valores_imputados": int(transacoes_brutas["valor"].isna().sum()),
        "cotacoes_interpoladas": int(cotacoes["cotacao_ausente_original"].sum()),
    }
