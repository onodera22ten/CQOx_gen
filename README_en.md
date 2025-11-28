# CQOx – Causal Query Optimizer

**📖 Documentation**
[🏠 README (Quick Start)](README.md) | **🇺🇸 English (Full)** | [🇯🇵 日本語 (Full)](README_jp.md)

---

**CQOx** is a full–stack platform for **causal marketing decisions**.  
It turns raw event data (CSV or DB extracts) into **incremental profit (Δ¥)**,  
**risk**, and **go / canary / hold** recommendations – with **governance and fairness**
controls that match what top tech and consulting firms build in-house.

> Short version: CQOx gives you a “Google/Netflix-grade” causal decision console  
> for marketing – without needing a research team to recreate it.

---

## 1. Why CQOx exists

Most marketing analytics tools stop at:

- **descriptive dashboards** (CTR, CVR, open rate, revenue),
- or **black-box ML scores** (“propensity: 0.83”).

What business owners actually need is:

- “If we **run this campaign on this segment**,  
  **how much incremental profit (Δ¥)** do we expect?
- **How risky is it?**  
- **Is it fair and compliant?**  
- **Which portfolio of campaigns** maximizes growth under budget / risk / fairness constraints?”

Top companies (Google, Meta, Netflix, Amazon, WPP, BCG, Accenture…)  
build internal stacks that combine:

1. **Causal inference** (uplift, DiD, IV, RD, SCM, etc.),
2. **Experimentation platforms** (A/B, multi-armed bandits),
3. **Portfolio optimization** (profit vs risk, CVaR),
4. **Governance** (fairness, exposure caps, quality gates).

CQOx packages these patterns into a single product that:

- ingests your **CSV or table extracts**,  
- runs **causal estimators & diagnostics**,  
- surfaces **decision-ready views** for marketers and executives,  
- and enforces **governance policies** before anything ships to customers.

---

## 2. Product storyline – from CSV to decisions

A typical flow looks like this:

1. **Upload dataset** (or connect to your warehouse).  
   - Example: campaign logs, user-level outcomes, demographics, costs.

2. **Causal Design**  
   - Auto-detects candidate columns for **treatment, outcome, user id, time, channel, cost**.  
   - You confirm / adjust the causal design (treatment column, outcome column, feature set).  
   - Choose estimators (DR, IPW, DiD, IV, CF, SCM, RD).

3. **Train causal models & run diagnostics**  
   - CQOx trains multiple estimators, runs overlap checks, balance diagnostics,  
     and builds a **Causal Assurance Score (CAS)** for each design.

4. **Decision Console – Marketing Decisions**  
   - Aggregates executed “policies” (campaign decisions) into a **global growth console**.  
   - Shows **total incremental profit, average Δ¥ / policy, CAS, tail-risk (CVaR)**,  
     with drill-downs by segment and channel.

5. **Portfolio – Marketing Portfolio & ROI**  
   - Ranks policies on a **multi-objective Pareto frontier** (profit vs risk vs CAS).  
   - Recommends a **portfolio strategy** (which policies to include / test / exclude).

6. **Digital Twin – Customer Digital Twin**  
   - Simulates how different **customer personas** respond to scenarios  
     (premium vs discount vs nurture vs retention campaigns).  
   - Lets you run “what-if” simulations before touching real customers.

7. **Experiment Studio – Online & Multi-Arm Experiments**  
   - Orchestrates **live experiments** (A/B and multi-arm) with arm allocation and outcome updates.  
   - Supports **offline multi-arm analysis** for historical data.

8. **Governance Center – Fairness, Quality & Compliance**  
   - Checks **fairness** across sensitive attributes (gender, age_group, etc.).  
   - Monitors **data quality** for uplift inputs.  
   - Enforces **frequency caps / exposure limits** and logs violations.

9. **Export Gate**  
   - Exports recommended policies & segments to downstream systems  
     (e.g. ESP/CDP, marketing automation, or internal tools).

---

## 3. What makes CQOx different

### 3.1 Versus traditional BI dashboards

- BI dashboards show **what happened** (revenue, CVR).  
- CQOx shows **what changed because of the intervention** (Δ¥, uplift) –  
  and **what will likely happen** if you adjust your strategy.

Key differences:

- **Δ¥ first**: all views are built around **incremental profit**, not raw revenue.  
- **Policy unit of analysis**: decisions are grouped into **policies**  
  (e.g. “Push v3 to RFM 4–5 + App users”).  
- **Risk & CAS**: every number has a **quality score** and **risk metric** attached.

### 3.2 Versus generic ML / “AI” tools

Most “AI for marketing” tools:

- train **predictive models** (e.g. “probability of purchase next 7 days”),
- optimize **statistical loss functions** (AUC, log-loss),
- and often treat all positive outcomes as equally good, regardless of
  **incrementality, cost, or fairness**.

CQOx is fundamentally different:

- **Causal, not just predictive**  
  - AI/ML answers: “given features X, what is likely to happen?”  
  - CQOx answers: “for the same user, what would have happened  
    **if we did not run this campaign**?” – a **counterfactual** question.  
  - This requires explicit assumptions, estimators, and diagnostics.

- **Business objective, not generic accuracy**  
  - Objective is **incremental profit (Δ¥)** under **risk and governance constraints**,  
    not AUC or generic accuracy.  
  - A model that increases clicks but destroys incremental profit  
    is **penalized**, not celebrated.

- **Transparent & auditable**  
  - Estimators (DR, IPW, DiD, IV, CF, SCM, RD) and diagnostics are visible,  
    so data scientists can inspect what the system is doing.  
  - Governance rules (fairness, frequency caps, quality gates) are explicit –  
    not hidden in a black-box recommender.

- **Stable over time**  
  - Because CQOx models **effects of interventions**, not just correlations,
    policies tend to be more robust to distribution shifts than
    purely predictive recommenders.

In short:

> Generic AI finds patterns; CQOx estimates **effects**  
> and wraps them in **decision and governance logic**.

### 3.3 Versus uplift SaaS / consulting offers

- **Consulting firms (WPP/BCG/Accenture)** often deliver  
  PDFs & slide decks that **summarize one-off studies**.  
  CQOx instead provides a **continuous console** that runs every week/day.

- **Uplift SaaS tools** often focus only on model scores.  
  CQOx additionally offers:
  - **Global Growth Console** (portfolio view across policies),  
  - **Digital Twin** (persona-level simulation),  
  - **Experiment Studio** (online bandit orchestration),  
  - **Governance Center** (fairness, quality, compliance).

### 3.4 How CQOx uses AI (and what it does NOT do)

CQOx is **not** a generative AI tool that “decides everything automatically”.  
Instead, AI is used in **supporting roles**, while **causal estimators and rules**
remain the single source of truth for decisions.

Typical AI-assisted use cases:

- Generate **human-readable rationales** for recommended portfolios.  
- Draft **campaign narratives** or **policy names** based on segments.  
- Help analysts navigate diagnostics (e.g. “summarize key warnings for this policy”).

CQOx deliberately does **not**:

- let a language model override causal estimates or governance rules,  
- deploy campaigns without **explicit human or rule-based approval**,  
- hide the effect estimation logic behind an “AI” label.

This separation keeps the system **auditable, safe, and compliant**,  
while still benefiting from AI where it adds value: communication and workflow.


---

## 4. User Journey: From Data Upload to Action

> **CQOx is not a collection of disconnected features.**
> It is a **single, coherent story** from CSV upload to deployment—designed so that
> *"which policy, to whom, and how much"* flows naturally from data to decision to export.

This section follows the **end-to-end workflow** that users experience in CQOx,
matching the sequence described in `CQOx.PDF`.

---

### 4.1 ① Datasets – Bringing in Your Data

**Story Step:** *"What ingredients are in the refrigerator?"*

At this stage, you are **not yet analyzing**—you are simply **uploading and inspecting** your raw marketing data.

<img src="Picture/Screenshot%20from%202025-11-27%2017-59-03.png" alt="Dataset Management - Upload and Schema Detection" width="800"/>

**What happens here:**

1. **Upload CSV** or connect to your data warehouse (BigQuery, Snowflake, PostgreSQL, etc.)
   - Example file: `marketing_campaign_10k_processed.csv`
   - Contains: `user_id`, `treatment`, `outcome`, `cost`, `channel`, `age`, `income`, demographics, etc.

2. **Automatic Schema Detection**
   - CQOx scans the uploaded data and identifies:
     - Number of rows and columns
     - Data types (numeric, categorical, datetime)
     - Missing values and basic statistics
     - Potential treatment/outcome columns based on naming patterns

3. **Data Preview**
   - View the first N rows
   - Check column distributions
   - Verify data quality before proceeding to causal design

**At this point, you have NOT done any causal inference yet.**
You have simply confirmed: *"This is the raw material I'm working with."*

---

### 4.2 ② Causal Design – Creating the Blueprint

**Story Step:** *"What is treatment A vs B? What is the outcome? Which estimators should we use?"*

This is where you **design the causal inference problem**. You are not running models yet—you are **specifying the blueprint** that will guide all subsequent analysis.

#### Step 1: Select Estimators & Train Models

<img src="Picture/Screenshot%20from%202025-11-27%2016-38-40.png" alt="Causal Design - Estimator Selection and Training" width="800"/>

**What happens here:**

- **Dataset Selection**: Choose which uploaded dataset to analyze
- **Scenario Definition**: Baseline vs Treatment Scenario (e.g., S0 vs S1, A/B Test)
- **Target Metric**: Define what outcome you want to measure (y = ?)
- **Auto-Detection of Columns**:
  - **Treatment Column** `(auto-detected)`: `treatment`, `arm`, `variant`
  - **Outcome Column** `(auto-detected)`: `y`, `revenue`, `delta_yen`
  - **Feature Columns** `(auto-detected)`: Demographics, behavior, context variables
- Users can override any auto-detected column assignment

#### Step 2: Column Mapping and Feature Selection

<img src="Picture/Screenshot%20from%202025-11-27%2016-38-59.png" alt="Column Mapping - Treatment, Outcome, Covariates" width="800"/>

**Estimator Selection:**

Choose which causal inference methods to run in parallel:
- ☑ **DR (Doubly Robust)**: Combines propensity score + outcome regression
- ☑ **IPW (Inverse Propensity Weighting)**: Reweights samples by propensity
- ☐ **DiD (Difference-in-Differences)**: Pre/post comparison with control
- ☐ **IV (Instrumental Variables)**: Handles unmeasured confounding
- ☐ **CF (Causal Forest)**: ML-based CATE for heterogeneous effects
- ☐ **SCM (Synthetic Control)**: Constructs counterfactual from donor pool
- ☐ **RD (Regression Discontinuity)**: Cutoff-based treatment

**Click "実行中..." (Train Models)** → Triggers async Celery tasks

**Recent Analyses Table:**
- Shows all past causal analysis runs
- Columns: `ID`, `Status` (running/completed), `Δ¥`, `Verdict` (Go/Canary/Hold), `Started`
- Each row is clickable to view detailed results

#### Step 3: View Causal Analysis Result

<img src="Picture/Screenshot%20from%202025-11-27%2016-39-56.png" alt="Causal Analysis Result Summary" width="800"/>

**Result Card shows:**

- **Expected Δ¥**: `+¥133,177` (incremental profit)
- **95% CI**: [¥133,177, ¥133,177] (confidence interval)
- **CAS Score**: `0.15` (Low Confidence) — **This is the key quality metric**
- **Verdict**: `✓ GO` (automated decision based on CAS, ROI, and risk)
- **Decision Rationale**: "High expected profit with low risk. Causal quality checks passed."
- **Recommendations**:
  - Proceed with policy deployment
  - Monitor key metrics for first 7 days
  - Set up automated alerts for anomalies

**Button**: `View Detailed Diagnostics →` (leads to Section 4.3)

#### Step 4: S0 vs S1 Scenario Comparison

<img src="Picture/Screenshot%20from%202025-11-27%2016-40-16.png" alt="Baseline vs Treatment Scenario Comparison" width="800"/>

**Side-by-Side Comparison:**

| Metric | S0: Baseline (現状維持) | S1: Treatment (施策実施後) |
|--------|------------------------|---------------------------|
| **Revenue** | ¥0 (No intervention) | **+¥133,177** (Incremental) |
| **Cost** | ¥0 (Status quo) | ¥251K (Campaign cost) |
| **Conversion Rate** | 2.4% (Baseline) | - |
| **Users Affected** | 0 (Control group) | 4,152 (Treatment group) |
| **Projected Outcome/User** | - | ¥936.2 (+¥267.0/user uplift) |

**Key Insight:**

> This comparison answers: *"If we do nothing (S0) vs if we deploy this policy (S1), what is the causal difference in outcomes?"*
> The Δ¥ = S1 - S0 is the **incremental profit** attributable to the intervention.

**At this point:**
- You have specified the causal blueprint (Treatment, Outcome, Covariates)
- You have run multiple estimators in parallel
- You have received a **CAS Score** that tells you how trustworthy the estimate is
- You see the **S0 vs S1 comparison** that quantifies the causal effect

**Next step:** Dive into **Diagnostics** (Section 4.3) to understand *why* the CAS score is what it is.

---

### 4.3 ③ Diagnostics & Audit – Causal Quality Assurance

**Story Step:** *"Is this causal estimate trustworthy? Can we rely on this GO/CANARY/HOLD decision?"*

After running the causal analysis in Step 4.2, you now need to **validate the quality** of the causal inference. This is where the **CAS (Causal Assurance Score)** is calculated and where you verify that the treatment and control groups are comparable, the model is robust, and the heterogeneous treatment effects are credible.

CQOx provides **two modes** for diagnostics:

1. **ViewerMode** – Executive-friendly summary for decision-makers
2. **AnalystMode** – Deep diagnostic suite for data scientists

---

#### ViewerMode: Executive Summary

**For:** CEOs, Marketing Directors, Non-technical stakeholders

**Goal:** Get a quick GO/CANARY/HOLD verdict with confidence level at a glance.

<img src="Picture/Screenshot%20from%202025-11-27%2016-40-49.png" alt="ViewerMode - CAS Score Overview" width="800"/>

**What you see:**

- **CAS Score**: 0.15 (Low Confidence / Quality Level: LOW)
- **Overall Quality**: LOW (CAS Score: 0.15)
- **Validation Status**: 6/9 diagnostic checks passed successfully
- **Confidence Level**: MODERATE (Robustness: Γ=1.0)

**Executive Summary:**

- **Quality Assessment**: The causal analysis has achieved a LOW quality rating with a Causal Assurance Score (CAS) of 0.15. This score indicates limited confidence in the causal estimates.
- **Validation Results**: 6 out of 9 diagnostic checks passed successfully. 3 area(s) require attention.
- **Robustness**: The analysis shows moderate robustness to potential unmeasured confounding (Γ = 1.00). Consider additional validation if unmeasured confounders are plausible.

This single screen answers: *"Can I trust this result enough to make a decision?"*

---

<img src="Picture/Screenshot%20from%202025-11-27%2016-41-00.png" alt="Key Quality Indicators" width="800"/>

**Key Quality Indicators:**

| Indicator | Status | Details |
|-----------|--------|---------|
| **Data Quality** | ⚠️ WARN | Covariate balance: SMD 2.541 (threshold: 0.1) |
| **Statistical Power** | ⚠️ WARN | Common support: 2.9% (threshold: 5%) |
| **Effect Reliability** | ⚠️ WARN | Sensitivity: Γ=1.00 (threshold: 1.3) |
| **Model Performance** | ✅ PASS | CATE calibration: 0.82 (target: > 0.70) |

**What this means**: While the CATE model performs well, there are concerns about data quality (poor covariate balance), statistical power (low common support), and sensitivity to unmeasured confounding.

---

#### AnalystMode: Deep Diagnostic Suite

**For:** Data Scientists, Causal Inference Specialists, ML Engineers

**Goal:** Perform rigorous quality checks before deploying the policy to production.

<img src="Picture/Screenshot%20from%202025-11-27%2016-41-20.png" alt="Analyst Mode Overview Dashboard" width="800"/>

**Diagnostic Tabs Available:**

- **Overview** – Summary of all diagnostic checks
- **Overlap** – Propensity score overlap and common support
- **Balance** – Covariate balance between treatment and control
- **Sensitivity** – Robustness to unmeasured confounding
- **CATE Analysis** – Heterogeneous treatment effects
- **Refutation Tests** – Placebo and falsification tests
- **Advanced** – Network effects, temporal dynamics, heterogeneity

**Quick Status:**

- ✅ **Love Plot**: PASSED (covariate balance after matching)
- ❌ **Covariate Balance (SMD)**: WARNING (Score: 2.54, threshold: 0.1)
- ❌ **Overlap / Positivity**: WARNING (Score: 0.97, threshold: 0.05)
- ✅ **Propensity Density**: PASSED
- ❌ **Sensitivity (Γ)**: WARNING (Score: 1.00, threshold: 1.3)
- ✅ **E-value**: PASSED (Score: 265.85, threshold: 1.5)

---

##### Overlap & Positivity Diagnostics

<img src="Picture/Screenshot%20from%202025-11-27%2016-41-31.png" alt="Overlap Positivity Diagnostics" width="800"/>

**Metrics:**

- **Overlap Score**: 0.029 (Poor) – Measures the extent of overlap between treatment and control propensity distributions
- **Violation Rate**: 97.1% (Threshold: 5%) – Percentage of units outside common support region
- **Common Support**: 98.2% (Units in overlap region) – Percentage of units where both treatment and control exist

**Propensity Score Distribution:**

The chart shows propensity score distributions for treated (blue) and control (red) groups. Good overlap ensures that we can find comparable units across treatment conditions, which is essential for valid causal inference. The propensity score distribution should have substantial overlap between groups.

**Interpretation**: The overlap score of 0.029 indicates **poor overlap**, which raises concerns about the validity of causal estimates in regions with limited common support.

---

<img src="Picture/Screenshot%20from%202025-11-27%2016-41-50.png" alt="Common Support Region" width="800"/>

**Common Support Region:**

This chart shows the overlap region where both treated and control units exist. Higher overlap values indicate better positivity.

- **X-axis**: Propensity Score (probability of receiving treatment)
- **Y-axis**: Overlap Density

The green area represents the region where causal inference is valid (where we have both treatment and control units with similar propensity scores).

**Ideal result**: A large, smooth overlap region across the full range of propensity scores.

---

##### Covariate Balance Diagnostics

<img src="Picture/Screenshot%20from%202025-11-27%2016-42-09.png" alt="Covariate Balance Diagnostics" width="800"/>

**Balance Metrics:**

- **Max SMD (After)**: 2.541 (Threshold: 0.100) – Worst covariate imbalance after matching/weighting
- **Balanced Covariates**: 8/8 (All covariates balanced after matching)
- **Mean SMD (After)**: 0.042 (Average across covariates)

**Love Plot - Standardized Mean Differences:**

- **X-axis**: Standardized Mean Difference (SMD)
- **Y-axis**: List of covariates (Age, Income, Education, Experience, Location_Urban, Gender_Male, Married, Children)
- **Red dots (●)**: Before Matching
- **Green dots (●)**: After Matching

**Interpretation**: Points should be close to zero (vertical line at SMD = 0) for good balance. The plot shows that after matching/weighting, most covariates are well-balanced (green dots near zero), indicating that matching procedure has successfully created comparable treatment and control groups.

**Threshold**: SMD < 0.1 is generally considered good balance (indicated by dashed vertical lines).

---

<img src="Picture/Screenshot%20from%202025-11-27%2016-42-22.png" alt="Covariate Balance Table" width="800"/>

**Detailed Balance Statistics:**

| Covariate | SMD BEFORE | SMD AFTER | IMPROVEMENT | STATUS |
|-----------|------------|-----------|-------------|--------|
| Age | -0.154 | 0.042 | ↓ 0.112 | ✅ BALANCED |
| Income | -0.111 | 0.026 | ↓ 0.084 | ✅ BALANCED |
| Education | -0.172 | 0.018 | ↓ 0.154 | ✅ BALANCED |
| Experience | 0.195 | 0.048 | ↓ 0.148 | ✅ BALANCED |
| Location_Urban | -0.166 | -0.006 | ↓ 0.159 | ✅ BALANCED |
| Gender_Male | -0.091 | -0.031 | ↓ 0.059 | ✅ BALANCED |
| Married | 0.184 | -0.016 | ↓ 0.168 | ✅ BALANCED |
| Children | -0.157 | 0.020 | ↓ 0.137 | ✅ BALANCED |

**Balance Assessment (Green Box):**

All covariates show good balance (SMD < 0.1) after matching. The matching procedure has successfully created comparable treatment and control groups. This supports the assumption that treated and control units are exchangeable conditional on observed covariates.

**Usage**: Analysts can export this table to verify that all covariates meet balance criteria before approving the causal estimate.

---

##### Sensitivity Analysis

<img src="Picture/Screenshot%20from%202025-11-27%2016-42-39.png" alt="Sensitivity Analysis Overview" width="800"/>

**Sensitivity Metrics:**

- **Critical Γ (Gamma)**: 1.00 (Sensitive) – The critical value where conclusions would change
- **E-value**: 265.85 (Minimum confounder strength) – Strength of unmeasured confounding needed to explain away the effect
- **Robustness Level**: MODERATE (Overall assessment)

**Rosenbaum Bounds (Γ Sensitivity):**

This chart shows how p-values change as we vary the strength of potential unmeasured confounding (Γ). The critical Γ is where conclusions would change at the 0.05 significance level.

- **X-axis**: Strength of unmeasured confounding (Γ values)
- **Y-axis**: p-value
- **Orange line**: Critical Γ = 1.00 (where effect becomes non-significant)
- **Blue line**: α = 0.05 (significance threshold)

**Interpretation**:
- Γ = 1.00 means that even a weak unmeasured confounder could invalidate our conclusions
- The analysis shows **moderate robustness** to unmeasured confounding

---

<img src="Picture/Screenshot%20from%202025-11-27%2016-42-52.png" alt="Gamma Interpretation and E-value" width="800"/>

**Γ (Gamma) Interpretation:**

| Γ Value | Interpretation |
|---------|---------------|
| **Γ = 1.0** | No unmeasured confounding. This is the baseline assumption where our estimates are valid. |
| **Γ = 1.0 (Critical Value)** | An unmeasured confounder would need to increase the odds of treatment assignment by 1.0x to change our conclusions at the 0.05 significance level. |
| **Γ = 2.0** | Considered moderately robust. An unmeasured confounder would need to double the odds of treatment to invalidate conclusions. |
| **Γ > 3.0** | Highly robust. Would require very strong unmeasured confounding to change conclusions. |

**E-value Analysis:**

**E = 265.85**

The E-value quantifies the minimum strength of association an unmeasured confounder would need to have with both treatment and outcome to explain away the observed effect.

**Interpretation**: An unmeasured confounder would need to be associated with both treatment and outcome by a risk ratio of at least 265.85-fold each, above and beyond the measured covariates, to explain away the observed treatment effect.

**Conclusion**: E-value > 2.0 indicates robustness to unmeasured confounding.

---

##### CATE Analysis & Model Performance

<img src="Picture/Screenshot%20from%202025-11-27%2016-43-21.png" alt="CATE Analysis Model Performance" width="800"/>

**CATE Metrics:**

- **CATE Calibration Score**: 0.82 (Target: > 0.70) – Measures how well predicted treatment effects match observed effects
- **Qini Coefficient**: 0.24 (Uplift model quality) – Measures targeting ability
- **Heterogeneity Index**: High (Significant effect variation) – Indicates substantial variation in treatment effects across subpopulations

**Qini Curve - Uplift Model Performance:**

The Qini curve evaluates how well the model ranks individuals by treatment benefit. Higher curves indicate better targeting ability.

- **X-axis**: Fraction of Population Targeted (sorted by predicted uplift)
- **Y-axis**: Qini Value (cumulative incremental outcome)
- **Cyan line**: Qini Curve (actual model performance)
- **Dashed line**: Random baseline (no targeting)

**Interpretation**:
- The **steep curve** indicates the model successfully identifies high-uplift users
- A **flat curve** would indicate no predictive power (random targeting)

**Business Implication**: If the curve plateaus early, you can **target only the top 20-30% of users** and still capture 80% of the total uplift, maximizing ROI.

---

<img src="Picture/Screenshot%20from%202025-11-27%2016-43-31.png" alt="CATE Calibration Plot" width="800"/>

**CATE Calibration Plot:**

Compares predicted CATE values with observed treatment effects. Points should fall close to the diagonal line for well-calibrated models.

- **X-axis**: Predicted CATE (model's predicted treatment effect)
- **Y-axis**: Observed CATE (actual treatment effect in validation set)
- **Diagonal line (dashed)**: Perfect calibration
- **Cyan dots**: Individual predictions with confidence intervals

**Interpretation**:

- Points **near the diagonal** → Well-calibrated model
- Points **far from diagonal** → Model is over/under-estimating treatment effects

**CATE Model Assessment (Green Box):**

- Qini curve shows strong uplift model performance with area significantly above random baseline
- Calibration score of 0.82 indicates good agreement between predicted and observed treatment effects
- CATE distribution reveals significant heterogeneity, supporting personalized treatment strategies
- Model successfully identifies high-benefit and low-benefit subpopulations

**Why this matters**: A poorly calibrated model might recommend targeting users with **low actual uplift**, wasting marketing budget.

---

##### Refutation Tests & Robustness Checks

<img src="Picture/Screenshot%20from%202025-11-27%2016-44-03.png" alt="Refutation Tests" width="800"/>

**Refutation Tests:**

Refutation tests attempt to falsify the causal estimate through various robustness checks. These include placebo tests, random treatment assignment, and testing alternative causal mechanisms.

| Test | Status | Details |
|------|--------|---------|
| **Placebo Test** | ✅ PASSED | Placebo outcome: p = 0.72 |
| **Random Common Cause** | ✅ PASSED | Effect: 0.012 ± 0.15 |
| **Data Subset Validation** | ✅ PASSED | Consistent across subsets |

**Placebo Outcome Test:**

Tests whether the treatment affects an outcome that should not be causally related. No significant effect should be found.

- **X-axis**: Group (Control vs Treated)
- **Y-axis**: Placebo Outcome
- **Blue dots**: Group means

**Interpretation**: The plot shows no significant difference between treatment and control groups on the placebo outcome (p = 0.72), which supports the validity of our causal identification strategy.

**Ideal result**: All refutation tests pass (effect disappears when expected).

---

<img src="Picture/Screenshot%20from%202025-11-27%2016-44-14.png" alt="Treatment Effect Robustness Across Subsets" width="800"/>

**Treatment Effect Robustness Across Data Subsets:**

Shows treatment effect estimates across different random subsamples. Consistent estimates indicate robustness.

- **X-axis**: Data Subsets (Subset 1 through Subset 10)
- **Y-axis**: Treatment Effect
- **Blue dots**: Subset-specific estimates
- **Orange dashed line**: Original Effect (reference)

**Interpretation**: All subset estimates are close to the original effect, indicating that the treatment effect is stable and not driven by specific subgroups or outliers.

**Refutation Test Summary (Green Box):**

All refutation tests passed successfully, strengthening confidence in the causal estimate. The placebo test shows no spurious effects, random common cause test confirms no confounding from random variables, and the treatment effect remains stable across data subsets. These results support the validity of our causal identification strategy.

---

##### Advanced Diagnostics

<img src="Picture/Screenshot%20from%202025-11-27%2016-44-41.png" alt="Advanced Diagnostics" width="800"/>

**Advanced Diagnostic Checks:**

| Test | Status | Details |
|------|--------|---------|
| **Network Spillover Test** | ✅ PASSED | Spillover coefficient: 0.03 |
| **Temporal Interference Test** | ✅ PASSED | Lag effect: p = 0.42 |
| **Effect Heterogeneity** | ℹ️ DETECTED | τ² = 125.3, I² = 68% |

**Explanations:**

- **Network Spillover**: No significant network interference detected. Treatment of one unit does not significantly affect outcomes of connected units.
- **Temporal Interference**: No significant temporal carryover effects. Past treatments do not contaminate current treatment effects.
- **Effect Heterogeneity**: Significant heterogeneity detected across subgroups. Effect varies meaningfully by observable characteristics.

**Treatment Effect Heterogeneity by Subgroup:**

Forest plot showing treatment effects across different subpopulations. Varying effects indicate important heterogeneity.

- **X-axis**: Treatment Effect (0-100 scale)
- **Y-axis**: Subgroups (Rural, Urban, Low Income, High Income, Age > 50, Age 30-50, Age < 30, Overall)
- **Blue dots (◆)**: Subgroup-specific treatment effects with confidence intervals
- **Orange dashed line**: Overall Effect (reference)

**Interpretation**:
- Different subgroups show varying treatment effects
- Age < 30 and High Income groups show stronger effects than the overall average
- Rural and Age > 50 groups show weaker effects

**Business Implication**: Consider **targeted strategies** for high-response subgroups (Age < 30, High Income) to maximize ROI.

---

<img src="Picture/Screenshot%20from%202025-11-27%2016-44-52.png" alt="Treatment Effect Temporal Stability" width="800"/>

**Treatment Effect Temporal Stability:**

Shows how the treatment effect evolves over time. Stable effects indicate robust long-term impact.

- **X-axis**: Time (Month 1 through Month 12)
- **Y-axis**: Treatment Effect
- **Cyan line**: Effect over time
- **Dashed lines**: 95% CI (Lower and Upper bounds)

**Interpretation**: The treatment effect remains stable over the 12-month period, indicating robust long-term impact. The effect does not decay or amplify over time.

**Advanced Diagnostics Summary (Light Blue Box):**

- **Network Effects**: No significant spillover detected - SUTVA assumption holds
- **Temporal Stability**: Treatment effects remain stable over 12-month period
- **Heterogeneity**: Significant subgroup variation detected - younger age groups show stronger effects
- **Recommendation**: Consider targeted strategies for high-response subgroups (Age < 30, High Income)

---

**At this point in the story:**

✅ You have uploaded data (Step 4.1)
✅ You have designed the causal analysis (Step 4.2)
✅ You have validated the causal quality (Step 4.3)

**Next step:** Present the results to executives in the **Decision Console** (Section 4.4).

---

### 4.4 ④ Policies & Policy Lab – Custom Scenario Builder

**Story Step:** *"For each policy candidate, what is the expected uplift? Can I create custom targeting scenarios?"*

After validating causal quality in Diagnostics (4.3), you now have a **policy library** — a collection of treatment recommendations, each with its own ATE, CAS score, ROI, and risk profile.

CQOx provides two capabilities here:

1. **Policy Management** – View all policy candidates in a sortable table
2. **Policy Lab** – Create custom scenarios with SQL-based segment definitions

---

#### Policy Management Dashboard

<img src="Picture/Screenshot%20from%202025-11-27%2016-47-53.png" alt="Policy Management - Experiment Orchestrator" width="800"/>

**What you see:**

This is the **Experiment Orchestrator** view, which also serves as the policy management interface.

**Key Features:**

- **Experiment Name**: Assign a name to each policy experiment (e.g., "Premium Email Campaign", "Discount Offer to High-Value Users")
- **Target Metric**: Define the outcome variable (e.g., `delta_yen`, `conversion_rate`, `retention_rate`)
- **Treatment Arms**: Multi-arm setup supporting Control, Variant A, Variant B, etc.

**Actions:**

- **Create Experiment**: Initialize a new policy experiment with specified arms
- **View Online Experiments**: List all running/stopped experiments with status indicators
- **View Allocation**: See current traffic allocation percentages across arms

**Offline Analysis:**

For historical data, you can:
- Select `treatment_arm` column (categorical: control, variant_a, variant_b, ...)
- Select `delta_yen` column (numeric outcome)
- Run multi-arm uplift estimators to compare arm-level performance

---

#### Policy Lab: Custom Scenario Builder

<img src="Picture/Screenshot%20from%202025-11-27%2016-48-07.png" alt="Policy Lab - Custom Scenario Builder with SQL Segmentation" width="800"/>

**What this shows:**

The **Policy Lab** is CQOx's most powerful feature for creating **custom targeting scenarios** without writing code.

**Workflow:**

1. **Define Scenario Name**: e.g., "High-Income Users, Age 30-50, Urban"
2. **SQL-Based Segment Definition**: Use SQL `WHERE` clause syntax to define your target segment
   - Example: `age BETWEEN 30 AND 50 AND income > 100000 AND location = 'Urban'`
3. **Select Treatment Parameters**: Define intervention specifics (discount rate, email frequency, personalization level)
4. **Run Causal Simulation**: Apply trained causal models to predict outcomes for this custom segment
5. **Export Scenario**: Download as YAML/JSON for deployment to marketing automation systems

**Key Capabilities:**

- **No-code segment builder** with SQL-like syntax
- **Instant uplift prediction** using pre-trained causal models
- **S0 vs S1 comparison**: Baseline (no intervention) vs Treatment scenario side-by-side
- **Scenario versioning**: Save and compare multiple scenario variants
- **YAML/JSON export**: Deploy directly to CDP/ESP systems

**Business Value:**

Instead of running costly A/B tests for every segment, you can **pre-test scenarios** using the Digital Twin before deploying to real customers.

**Example Use Cases:**

- "What if we send 2x emails to users who haven't purchased in 30 days?"
- "What if we offer 20% discount only to high-income users in Tokyo?"
- "What if we personalize product recommendations for users with high engagement scores?"

---

### 4.5 ⑤ Decision Console – Executive Dashboard

**Story Step:** *"Which policies should we GO/CANARY/HOLD? Show me the one-page executive summary."*

The **Decision Console** is the single pane of glass for executives to make GO/CANARY/HOLD decisions.

<img src="Picture/Screenshot%20from%202025-11-27%2016-45-11.png" alt="Decision Console - Pareto Frontier and Portfolio Analysis" width="800"/>

**What you see:**

This is the **Pareto Frontier visualization** showing the tradeoff between **Profit (Δ¥)** and **Risk**.

**Key Elements:**

#### Pareto Frontier Chart

- **X-axis**: Risk Score (0.0 - 1.0 scale)
  - Calculated from confidence interval width, sensitivity to unmeasured confounding, and variance of treatment effects
- **Y-axis**: Expected Profit (Δ¥) in millions
- **Point Color**: CAS Quality Level
  - 🟢 **Green**: High Confidence (CAS > 0.7)
  - 🟡 **Yellow**: Medium Confidence (CAS 0.4-0.7)
  - 🔴 **Red**: Low Confidence (CAS < 0.4)
- **Point Size**: Treatment group size (number of users affected)
- **Dashed Curve**: Pareto efficient frontier

**Interpretation:**

- **Points on the frontier** are "efficient" — you cannot get more profit without taking more risk
- **Points below the frontier** are dominated (there exists a better policy with same risk but higher profit)
- **Ideal policies**: Upper-left corner (high profit, low risk, high CAS)

**Decision Verdicts:**

Based on the automated decision logic (see `decision_flow_logic.png`):

- ✅ **GO**: High CAS (> 0.7) + High ROI (> 1.5x) + Low Risk
- ⚠️ **CANARY**: Medium CAS (0.4-0.7) + Moderate ROI + Medium Risk → Test on 10-30% of users first
- 🛑 **HOLD**: Low CAS (< 0.4) OR Negative ROI OR High Risk → Do not deploy

**Example Policies on Chart:**

Looking at the chart, we can see several policy candidates:
- **Policy A** (upper-left, green): High profit (~¥2M), low risk (0.1), high CAS → **GO**
- **Policy B** (middle, yellow): Medium profit (~¥1M), medium risk (0.5), medium CAS → **CANARY**
- **Policy C** (lower-right, red): Low profit (~¥0.5M), high risk (0.9), low CAS → **HOLD**

---

### 4.6 ⑥ Portfolio – Marketing Portfolio Optimization

**Story Step:** *"I don't want to run just one policy. Which combination of policies maximizes ROI under budget constraints?"*

The **Portfolio** page solves the **portfolio optimization problem**:

> Given N policy candidates with expected Δ¥, costs, risks, and CAS scores,
> select the optimal subset that maximizes total Δ¥ subject to:
> - Budget constraint: Σ cost ≤ Budget
> - Risk constraint: Portfolio risk ≤ Max acceptable risk
> - Quality constraint: Mean CAS ≥ Min CAS threshold

---

#### Governance Center: Fairness & Compliance Checks

<img src="Picture/Screenshot%20from%202025-11-27%2016-48-28.png" alt="Governance Center - Fairness and Compliance Monitoring" width="800"/>

**What this shows:**

The **Governance Center** ensures that **no policy violates fairness, quality, or compliance rules** before deployment.

**Sections:**

**1. Data & Sensitivity**

Inputs:
- **Fairness Threshold (Δ¥)**: Maximum allowable disparity in treatment effects across protected groups
- **Min Samples Required**: Minimum sample size per group for valid statistical inference
- **Sensitive Attributes JSON**: Define protected attributes
  ```json
  {
    "gender": ["male", "female"],
    "age_group": ["18-24", "25-34", "35-50", "50+"]
  }
  ```
- **Uplift Data JSON**: User-level treatment effects with sensitive attributes

Actions:
- **Check Fairness**: Compute Δ¥ disparities across groups (Demographic Parity, Equalized Odds)
- **Check Data Quality**: Validate missingness, outliers, extreme uplift values

**2. Compliance (Frequency Cap)**

Inputs:
- **User Exposure JSON**: User ID → impression count mapping
  ```json
  {
    "user_123": 8,
    "user_456": 12,
    "user_789": 5
  }
  ```
- **Max Frequency Cap**: Maximum impressions per user (e.g., 10)

Action:
- **Check Compliance**: Flag users/campaigns exceeding frequency caps

**3. Quality Gates Overview**

List of configured governance rules:
- **Type**: fairness | quality | compliance
- **Severity**: warning | error | critical
- **Action**: log | warn | block
- **Thresholds**: Specific thresholds for each rule

**4. Violation Log**

Timestamped audit trail of all rule violations:
- Which policy violated which rule
- When the violation occurred
- Severity level
- Action taken (warned, blocked, etc.)

---

#### Policy Lab: Custom Scenario Export

<img src="Picture/Screenshot%20from%202025-11-27%2016-48-45.png" alt="Policy Lab - Scenario Builder and Segment Definition" width="800"/>

**What this shows:**

The **Scenario Builder** interface for creating custom targeting scenarios.

**Features:**

**1. Scenario Configuration**

- **Scenario Name**: User-defined label (e.g., "Q4_HighValue_Retention")
- **Target Segment**: SQL-based WHERE clause definition
  - Example: `age BETWEEN 30 AND 50 AND income > 100000 AND previous_purchase_count > 5`
- **Treatment Parameters**:
  - `discount_rate`: 0.0 - 1.0 (e.g., 0.15 = 15% discount)
  - `email_frequency`: emails per week
  - `personalization_level`: 0 (none), 1 (basic), 2 (advanced)

**2. Causal Simulation**

- **Run Simulation** button: Applies trained causal models to predict outcomes
- **S0 vs S1 Comparison**:
  - S0 (Baseline): Expected outcome with no intervention
  - S1 (Treatment): Expected outcome with specified treatment
  - Δ¥: S1 - S0 (incremental profit)

**3. Export Options**

- **YAML Export**:
  ```yaml
  scenario:
    name: Q4_HighValue_Retention
    segment:
      sql: "age BETWEEN 30 AND 50 AND income > 100000"
    treatment:
      discount_rate: 0.15
      email_frequency: 2
    predicted_uplift: 245000
    cas_score: 0.78
  ```

- **JSON Export**:
  ```json
  {
    "scenario_id": "q4_highvalue_retention",
    "segment": {"sql": "age BETWEEN 30 AND 50 AND income > 100000"},
    "treatment": {"discount_rate": 0.15, "email_frequency": 2},
    "predicted_uplift": 245000,
    "cas_score": 0.78
  }
  ```

**4. Scenario Version History**

- Track all scenario iterations
- Compare performance across versions
- Roll back to previous configurations

---

### 4.7 ⑦ Digital Twin – Customer Simulation

**Story Step:** *"Before deploying to real customers, can I simulate the impact on different customer personas?"*

The **Digital Twin** allows you to test policies on **synthetic personas** that represent real customer segments.

---

#### Digital Twin: Persona Cards

<img src="Picture/Screenshot%20from%202025-11-27%2016-49-51.png" alt="Digital Twin - Customer Personas" width="800"/>

**What you see:**

**Customer Persona Cards** representing different customer archetypes.

**Typical Personas:**

1. **High-Value Urban Professional**
   - Age: 30-40
   - Income: ¥8M+
   - Location: Tokyo, Osaka
   - Purchase Frequency: Weekly
   - Average Order Value: ¥15,000
   - Preferred Channel: Mobile App
   - Sensitivity to: Personalization, Premium Products

2. **Budget-Conscious Family**
   - Age: 35-50
   - Income: ¥4-6M
   - Location: Suburban
   - Purchase Frequency: Monthly
   - Average Order Value: ¥8,000
   - Preferred Channel: Email
   - Sensitivity to: Discounts, Bulk Offers

3. **Young Digital Native**
   - Age: 18-29
   - Income: ¥2-4M
   - Location: Urban
   - Purchase Frequency: Weekly
   - Average Order Value: ¥3,000
   - Preferred Channel: Social Media
   - Sensitivity to: Trends, Influencer Recommendations

4. **Senior Loyalist**
   - Age: 60+
   - Income: ¥6-8M
   - Location: Rural/Suburban
   - Purchase Frequency: Bi-weekly
   - Average Order Value: ¥12,000
   - Preferred Channel: Phone, Physical Store
   - Sensitivity to: Loyalty Programs, Personal Service

**Each Persona Card Shows:**

- Demographics
- Behavioral metrics (LTV, frequency, recency)
- Predicted response to different interventions
- Risk factors (churn probability, price sensitivity)

---

#### Digital Twin: Scenario Simulation

<img src="Picture/Screenshot%20from%202025-11-27%2016-50-28.png" alt="Digital Twin - Scenario Simulation Results" width="800"/>

**What this shows:**

**Simulation Results** comparing different intervention scenarios across personas.

**Scenario Tabs:**

- **Predefined Scenarios**:
  1. Premium Email Campaign
  2. Aggressive Discount (20% off)
  3. Nurture Campaign (educational content)
  4. Retention Offer (exclusive benefits)

- **Custom Scenario**: User-defined parameters

**For Each Scenario:**

**Treatment Parameters:**
- `email_frequency`: Number of emails per week
- `discount_rate`: 0.0 - 1.0
- `personalization`: None | Basic | Advanced

**Simulation Results Table:**

| Persona | Baseline Revenue | Treatment Revenue | Δ¥ (Uplift) | ROI | Churn Risk |
|---------|------------------|-------------------|-------------|-----|------------|
| High-Value Urban | ¥180,000 | ¥225,000 | +¥45,000 | 3.2x | -15% |
| Budget-Conscious | ¥96,000 | ¥108,000 | +¥12,000 | 1.5x | -8% |
| Young Digital Native | ¥36,000 | ¥42,000 | +¥6,000 | 2.1x | -5% |
| Senior Loyalist | ¥144,000 | ¥156,000 | +¥12,000 | 1.8x | -12% |

**Visualization:**

- **Δ¥ per Persona × Scenario** (heatmap)
- **Trade-off charts**: Profit vs Churn Risk, Profit vs Cost
- **Sensitivity analysis**: How results change with parameter variations

**Business Decisions from Simulation:**

- **High-Value Urban**: Responds best to Premium Email → Allocate high budget here
- **Budget-Conscious**: Responds to discounts → Use discount campaigns
- **Young Digital Native**: Responds to trends → Use influencer marketing
- **Senior Loyalist**: Responds to loyalty programs → Offer exclusive benefits

**Run Simulation Button:**

Applies the causal model to all personas and shows predicted outcomes **before deploying to real customers**.

---

### 4.8 ⑨ Experiment Studio – A/B Test Management

**Story Step:** *"I need to run controlled experiments. How do I set up A/B tests and analyze results?"*

The **Experiment Studio** orchestrates **online experiments** and analyzes **multi-arm variants**.

---

#### Multi-Arm Experiment Setup

<img src="Picture/Screenshot%20from%202025-11-27%2016-45-41.png" alt="Experiment Studio - Multi-Arm Experiment Setup" width="800"/>

**What this shows:**

**Multi-Arm Experiment Configuration** for setting up A/B/C/... tests.

**Setup Steps:**

1. **Experiment Name**: e.g., "Q4 Email Frequency Test"
2. **Target Metric**: Select outcome variable (e.g., `conversion_rate`, `delta_yen`, `retention_rate`)
3. **Treatment Arms**:
   - **Control**: Baseline (no intervention)
   - **Variant A**: 1 email per week
   - **Variant B**: 2 emails per week
   - **Variant C**: 3 emails per week
   - **Variant D**: (optional) 4 emails per week

4. **Allocation Method**:
   - **Uniform**: Equal traffic to all arms (e.g., 25% each for 4 arms)
   - **Thompson Sampling**: Adaptive allocation based on observed rewards
   - **UCB (Upper Confidence Bound)**: Explore-exploit tradeoff optimization

5. **Sample Size Calculator**: Estimates required sample size for desired statistical power

**Offline Analysis:**

For historical data:
- Select `treatment_arm` column (categorical)
- Select `delta_yen` column (numeric outcome)
- CQOx runs multi-arm uplift estimators (CausalForest, S-Learner, T-Learner, X-Learner)

---

#### Experiment Results & Analysis

<img src="Picture/Screenshot%20from%202025-11-27%2016-46-06.png" alt="Experiment Studio - Results Analysis" width="800"/>

**What this shows:**

**Experiment Results Dashboard** showing performance metrics for each arm.

**Results Table:**

| Arm | Users | Conversion Rate | Avg Δ¥ | 95% CI | Lift vs Control | p-value |
|-----|-------|----------------|---------|---------|-----------------|---------|
| Control | 10,000 | 2.4% | ¥0 | - | - | - |
| Variant A | 10,000 | 2.8% | +¥12,500 | [¥10K, ¥15K] | +16.7% | 0.001 |
| Variant B | 10,000 | 3.1% | +¥18,200 | [¥15K, ¥21K] | +29.2% | <0.001 |
| Variant C | 10,000 | 2.9% | +¥14,800 | [¥12K, ¥18K] | +20.8% | 0.002 |

**Visualizations:**

- **Conversion funnel** by arm
- **Cumulative Δ¥ over time** (sequential analysis)
- **Confidence intervals** (forest plot)
- **Subgroup analysis** (CATE by demographics)

**Statistical Tests:**

- **Multiple Testing Correction**: Bonferroni, Benjamini-Hochberg
- **Sequential Testing**: Allow early stopping for significant results
- **Heterogeneity Tests**: Check if treatment effects vary by segment

**Decision:**

Based on results:
- **Variant B** (2 emails/week) has highest Δ¥ and is statistically significant
- **Recommendation**: Deploy Variant B to 100% of users

---

#### Online Experiment Monitoring

<img src="Picture/Screenshot%20from%202025-11-27%2016-46-36.png" alt="Experiment Studio - Online Monitoring Dashboard" width="800"/>

**What this shows:**

**Real-time Experiment Monitoring** for live A/B tests.

**Monitoring Metrics:**

1. **Sample Ratio Mismatch (SRM)**:
   - Expected allocation: 50% control, 50% treatment
   - Observed allocation: 49.8% control, 50.2% treatment
   - χ² test p-value: 0.42 (no SRM detected ✅)

2. **Metric Guardrails**:
   - **Latency**: < 200ms threshold → Current: 185ms ✅
   - **Error Rate**: < 1% threshold → Current: 0.3% ✅
   - **Bounce Rate**: No significant increase → +0.5% (not significant) ✅

3. **Sequential Analysis**:
   - Plot showing cumulative p-value over time
   - Horizontal lines: α-spending boundaries (e.g., O'Brien-Fleming)
   - Current status: p = 0.003, crossed efficacy boundary → **Early stop recommended**

4. **Allocation Updates**:
   - For Thompson Sampling / Bandits: shows current allocation percentages
   - Updates in real-time based on observed rewards

**Actions:**

- **Stop Experiment**: Declare winner and ramp to 100%
- **Extend Duration**: Continue collecting data
- **Add Arm**: Introduce new variant mid-experiment

---

### 4.9 ⑩ Governance Center – Fairness & Compliance

**Story Step:** *"Before deployment, I need to ensure this policy doesn't violate fairness, quality, or compliance rules."*

The **Governance Center** is the final checkpoint before any policy goes live.

---

#### Fairness Dashboard

<img src="Picture/Screenshot%20from%202025-11-27%2016-47-04.png" alt="Governance Center - Fairness Metrics Dashboard" width="800"/>

**What this shows:**

**Fairness Metrics** showing treatment effect disparities across protected groups.

**Fairness Metrics:**

1. **Demographic Parity**:
   - Measures: P(Ŷ=1 | A=a) should be similar across protected attribute values
   - Example: Treatment allocation rate should be similar for Male vs Female
   - Current: Male 52%, Female 48% → Disparity: 4% ✅

2. **Equalized Odds**:
   - Measures: TPR and FPR should be similar across groups
   - True Positive Rate (Sensitivity): P(Ŷ=1 | Y=1, A=a)
   - False Positive Rate: P(Ŷ=1 | Y=0, A=a)
   - Current: TPR disparity: 3%, FPR disparity: 2% ✅

3. **Uplift Disparity**:
   - Measures: Δ¥ should not have extreme disparities across groups
   - Threshold: Max allowable disparity = ¥50,000
   - Current disparities:
     - Male vs Female: Δ¥_male = ¥135K, Δ¥_female = ¥128K → Disparity: ¥7K ✅
     - Age 18-30 vs 50+: Δ¥_young = ¥145K, Δ¥_senior = ¥110K → Disparity: ¥35K ✅
     - Urban vs Rural: Δ¥_urban = ¥142K, Δ¥_rural = ¥118K → Disparity: ¥24K ✅

**Visualization:**

- **Bar charts** showing Δ¥ by protected groups
- **Disparity thresholds** (dashed lines)
- **Pass/Fail indicators** for each fairness metric

---

#### Data Quality Checks

<img src="Picture/Screenshot%20from%202025-11-27%2016-47-37.png" alt="Governance Center - Data Quality Monitoring" width="800"/>

**What this shows:**

**Data Quality Dashboard** validating input data before causal analysis.

**Quality Checks:**

1. **Missingness**:
   - **Threshold**: < 5% missing values per column
   - **Current**:
     - `age`: 0.2% missing ✅
     - `income`: 1.8% missing ✅
     - `previous_purchases`: 3.1% missing ✅
     - `engagement_score`: 4.9% missing ✅

2. **Outliers**:
   - **Method**: IQR-based detection (values > Q3 + 1.5×IQR or < Q1 - 1.5×IQR)
   - **Threshold**: < 2% outliers per column
   - **Current**:
     - `delta_yen`: 1.2% outliers ✅
     - `cost`: 0.8% outliers ✅
     - `age`: 0.3% outliers ✅

3. **Extreme Uplift Values**:
   - **Threshold**: |Δ¥| < ¥1,000,000 (sanity check)
   - **Current**: Max Δ¥ = ¥285,000, Min Δ¥ = -¥45,000 ✅

4. **Sample Size**:
   - **Threshold**: Min 1,000 samples per treatment group
   - **Current**:
     - Control: 8,524 ✅
     - Treatment: 8,476 ✅

5. **Balance Diagnostics**:
   - **Threshold**: All covariates must have SMD < 0.1 after matching
   - **Current**: Max SMD = 0.042 ✅ (see Section 4.3)

**Actions:**

- **Flag violations**: Red indicators for failed checks
- **Block deployment**: If critical checks fail
- **Generate report**: Export data quality summary

---

#### Compliance Monitoring

<img src="Picture/Screenshot%20from%202025-11-27%2016-47-20.png" alt="Governance Center - Compliance and Frequency Cap Monitoring" width="800"/>

**What this shows:**

**Compliance Dashboard** tracking regulatory and business rule violations.

**Compliance Checks:**

1. **Frequency Cap**:
   - **Rule**: Max 10 marketing touchpoints per user per week
   - **Violation Detection**:
     - User `user_1234`: 12 touches → ⚠️ VIOLATION
     - User `user_5678`: 11 touches → ⚠️ VIOLATION
     - User `user_9012`: 8 touches → ✅ OK
   - **Total Violations**: 127 users (0.8% of population)

2. **Opt-Out Enforcement**:
   - **Rule**: Users on opt-out list must not receive marketing
   - **Violation Detection**: 0 violations ✅

3. **GDPR Compliance**:
   - **Right to Erasure**: 5 deletion requests processed ✅
   - **Data Minimization**: Only essential features used ✅
   - **Consent Tracking**: 100% of users have valid consent ✅

4. **Channel Restrictions**:
   - **Rule**: SMS only between 9 AM - 9 PM
   - **Violation Detection**: 3 SMS sent at 9:15 PM → ⚠️ VIOLATION
   - **Action**: SMS scheduler updated ✅

**Violation Log:**

| Timestamp | User ID | Rule | Severity | Action |
|-----------|---------|------|----------|--------|
| 2025-11-27 16:45 | user_1234 | Frequency Cap | WARNING | Email suppressed |
| 2025-11-27 16:42 | user_5678 | Frequency Cap | WARNING | Email suppressed |
| 2025-11-27 21:15 | user_9012 | SMS Time Restriction | ERROR | SMS blocked |

**Automated Actions:**

- **Suppress**: Prevent message delivery
- **Warn**: Log violation but allow delivery
- **Block**: Halt entire campaign until violation resolved

---

**At this point in the story:**

✅ You have uploaded data (4.1)
✅ You have designed causal analysis (4.2)
✅ You have validated quality (4.3)
✅ You have reviewed policy candidates (4.4)
✅ You have made GO/CANARY/HOLD decisions (4.5)
✅ You have optimized portfolio (4.6)
✅ You have simulated on personas (4.7)
✅ You have run experiments (4.8)
✅ You have passed governance checks (4.9)

**Next step:** Export approved policies to production systems (Export Gate - Section 5).

---

## 5. Visualization Map (specs for each page)

This section is intended as a **spec sheet** for designers & engineers.

### Decision Console

- `Card[0]`: Total Incremental Profit (Δ¥) – sum of Δ¥ over Go (and Canary) decisions.  
- `Card[1]`: Average Δ¥ / Policy – mean Δ¥ over decisions in range.  
- `Card[2]`: Mean CAS – average CAS; show label Low / Medium / High.  
- `Card[3]`: CVaR (worst 10%) – tail-risk estimate (negative values allowed).

- `Chart[Δ¥ Trend]`:  
  - X: week index (`YYYY-Www`), Y: total Δ¥.  
  - Bars for Δ¥, optional line for CAS.

- `Chart[Segment Portfolio]`:  
  - X: segment size (users), Y: Δ¥ / user.  
  - Size: total Δ¥, Color: CAS bucket.

- `Chart[Channel Performance]`:  
  - Bars: Δ¥, line: ROI (%).  
  - X: channel.

- `Table[Decision Cards]`:  
  - Fields: `policy_name`, `dataset`, `channel`, `segment`,  
    `delta_yen`, `roi`, `cas`, `risk_score`, `verdict`, `period`.  
  - Filters: verdict chips (All, Go, Canary, Hold) + text search.

### Portfolio

- `CardGroup[Recommended Portfolio Strategy]`:  
  - `expected_delta_yen`, `portfolio_cas`, `portfolio_risk`, `portfolio_roi`.  
  - `decision_rationale` (text) + bullet `recommendations`.

- `Chart[Pareto Frontier]`:  
  - X: risk, Y: Δ¥, color: CAS, dashed line: frontier.

- `Chart[Portfolio Contribution]`:  
  - Top-N policies by Δ¥; bars show absolute Δ¥ + share of total.

- `Table[Portfolio Policies]`:  
  - Fields: `policy_name`, `dataset`, `channel`, `delta_yen`,  
    `roi`, `risk`, `cas`, `verdict`, `tag (include/test/exclude)`.

### Digital Twin

- `Row[Persona Cards]`: persona name, segment type, age range, LTV, frequency, income.  
- `Row[Scenario Cards]`: scenario name + parameters (`email_frequency`, `discount_rate`, `personalization`).  
- `Button[Run Simulation]`: triggers simulation; results fill charts below.  
- `Chart[Outcome Summary]`: Δ¥ per persona × scenario.  
- `Chart[Trade-off]`: Δ¥ vs risk per scenario.

### Experiment Studio

- `Form[Experiment Orchestrator]`: name, target metric, arms.  
- `List[Online Experiments]`: experiment rows with status and “View Allocation”.  
- `Editor[Update Outcomes JSON]`: array of `{arm_id, reward}`.  
- `Form[Multi-Arm Setup]`: treatment column, outcome column, arms.  
- `Editor[Offline Analysis JSON]`: `X`, `T`, `Y`.

### Governance Center

- `Form[Data & Sensitivity]`: fairness threshold, min samples, sensitive attributes, uplift data.  
- `Buttons`: `Check Fairness`, `Check Data Quality`.  
- `Form[Compliance]`: exposure JSON, max frequency cap, `Check Compliance`.  
- `Table[Quality Gates Overview]`: rule, type, severity, action, threshold.  
- `Table[Violation Log]`: type, severity, details, timestamp.

---

## 6. Architecture (high level)

CQOx is designed as a small set of services:

- **Frontend**: React + Vite + TanStack Query SPA (port 3004).  
- **API Gateway**: FastAPI app for `/api/v1` & `/api/v2` endpoints (port 8000).  
- **Causal Engine**: Python service hosting estimators, diagnostics, simulations.  
- **Reverse Proxy**: Nginx in front of frontend + API, and as SSE/WebSocket gateway.  
- **Monitoring**: Prometheus + Grafana for metrics / dashboards.  

All components are Dockerized so you can run the whole stack with a single command.

---

## 7. Quickstart (example)

> Adjust repository name / ports as needed for your environment.

```bash
# 1. Clone repository
git clone <your-repo-url> cqox
cd cqox

# 2. Start the full stack (frontend, backend, proxy, monitoring)
docker compose up --build

# 3. Open the app
# Frontend (CQOx UI)
open http://localhost:3004

# Optional: Monitoring
open http://localhost:3000   # Grafana
open http://localhost:9090   # Prometheus

