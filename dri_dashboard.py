import streamlit as st
import pandas as pd
import numpy as np
import os
 
st.set_page_config(page_title="Deployment Rollout Index (DRI)", layout="wide")
 
# -------------------------
# 1. SIDEBAR – GLOBAL SETTINGS
# -------------------------
st.sidebar.title("DRI Control Panel")
 
st.sidebar.markdown("### Dimension Weights (sum ≈ 100%)")
w_scope = st.sidebar.slider("Scope Repeatability %", 0, 50, 20, 1)
w_template = st.sidebar.slider("Template Maturity %", 0, 50, 20, 1)
w_variance = st.sidebar.slider("Variance Predictability %", 0, 50, 20, 1)
w_dependency = st.sidebar.slider("Dependency Complexity %", 0, 50, 15, 1)
w_language = st.sidebar.slider("Language / Business Intensity %", 0, 50, 10, 1)
w_governance = st.sidebar.slider("Governance & Data Readiness %", 0, 50, 15, 1)
 
weight_sum = w_scope + w_template + w_variance + w_dependency + w_language + w_governance
if weight_sum == 0:
    weight_sum = 1  # avoid division by zero
 
weights = {
    "Scope Repeatability": w_scope / weight_sum,
    "Template Maturity": w_template / weight_sum,
    "Variance Predictability": w_variance / weight_sum,
    "Dependency Complexity": w_dependency / weight_sum,
    "Language / Business Intensity": w_language / weight_sum,
    "Governance & Data Readiness": w_governance / weight_sum,
}
 
st.sidebar.markdown("---")
pilot_threshold = st.sidebar.slider("Minimum DRI score to qualify as FP Pilot", 0.0, 5.0, 3.5, 0.1)
st.sidebar.markdown("Projects with DRI ≥ threshold will be flagged as **Pilot Candidates**.")
 
# -------------------------
# 2. SAMPLE BASELINE DATA
# -------------------------
# Scores are on a 1–5 scale, 5 = high readiness
@st.cache_data(ttl=60)
def load_observed_scores():
    if os.path.exists("dri_observations.csv"):
        return pd.read_csv("dri_observations.csv")
    else:
        # fallback until agent runs first time
        return pd.DataFrame(
            [
                ["MDG-S Rollout", 4.5, 4.5, 4.0, 3.5, 3.5, 4.0],
            ],
            columns=[
                "Project",
                "Scope Repeatability",
                "Template Maturity",
                "Variance Predictability",
                "Dependency Complexity",
                "Language / Business Intensity",
                "Governance & Data Readiness",
            ],
        )
 
def run_observability_agent():
    # Read raw metrics for all 8 projects
    raw = pd.read_csv("raw_rollout_metrics.csv")
 
    def jitter(value, pct=0.15, min_val=None, max_val=None):
        delta = value * pct
        new = value + np.random.uniform(-delta, delta)
        if min_val is not None:
            new = max(min_val, new)
        if max_val is not None:
            new = min(max_val, new)
        return new
 
    # Simulate new observations
    if "avg_effort_deviation_pct" in raw.columns:
        raw["avg_effort_deviation_pct"] = raw["avg_effort_deviation_pct"].apply(
            lambda v: jitter(v, pct=0.2, min_val=0, max_val=60)
        )
    if "avg_duration_deviation_pct" in raw.columns:
        raw["avg_duration_deviation_pct"] = raw["avg_duration_deviation_pct"].apply(
            lambda v: jitter(v, pct=0.2, min_val=0, max_val=60)
        )
    if "data_readiness_pct" in raw.columns:
        raw["data_readiness_pct"] = raw["data_readiness_pct"].apply(
            lambda v: jitter(v, pct=0.05, min_val=70, max_val=99)
        )
 
    def score_scope_repeatability(row):
        if row["rollouts_done"] >= 10:
            return 5
        elif row["rollouts_done"] >= 6:
            return 4
        elif row["rollouts_done"] >= 3:
            return 3
        elif row["rollouts_done"] >= 1:
            return 2
        else:
            return 1
 
    def score_template_maturity(row):
        changes = row["template_changes_last3"]
        if changes == 0:
            return 5
        elif changes == 1:
            return 4
        elif changes == 2:
            return 3
        elif changes == 3:
            return 2
        else:
            return 1
 
    def score_variance_predictability(row):
        dev = max(row["avg_effort_deviation_pct"], row["avg_duration_deviation_pct"])
        if dev <= 10:
            return 5
        elif dev <= 15:
            return 4
        elif dev <= 25:
            return 3
        elif dev <= 35:
            return 2
        else:
            return 1
 
    def score_dependency_complexity(row):
        integ = row["integrations_count"]
        incidents = row["dependency_incidents_last3"]
        if integ <= 2 and incidents == 0:
            return 5
        elif integ <= 3 and incidents <= 1:
            return 4
        elif integ <= 4 and incidents <= 2:
            return 3
        elif integ <= 5 and incidents <= 4:
            return 2
        else:
            return 1
 
    def score_language_intensity(row):
        workshops = row["business_workshops"]
        loc = row["localisation_changes"]
        if workshops <= 2 and loc == 0:
            return 5
        elif workshops <= 3 and loc <= 1:
            return 4
        elif workshops <= 4 and loc <= 1:
            return 3
        elif workshops <= 6 and loc <= 3:
            return 2
        else:
            return 1
 
    def score_governance_readiness(row):
        readiness = row["data_readiness_pct"]
        failed = row["failed_quality_gates_last3"]
        if readiness >= 95 and failed == 0:
            return 5
        elif readiness >= 92 and failed <= 1:
            return 4
        elif readiness >= 88 and failed <= 2:
            return 3
        elif readiness >= 80 and failed <= 3:
            return 2
        else:
            return 1
 
    out = pd.DataFrame()
    out["Project"] = raw["project_id"]
    out["Scope Repeatability"] = raw.apply(score_scope_repeatability, axis=1)
    out["Template Maturity"] = raw.apply(score_template_maturity, axis=1)
    out["Variance Predictability"] = raw.apply(score_variance_predictability, axis=1)
    out["Dependency Complexity"] = raw.apply(score_dependency_complexity, axis=1)
    out["Language / Business Intensity"] = raw.apply(score_language_intensity, axis=1)
    out["Governance & Data Readiness"] = raw.apply(score_governance_readiness, axis=1)
 
    out.to_csv("dri_observations.csv", index=False)
 
df = load_observed_scores()
st.markdown("### Observability Agent")
if st.button("Simulate new rollout data (run agent)"):
    run_observability_agent()
    load_observed_scores.clear()
    st.experimental_rerun() 
# Allow user tweaks of baseline scores
st.markdown("## Deployment Rollout Index – Baseline Projects")
st.markdown(
    "You can fine‑tune 1–5 scores below (while on T&M) to reflect actual rollout experience. "
    "The DRI engine recomputes scores and pilot candidates in real time."
)
 
edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "Scope Repeatability": st.column_config.NumberColumn(min_value=1.0, max_value=5.0, step=0.5),
        "Template Maturity": st.column_config.NumberColumn(min_value=1.0, max_value=5.0, step=0.5),
        "Variance Predictability": st.column_config.NumberColumn(min_value=1.0, max_value=5.0, step=0.5),
        "Dependency Complexity": st.column_config.NumberColumn(min_value=1.0, max_value=5.0, step=0.5),
        "Language / Business Intensity": st.column_config.NumberColumn(min_value=1.0, max_value=5.0, step=0.5),
        "Governance & Data Readiness": st.column_config.NumberColumn(min_value=1.0, max_value=5.0, step=0.5),
    },
)
 
# -------------------------
# 3. DRI CALCULATION
# -------------------------
def compute_dri(row, w):
    return (
        row["Scope Repeatability"] * w["Scope Repeatability"]
        + row["Template Maturity"] * w["Template Maturity"]
        + row["Variance Predictability"] * w["Variance Predictability"]
        + row["Dependency Complexity"] * w["Dependency Complexity"]
        + row["Language / Business Intensity"] * w["Language / Business Intensity"]
        + row["Governance & Data Readiness"] * w["Governance & Data Readiness"]
    )
 
edited_df["DRI Score"] = edited_df.apply(lambda r: compute_dri(r, weights), axis=1)
edited_df["Pilot Candidate"] = np.where(
    edited_df["DRI Score"] >= pilot_threshold, "Yes", "No"
)
 
sorted_df = edited_df.sort_values("DRI Score", ascending=False).reset_index(drop=True)
 
# -------------------------
# 4. MAIN LAYOUT
# -------------------------
col1, col2 = st.columns([2, 1])
 
with col1:
    st.markdown("### Ranked Project List by DRI Score")
    st.dataframe(
        sorted_df,
        use_container_width=True,
        hide_index=True,
    )
 
with col2:
    st.markdown("### Pilot Candidate Summary")
    st.metric("Pilot Threshold (DRI)", f"{pilot_threshold:0.1f}")
    total = len(sorted_df)
    pilots = (sorted_df["Pilot Candidate"] == "Yes").sum()
    st.metric("Number of Pilot Candidates", f"{pilots} of {total}")
    st.progress(pilots / total if total > 0 else 0.0)
 
    st.markdown("#### Dimension Weights (Normalised)")
    for dim, w in weights.items():
        st.write(f"{dim}: {w*100:0.1f}%")
 
st.markdown("---")
st.markdown(
    """
### How to use in a bid defense
 
1. **Start with baseline** scores from historic T&M rollouts.  
2. **Show weight sliders** to reflect what matters most for the client (template maturity vs. dependency risk, etc.).  
3. **Adjust scores live** based on new information about specific projects.  
4. The **DRI ranking and pilot flags update instantly**, demonstrating an evidence‑based, objective route to Fixed Price pilots.
"""
)
