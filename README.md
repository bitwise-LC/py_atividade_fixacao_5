# Atividade de Fixação 5 — Análise de Dados de uma Fintech

Aplicação Streamlit que executa um pipeline completo de ingestão, limpeza,
transformação, consolidação, detecção de anomalias e visualização de transações
financeiras.

## Como executar

No terminal, entre na pasta do projeto e execute:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python dados.py
streamlit run app.py
```

O navegador abrirá o painel. A aplicação usa por padrão os arquivos da pasta
`data/`, mas também aceita outros CSVs pelos campos de upload da barra lateral.

## Estrutura

```text
AtvFixacao5/
├── app.py                    # interface e gráficos do dashboard
├── dados.py                  # geração reprodutível dos dois CSVs
├── processamento.py          # pipeline de dados e regras do exercício
├── data/
│   ├── transacoes.csv        # gerado em Latin-1
│   └── cotacoes.csv          # gerado em UTF-8
├── tests/
│   └── test_processamento.py
├── requirements.txt
└── README.md
```

## Requisitos atendidos

- leitura de `transacoes.csv` com `encoding="latin1"`;
- imputação de `valor` pela mediana do respectivo estado;
- coluna estática `plataforma = "Mobile"`;
- conversão para datetime e `tz_localize("America/Sao_Paulo")`;
- dia da semana e mês obtidos com o acessor `.dt`;
- remoção de duplicatas, mantendo a primeira ocorrência;
- filtro vetorizado de setembro com os operadores bitwise `&` e `|`;
- risco associado por `Series.map()`;
- `pivot_table` por mês e risco, incluindo `margins=True`;
- Z-Score vetorizado por estado e seleção de casos com `Z > 2.5`;
- gráfico Matplotlib pela API orientada a objetos (`fig, ax = plt.subplots()`),
  contendo o total diário e a média móvel de sete dias;
- eixo Y iniciado em zero por `ax.set_ylim(bottom=0)`;
- tratamento e alinhamento diário das cotações com as transações;
- testes automatizados para as principais regras do pipeline.

## Executar os testes

```bash
pytest -q
```

## Publicação no GitHub

Depois de criar um repositório no GitHub, faça o versionamento desta pasta com
os comandos habituais do Git. Nenhuma credencial ou arquivo de ambiente precisa
ser incluído.
