"""Dashboard Streamlit para a Atividade de Fixacao 5."""

from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.ticker import FuncFormatter

from processamento import executar_pipeline


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

st.set_page_config(
    page_title="Fintech | Análise de Transações",
    page_icon="📊",
    layout="wide",
)


def moeda(valor: float) -> str:
    """Formata um numero no padrao monetario brasileiro."""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


@st.cache_data(show_spinner=False)
def processar_arquivos(
    bytes_transacoes: bytes | None, bytes_cotacoes: bytes | None
) -> dict[str, object]:
    """Usa uploads, quando informados; caso contrario, usa a base local."""
    fonte_transacoes = (
        BytesIO(bytes_transacoes)
        if bytes_transacoes is not None
        else DATA_DIR / "transacoes.csv"
    )
    fonte_cotacoes = (
        BytesIO(bytes_cotacoes)
        if bytes_cotacoes is not None
        else DATA_DIR / "cotacoes.csv"
    )
    return executar_pipeline(fonte_transacoes, fonte_cotacoes)


def grafico_transacoes(diario: pd.DataFrame) -> plt.Figure:
    """Cria o grafico exigido usando a API orientada a objetos."""
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(
        diario["data"],
        diario["total_transacoes"],
        color="#2563EB",
        linewidth=1.8,
        label="Total diário",
    )
    ax.plot(
        diario["data"],
        diario["media_movel_7d"],
        color="#F97316",
        linewidth=2.5,
        label="Média móvel de 7 dias",
    )
    ax.set_ylim(bottom=0)
    ax.set_title("Volume financeiro diário e tendência de 7 dias")
    ax.set_xlabel("Data")
    ax.set_ylabel("Valor total (R$)")
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda valor, _: moeda(valor).replace("R$ ", "R$"))
    )
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def grafico_cotacoes(cotacoes: pd.DataFrame) -> plt.Figure:
    """Apresenta a serie de cotacao usada no alinhamento diario."""
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(
        cotacoes["data"],
        cotacoes["cotacao_usd"],
        color="#0F766E",
        marker="o",
        markersize=3,
        label="Cotação USD",
    )
    interpoladas = cotacoes.loc[cotacoes["cotacao_ausente_original"]]
    ax.scatter(
        interpoladas["data"],
        interpoladas["cotacao_usd"],
        color="#DC2626",
        zorder=3,
        label="Valor interpolado",
    )
    ax.set_title("Cotação diária do dólar")
    ax.set_xlabel("Data")
    ax.set_ylabel("R$ por US$ 1")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


st.title("Análise de transações financeiras")
st.caption(
    "Pipeline de limpeza, consolidação, métricas de risco e detecção de anomalias."
)

with st.sidebar:
    st.header("Fontes de dados")
    st.write("Sem upload, a aplicação utiliza os CSVs da pasta `data/`.")
    upload_transacoes = st.file_uploader(
        "transacoes.csv (Latin-1)", type="csv", key="transacoes"
    )
    upload_cotacoes = st.file_uploader(
        "cotacoes.csv (UTF-8)", type="csv", key="cotacoes"
    )
    st.divider()
    st.info(
        "O Z-Score é calculado separadamente por estado. "
        "São sinalizados os registros com Z > 2,5."
    )

try:
    resultado = processar_arquivos(
        upload_transacoes.getvalue() if upload_transacoes else None,
        upload_cotacoes.getvalue() if upload_cotacoes else None,
    )
except (FileNotFoundError, UnicodeDecodeError, ValueError) as erro:
    st.error(f"Não foi possível processar os arquivos: {erro}")
    st.info("Execute `python dados.py` para gerar os arquivos padrão.")
    st.stop()

transacoes = resultado["transacoes"]
anomalias = resultado["anomalias"]
diario = resultado["consolidado_diario"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Transações válidas", f"{len(transacoes):,}".replace(",", "."))
col2.metric("Valor total", moeda(transacoes["valor"].sum()))
col3.metric("Ticket médio", moeda(transacoes["valor"].mean()))
col4.metric("Anomalias (Z > 2,5)", len(anomalias))

aba_resumo, aba_filtro, aba_risco, aba_anomalias, aba_cotacoes = st.tabs(
    [
        "Visão geral",
        "Filtro bitwise",
        "Risco e pivot",
        "Anomalias",
        "Cotações e qualidade",
    ]
)

with aba_resumo:
    st.subheader("Evolução das transações")
    figura = grafico_transacoes(diario)
    st.pyplot(figura, width="stretch")
    plt.close(figura)

    st.subheader("Dados consolidados por dia")
    st.dataframe(
        diario,
        width="stretch",
        hide_index=True,
        column_config={
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "total_transacoes": st.column_config.NumberColumn(
                "Total das transações", format="R$ %.2f"
            ),
            "media_movel_7d": st.column_config.NumberColumn(
                "Média móvel (7 dias)", format="R$ %.2f"
            ),
            "cotacao_usd": st.column_config.NumberColumn(
                "Cotação USD", format="R$ %.4f"
            ),
        },
    )

with aba_filtro:
    st.subheader("Transações de setembro em SP ou RJ acima de R$ 5.000")
    st.code(
        "(mes == 9) & ((estado == 'SP') | (estado == 'RJ')) & (valor > 5000)",
        language="python",
    )
    filtro_setembro = resultado["filtro_setembro"]
    st.write(f"Foram encontrados **{len(filtro_setembro)} registros**.")
    st.dataframe(
        filtro_setembro[
            [
                "id_cliente",
                "data_transacao",
                "estado_cliente",
                "valor",
                "origem",
                "nivel_risco",
            ]
        ],
        width="stretch",
        hide_index=True,
        column_config={
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")
        },
    )

with aba_risco:
    st.subheader("Tabela dinâmica: valor por mês e nível de risco")
    st.caption(
        "Criada com `pivot_table`, soma de valores e `margins=True`."
    )
    pivot_exibicao = resultado["pivot_risco"].copy()
    # O total geral torna o indice misto (inteiro e texto); a conversao evita
    # ambiguidade na serializacao da tabela pelo Streamlit/Arrow.
    pivot_exibicao.index = pivot_exibicao.index.map(str)
    st.dataframe(pivot_exibicao.style.format(moeda), width="stretch")

    st.subheader("Mapeamento de risco aplicado")
    mapa_risco = (
        transacoes[["id_cliente", "nivel_risco"]]
        .drop_duplicates()
        .sort_values("id_cliente")
    )
    st.dataframe(mapa_risco, hide_index=True, width="stretch")

with aba_anomalias:
    st.subheader("Potenciais anomalias ou fraudes")
    st.latex(r"Z = \frac{x - \mu_{estado}}{\sigma_{estado}}")
    if anomalias.empty:
        st.success("Nenhuma transação ultrapassou o limiar Z > 2,5.")
    else:
        st.warning(f"{len(anomalias)} transações requerem análise.")
        st.dataframe(
            anomalias[
                [
                    "id_cliente",
                    "data_transacao",
                    "estado_cliente",
                    "valor",
                    "nivel_risco",
                    "z_score",
                ]
            ].sort_values("z_score", ascending=False),
            width="stretch",
            hide_index=True,
            column_config={
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "z_score": st.column_config.NumberColumn("Z-Score", format="%.3f"),
            },
        )

with aba_cotacoes:
    st.subheader("Cotações alinhadas ao relatório diário")
    figura_cotacoes = grafico_cotacoes(resultado["cotacoes"])
    st.pyplot(figura_cotacoes, width="stretch")
    plt.close(figura_cotacoes)

    st.subheader("Resumo de qualidade dos dados")
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Linhas recebidas", resultado["linhas_brutas"])
    q2.metric("Duplicatas removidas", resultado["duplicatas_removidas"])
    q3.metric("Valores imputados", resultado["valores_imputados"])
    q4.metric("Cotações interpoladas", resultado["cotacoes_interpoladas"])

    csv_processado = transacoes.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar transações tratadas",
        data=csv_processado,
        file_name="transacoes_tratadas.csv",
        mime="text/csv",
    )
