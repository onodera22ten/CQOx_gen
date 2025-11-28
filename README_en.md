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

## 4. Main modules

### 4.1 Datasets & Causal Design

**Goal:** turn raw data into a **well-specified causal problem**.

- Upload CSVs or connect to warehouse tables.  
- Auto-detect columns for:
  - `treatment`, `control`, `variant_*`, `arm`  
  - `outcome` (revenue, conversion, CLV, insurance payout, etc.)  
  - `user_id` / `customer_id`  
  - `timestamp` / `date`  
  - `channel`, `segment`, `campaign_id`  
  - `cost` / `spend`

**Column auto-detection heuristics:**

- Uses **column names**, **value cardinality**, and **value distributions**:
  - binary 0/1 or {0,1} with names containing `treatment`, `treated`, `is_*` → treatment candidates  
  - low-cardinality integer or string with values like `control`, `variant_a` → multi-arm treatment  
  - monetary columns with skewed positive values and names like `revenue`, `sales`, `ltv`, `delta_yen` → outcome candidates  
  - high-cardinality IDs → user_id / campaign_id  
- UI shows **“(auto-detected)” label** and lets users override.

**Estimators:**

- **DR, IPW, AIPW, X-Learner** (ATE / CATE uplift)  
- **DiD** (staggered adoption)  
- **IV** (instrumental variables, LATE)  
- **CF / SCM** (synthetic controls)  
- **RD** (regression discontinuity)

All estimators feed into a **Causal Assurance Score (CAS)** that combines:

- overlap diagnostics,  
- covariate balance,  
- model agreement,  
- and sensitivity checks.

---

### 4.2 Decision Console – Marketing Decisions (Global Growth Console)

**Goal:** a single page where CMOs can see
"how much incremental money the machine is printing, at what risk."

![Decision Console](Picture/Screenshot%20from%202025-11-27%2016-46-06.png)
*Decision Console with KPIs, Δ¥ Trend, Segment Portfolio, and Decision Cards*

#### KPIs row

- **Total Incremental Profit (Δ¥)**  
  - Sum of Δ¥ across “Go” (and optionally “Canary”) decisions  
    for the selected period.

- **Average Δ¥ / Policy**  
  - Mean incremental profit per policy in the period.  
  - Target ≥ 0.

- **Mean CAS (Causal Assurance Score)**  
  - Average CAS across policies;  
  - Thresholds: Low / Medium / High (e.g. 0–0.6 / 0.6–0.8 / 0.8–1.0).

- **CVaR (worst 10%)**  
  - Conditional Value at Risk on Δ¥.  
  - Interpreted as “expected downside in the worst 10% of policies”.

#### Charts & tables

- **Δ¥ Trend**  
  - X-axis: time (week or day).  
  - Y-axis: total Δ¥ (bars) + CAS overlay (optional line).  
  - Shows trajectory of incremental profit.

- **Segment Portfolio**  
  - Bubble chart.  
  - X-axis: segment size (reach).  
  - Y-axis: Δ¥ per user or per segment.  
  - Bubble size: total Δ¥.  
  - Color: CAS bucket (High / Medium / Low).

- **Channel Performance**  
  - Bar or dot chart.  
  - X-axis: channel (Email, Push, App, Web, etc.).  
  - Left Y-axis: total Δ¥ (bars).  
  - Right Y-axis: ROI (line).

- **Decision Cards table**  
  - Columns:  
    `Policy`, `Dataset`, `Channel`, `Segment`, `Δ¥`, `ROI`, `CAS`, `Risk`, `Verdict`, `Period`.  
  - Verdict: `Go`, `Canary`, `Hold`.  
  - Filters: by verdict & search by policy/segment name.

> This page should be usable by executives with **zero knowledge of causal inference**.  
> All technical details are pushed into Diagnostics and Policy Lab.

---

### 4.3 Diagnostics & Quality Assurance

**Goal:** Verify causal assumptions with comprehensive diagnostic checks that validate result trustworthiness before presenting to executives.

<img src="Picture/Screenshot%20from%202025-11-27%2016-38-40.png" alt="Diagnostics Overview - CAS Score Summary" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-39-56.png" alt="Overlap/Positivity Diagnostics" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-40-16.png" alt="Common Support Region - Propensity Score Distribution" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-40-49.png" alt="Covariate Balance (SMD)" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-41-00.png" alt="Love Plot - Standardized Mean Differences" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-41-31.png" alt="Covariate Balance Table" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-41-50.png" alt="Sensitivity Analysis Overview" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-42-09.png" alt="Rosenbaum Bounds (Γ Sensitivity)" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-42-22.png" alt="Gamma Interpretation Guide" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-42-39.png" alt="E-value Analysis" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-42-52.png" alt="CATE Analysis & Model Performance" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-43-21.png" alt="Qini Curve - Uplift Model Quality" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-43-31.png" alt="CATE Calibration Plot & Refutation Tests" width="800"/>

**Key Diagnostics:**
- **Overlap/Positivity**: Ensure treated and control units exist across covariate distributions; visualize propensity scores
- **Covariate Balance**: Check comparability via Love Plots showing SMD before/after adjustment
- **Sensitivity Analysis**: Compute Rosenbaum bounds and E-values to quantify robustness against unmeasured confounding
- **Refutation Tests**: Placebo tests, random common cause, data subset validation to catch spurious results
- **CATE Analysis**: Assess treatment effect heterogeneity and uplift model performance (Qini curve)

All diagnostics aggregate into the **CAS Score** (0-1): CAS ≥ 0.8 → GO, 0.6-0.8 → CANARY, < 0.6 → HOLD.

---

### 4.4 Policy Lab

**Goal:** Design, evaluate, and simulate marketing policies before production deployment.

<img src="Picture/Screenshot%20from%202025-11-27%2016-48-45.png" alt="Custom Scenario Builder" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-49-51.png" alt="Target Segment Builder" width="800"/>

**Custom Scenario Builder:**
Define intervention parameters using interactive sliders and checkboxes:
- **Contact Frequency**: Touchpoints per month (1-30)
- **Discount Rate**: Discount percentage (0-50%)
- **Budget Cap**: Maximum spend per customer or campaign
- **Communication Channels**: Email, SMS, Push, LINE, In-App, Direct Mail (select multiple)

**Target Segment Builder:**
Define exactly which customers receive the intervention:
- **GUI Builder**: Point-and-click interface for common segments (RFM score, recency, engagement)
- **SQL Editor**: Write arbitrary SQL WHERE clauses for advanced targeting

Example segments:
- "High-Value Dormant Users": `rfm_score >= 4 AND days_since_last_purchase > 90`
- "Weekend Shoppers in Major Cities": `purchase_day_of_week IN ('Sat', 'Sun') AND city IN ('Tokyo', 'Osaka', 'Nagoya')`
- "Mobile App Power Users": `app_sessions_last_30d > 15 AND platform = 'mobile'`
- "Cart Abandoners with High Intent": `cart_value > 5000 AND cart_abandoned = TRUE AND days_since_abandon < 7`

---

### 4.5 Digital Twin – Customer Digital Twin

**Goal:** Simulate customer-level responses before deploying to real customers using a persona-based prediction engine.

<img src="Picture/Screenshot%20from%202025-11-27%2016-44-14.png" alt="Digital Twin - Persona Selection" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-44-41.png" alt="Digital Twin - Scenario Simulation" width="800"/>

Key elements:

- **Persona cards**  
  - Each card: demographics, LTV, frequency, income, brief description.  
  - Example personas: “High-Value Urban Professional”,  
    “Budget-Conscious Family”, “Young Digital Native”, etc.

- **Intervention scenarios**  
  - Tabs: `Predefined Scenarios`, `Custom Scenario`.  
  - Predefined:  
    - Premium Email Campaign  
    - Aggressive Discount  
    - Nurture Campaign  
    - Retention Offer  
  - Each scenario shows parameters: `email_frequency`, `discount_rate`, `personalization`.

- **Run Simulation button**  
  - Runs the **causal model** on persona-like profiles  
    to estimate Δ¥, churn, engagement, etc.

- **Simulation results**  
  - Δ¥ per persona × scenario.  
  - Trade-off charts (e.g. profit vs retention risk).

This view is especially helpful for **non-technical marketers**.

---

### 4.6 Portfolio – Marketing Portfolio & ROI

**Goal:** Optimize the portfolio of interventions considering budget constraints, audience overlap, and cannibalization.

<img src="Picture/Screenshot%20from%202025-11-27%2016-44-52.png" alt="Recommended Portfolio Strategy" width="800"/>

<img src="Picture/Screenshot%20from%202025-11-27%2016-45-11.png" alt="Pareto Frontier - Profit vs Risk" width="800"/>

Not all policies can be deployed simultaneously due to budget constraints, audience overlap, and cannibalization. This module computes the **Pareto Frontier** – policy combinations that maximize:
- **Profit (Δ¥)**: Total incremental revenue
- **Risk (CVaR)**: Worst-case downside
- **Quality (CAS)**: Confidence in results

**How it works:**
1. Input all GO and CANARY-rated policies
2. Specify constraints (total budget, max frequency caps, channel limits)
3. CQOx runs multi-objective optimization to find efficient portfolios
4. Visualize Pareto Frontier: trade-off between Profit and Risk

**Key Features:**
- **Recommended Portfolio Card**: Optimal policy combination with Expected Δ¥, CAS Score, Risk Score, ROI, and decision rationale
- **Pareto Frontier Visualization**: Scatter plot of Profit vs Risk, color-coded by CAS quality (High/Med/Low)
- **Portfolio Contribution Ranking**: Top 5 policies by marginal contribution to total Δ¥
- **Constraint Satisfaction Check**: Validate portfolio respects budget caps, frequency limits, channel restrictions

---

### 4.7 Experiment Studio – Online & Multi-Arm Experiments

**Goal:** orchestrate live experiments and analyze multi-arm variants.

![Experiment Studio](Picture/Screenshot%20from%202025-11-27%2016-46-36.png)

![Offline Analysis](Picture/Screenshot%20from%202025-11-27%2016-47-04.png)

![Experiment Orchestrator](Picture/Screenshot%20from%202025-11-27%2016-47-53.png)

Sections:

- **Experiment Orchestrator**  
  - Setup: experiment name, target metric, arms (`control`, `variant_a`, …).  
  - Create experiment → backend initializes allocation state.  
  - Online Experiments list: shows status (`running`, `stopped`)  
    and exposes a **View Allocation** action.

- **Update Outcomes**  
  - JSON input of observed rewards per arm.  
  - Backend updates allocation policy (e.g. Thompson sampling / UCB).

- **Multi-Arm Experiment Setup**  
  - For offline data: select `treatment_arm` and `delta_yen` columns.  
  - Add arms (Control, Variant A/B/C, etc.).  
  - Create experiment and analyze historical uplift.

- **Offline Analysis (Multi-Arm)**  
  - JSON payload with feature matrix `X`, treatment vector `T`, outcome `Y`.  
  - Runs multi-arm uplift estimators; returns arm-level performance and risks.

---

### 4.7 Governance Center – Fairness, Quality & Compliance

**Goal:** ensure that **no policy goes live**
if it violates fairness, quality, or exposure rules.

![Governance Center](Picture/Screenshot%20from%202025-11-27%2016-47-37.png)

![Data Quality Warnings](Picture/Screenshot%20from%202025-11-27%2016-47-53.png)

![Compliance Frequency Cap](Picture/Screenshot%20from%202025-11-27%2016-48-07.png)

![Quality Gates Overview](Picture/Screenshot%20from%202025-11-27%2016-48-28.png)

Sections:

- **Data & Sensitivity**  
  - Inputs:  
    - Fairness Threshold (Δ¥)  
    - Min Samples Required  
    - `Sensitive Attributes JSON` (e.g. `{"gender": ["male","female"], "age_group": ["25-34","18-24"]}`)  
    - `Uplift Data JSON` (user-level Δ¥ and sensitive attributes).  
  - Actions:  
    - `Check Fairness` – compute disparities in Δ¥ across groups.  
    - `Check Data Quality` – check missingness, outliers, and extreme uplift.

- **Compliance (Frequency Cap)**  
  - `User Exposure JSON` (user → impression count).  
  - `Max Frequency Cap` (e.g. 10).  
  - `Check Compliance` – flag users/campaigns exceeding configured caps.

- **Quality Gates Overview**  
  - List of configured rules:  
    - type (fairness, quality, compliance),  
    - severity,  
    - action (warn, block),  
    - thresholds.

- **Violation Log**  
  - Timestamped log of rule violations;  
  - used as an **audit trail** for governance.

> In practice, you can wire these gates so that  
> **no export / activation is allowed if severe violations are present**.

---

### 4.8 Growth Studio / Global Growth Console

This is the “zoomed-out” view of growth experiments:

- Summarizes **experiments**, **policies**, and **segments** over time.  
- Helps Growth / Strategy teams track progress toward  
  long-term KPIs (CLV, churn reduction, market expansion).

Visualizations are typically:

- Number of policies / experiments by status.  
- Cumulative Δ¥ vs target trajectory.  
- Heatmaps by region / product line / channel.

---

### 4.9 Export Gate & Admin

- **Export Gate**  
  - Exports selected segments, policies, and templates  
    as CSV / JSON or via APIs to ESP/CDP systems.

- **Admin**  
  - User roles (admin / analyst / viewer),  
  - language toggle (EN / 日本語),  
  - system health shortcuts (Grafana, Prometheus, logs).

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

