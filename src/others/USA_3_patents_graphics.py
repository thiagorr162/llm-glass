from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots 

# ------------------------------------------------------------------
# 1. Paths and constants
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = BASE_DIR / 'data' / 'filtered' / 'USA_3_patents_analysis.csv'

COMPOSITION_COLS = [
    'SiO2', 'Al2O3' ,'BaO', 'B2O3', 'MgO', 'CaO', 'SrO', 'SnO2', 
    '∑RO/Al2O3','Na2O', 'K2O', 'ZnO', 'TiO2', 'Sb2O3', 'SO3', 
    'Fe2O3', 'V2O5', 'AS2O3', 'Cl', 'F', 'Li2O', 'ZrO2','Cr2O3',
    'P2O5', 'CeO2', 'La2O3', 'Y2O3'
]

CORNING_COMPOSITION_COLS = [
    'SiO2', 'Al2O3', 'BaO', 'B2O3', 'MgO', 'CaO', 'SrO', 'SnO2',
    '∑RO/Al2O3'
]

PROPERTY_COLS = [
    'Density', 'CTE', 'Strain Point',
    'Melting. Temp', 'Liquidus Temp.', 'Tg', 'Liquidus Viscosity'
]

CORNING_PROPERTY_COLS = [
    'Density', 'CTE', 'Strain Point',
    'Melting. Temp', 'Liquidus Temp.', 'Liquidus Viscosity'
]

US2002_COMPOSITION_COLS = [
    'SiO2', 'Al2O3', 'BaO', 'MgO', 'CaO', 'SnO2',
    'Na2O','K2O', 'ZnO', 'TiO2', 'Li2O', 'ZrO2', 'P2O5'
]

THEORETICAL_RANGES = {
    'SiO2':  (64.0, 71.0),
    'Al2O3': ( 9.0, 12.0),
    'BaO':   ( 0.0,  0.1),
    'B2O3':  ( 7.0, 12.0),
    'MgO':   ( 1.0,  3.0),
    'CaO':   ( 6.0, 11.5),
    'SrO':   ( 0.0,  2.0),
    '∑RO/Al2O3': (1.0, 1.25)
}

PROPERTY_LIMITS = {
    'Density'            : (2.41, None),
    'CTE'                : (28,   34),
    'Liquidus Temp.'     : (None, 1170),
    'Strain Point'       : (650,  None),
    'Liquidus Viscosity' : (200000, None)
}


# ------------------------------------------------------------------
# 2. Load & preprocess
# ------------------------------------------------------------------
# Load everything
df_all = pd.read_csv(CSV_PATH, sep=';', na_values=['', ' '], decimal='.')
# logo após o read_csv
df_all[COMPOSITION_COLS] = df_all[COMPOSITION_COLS].apply(pd.to_numeric, errors='coerce')

# subset 1: only US8642491B2 (use Corning cols)
df_us = df_all[df_all['Patent ID'] == 'US8642491B2'].copy()

# subset 2: rest of patents (use Composition_cols)
df_fin = df_all[df_all['Patent ID'] != 'US8642491B2'].copy()

# --- preprocess US8642491B2 ---
df_us[CORNING_COMPOSITION_COLS + CORNING_PROPERTY_COLS] = (
    df_us[CORNING_COMPOSITION_COLS + CORNING_PROPERTY_COLS]
    .apply(pd.to_numeric, errors='coerce')
)

df_us_norm = df_us.copy()
df_us_norm[CORNING_COMPOSITION_COLS] = (
    df_us_norm[CORNING_COMPOSITION_COLS]
    .div(df_us_norm[CORNING_COMPOSITION_COLS].sum(axis=1), axis=0)
    * 100
)
df_us_norm.insert(0, 'SampleID', df_us_norm.index + 1)

stats_us = (
    df_us_norm[CORNING_COMPOSITION_COLS]
    .agg(['min', 'mean', 'max'])
    .T
    .reset_index()
    .rename(columns={'index': 'Oxide'})
)

# --- preprocess US20020023463A1 -----------------------------------
df_2002 = df_all[df_all['Patent ID'] == 'US20020023463A1'].copy()

# 1) conversão numérica apenas nas colunas declaradas
df_2002[US2002_COMPOSITION_COLS + PROPERTY_COLS] = (
    df_2002[US2002_COMPOSITION_COLS + PROPERTY_COLS]
    .apply(pd.to_numeric, errors='coerce')
)

# 2) normalização – 100 mol %
df_2002_norm = df_2002.copy()
df_2002_norm[US2002_COMPOSITION_COLS] = (
    df_2002_norm[US2002_COMPOSITION_COLS]
    .div(df_2002_norm[US2002_COMPOSITION_COLS].sum(axis=1), axis=0) * 100
)
df_2002_norm.insert(0, 'SampleID', df_2002_norm.index + 1)

# 3) estatísticas min-média-máx
stats_2002 = (
    df_2002_norm[US2002_COMPOSITION_COLS]
    .agg(['min', 'mean', 'max'])
    .T
    .reset_index()
    .rename(columns={'index': 'Oxide'})
)

# --- preprocess US20090133441A1 -----------------------------------
df_2009 = df_all[df_all['Patent ID'] == 'US20090133441A1'].copy()

# 1) conversão numérica (mesmos grupos do US864)
df_2009[CORNING_COMPOSITION_COLS + CORNING_PROPERTY_COLS] = (
    df_2009[CORNING_COMPOSITION_COLS + CORNING_PROPERTY_COLS]
    .apply(pd.to_numeric, errors='coerce')
)

# 2) normalização para 100 mol %
df_2009_norm = df_2009.copy()
df_2009_norm[CORNING_COMPOSITION_COLS] = (
    df_2009_norm[CORNING_COMPOSITION_COLS]
    .div(df_2009_norm[CORNING_COMPOSITION_COLS].sum(axis=1), axis=0)
    * 100
)
df_2009_norm.insert(0, 'SampleID', df_2009_norm.index + 1)

# 3) estatísticas min-mean-max
stats_2009 = (
    df_2009_norm[CORNING_COMPOSITION_COLS]
    .agg(['min', 'mean', 'max'])
    .T
    .reset_index()
    .rename(columns={'index': 'Oxide'})
)

# --- preprocess 'Finning comparison compositions' ---
df_fin[COMPOSITION_COLS + PROPERTY_COLS] = (
    df_fin[COMPOSITION_COLS + PROPERTY_COLS]
    .apply(pd.to_numeric, errors='coerce')
)

df_fin_norm = df_fin.copy()
df_fin_norm[COMPOSITION_COLS] = (
    df_fin_norm[COMPOSITION_COLS]
    .div(df_fin_norm[COMPOSITION_COLS].sum(axis=1), axis=0)
    * 100
)
df_fin_norm.insert(0, 'SampleID', df_fin_norm.index + 1)

stats_fin = (
    df_fin_norm[COMPOSITION_COLS]
    .agg(['min', 'mean', 'max'])
    .T
    .reset_index()
    .rename(columns={'index': 'Oxide'})
)

# 1) Unic style config for the samples
sample_colors  = ["magenta", "blue"]
sample_symbols = ["circle",  "square"]

# 2) Function to add samples
def add_sample_markers(fig, df, sample_ids, *,
                       x_val=None, y_col=None,
                       row=None, col=None,
                       showlegend=False):
    """
    Adiciona marcadores “Sample {sid}”.

    • Se x_val is None  →  plota horizontal  (x = valor, y = y_col) –- FIG 6
    • Caso contrário    →  plota vertical    (x = x_val, y = valor) –- demais figs
    • Se a figura foi criada com make_subplots, passe row/col;
      caso contrário, deixe row=None, col=None.
    """
    for sid, color, sym in zip(sample_ids, sample_colors, sample_symbols):
        if sid not in df.SampleID.values:
            continue

        y_val = df.loc[df.SampleID == sid, y_col].iloc[0]

        if x_val is None:                     # modo horizontal
            trace = go.Scatter(
                x=[y_val],
                y=[y_col],
                mode="markers",
                marker=dict(color=color, size=8, symbol=sym),
                name=f"Sample {sid}" if showlegend else None,
                showlegend=showlegend,
            )
        else:                                 # modo vertical
            trace = go.Scatter(
                x=[x_val],
                y=[y_val],
                mode="markers",
                marker=dict(color=color, size=12, symbol=sym),
                name=f"Sample {sid}" if showlegend else None,
                showlegend=showlegend,
            )

        # adiciona o trace com ou sem row/col
        if row is None or col is None:
            fig.add_trace(trace)
        else:
            fig.add_trace(trace, row=row, col=col)

#Consistence checks
print("Total rows:", len(df_all))
print("Rows US8642491B2:", len(df_all[df_all['Patent ID']=='US8642491B2']))
print("Rows in df_fin:", len(df_fin))
print("Rows US8642491B2 in df_fin:", 
      df_fin['Patent ID'].eq('US8642491B2').sum())
# 1) Non-Zero values for each property in df_fin?
print(df_fin[PROPERTY_COLS].notnull().sum())

# 2) Wich Patent IDs in df_fin contain at least one value of property?
mask_prop = df_fin[PROPERTY_COLS].notnull().any(axis=1)
print("Patentes com dados de propriedade:", df_fin.loc[mask_prop, 'Patent ID'].unique())

def compute_hspace(n_cols: int, *,
                   default: float = 0.05,
                   small_fig: float = 0.2) -> float:
    """
    Retorna um horizontal_spacing adequado:
    - Se tiver 1 coluna, devolve default.
    - Se tiver 2 colunas, devolve small_fig (mais espaço entre elas).
    - Caso contrário, mantém algo compacto (default ou menor).
    """
    if n_cols <= 1:
        return default
    if n_cols == 2:
        return small_fig
    # para >=3 colunas, espaço proporcional ao número de colunas
    return min(default, 1.0 / (n_cols - 1) - 1e-6)


def generate_all_figures(
    df_norm: pd.DataFrame,
    stats: pd.DataFrame,
    comp_cols: list[str],
    prop_cols: list[str],
    label: str,
    theoretical_ranges: dict,
    property_limits: dict,
    sample_ids: tuple[int, int] = (23, 28),
    show: bool = False,
):
    """
    Gera todos os gráficos usados na análise de patentes/vidros
    para um dataframe normalizado (`df_norm`) e estatísticas pré‑calculadas
    (`stats`).  
    Retorna a lista de figuras Plotly; se `show=True`, também as exibe.

    Parameters
    ----------
    df_norm : pd.DataFrame
        Dados normalizados, já contendo a coluna `SampleID`.
    stats : pd.DataFrame
        Tabela com min/mean/max das colunas de composição (índice = 'Oxide').
    comp_cols : list[str]
        Lista de óxidos a plotar.
    prop_cols : list[str]
        Lista de propriedades a plotar.
    label : str
        Nome descritivo do subset (p.ex. “US8642491B2” ou “Finning”).
    theoretical_ranges : dict
        Dicionário {óxido: (min, max)} com limites de patente.
    property_limits : dict
        Dicionário {propriedade: (min, max)} com limites de patente.
    sample_ids : tuple[int, int], default (23,28)
        IDs de amostras a destacar.
    show : bool, default False
        Se True, exibe as figuras com `.show()`.
    """
    n_comp = len(comp_cols)

# ── Subsets flags ─────────────────────────────────────────────
    CORNING_IDS = {"US8642491B2", "US20090133441A1"}
    is_corning = label.upper() in CORNING_IDS
    is_finning  = label.lower().startswith("finning")
    is_chunked  = is_finning or label.lower() == "us20020023463a1"

#── Quality ─────────────────────────────────────────────────────

    hspace = compute_hspace(n_comp)
    palette = px.colors.qualitative.Set2


    # ── Zoom ────────────────────────────────────────────────────
    #  1) US8642491B2
    zoom_common = {
        "BaO":   (0,   0.5),
        "SiO2":  (60, 80),
        "SnO2":  (0,   0.5),
        "∑RO/Al2O3": (0, 2),
    }

    #  2) Finning subset
    zoom_finning = {
        "Al2O3": (0, 25),
        "BaO":   (0,  0.5), "ZnO": (0, 5),  "TiO2": (0, 5),
        "P2O5":  (0,  5), "SnO2": (0, 1), **{ox: (0, 2) for ox in
            ["CeO2","Sb2O3","SO3","Fe2O3","V2O5",
             "AS2O3","Cl","F","Cr2O3","Y2O3"]}
    }

    #  3) US20020023463A1
    zoom_us2002 = {
        "SiO2":  (60.0, 75.0),
        "Al2O3": (8.0, 18.0),
        "BaO":   (0, 2.0),
        "B2O3":  (5.0, 15.0),
        "MgO":   (0, 5.0),
        "CaO":   (0, 2.0),
        "SnO2":  (0, 0.5),
        "Na2O":  (0, 2.0),
        "K2O":   (0, 0.5),
        "ZnO":   (0, 2.0),
        "TiO2":  (0, 5.0),
        "Li2O":  (5.0, 10.0),
        "ZrO2":  (0, 2.0),
        "P2O5":  (0, 2.0),

    }

    # 4) Common width for graphics
    COL_W = 250
    MIN_W = 520
    MAX_W = 1600

    #  5) Executions
    if is_finning:
        y_ranges = zoom_common | zoom_finning
    elif is_chunked:
        y_ranges = zoom_common | zoom_us2002
    else:
        y_ranges = zoom_common

    figs = []

    # ------------------------------------------------------------------
    # FIG 1 – Stacked bars
    # ------------------------------------------------------------------
    if is_corning:
        comp_corning = [o for o in comp_cols if o != '∑RO/Al2O3']
        fig_stack = px.bar(
            df_norm, x="SampleID", y=comp_corning,
            title=f"{label} – Normalised Composition (mol %) – Stacked Bars",
            labels={"value": "mol %", "variable": "Oxide", "SampleID": "Sample"},
            height=800
        ).update_layout(barmode="stack", xaxis=dict(dtick=1))
        figs.append(fig_stack)

    # ------------------------------------------------------------------
    # FIG 2– OXIDE BOXPLOTS
    # ------------------------------------------------------------------
    if is_corning:
        fig_range_multi = make_subplots(
            rows=1, cols=n_comp, shared_yaxes=False,
            subplot_titles=comp_cols, horizontal_spacing=hspace
        )

        for i, oxide in enumerate(comp_cols, start=1):
            # 1) box
            fig_range_multi.add_trace(
                go.Box(
                    x=[oxide] * len(df_norm),
                    y=df_norm[oxide],
                    name=oxide,
                    boxpoints=False,
                    width=0.6,
                    marker_color=palette[(i - 1) % len(palette)],
                    showlegend=False,
                ),
                row=1, col=i,
            )

            # 2) Patent lines
            lo, hi = theoretical_ranges.get(oxide, (None, None))
            if lo is not None and hi is not None:
                xref_s = "x domain" if i == 1 else f"x{i} domain"
                yref_s = "y"        if i == 1 else f"y{i}"
                for y_line in (lo, hi):
                    fig_range_multi.add_shape(
                        type="line", x0=0, x1=1, xref=xref_s,
                        y0=y_line, y1=y_line, yref=yref_s,
                        line=dict(color="red", width=3),
                        row=1, col=i
                    )
                    fig_range_multi.add_annotation(
                        x=0.3, y=y_line+0.5, xref=xref_s, yref=yref_s,
                        text=f"{y_line}", showarrow=False,
                        font=dict( color="red"),
                        row=1, col=i
                    )

            # 3) Axis
            yrange = y_ranges.get(oxide, (0, 15))
            fig_range_multi.update_yaxes(range=yrange, dtick=5,
                                         title="mol %", row=1, col=i)
            fig_range_multi.update_xaxes(type="category", showticklabels=False,
                                         row=1, col=i)

            # 4) Highlighted 
            add_sample_markers(
                fig_range_multi, df_norm, sample_ids,                
                x_val=oxide, y_col=oxide,
                row=1, col=i,
                showlegend=(i==1),
            )

        fig_range_multi.update_layout(
            height=600,
            width=max(1600, 250 * n_comp),
            title=f"{label} – Composition Boxplots per Oxide",
            legend=dict(orientation="h", yanchor="bottom", y=1.1,
                        xanchor="center", x=0.7),
        )
        figs.append(fig_range_multi)

    # ------------------------------------------------------------------
    # 3) Patent limits & dataset span
    #    • US864… : uma figura para todos os comp_cols
    #    • Finning: três figuras com lotes de 9-9-8 óxidos
    # ------------------------------------------------------------------
    def build_rect(chunk_cols: list[str], suffix: str = ""):
        # cria um subplot com len(chunk_cols) colunas
        hs = compute_hspace(len(chunk_cols))
        fig = make_subplots(
            rows=1,
            cols=len(chunk_cols),
            shared_yaxes=False,
            subplot_titles=chunk_cols,
            horizontal_spacing=hs
        )
        for j, oxide in enumerate(chunk_cols, start=1):
            lo, hi = theoretical_ranges.get(oxide, (None, None))
            ds_min = stats.loc[stats.Oxide == oxide, 'min'].iloc[0]
            ds_max = stats.loc[stats.Oxide == oxide, 'max'].iloc[0]

            xref = f"x{j}" if j>1 else "x"
            yref = f"y{j}" if j>1 else "y"

            # (a) Patent limits
            if lo is not None and hi is not None:
                for y_line in (lo, hi):
                    fig.add_shape(
                        type="line", x0=0, x1=1, xref=f"{xref} domain",
                        y0=y_line, y1=y_line, yref=yref,
                        line=dict(color="red", width=3),
                        row=1, col=j
                    )
                    fig.add_annotation(
                        x= 0.5, y=y_line,
                        xref=f"{xref} domain", yref=yref,
                        text=f"{y_line:.1f}",
                        font=dict(color="red"),
                        showarrow=False,
                        yshift= 12,
                        row=1, col=j
                    )
                

            # (b) Dataset span rectange
            fig.add_shape(
                type="rect", x0=0, x1=1, xref=f"{xref} domain",
                y0=ds_min, y1=ds_max, yref=yref,
                fillcolor=palette[(j-1)%len(palette)],
                opacity=0.35, line_width=0,
                layer = "below",
                row=1, col=j
            )
            fig.add_annotation(
                x = 0.03, y=ds_min, xref=f"{xref} domain", yref=yref,
                text=f"{ds_min:.1f}", showarrow=False, font=dict(color="dark gray"),
                row=1, col=j
            )
            fig.add_annotation(
                x = 0.03, y=ds_max, xref=f"{xref} domain", yref=yref,
                text=f"{ds_max:.1f}", showarrow=False, font=dict(color="dark gray"),
                row=1, col=j
            )

            # (c) Sample markers
            add_sample_markers(
                fig, df_norm, sample_ids,
                x_val=0.5, y_col=oxide,
                row=1, col=j,
                showlegend=(j == 1),
            )

            # Axis 
            fig.update_yaxes(
                title="mol %", title_standoff = 12,
                row=1, col=j,
                range=y_ranges.get(oxide,(0,15),)
            )
            fig.update_xaxes(showticklabels=False, row=1, col=j)
            
        fig.update_layout(
            height=600,
            width=max(MIN_W, min(MAX_W, COL_W * len(chunk_cols))),
            title=f"{label}{suffix} – Patent Limits & Dataset Span",
            legend=dict(orientation="h", y=1.3, x=0.7, xanchor="center")
        )
        figs.append(fig)

    MAX_COLS = 7
    
    # Chunks numbers
    num_chunks = (n_comp + MAX_COLS - 1) // MAX_COLS

    # Inconditional loop
    for idx, start in enumerate(range(0, n_comp, MAX_COLS), start=1):
        chunk = comp_cols[start : start + MAX_COLS]
        suffix = f" (part {idx})" if num_chunks > 1 else ""
        build_rect(chunk, suffix=suffix)

    # ------------------------------------------------------------------
    # FIG 4‑rect –RANGE OF PROPERTIES
    # ------------------------------------------------------------------
    prop_stats = df_norm[prop_cols].agg(["min", "mean", "max"]).T.reset_index()
    prop_stats.rename(columns={"index": "Property"}, inplace=True)

    fig_prop_rect = make_subplots(
        rows=1,
        cols=len(prop_cols),
        shared_yaxes=False,
        subplot_titles=prop_cols,
        horizontal_spacing= hspace,
    )

    for i, prop in enumerate(prop_cols, start=1):
        lo_pat, hi_pat = property_limits.get(prop, (None, None))
        ds_min = prop_stats.loc[prop_stats.Property == prop, "min"].iloc[0]
        ds_max = prop_stats.loc[prop_stats.Property == prop, "max"].iloc[0]

        xref_s = "x domain" if i == 1 else f"x{i} domain"
        yref_s = "y" if i == 1 else f"y{i}"

        fig_prop_rect.add_shape(
            type="rect",
            x0=0,
            x1=1,
            xref=xref_s,
            y0=ds_min,
            y1=ds_max,
            yref=yref_s,
            fillcolor=palette[(i - 1) % len(palette)],
            opacity=0.35,
            line_width=0,
            row=1, col=i,
            layer = "below",
        )
        fig_prop_rect.add_annotation(
            x=0.08,
            y=ds_min,
            xref=xref_s,
            yref=yref_s,
            text=f"{ds_min:.2f}" if prop == "Density" else f"{ds_min:.0f}",
            showarrow=False,
            row=1,
            col=i,
        )
        fig_prop_rect.add_annotation(
            x=0.08,
            y=ds_max,
            xref=xref_s,
            yref=yref_s,
            text=f"{ds_max:.2f}" if prop == "Density" else f"{ds_max:.0f}",
            showarrow=False,
            row=1,
            col=i,
        )

        for lim in (lo_pat, hi_pat):
            if lim is None:
                continue
            delta = ds_max - ds_min or 1
            if prop == "Density":
                offset_factor = 0.35
            elif prop == "Strain Point":
                offset_factor = 0.20
            elif prop == "Liquidus Viscosity":
                offset_factor = 0.05
            else:
                offset_factor = 0.12
            y_offset = lim + offset_factor * delta
            fig_prop_rect.add_shape(
                type="line",
                x0=0,
                x1=1,
                xref=xref_s,
                y0=lim,
                y1=lim,
                yref=yref_s,
                line=dict(color="red", width=3),
                row=1,
                col=i,
            )
            fig_prop_rect.add_annotation(
                x=0.5,
                y=y_offset,
                xref=xref_s,
                yref=yref_s,
                text=f"{lim:.2f}" if prop == "Density" else f"{lim:.0f}",
                font=dict(color="red"),
                showarrow=False,
                row=1,
                col=i,
            )

        add_sample_markers(
            fig_prop_rect, df_norm, sample_ids,
            x_val=0.7, y_col=prop,
            row=1, col=i,
            showlegend=(i == 1),
        )

        #Scales for the axis legend
        if prop == "Density":
            fig_prop_rect.update_yaxes(
                range=[2.2, 2.6], title_text="g cm⁻³", dtick=0.1, row=1, col=i
            )
        elif prop == "CTE":
            fig_prop_rect.update_yaxes(
                range=[20, 40], title_text="10⁻⁷ °C⁻¹", dtick=5, row=1, col=i
            )
        elif prop == "Liquidus Temp.":
            fig_prop_rect.update_yaxes(
                range=[1000, 1300], title_text="°C",title_standoff=0, dtick=50, row=1, col=i
            )
        elif prop == "Melting. Temp":
            fig_prop_rect.update_yaxes(
                range=[1600, 1700], title_text="°C", title_standoff=0, dtick=25, row=1, col=i
            )
        elif prop == "Strain Point":
            fig_prop_rect.update_yaxes(
                range=[600, 750], title_text="°C", title_standoff=0, dtick=25, row=1, col=i
            )
        elif prop == "Liquidus Viscosity":
            fig_prop_rect.update_yaxes(
                range=[0, 800000], dtick = 100000, title_text="poise",title_standoff=0, row=1, col=i
            )
        else:
            pad = 0.05 * (ds_max - ds_min or 1)
            fig_prop_rect.update_yaxes(
                range=[ds_min - pad, ds_max + pad], title="", row=1, col=i
            )

        fig_prop_rect.update_xaxes(showticklabels=False, row=1, col=i)

    fig_prop_rect.update_layout(
        height=600,
        width=max(MIN_W, min(MAX_W, COL_W * len(prop_cols))),
        title=f"{label} – Property – Patent Limits & Dataset Span",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.1,
            xanchor="center",
            x=0.7,
        ),
        
    )
    figs.append(fig_prop_rect)

    # ------------------------------------------------------------------
    # FIG 5 – Radar 
    # ------------------------------------------------------------------
    def radar_sample(sample_id: int) -> go.Figure:
        idx = df_norm.index[df_norm.SampleID == sample_id][0]
        data = df_norm[comp_cols + prop_cols]
        data_norm = (data - data.min()) / (data.max() - data.min())
        sample = data_norm.iloc[idx]
        mean = data_norm.mean()
        cats = list(sample.index)

        fig = go.Figure()
        fig.add_scatterpolar(
            r=mean.tolist() + [mean.iloc[0]],
            theta=cats + [cats[0]],
            name="Global mean",
            line_color="red",
            line=dict(dash="dash"),
        )
        fig.add_scatterpolar(
            r=sample.tolist() + [sample.iloc[0]],
            theta=cats + [cats[0]],
            name=f"Sample {sample_id}",
            marker_color = "cyan",
            fill="toself",
            opacity=0.6,
        )
        fig.update_layout(
            title=f"{label} – Radar – Sample {sample_id} vs Global Mean",
            polar=dict(radialaxis=dict(range=[0, 1])),
            height=650,
        )
        return fig

    # One radar for each existent Sample ID
    for sid in sample_ids:
        if sid in df_norm.SampleID.values:
            figs.append(radar_sample(sid))


    # ------------------------------------------------------------------
    # FIG 6 – Confidence-interval 
    # ------------------------------------------------------------------:
    fig_ci = go.Figure()

    for i, oxide in enumerate(comp_cols):
        ds_min = stats.loc[stats.Oxide == oxide, "min"].iloc[0]
        ds_max = stats.loc[stats.Oxide == oxide, "max"].iloc[0]
        pat_min, pat_max = theoretical_ranges.get(oxide, (None, None))

        # dataset range
        fig_ci.add_trace(
            go.Scatter(
                x=[ds_min, ds_max],
                y=[oxide, oxide],
                mode="lines",
                line=dict(color="#00cccc", width=12),
                name="Dataset range" if i == 0 else None,
                showlegend=(i == 0),
            )
        )
       
        if is_finning:
        # dataset limits
            fig_ci.add_annotation(
                x=ds_min-1.25,
                y=oxide,
                xanchor="left",
                yanchor="middle",
                yshift=14,                
                text=f"{ds_min:.1f}",
                font=dict(color="#00cccc", size=16),
                showarrow=False
            )

            fig_ci.add_annotation(
                x=ds_max+1.25,
                y=oxide,
                xanchor="right",
                yanchor="middle",
                yshift=14,
                text=f"{ds_max:.1f}",
                font=dict(color="#00cccc",size=16),
                showarrow=False
            )

        else:
        # dataset limits
            fig_ci.add_annotation(
                x=ds_min-1.5,
                y=oxide,
                xanchor="left",
                yanchor="middle",
                yshift=20,                
                text=f"{ds_min:.1f}",
                font=dict(color="#00cccc", size=18),
                showarrow=False
            )

            fig_ci.add_annotation(
                x=ds_max+1.5,
                y=oxide,
                xanchor="right",
                yanchor="middle",
                yshift=20,
                text=f"{ds_max:.1f}",
                font=dict(color="#00cccc",size=18),
                showarrow=False
            )

        # patent spec error bars
        if pat_min is not None and pat_max is not None:
            mid = 0.5 * (pat_min + pat_max)
            fig_ci.add_trace(
                go.Scatter(
                    x=[mid],
                    y=[oxide],
                    mode="markers",
                    marker=dict(color="red", size=8, symbol="line-ns-open"),
                    error_x=dict(
                        type="data",
                        symmetric=False,
                        array=[pat_max - mid],
                        arrayminus=[mid - pat_min],
                        thickness=4,
                        width=6,
                        color="red",
                    ),
                    name="Patent spec" if i == 0 else None,
                    showlegend=(i == 0),
                )
            )
        # Min
            fig_ci.add_annotation(
                x=pat_min,
                y=oxide,
                xanchor="right",
                yanchor="bottom",
                yshift=-10,
                text=f"{pat_min:.1f}",
                font=dict(color="red"),
                showarrow=False
            )
        # Max
            fig_ci.add_annotation(
               x=pat_max,
               y=oxide,
               xanchor="left",
               yanchor="bottom",
               yshift=-10,
               text=f"{pat_max:.1f}",
               font=dict(color="red"),
               showarrow=False
            )

        # sample points
        add_sample_markers(
            fig_ci, df_norm, sample_ids,
            x_val = None, y_col = oxide, 
            showlegend=(i == 1),
        )

    fig_ci.update_layout(
    title=f"{label} – Composition Ranges – Dataset vs Patent",
    xaxis_title="mol %",
    yaxis_title="Oxide",
    yaxis=dict(
        categoryorder='array',
        categoryarray=comp_cols,
        tickmode='array',
        tickvals=comp_cols,
        ticktext=comp_cols,
    ),
    height=1100,
    legend=dict(
        orientation="h",
        x=0.7,
        y=1.1,
        xanchor="center",
    ),
    )
    figs.append(fig_ci)


    # ------------------------------------------------------------------
    # Exihibition
    # ------------------------------------------------------------------
    if show:
      PRESENT_FONT, TITLE_FONT, LEGEND_FONT = 18, 24, 16
      for f in figs:
          f.update_layout(
            font=dict(size=PRESENT_FONT),
            title_font=dict(size=TITLE_FONT),
            legend_font=dict(size=LEGEND_FONT),
          )
          f.show()
    return figs

# ------------------------------------------------------------------
# 11. Display all figures

# ------------------------------------------------------------------
if __name__ == "__main__":
    subsets = [
        ("US8642491B2", df_us_norm, stats_us,
        CORNING_COMPOSITION_COLS, CORNING_PROPERTY_COLS),

        ("US20090133441A1",  df_2009_norm, stats_2009,   
        CORNING_COMPOSITION_COLS, CORNING_PROPERTY_COLS),

        ("US20020023463A1", df_2002_norm, stats_2002,
        US2002_COMPOSITION_COLS,              PROPERTY_COLS),

        ("Finning",     df_fin_norm, stats_fin,
        COMPOSITION_COLS,          PROPERTY_COLS),
    ]

    all_figs = []
    for label, df_n, st, cc, pc in subsets:
        all_figs.extend(
            generate_all_figures(
                df_norm=df_n,
                stats=st,
                comp_cols=cc,
                prop_cols=pc,
                label=label,
                theoretical_ranges=THEORETICAL_RANGES,
                property_limits=PROPERTY_LIMITS, 
                show=True                          
            )
        )
