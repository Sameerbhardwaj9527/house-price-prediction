"""Ames House Price Studio — animated Streamlit app.  Run: streamlit run app.py"""
import json, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd, joblib
import plotly.express as px, plotly.graph_objects as go
import streamlit as st, streamlit.components.v1 as components
from common import prep
from scene import render

A = Path(__file__).parent / "app_assets"
st.set_page_config(page_title="House Price Studio", page_icon="🏡", layout="wide")

@st.cache_resource
def load():
    return joblib.load(A / "model.joblib")["model"], json.load(open(A / "meta.json"))
@st.cache_data
def data():
    return pd.read_csv(A / "app_data.csv"), pd.read_csv(A / "oof.csv")
model, meta = load(); df, oof = data()
HOODS = meta["neighborhoods"]; MAPE = meta["mape"]
hood_med = df.groupby("Neighborhood").SalePrice.median()

def show_html(html, height):            # st.components.v1.html is deprecated in newer Streamlit -> st.iframe
    if hasattr(st, "iframe"): st.iframe(html, height=height)
    else: components.html(html, height=height)
def plot(fig):                          # use_container_width -> width='stretch' in newer Streamlit
    try: st.plotly_chart(fig, width="stretch")
    except TypeError: plot(fig)
def btn(label, **kw):
    try: return st.button(label, width="stretch", **kw)
    except TypeError: return st.button(label, use_container_width=True, **kw)

def predict(**p):
    row = pd.DataFrame([p]); return float(np.expm1(model.predict(prep(row))[0]))

st.markdown("""<style>
.block-container{padding-top:1.4rem} h1{margin-bottom:0}
.sub{opacity:.7;margin-bottom:.6rem}
</style>""", unsafe_allow_html=True)
st.title("🏡 House Price Studio")
st.markdown('<div class="sub">Machine-learning price estimates for Ames, Iowa homes (Kaggle data, 2006–2010 sales). Move a slider — the house, the garage and the price all react.</div>', unsafe_allow_html=True)

DEFAULTS = dict(hood="NAmes", qual=6, cond=5, area=1500, bsmt=900, lot=9500, cars=2, bath=2, beds=3, year=1975, kitchen="TA", fire=1, ac=True)
PRESETS = {
  "🏠 Starter home": dict(hood="OldTown", qual=4, cond=5, area=1000, bsmt=600, lot=6500, cars=1, bath=1, beds=2, year=1940, kitchen="TA", fire=0, ac=False),
  "👨‍👩‍👧 Family home": dict(DEFAULTS),
  "🏰 Luxury estate": dict(hood="NridgHt", qual=9, cond=5, area=3000, bsmt=1800, lot=16000, cars=4, bath=3, beds=5, year=2007, kitchen="Ex", fire=2, ac=True),
}
for k, v in DEFAULTS.items(): st.session_state.setdefault(k, v)
def apply(name): st.session_state.update(PRESETS[name])

tab1, tab2, tab3 = st.tabs(["🎛️ Price Studio", "📊 Explore the data", "🧪 How good is the model?"])

# ------------------------------------------------------------------ TAB 1
with tab1:
    c1, c2 = st.columns([1, 1.9], gap="large")
    with c1:
        st.markdown("**Quick presets**")
        for n in PRESETS: btn(n, on_click=apply, args=(n,))
        st.divider()
        st.selectbox("Neighborhood", HOODS, key="hood")
        st.slider("Overall quality (1–10)", 1, 10, key="qual")
        st.slider("Overall condition (1–9)", 1, 9, key="cond")
        st.slider("Living area (sq ft)", 500, 4000, step=50, key="area")
        st.slider("Basement (sq ft)", 0, 3000, step=50, key="bsmt")
        st.slider("Lot size (sq ft)", 2000, 30000, step=250, key="lot")
        st.select_slider("🚗 Garage cars", options=[0, 1, 2, 3, 4], key="cars")
        a, b = st.columns(2)
        a.slider("Full baths", 0, 4, key="bath"); b.slider("Bedrooms", 0, 6, key="beds")
        st.slider("Year built", 1880, 2010, key="year")
        a, b = st.columns(2)
        a.select_slider("Kitchen", ["Po", "Fa", "TA", "Gd", "Ex"], key="kitchen")
        b.slider("Fireplaces", 0, 3, key="fire")
        st.toggle("Central air", key="ac")
    s = st.session_state
    P = dict(Neighborhood=s.hood, OverallQual=s.qual, OverallCond=s.cond, GrLivArea=s.area, TotalBsmtSF=s.bsmt, LotArea=s.lot,
             GarageCars=s.cars, FullBath=s.bath, BedroomAbvGr=s.beds, YearBuilt=s.year, KitchenQual=s.kitchen,
             Fireplaces=s.fire, CentralAir="Y" if s.ac else "N")
    price = predict(**P)
    with c2:
        show_html(render(dict(price=price, lo=price*(1-MAPE), hi=price*(1+MAPE), hood=s.hood, quality=s.qual, area=s.area,
                        cars=s.cars, lot=s.lot, fire=s.fire, beds=s.beds, ac=bool(s.ac), year=s.year)), 500)
        m1, m2, m3 = st.columns(3)
        med = hood_med[s.hood]
        m1.metric("Estimated price", f"${price:,.0f}")
        m2.metric(f"vs {s.hood} median", f"{(price/med-1)*100:+.0f}%", help=f"Median sale in {s.hood}: ${med:,.0f}")
        m3.metric("Price per sq ft", f"${price/s.area:,.0f}")
        # what-if upgrades
        ups = {"+1 quality": dict(OverallQual=min(10, s.qual+1)), "+1 garage car": dict(GarageCars=min(4, s.cars+1)),
               "+300 sq ft": dict(GrLivArea=s.area+300), "+1 bathroom": dict(FullBath=min(4, s.bath+1)),
               "Central air": dict(CentralAir="Y"), "Remodel kitchen (Gd)": dict(KitchenQual="Gd")}
        rows = [(k, predict(**{**P, **v}) - price) for k, v in ups.items()]
        wf = pd.DataFrame(rows, columns=["Upgrade", "Δ price"]).sort_values("Δ price")
        fig = px.bar(wf, x="Δ price", y="Upgrade", orientation="h", title="💡 What-if: value of one upgrade",
                     color="Δ price", color_continuous_scale="RdYlGn", color_continuous_midpoint=0)
        fig.update_layout(height=290, coloraxis_showscale=False, margin=dict(l=0, r=0, t=40, b=0), transition_duration=500)
        plot(fig)
        st.caption(f"Typical error of this model ≈ ±{MAPE*100:.0f}%. It was trained on Ames, Iowa sales from 2006–2010, so treat it as a demo, not a valuation.")

# ------------------------------------------------------------------ TAB 2
with tab2:
    f1, f2 = st.columns([2, 1])
    sel = f1.multiselect("Neighborhoods", HOODS, default=HOODS[:0], placeholder="All neighborhoods")
    qr = f2.slider("Quality range", 1, 10, (1, 10))
    d = df[df.OverallQual.between(*qr)]
    if sel: d = d[d.Neighborhood.isin(sel)]
    if len(d) < 10: st.warning("Too few houses match — widen the filters."); st.stop()
    d = d.assign(Decade=(d.YearBuilt // 10 * 10).astype(int).astype(str) + "s").sort_values("YearBuilt")
    st.subheader("Houses through the decades  ▶ press play")
    fig = px.scatter(d, x="GrLivArea", y="SalePrice", animation_frame="Decade", color="OverallQual", size="LotArea", size_max=18,
                     hover_name="Neighborhood", range_x=[400, 4200], range_y=[0, 780000], color_continuous_scale="Viridis",
                     labels=dict(GrLivArea="Living area (sq ft)", SalePrice="Sale price ($)"))
    fig.update_layout(height=470, margin=dict(l=0, r=0, t=10, b=0))
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 900
    plot(fig)
    g1, g2 = st.columns(2)
    nb = d.groupby("Neighborhood").SalePrice.median().sort_values().reset_index()
    plot(px.bar(nb, x="SalePrice", y="Neighborhood", orientation="h", title="Median price by neighborhood",
                           color="SalePrice", color_continuous_scale="Tealgrn").update_layout(height=520, coloraxis_showscale=False, margin=dict(l=0, r=0, t=40, b=0)))
    gc = d.assign(Cars=d.GarageCars.astype(int).astype(str) + " 🚗")
    plot(px.box(gc.sort_values("GarageCars"), x="Cars", y="SalePrice", color="Cars", title="Price by garage size",
                           points=False).update_layout(height=520, showlegend=False, margin=dict(l=0, r=0, t=40, b=0)))

# ------------------------------------------------------------------ TAB 3
with tab3:
    k1, k2, k3 = st.columns(3)
    k1.metric("This app's model — CV RMSE (log)", f"{meta['cv_rmse_log']:.3f}", help="13 simple inputs, 5-fold cross-validation")
    k2.metric("Typical error", f"±{MAPE*100:.1f}%")
    k3.metric("Full notebook pipeline — CV RMSE (log)", "0.109", help="All 79 features, Lasso + Gradient Boosting blend (notebook 04)")
    lim = [oof.actual.min(), oof.actual.max()]
    fig = go.Figure([go.Scatter(x=oof.actual, y=oof.predicted, mode="markers", marker=dict(size=5, opacity=.5), name="houses"),
                     go.Scatter(x=lim, y=lim, mode="lines", line=dict(color="red", dash="dash"), name="perfect")])
    fig.update_layout(title="Predicted vs actual price (out-of-fold)", xaxis_title="Actual ($)", yaxis_title="Predicted ($)", height=440)
    h1, h2 = st.columns(2)
    plot(fig)
    err = (oof.predicted / oof.actual - 1) * 100
    plot(px.histogram(err, nbins=50, title="Error distribution (%)", labels={"value": "% error"}).update_layout(height=440, showlegend=False))
    ct, gbr = model.named_steps["ct"], model.named_steps["gbr"]
    names = [n.split("__")[1] for n in ct.get_feature_names_out()]
    imp = pd.Series(gbr.feature_importances_, index=names)
    hood = imp[[n for n in imp.index if n.startswith("Neighborhood_")]].sum()
    imp = imp.drop([n for n in imp.index if n.startswith("Neighborhood_")]); imp["Neighborhood"] = hood
    imp = imp.sort_values()
    plot(px.bar(imp, orientation="h", title="What the model pays attention to", labels={"value": "importance", "index": ""}).update_layout(height=420, showlegend=False))
