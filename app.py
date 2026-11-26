"""P717 historical forecast lab; reads a precomputed private artifact."""
import json
import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="P717 Apple Forecast Lab", page_icon="📈", layout="wide")
st.title("Apple stock: historical forecast lab")
st.caption("ExcelR P717 · Historical evaluation, not a live forecast or investment advice")

artifact_path = Path(os.environ.get("P717_DEMO_ARTIFACT", Path(__file__).parent / "artifacts" / "p717_demo_v2.json"))
try:
    with artifact_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    required = {"artifact_version", "dataset_start", "dataset_cutoff", "horizon_sessions", "selected_model", "evaluation", "experiments", "yearly_change", "return_histogram"}
    if not required.issubset(data) or data["artifact_version"] != "2.0" or data["horizon_sessions"] != 30:
        raise ValueError("Unsupported or incomplete forecast artifact")
    experiments = sorted(data["experiments"], key=lambda item: item["origin"])
    models = ["Naive", "ARIMA", "SARIMA", "Random Forest", "XGBoost"]
    if not experiments:
        raise ValueError("No evaluated origins")
    for item in experiments:
        dates = pd.to_datetime(item["dates"], errors="raise")
        if len(dates) != 30 or not dates.is_monotonic_increasing or dates.has_duplicates:
            raise ValueError("Invalid forecast dates")
        if len(item["actual"]) != 30 or any(name not in item["predictions"] or len(item["predictions"][name]) != 30 for name in models):
            raise ValueError("Incomplete evaluated forecasts")
except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
    st.error("The forecast artifact is missing or invalid. After sharing permission is confirmed, place p717_demo_v2.json in the artifacts folder beside this app. See README.md for setup.")
    st.stop()

start, cutoff = data["dataset_start"], data["dataset_cutoff"]
st.info(f"Dataset coverage: {start} to {cutoff}. All forecasts shown are historical; 30 trading sessions is a provisional interpretation of the project horizon.")
overview, eda, comparison, historical = st.tabs(["Overview", "EDA", "Model Comparison", "Historical Forecast"])

with overview:
    st.header("From historical prices to an honest comparison")
    st.write("Explore forecasts made at real evaluation dates, compare them with the next observed Close prices, and see how errors change over the forecast horizon.")
    a, b, c, d = st.columns(4)
    a.metric("Dataset cutoff", cutoff)
    b.metric("Evaluated origins", str(len(experiments)))
    c.metric("Models compared", str(len(models)))
    d.metric("Validation-selected baseline", "Naïve" if data["selected_model"] == "Naive" else data["selected_model"])
    val = data["evaluation"]["validation"]["Naive"]["overall"]["mae"]
    test_naive = data["evaluation"]["test"]["Naive"]["overall"]["mae"]
    test_xgb = data["evaluation"]["test"]["XGBoost"]["overall"]["mae"]
    st.subheader("Why is Naïve the champion?")
    st.write(f"Naïve had the lowest pooled 2018 validation MAE ({val:.3f}). XGBoost scored better on the separate 2019 test ({test_xgb:.3f} versus {test_naive:.3f}), but test scores were not used to change the selection.")
    st.caption("Close and adjusted close are distinct. The supplied file does not establish its exact adjustment method or price currency.")

with eda:
    st.header("Historical data at a glance")
    st.write("Yearly and return-distribution summaries describe the supplied sample; they do not establish a seasonal pattern.")
    yearly = pd.DataFrame(data["yearly_change"])
    yearly["year"] = yearly["year"].astype(str)
    year_axis = alt.X("year:N", title="Year", sort="ascending", axis=alt.Axis(labelAngle=0))
    st.subheader("Year-end Close price")
    price = alt.Chart(yearly).mark_line(point=True, color="#1767aa").encode(
        x=year_axis, y=alt.Y("year_end_close:Q", title="Close price (source units)", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("year:N", title="Year"), alt.Tooltip("year_end_close:Q", title="Close", format=".2f")])
    st.altair_chart(price, width="stretch")
    st.subheader("First-to-last Close change within each year")
    yearly_chart = alt.Chart(yearly).mark_bar(color="#197d91").encode(
        x=year_axis, y=alt.Y("change_pct:Q", title="Change (%)"),
        tooltip=[alt.Tooltip("year:N", title="Year"), alt.Tooltip("change_pct:Q", title="Change (%)", format=".2f")])
    st.altair_chart(yearly_chart, width="stretch")
    hist = pd.DataFrame(data["return_histogram"])
    st.subheader("Distribution of daily Close returns")
    histogram = alt.Chart(hist).mark_bar(color="#537fb5", size=12).encode(
        x=alt.X("return_pct:Q", title="Daily Close return (%)", axis=alt.Axis(tickCount=7, labelExpr="format(datum.value, '.1f') + '%'")),
        y=alt.Y("count:Q", title="Number of sessions"),
        tooltip=[alt.Tooltip("return_pct:Q", title="Bin center (%)", format=".2f"), alt.Tooltip("count:Q", title="Sessions")])
    st.altair_chart(histogram, width="stretch")
    st.caption("Yearly changes exclude the return into the first observed session of each year. Histogram bars summarize return bins.")

with comparison:
    st.header("Overall 30-session model comparison")
    st.write("MAE and RMSE pool all 30 steps across five rolling origins. Lower is better; improvement compares MAE with the naïve baseline.")
    for split, label in [("validation", "Validation · 2018"), ("test", "Test · 2019")]:
        st.subheader(label)
        rows = []
        for name, item in data["evaluation"][split].items():
            rows.append({"Model": "Naïve" if name == "Naive" else name,
                         "MAE": item["overall"]["mae"], "RMSE": item["overall"]["rmse"],
                         "Step 30 MAE": item["step_30"]["mae"],
                         "MAE improvement vs naïve (%)": item["mae_improvement_pct"], "Origins": item["origins"]})
        st.table(pd.DataFrame(rows).round(3))
    if data.get("failures"):
        st.warning("Some model fits failed and are excluded from complete-period comparisons.")
    st.caption("The champion is chosen using validation only. Exploring another model does not change it.")

with historical:
    st.header("Explore an evaluated forecast")
    st.write("Choose a model, an evaluated origin, and a horizon. The lines and metrics below use saved predictions; changing controls does not retrain a model.")
    left, right = st.columns(2)
    model = left.selectbox("Model to explore", models, format_func=lambda name: "Naïve" if name == "Naive" else name)
    labels = [f"{item['origin']} · {item['split'].title()}" for item in experiments]
    selected_label = right.selectbox("Forecast origin", labels, index=len(labels) - 1)
    item = experiments[labels.index(selected_label)]
    horizon = st.slider("Displayed horizon (trading sessions)", 1, 30, 30)
    show_naive = st.checkbox("Show naïve benchmark", value=True)
    actual = pd.Series(item["actual"][:horizon], dtype=float)
    prediction = pd.Series(item["predictions"][model][:horizon], dtype=float)
    baseline = pd.Series(item["predictions"]["Naive"][:horizon], dtype=float)
    mae = float((prediction - actual).abs().mean())
    rmse = float(((prediction - actual) ** 2).mean() ** 0.5)
    baseline_mae = float((baseline - actual).abs().mean())
    baseline_rmse = float(((baseline - actual) ** 2).mean() ** 0.5)
    improvement = None if baseline_mae == 0 else 100 * (1 - mae / baseline_mae)
    m1, m2, m3 = st.columns(3)
    m1.metric("Selected forecast MAE", f"{mae:.3f}")
    m2.metric("Selected forecast RMSE", f"{rmse:.3f}")
    m3.metric("MAE improvement vs naïve", "N/A" if improvement is None else f"{improvement:+.2f}%")
    st.caption(f"Naïve benchmark for this origin and horizon: MAE {baseline_mae:.3f}, RMSE {baseline_rmse:.3f}. Champion: Naïve. Exploring: {'Naïve' if model == 'Naive' else model}.")
    if model == "Naive" and show_naive:
        st.caption("The selected Naïve forecast is the benchmark, so it is shown once.")
    dates = item["dates"][:horizon]
    series = {"Actual Close": actual.tolist(), ("Naïve forecast" if model == "Naive" else model + " forecast"): prediction.tolist()}
    if show_naive and model != "Naive":
        series["Naïve benchmark"] = baseline.tolist()
    frame = pd.DataFrame({"Date": dates, **series})
    long = frame.melt(id_vars="Date", var_name="Series", value_name="Close")
    values = long["Close"]
    padding = max((values.max() - values.min()) * 0.12, abs(float(values.mean())) * 0.005, 0.01)
    names = list(series)
    colors = ["#1767aa", "#d35400", "#616e7c"][:len(names)]
    dashes = [[1, 0], [7, 4], [2, 3]][:len(names)]
    chart = alt.Chart(long).mark_line(point=alt.OverlayMarkDef(size=45, filled=True)).encode(
        x=alt.X("Date:N", sort=dates, title="Evaluated trading session", axis=alt.Axis(labelAngle=-40, labelOverlap="greedy", tickCount=6)),
        y=alt.Y("Close:Q", title="Close price (source units)", scale=alt.Scale(domain=[float(values.min() - padding), float(values.max() + padding)], zero=False)),
        color=alt.Color("Series:N", scale=alt.Scale(domain=names, range=colors), title="Series"),
        strokeDash=alt.StrokeDash("Series:N", scale=alt.Scale(domain=names, range=dashes), legend=None),
        tooltip=[alt.Tooltip("Date:N"), alt.Tooltip("Series:N"), alt.Tooltip("Close:Q", format=".3f")])
    st.altair_chart(chart, width="stretch")
    with st.expander("Show forecast values"):
        st.dataframe(frame.round(3), hide_index=True, width="stretch")
    st.caption("The x-axis contains observed trading sessions only. Price values use the dataset's source units; the naïve forecast repeats the origin's last Close.")
