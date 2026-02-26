import streamlit as st
import pandas as pd
import numpy as np
import os
import subprocess
 
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
        # fallback if agent hasn’t run yet
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
    subprocess.run(["python", "observability_agent.py"], check=False)
 
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
