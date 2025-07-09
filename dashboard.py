import pandas as pd
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px

# === Leitura da planilha ===
df = pd.read_excel("Resultados Finais.xlsx")

# Corrigir e padronizar a coluna "Ano"
df["Ano"] = pd.to_datetime(df["Ano"], errors="coerce").dt.year
df = df.dropna(subset=["Ano"])
df["Ano"] = df["Ano"].astype(int)

# Nome da coluna de palavras-chave
coluna_palavras = "Palavras-chave encontradas"

# Pré-processamento
df["Palavras-chave"] = df[coluna_palavras].fillna("").str.split(r",\s*")
df_exploded = df.explode("Palavras-chave")
df_exploded["Palavras-chave"] = df_exploded["Palavras-chave"].str.strip()

# Frequência das palavras-chave
palavra_freq = df_exploded["Palavras-chave"].value_counts().to_dict()

# Inicializar app
app = dash.Dash(__name__)
app.title = "Levantamento de Publicações"

# Layout
app.layout = html.Div([
    html.H2("Filtro dinâmico de publicações por palavra-chave e repositório"),

    html.Div([
        html.Label("Palavra-chave:"),
        dcc.Dropdown(
            options=[
                {"label": f"{kw} ({palavra_freq[kw]})", "value": kw}
                for kw in sorted(palavra_freq.keys())
            ],
            multi=True,
            id="filtro-palavra"
        ),
    ], style={"width": "45%", "display": "inline-block", "padding": "0 10px"}),

    html.Div([
        html.Label("Repositório:"),
        dcc.Checklist(
            options=[
                {"label": r, "value": r}
                for r in sorted(df_exploded["Repositório"].unique())
            ],
            value=sorted(df_exploded["Repositório"].unique()),
            id="filtro-repositorio",
            inline=True
        ),
    ], style={"width": "50%", "display": "inline-block", "padding": "0 10px"}),

    html.Div([
        html.Label("Tipo de gráfico:"),
        dcc.RadioItems(
            options=[
                {"label": "📈 Linha", "value": "linha"},
                {"label": "📊 Barra", "value": "barra"}
            ],
            value="linha",
            id="tipo-grafico",
            inline=True
        )
    ], style={"marginTop": "20px"}),

    dcc.Graph(id="grafico-publicacoes"),

    html.Hr(),

    html.H4("📋 Dados filtrados:"),

    dash_table.DataTable(
        id="tabela-dados",
        columns=[
            {"name": col, "id": col}
            for col in ["Repositório", "Título", "Autor", "Ano", "Palavras-chave encontradas", "Páginas"]
        ],
        data=[],
        filter_action="native",  # campo de busca interno
        style_table={
            "overflowX": "auto",
            "overflowY": "scroll",
            "height": "500px"
        },
        style_cell={
            "textAlign": "left",
            "padding": "5px",
            "minWidth": "100px",
            "whiteSpace": "normal"
        },
        style_header={
            "fontWeight": "bold",
            "backgroundColor": "#f0f0f0"
        },
    )
], style={"padding": "30px"})


# Callback
@app.callback(
    Output("grafico-publicacoes", "figure"),
    Output("tabela-dados", "data"),
    Input("filtro-palavra", "value"),
    Input("filtro-repositorio", "value"),
    Input("tipo-grafico", "value")
)
def atualizar_grafico(keywords, repositorios, tipo):
    df_filtrado = df_exploded[df_exploded["Repositório"].isin(repositorios)]

    if keywords:
        df_filtrado = df_filtrado[df_filtrado["Palavras-chave"].isin(keywords)]

    # Agrupamento
    df_grouped = df_filtrado.groupby(["Ano", "Repositório"]).size().reset_index(name="Nº de publicações")

    # Gráfico
    if df_grouped.empty:
        fig = px.scatter(title="Nenhum dado encontrado com os filtros atuais.")
    elif tipo == "linha":
        fig = px.line(
            df_grouped,
            x="Ano",
            y="Nº de publicações",
            color="Repositório",
            markers=True,
            title="Número de publicações por ano"
        )
    else:
        fig = px.bar(
            df_grouped,
            x="Ano",
            y="Nº de publicações",
            color="Repositório",
            barmode="group",
            title="Número de publicações por ano"
        )

    fig.update_layout(hovermode="x unified")

    # Tabela
    colunas_originais = ["Repositório", "Título", "Autor", "Ano", "Palavras-chave encontradas", "Páginas"]
    tabela = df_filtrado[colunas_originais].drop_duplicates().to_dict("records")

    return fig, tabela


# Rodar o app
if __name__ == "__main__":
    app.run(debug=True)
