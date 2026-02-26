import pandas as pd
import numpy as np
 
RAW_FILE = "raw_rollout_metrics.csv"
OUTPUT_FILE = "dri_observations.csv"
 
def jitter(value, pct=0.15, min_val=None, max_val=None):
    delta = value * pct
    new = value + np.random.uniform(-delta, delta)
    if min_val is not None:
        new = max(min_val, new)
    if max_val is not None:
        new = min(max_val, new)
    return new
 
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
 
def run_agent():
    raw = pd.read_csv(RAW_FILE)
 
    # add some randomness to simulate new observations
    raw["avg_effort_deviation_pct"] = raw["avg_effort_deviation_pct"].apply(
        lambda v: jitter(v, pct=0.2, min_val=0, max_val=60)
    )
    raw["avg_duration_deviation_pct"] = raw["avg_duration_deviation_pct"].apply(
        lambda v: jitter(v, pct=0.2, min_val=0, max_val=60)
    )
    raw["data_readiness_pct"] = raw["data_readiness_pct"].apply(
        lambda v: jitter(v, pct=0.05, min_val=70, max_val=99)
    )
 
    out = pd.DataFrame()
    out["Project"] = raw["project_id"]
    out["Scope Repeatability"] = raw.apply(score_scope_repeatability, axis=1)
    out["Template Maturity"] = raw.apply(score_template_maturity, axis=1)
    out["Variance Predictability"] = raw.apply(score_variance_predictability, axis=1)
    out["Dependency Complexity"] = raw.apply(score_dependency_complexity, axis=1)
    out["Language / Business Intensity"] = raw.apply(score_language_intensity, axis=1)
    out["Governance & Data Readiness"] = raw.apply(score_governance_readiness, axis=1)
 
    out.to_csv(OUTPUT_FILE, index=False)
 
if __name__ == "__main__":
    run_agent()
