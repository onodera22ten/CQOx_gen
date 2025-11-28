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

<img src="Picture/Screenshot%20from%202025-11-27%2016-38-59.png" alt="Causal Design - Column Mapping and Estimator Selection" width="800"/>

**What happens here:**

1. **Auto-Detection of Columns**
   - CQOx automatically suggests which columns represent:
     - **Treatment (T)**: `treatment`, `arm`, `variant_a`, etc.
     - **Outcome (Y)**: `revenue`, `sales`, `delta_yen`, `conversion`, etc.
     - **Covariates (X)**: `age`, `income`, `gender`, `region`, `previous_purchases`, etc.
     - **ID / Timestamp**: `user_id`, `date`, etc.
   - UI shows **(auto-detected)** labels
   - You can override any column assignment

2. **Select Estimators**
   - Choose which causal inference methods to run in parallel:
     - **DR (Doubly Robust)**: Combines propensity score + outcome regression, robust to misspecification
     - **IPW (Inverse Propensity Weighting)**: Reweights samples by propensity score
     - **DiD (Difference-in-Differences)**: For pre/post comparison with control group
     - **IV (Instrumental Variables)**: Handles unmeasured confounding with instruments
     - **CF (Causal Forest)**: ML-based CATE estimation for heterogeneous effects
     - **SCM (Synthetic Control Method)**: Constructs counterfactual from donor pool
     - **RD (Regression Discontinuity)**: For cutoff-based treatment assignment

3. **Specify Analysis Unit**
   - Global (entire dataset)
   - By segment (e.g., RFM tier, geography, channel)
   - By time period

4. **Click "Train Models" Button**
   - This triggers async Celery tasks
   - All selected estimators run **in parallel**
   - Results feed into the next step: Diagnostics

**Key Insight:**

> By clearly specifying "what is A vs B" and "what is the outcome," you create a **causal blueprint**.
> This blueprint determines whether your downstream numbers have causal meaning or are just correlation.

---

### 4.3 Policy Lab & Diagnostics

**Goal:** explain **why** the model recommends each policy,  
and let analysts deep-dive into model behavior.

Typical views:

- **Causal effect distributions** (Δ¥ density, Qini / uplift curves).  
- **Propensity overlap plots**.  
- **Balance tables** (SMD lollipop, Love plots).  
- **Sensitivity analysis** (Rosenbaum bounds, etc.).  
- **Segment-level breakdowns** (e.g. uplift by RFM, device, geography).

In the README you can briefly say:

> Policy Lab is where data scientists verify each decision  
> before executives see it in the Decision Console.

---

### 4.4 Portfolio – Marketing Portfolio & ROI

**Goal:** decide **which set of policies** to run together,
given budget, risk, and CAS constraints.

![Portfolio](Picture/Screenshot%20from%202025-11-27%2016-44-03.png)
*Portfolio with Pareto Frontier, Contribution Analysis, and Policy Selection*

#### Recommended Portfolio Strategy

- **Expected Δ¥** for the selected portfolio  
- **Portfolio CAS score** (mean or weighted CAS)  
- **Portfolio risk score** (e.g. variance / downside risk)  
- **Portfolio-level ROI**  
- **Decision rationale** (generated explanation)  
- **Recommendations list**, for example:
  - “Selected 5 / 19 policies.”  
  - “Mean CAS score: 0.75 – Moderate Confidence.”  
  - “Portfolio risk: 0.15 – Low risk.”  
  - “Total budget: ¥133,177.”

#### Pareto Frontier (Profit vs Risk)

- Scatter plot of policies:  
  - X-axis: Risk.  
  - Y-axis: Profit (Δ¥).  
  - Color: CAS quality (High / Medium / Low).  
  - Dashed line: Pareto frontier.  
- **Interpretation hint**: points on the frontier are “efficient” —  
  you cannot get more profit without taking more risk.

#### Portfolio Contribution

- Ranked bar chart of **top contributing policies**.  
  - Shows Δ¥ per policy and share of total portfolio Δ¥.

#### Portfolio Policies table

- All policies with columns:  
  `Policy Name`, `Dataset`, `Channel`, `Δ¥`, `ROI`, `Risk`, `CAS`, `Verdict`.  
- Buttons: `Include`, `Test`, `Exclude`.  
- The **portfolio recommendation** reacts to these toggles.

---

### 4.5 Digital Twin – Customer Digital Twin

**Goal:** answer
"if we change our strategy, what happens to *personas* we care about?"

![Digital Twin](Picture/Screenshot%20from%202025-11-27%2016-46-06.png)
*Digital Twin with Persona Cards and Scenario Simulations*

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

### 4.6 Experiment Studio – Online & Multi-Arm Experiments

**Goal:** orchestrate live experiments and analyze multi-arm variants.

![Experiment Studio](Picture/Screenshot%20from%202025-11-27%2016-47-53.png)
*Experiment Orchestrator with Multi-Arm Setup and Allocation*

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

![Governance Center](Picture/Screenshot%20from%202025-11-27%2016-48-28.png)
*Governance Center with Fairness Checks, Data Quality, and Compliance Monitoring*

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

