import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gram Stain and Antibiotic Effectiveness", page_icon="🧫", layout="wide"
)

BLUE = "#2a78d6"
AQUA = "#1baf7a"
YELLOW = "#eda100"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"

READING_COLS = [1, 6, 1]


@alt.theme.register("article", enable=True)
def article_theme():
    return alt.theme.ThemeConfig(
        {
            "background": "#fcfcfb",
            "font": "system-ui, -apple-system, Segoe UI, sans-serif",
            "title": {"color": INK, "fontSize": 15, "fontWeight": 600, "anchor": "start"},
            "axis": {
                "labelColor": INK_MUTED,
                "titleColor": INK_SECONDARY,
                "gridColor": GRID,
                "domainColor": "#c3c2b7",
                "tickColor": "#c3c2b7",
                "labelFontSize": 11,
                "titleFontSize": 12,
            },
            "legend": {
                "labelColor": INK_SECONDARY,
                "titleColor": INK_SECONDARY,
                "labelFontSize": 11,
                "titleFontSize": 12,
            },
            "view": {"stroke": "transparent"},
        }
    )

GRAM_ORDER = ["positive", "negative"]
DRUG_ORDER = ["Penicillin", "Streptomycin", "Neomycin"]
GRAM_COLORS = alt.Scale(domain=GRAM_ORDER, range=[BLUE, AQUA])
GRAM_SHAPES = alt.Scale(domain=GRAM_ORDER, range=["circle", "square"])
DRUG_COLORS = alt.Scale(domain=DRUG_ORDER, range=[BLUE, AQUA, YELLOW])


@st.cache_data
def load_data():
    df = pd.read_csv("burtin_antibiotics.csv")
    df["Best_Drug"] = df[["Penicillin", "Streptomycin", "Neomycin"]].idxmin(axis=1)
    long = df.melt(
        id_vars=["Bacteria", "Gram_Staining", "Genus", "Best_Drug"],
        value_vars=["Penicillin", "Streptomycin", "Neomycin"],
        var_name="Antibiotic",
        value_name="MIC",
    )
    long["Best"] = long["Antibiotic"] == long["Best_Drug"]
    return df, long


df, long = load_data()

best = long[long["Best"]].copy()
pos_med = df.loc[df.Gram_Staining == "positive", "Penicillin"].median()
neg_med = df.loc[df.Gram_Staining == "negative", "Penicillin"].median()
gap_x = round(neg_med / pos_med)
worst = df.loc[df.Penicillin.idxmax()]

bacteria_order = pd.concat(
    [df[df.Gram_Staining == g].sort_values("Penicillin", ascending=False) for g in GRAM_ORDER]
)["Bacteria"].tolist()

# ---------- Header ----------
_, body_col, _ = st.columns(READING_COLS)
with body_col:
    st.title("Gram Stain and Antibiotic Effectiveness")
    st.markdown(
        "##### What a 1951 dataset on Penicillin, Streptomycin and Neomycin shows "
        "about Gram-positive and Gram-negative bacteria"
    )
    st.caption(
        "Data: Will Burtin's 1951 antibiotic sensitivity study. Values are minimum "
        "inhibitory concentration (MIC, µg/mL) for Penicillin, Streptomycin and "
        "Neomycin against 16 bacteria. Lower MIC means the drug is more effective. "
        "The scales below are logarithmic because effective doses span nearly six "
        "orders of magnitude."
    )

    st.markdown(
        f"""
        <div style="display:flex; align-items:baseline; gap:14px; margin:18px 0 4px 0;">
          <div style="font-size:52px; font-weight:700; color:{INK}; line-height:1;">{gap_x:,}x</div>
          <div style="font-size:14px; color:{INK_SECONDARY}; max-width:340px;">
            higher median Penicillin dose needed to stop a Gram-negative bacterium
            than a Gram-positive one
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    # ---------- Section 1: the whole board ----------
    st.markdown(
        """
The dataset covers three antibiotics tested against sixteen bacteria. The
clearest pattern in it is not about species. It is about whether a bacterium is
Gram-positive or Gram-negative. Gram-negative bacteria have an extra outer
membrane that keeps Penicillin from reaching its target, and that shows up
directly in the numbers below: Penicillin is pale (effective) for every
Gram-positive row and dark (ineffective) for nearly every Gram-negative one.
"""
    )

    heatmap = (
        alt.Chart(long)
        .mark_rect(cornerRadius=2)
        .encode(
            x=alt.X("Antibiotic:N", title=None, sort=DRUG_ORDER),
            y=alt.Y(
                "Bacteria:N",
                title=None,
                sort=bacteria_order,
                axis=alt.Axis(labelLimit=280),
            ),
            color=alt.Color(
                "MIC:Q",
                title="MIC (µg/mL, log)",
                scale=alt.Scale(type="log", scheme="blues"),
                legend=alt.Legend(orient="bottom", gradientLength=180),
            ),
            tooltip=[
                alt.Tooltip("Bacteria:N"),
                alt.Tooltip("Gram_Staining:N", title="Gram stain"),
                alt.Tooltip("Antibiotic:N"),
                alt.Tooltip("MIC:Q", title="MIC (µg/mL)"),
            ],
        )
        .properties(height=190)
        .facet(
            row=alt.Row(
                "Gram_Staining:N",
                title=None,
                sort=GRAM_ORDER,
                header=alt.Header(
                    labelFontSize=13, labelFontWeight=700, labelColor=INK, labelAngle=0, labelPadding=6
                ),
            )
        )
        .resolve_scale(y="independent")
        .properties(title="Penicillin turns dark right where Gram-positive gives way to Gram-negative")
    )
    st.altair_chart(heatmap, use_container_width=True)
    st.caption(
        "Each row group is sorted by Penicillin dose, worst to best. The row labels "
        "on the left are the Gram stain groups, and they line up with the color "
        "shift in the Penicillin column."
    )

    st.divider()

    # ---------- Section 2: Penicillin's blind spot ----------
    st.markdown(
        f"""
### Penicillin by Gram stain

Plotting Penicillin alone on a log scale, the two Gram groups barely overlap.
Gram-positive bacteria cluster near the bottom, where tiny doses are enough.
Gram-negative bacteria sit much higher on the scale. The black diamonds mark
the median for each group, and *{worst.Bacteria}* is called out as the most
extreme case in the dataset.
"""
    )

    pen = df.copy()
    extreme = df[df.Bacteria == worst.Bacteria]
    medians = pd.DataFrame({"Gram_Staining": GRAM_ORDER, "Penicillin": [pos_med, neg_med]})

    x_scale = alt.Scale(type="log")
    x_enc = alt.X("Penicillin:Q", title="Penicillin MIC, µg/mL (log scale)", scale=x_scale)
    y_enc = alt.Y("Gram_Staining:N", title=None, sort=GRAM_ORDER)

    points = (
        alt.Chart(pen)
        .mark_point(size=130, opacity=0.85, filled=True)
        .encode(
            x=x_enc,
            y=y_enc,
            color=alt.Color("Gram_Staining:N", title="Gram stain", scale=GRAM_COLORS),
            shape=alt.Shape("Gram_Staining:N", title="Gram stain", scale=GRAM_SHAPES),
            tooltip=[
                alt.Tooltip("Bacteria:N"),
                alt.Tooltip("Gram_Staining:N", title="Gram stain"),
                alt.Tooltip("Penicillin:Q", title="MIC (µg/mL)"),
            ],
        )
    )
    median_ticks = (
        alt.Chart(medians)
        .mark_point(shape="diamond", size=220, filled=True, color=INK)
        .encode(x=x_enc, y=y_enc)
    )
    median_labels = (
        alt.Chart(medians)
        .mark_text(dy=-16, fontSize=11, fontWeight=600, color=INK)
        .encode(x=x_enc, y=y_enc, text=alt.Text("Penicillin:Q", format=".3g"))
    )
    extreme_ring = (
        alt.Chart(extreme)
        .mark_point(size=320, filled=False, strokeWidth=1.5, color=INK)
        .encode(x=x_enc, y=y_enc)
    )
    extreme_label = (
        alt.Chart(extreme)
        .mark_text(align="left", dx=12, dy=16, fontSize=11, fontStyle="italic", color=INK_SECONDARY)
        .encode(x=x_enc, y=y_enc, text=alt.value(f"{worst.Bacteria}, {worst.Penicillin:g} µg/mL"))
    )

    strip = alt.layer(points, median_ticks, median_labels, extreme_ring, extreme_label).properties(
        height=200, title="Gram-positive and Gram-negative bacteria occupy separate dose ranges"
    )
    st.altair_chart(strip, use_container_width=True)

    st.divider()

    # ---------- Section 3: who fills the gap ----------
    neg_best_counts = best[best.Gram_Staining == "negative"]["Antibiotic"].value_counts()
    neomycin_share = neg_best_counts.get("Neomycin", 0)
    n_negative = (df.Gram_Staining == "negative").sum()

    st.markdown(
        f"""
### Which drug works best, by bacterium

Penicillin does not work against most Gram-negative bacteria, so something else
has to. For each bacterium, take whichever antibiotic needed the *lowest* dose,
that is, the most effective one. Penicillin wins most often on the
Gram-positive side, while **Neomycin** is the best option for
**{neomycin_share} of the {n_negative}** Gram-negative bacteria in this dataset.
"""
    )

    best_counts = (
        best.groupby(["Gram_Staining", "Antibiotic"])
        .size()
        .reindex(
            pd.MultiIndex.from_product([GRAM_ORDER, DRUG_ORDER], names=["Gram_Staining", "Antibiotic"]),
            fill_value=0,
        )
        .reset_index(name="Count")
    )
    count_x = alt.X("Antibiotic:N", title=None, sort=DRUG_ORDER)
    count_y = alt.Y("Count:Q", title="Bacteria for which this drug is most effective")

    bar_mark = alt.Chart(best_counts).mark_bar(
        cornerRadiusTopLeft=3, cornerRadiusTopRight=3, size=28
    ).encode(
        x=count_x,
        y=count_y,
        color=alt.Color("Antibiotic:N", scale=DRUG_COLORS, legend=None),
        tooltip=[
            alt.Tooltip("Gram_Staining:N", title="Gram stain"),
            alt.Tooltip("Antibiotic:N"),
            alt.Tooltip("Count:Q", title="Bacteria"),
        ],
    )
    bar_labels = alt.Chart(best_counts).mark_text(
        dy=-8, fontSize=12, fontWeight=600, color=INK
    ).encode(x=count_x, y=count_y, text="Count:Q")

    bars = (
        alt.layer(bar_mark, bar_labels)
        .properties(height=240, width=150)
        .facet(
            column=alt.Column(
                "Gram_Staining:N",
                title=None,
                sort=GRAM_ORDER,
                header=alt.Header(labelFontSize=13, labelFontWeight=700, labelColor=INK),
            )
        )
        .properties(title="Neomycin is the top performer against Gram-negative bacteria")
    )

    bars_left, bars_mid, bars_right = st.columns([1, 2, 1])
    with bars_mid:
        st.altair_chart(bars, use_container_width=False)

    st.divider()

    # ---------- Summary ----------
    st.markdown(
        """
### Summary

In this dataset, Gram stain predicts antibiotic choice better than the
bacterium's identity does. Penicillin is the strongest option for
Gram-positive infections. For Gram-negative infections, Streptomycin or
Neomycin is generally the better choice.
"""
    )

    st.markdown(
        "<div style='text-align:center; margin-top:24px;'>"
        "(Created in collaboration with Claude Sonnet 4.6)</div>",
        unsafe_allow_html=True,
    )
