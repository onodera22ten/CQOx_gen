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

## 📊 System Overview

CQOx is a comprehensive causal marketing decision platform that transforms raw event data into actionable insights through a sophisticated pipeline of causal inference, experimentation, portfolio optimization, and governance controls.

**High-Level Architecture:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer (React + Vite)                │
│  Decision Console │ Portfolio │ Digital Twin │ Experiment Studio    │
│  Governance Center │ Policy Lab │ Growth Studio │ Export Gate       │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│                    API Gateway (FastAPI - Port 8000)                │
│              REST API (v1/v2) + WebSocket + SSE Endpoints           │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│                      Causal Engine (Python)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Estimators  │  │  Diagnostics │  │  Simulations │             │
│  │  DR, IPW,    │  │  Balance,    │  │  Digital     │             │
│  │  DiD, IV,    │  │  Overlap,    │  │  Twin,       │             │
│  │  CF, SCM, RD │  │  Sensitivity │  │  Scenarios   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│              Data Layer (PostgreSQL with RLS)                       │
│  Datasets │ Policies │ Experiments │ Governance Logs │ Audit Trail │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                  Monitoring & Observability                         │
│              Prometheus + Grafana + Application Logs                │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Components:**

- **Frontend (Port 3004)**: React SPA with TanStack Query for state management
- **API Gateway (Port 8000)**: FastAPI with JWT authentication and RBAC
- **Causal Engine**: Python service hosting all statistical estimators and diagnostics
- **Reverse Proxy (Nginx)**: Routes traffic, handles SSL, enables WebSocket/SSE
- **Database**: PostgreSQL with Row-Level Security (RLS) for multi-tenancy
- **Monitoring**: Prometheus (Port 9090) + Grafana (Port 3000)

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

### 3.5 What Makes CQOx Different: Comparative Analysis

The table below compares CQOx with alternative approaches to marketing decision-making:

| **Dimension** | **Traditional BI Dashboards** | **Generic AI/ML Tools** | **Uplift SaaS** | **Consulting Firms** | **CQOx** |
|---------------|------------------------------|------------------------|-----------------|---------------------|----------|
| **Primary Focus** | Descriptive analytics (what happened) | Predictive models (who will convert) | Uplift scoring | One-time strategic studies | Causal decision-making (what to do next) |
| **Metric** | Revenue, CVR, CTR | Propensity scores, AUC | Uplift scores | Custom KPIs | Incremental profit (Δ¥), CAS, CVaR |
| **Causality** | None – correlation only | Indirect (prediction ≠ causation) | Yes – uplift modeling | Yes – but ad-hoc | Yes – multiple estimators with diagnostics |
| **Estimators** | N/A | ML classifiers (XGBoost, NN) | DR, S-Learner, T-Learner | Varies by project | DR, IPW, DiD, IV, CF, SCM, RD |
| **Portfolio Optimization** | No | No | Limited | Manual / spreadsheet | Automated Pareto frontier analysis |
| **Digital Twin** | No | No | No | Rarely | Yes – persona-level simulation |
| **Experimentation Platform** | No | No | Limited | No | Full A/B + multi-arm bandit orchestration |
| **Governance & Fairness** | No | No | No | Manual checks | Automated fairness, quality gates, audit trails |
| **Risk Management** | No | No | Limited | Qualitative | Quantitative (CVaR, portfolio risk) |
| **Transparency** | High (SQL queries) | Low (black-box models) | Medium | High (slides) | High (visible estimators + diagnostics) |
| **Real-Time Updates** | Yes | Depends | Limited | No | Yes – continuous console |
| **Multi-Tenancy** | Depends | No | Depends | N/A | Yes – RLS + RBAC |
| **Deployment Model** | Cloud SaaS | Cloud SaaS | Cloud SaaS | Consulting project | Self-hosted or cloud (Docker) |
| **Cost Structure** | Subscription | Subscription | Subscription | Per-project fees | One-time + infrastructure |
| **Time to Value** | Days | Weeks | Weeks | Months | Days (after data prep) |
| **Ideal For** | Tracking performance | Lead scoring, churn prediction | Campaign optimization | Strategic initiatives | Continuous causal marketing decisions |

**Key Takeaways:**

- **BI Dashboards** tell you what happened, but not why or what to do.
- **Generic AI/ML** optimizes predictions, but ignores causality and business constraints.
- **Uplift SaaS** focuses on scoring, but lacks portfolio, experimentation, and governance.
- **Consulting Firms** deliver deep insights once, but not a continuous operational system.
- **CQOx** combines causality, portfolio optimization, experimentation, and governance into a single, auditable, self-service platform.

---

## 🔄 Causal Inference Workflow

CQOx follows a rigorous workflow from raw data to actionable decisions:

```
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 1: DATA INGESTION & VALIDATION                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ • Upload CSV or connect to data warehouse                           │
│ • Schema validation & data quality checks                           │
│ • Missing value detection & outlier flagging                        │
└────────────────────────────┬─────────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 2: CAUSAL DESIGN SPECIFICATION                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ • Auto-detect columns: treatment, outcome, user_id, time, features  │
│ • User confirms/adjusts causal design                               │
│ • Select estimators: DR, IPW, DiD, IV, CF, SCM, RD                  │
│ • Define segments, channels, cost structure                         │
└────────────────────────────┬─────────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 3: CAUSAL MODEL TRAINING                                       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ • Train multiple estimators in parallel                             │
│ • Propensity modeling (for IPW, DR)                                 │
│ • Outcome modeling (for DR, T-Learner)                              │
│ • CATE estimation per user/segment                                  │
└────────────────────────────┬─────────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 4: DIAGNOSTICS & VALIDATION                                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ • Overlap diagnostics (propensity distribution)                     │
│ • Covariate balance checks (SMD, Love plots)                        │
│ • Sensitivity analysis (Rosenbaum bounds)                           │
│ • Refutation tests (placebo, random cause)                          │
│ • Compute Causal Assurance Score (CAS)                              │
└────────────────────────────┬─────────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 5: POLICY GENERATION                                           │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ • Aggregate user-level CATE to policy-level Δ¥                      │
│ • Compute policy-level metrics: ROI, risk, CAS                      │
│ • Generate policy recommendations (Go/Canary/Hold)                  │
└────────────────────────────┬─────────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 6: PORTFOLIO OPTIMIZATION                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ • Multi-objective optimization: profit vs risk vs CAS               │
│ • Pareto frontier analysis                                          │
│ • Budget constraint enforcement                                     │
│ • Recommend optimal policy portfolio                                │
└────────────────────────────┬─────────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 7: GOVERNANCE & COMPLIANCE CHECKS                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ • Fairness audit across sensitive attributes                        │
│ • Data quality verification                                         │
│ • Frequency cap compliance                                          │
│ • Quality gate enforcement                                          │
│ • Log violations & generate audit trail                             │
└────────────────────────────┬─────────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 8: DECISION EXPORT & ACTIVATION                                │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ • Export approved policies to CSV/JSON                              │
│ • API integration with ESP/CDP/marketing automation                 │
│ • Schedule campaigns with target segments                           │
│ • Monitor outcomes & update models                                  │
└──────────────────────────────────────────────────────────────────────┘
```

**Feedback Loop:**
Once campaigns are executed, outcome data flows back into the system, enabling continuous model refinement and policy updates.

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

![Decision Console](Picture/Screenshot%20from%202025-11-27%2016-41-20.png)
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

## 6. System Architecture

CQOx follows a modern microservices architecture with clear separation of concerns, enabling scalability, maintainability, and security.

### 6.1 Architectural Layers

```
┌───────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                   │
│  Web Browser (React SPA) │ Mobile App │ API Clients                  │
└─────────────────────────────┬─────────────────────────────────────────┘
                              │ HTTPS
                              ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    REVERSE PROXY (Nginx)                              │
│  • SSL Termination                                                    │
│  • Load Balancing                                                     │
│  • Rate Limiting                                                      │
│  • WebSocket/SSE Gateway                                              │
└──────────────┬────────────────────────┬───────────────────────────────┘
               │                        │
               ▼                        ▼
┌──────────────────────────┐  ┌────────────────────────────────────────┐
│   FRONTEND (Port 3004)   │  │  API GATEWAY (FastAPI - Port 8000)    │
│  • React 18 + Vite       │  │  • JWT Authentication                 │
│  • TanStack Query        │  │  • OAuth2 Integration                 │
│  • React Router          │  │  • RBAC Middleware                    │
│  • Recharts/D3           │  │  • Request Validation (Pydantic)      │
│  • Tailwind CSS          │  │  • Rate Limiting                      │
└──────────────────────────┘  └─────────────┬──────────────────────────┘
                                            │
                                            ▼
                              ┌──────────────────────────────────────────┐
                              │    BUSINESS LOGIC LAYER                  │
                              │  ┌────────────────────────────────────┐  │
                              │  │  CAUSAL ENGINE (Python)            │  │
                              │  │  • Estimators (DR, IPW, DiD, etc.) │  │
                              │  │  • Diagnostics Engine              │  │
                              │  │  • Simulation Engine               │  │
                              │  │  • Portfolio Optimizer             │  │
                              │  └────────────────────────────────────┘  │
                              │  ┌────────────────────────────────────┐  │
                              │  │  GOVERNANCE ENGINE                 │  │
                              │  │  • Fairness Auditor                │  │
                              │  │  • Quality Gate Enforcer           │  │
                              │  │  • Compliance Monitor              │  │
                              │  └────────────────────────────────────┘  │
                              │  ┌────────────────────────────────────┐  │
                              │  │  EXPERIMENT ENGINE                 │  │
                              │  │  • A/B Test Manager                │  │
                              │  │  • Multi-Arm Bandit Allocator      │  │
                              │  │  • Outcome Tracker                 │  │
                              │  └────────────────────────────────────┘  │
                              └─────────────┬────────────────────────────┘
                                            │
                                            ▼
┌───────────────────────────────────────────────────────────────────────┐
│                     DATA PERSISTENCE LAYER                            │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  PostgreSQL (Primary Database)                               │    │
│  │  • User & Role Management (with RLS)                         │    │
│  │  • Dataset Storage & Metadata                                │    │
│  │  • Policy & Analysis Results                                 │    │
│  │  • Experiment State & Allocations                            │    │
│  │  • Governance Logs & Audit Trail                             │    │
│  └──────────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Object Storage (Optional - S3/MinIO)                        │    │
│  │  • Large CSV Files                                           │    │
│  │  • Model Artifacts                                           │    │
│  │  • Export Archives                                           │    │
│  └──────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│                  MONITORING & OBSERVABILITY                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  Prometheus  │  │   Grafana    │  │     Logs     │               │
│  │  (Port 9090) │  │  (Port 3000) │  │  (Stdout/    │               │
│  │  • Metrics   │  │  • Dashboards│  │   Files)     │               │
│  │  • Alerts    │  │  • Alerting  │  │              │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└───────────────────────────────────────────────────────────────────────┘
```

### 6.2 Key Architectural Patterns

**1. Multi-Tenancy with Row-Level Security (RLS)**
- PostgreSQL RLS policies ensure data isolation between tenants
- Each API request authenticated with JWT containing tenant_id
- Database automatically filters queries based on authenticated tenant

**2. Role-Based Access Control (RBAC)**
- Three primary roles: `admin`, `analyst`, `viewer`
- Permissions enforced at API gateway and database level
- Admin: full access; Analyst: read + analysis + export; Viewer: read-only

**3. Event-Driven Architecture**
- Long-running tasks (model training, simulations) executed asynchronously
- WebSocket/SSE for real-time progress updates to frontend
- Job queue (optional: Redis/Celery) for background processing

**4. Stateless API Design**
- All state stored in database or client (JWT)
- Enables horizontal scaling of API gateway and compute nodes
- Session management via JWT tokens with configurable expiration

**5. Defense in Depth Security**
- SSL/TLS encryption in transit (Nginx)
- Data encryption at rest (PostgreSQL encryption)
- JWT signature verification
- SQL injection prevention (parameterized queries)
- XSS prevention (React escaping + CSP headers)
- CSRF tokens for state-changing operations

### 6.3 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, Vite, TypeScript | Modern SPA framework with fast build times |
| **State Management** | TanStack Query (React Query) | Server state synchronization & caching |
| **UI Components** | Tailwind CSS, Radix UI | Responsive, accessible component library |
| **Data Visualization** | Recharts, D3.js | Charts, graphs, and interactive visualizations |
| **API Gateway** | FastAPI (Python 3.11+) | High-performance async API framework |
| **Authentication** | JWT + OAuth2 | Secure token-based authentication |
| **Causal Inference** | EconML, CausalML, DoWhy | Industry-standard causal estimation libraries |
| **ML/Stats** | scikit-learn, scipy, statsmodels | Statistical computing and ML utilities |
| **Database** | PostgreSQL 15+ with RLS | ACID-compliant relational database |
| **Reverse Proxy** | Nginx | Load balancing, SSL termination, caching |
| **Monitoring** | Prometheus, Grafana | Metrics collection and visualization |
| **Containerization** | Docker, Docker Compose | Reproducible deployment |
| **Orchestration (Prod)** | Kubernetes (optional) | Container orchestration for scale |

### 6.4 Data Flow Example: Running Causal Analysis

```
User Action → Frontend → API Gateway → Causal Engine → Database
─────────────────────────────────────────────────────────────────

1. User clicks "Run Analysis" on Causal Design page
   └─> POST /api/v1/analysis/run { dataset_id, design_id }

2. API Gateway validates JWT, checks RBAC, validates payload
   └─> If authorized → forward to Causal Engine

3. Causal Engine:
   a. Fetch dataset from database
   b. Load causal design (treatment, outcome, covariates)
   c. Train estimators (DR, IPW, DiD, etc.) in parallel
   d. Run diagnostics (overlap, balance, sensitivity)
   e. Compute Causal Assurance Score (CAS)
   f. Store results in database
   g. Emit progress events via WebSocket

4. API Gateway returns analysis_id
   └─> Frontend polls GET /api/v1/analysis/{id}/status
   └─> Or receives real-time updates via WebSocket

5. User views results in Diagnostics & Audit page
```

---

## 7. API Usage Examples

CQOx exposes a comprehensive REST API for all core operations. Below are examples using `curl` and Python.

### 7.1 Authentication

**Obtain JWT Token:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@cqox.com",
    "password": "your-password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Python Example:**
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "admin@cqox.com",
    "password": "your-password"
})
token = response.json()["access_token"]

# Use token in subsequent requests
headers = {"Authorization": f"Bearer {token}"}
```

---

### 7.2 Upload Dataset

**Endpoint:** `POST /api/v1/datasets`

```bash
curl -X POST http://localhost:8000/api/v1/datasets \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@campaign_data.csv" \
  -F "name=Q4 Email Campaign" \
  -F "description=Email campaign with treatment assignment"
```

**Python Example:**
```python
with open("campaign_data.csv", "rb") as f:
    files = {"file": f}
    data = {
        "name": "Q4 Email Campaign",
        "description": "Email campaign with treatment assignment"
    }
    response = requests.post(
        f"{BASE_URL}/datasets",
        headers=headers,
        files=files,
        data=data
    )
    dataset_id = response.json()["dataset_id"]
    print(f"Dataset uploaded: {dataset_id}")
```

---

### 7.3 Configure Causal Design

**Endpoint:** `POST /api/v1/causal-design`

```bash
curl -X POST http://localhost:8000/api/v1/causal-design \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "ds_abc123",
    "treatment_column": "treatment",
    "outcome_column": "revenue",
    "user_id_column": "customer_id",
    "time_column": "timestamp",
    "cost_column": "campaign_cost",
    "features": ["age", "gender", "tenure", "rfm_score"],
    "estimators": ["DR", "IPW", "DiD"],
    "channel": "Email",
    "segment": "High-Value Customers"
  }'
```

**Python Example:**
```python
design_config = {
    "dataset_id": dataset_id,
    "treatment_column": "treatment",
    "outcome_column": "revenue",
    "user_id_column": "customer_id",
    "time_column": "timestamp",
    "cost_column": "campaign_cost",
    "features": ["age", "gender", "tenure", "rfm_score"],
    "estimators": ["DR", "IPW", "DiD"],
    "channel": "Email",
    "segment": "High-Value Customers"
}

response = requests.post(
    f"{BASE_URL}/causal-design",
    headers=headers,
    json=design_config
)
design_id = response.json()["design_id"]
```

---

### 7.4 Run Causal Analysis

**Endpoint:** `POST /api/v1/analysis/run`

```bash
curl -X POST http://localhost:8000/api/v1/analysis/run \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "ds_abc123",
    "design_id": "cd_xyz789"
  }'
```

**Python Example:**
```python
response = requests.post(
    f"{BASE_URL}/analysis/run",
    headers=headers,
    json={
        "dataset_id": dataset_id,
        "design_id": design_id
    }
)
analysis_id = response.json()["analysis_id"]
status_url = response.json()["status_url"]

# Poll for completion
import time
while True:
    status = requests.get(f"{BASE_URL}/analysis/{analysis_id}/status", headers=headers)
    state = status.json()["status"]
    print(f"Analysis status: {state}")
    if state in ["completed", "failed"]:
        break
    time.sleep(2)
```

---

### 7.5 Get Decision Console Summary

**Endpoint:** `GET /api/v1/console/summary`

```bash
curl -X GET "http://localhost:8000/api/v1/console/summary?period=last_28d" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_delta_yen": 1245000,
  "avg_delta_yen_per_policy": 62250,
  "mean_cas": 0.73,
  "cvar_worst_10": -15000,
  "trend": [
    {"week": "2025-W01", "delta_yen": 245000, "cas": 0.71},
    {"week": "2025-W02", "delta_yen": 312000, "cas": 0.75}
  ],
  "segments": [
    {"name": "High-Value", "size": 5000, "delta_yen": 500000, "cas": 0.80},
    {"name": "Medium-Value", "size": 12000, "delta_yen": 450000, "cas": 0.68}
  ],
  "channels": [
    {"name": "Email", "delta_yen": 600000, "roi": 4.5},
    {"name": "Push", "delta_yen": 400000, "roi": 6.2}
  ]
}
```

**Python Example:**
```python
response = requests.get(
    f"{BASE_URL}/console/summary",
    headers=headers,
    params={"period": "last_28d"}
)
summary = response.json()
print(f"Total Δ¥: ¥{summary['total_delta_yen']:,}")
print(f"Mean CAS: {summary['mean_cas']:.2f}")
```

---

### 7.6 Get Portfolio Recommendations

**Endpoint:** `GET /api/v1/portfolio`

```bash
curl -X GET "http://localhost:8000/api/v1/portfolio?budget=500000&max_risk=0.7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "recommended_portfolio": {
    "expected_delta_yen": 665883,
    "portfolio_cas": 0.15,
    "portfolio_risk": 0.59,
    "portfolio_roi": 5.0,
    "num_policies": 5,
    "total_budget": 133177
  },
  "policies": [
    {
      "policy_id": "pol_001",
      "policy_name": "Email Campaign - High RFM",
      "delta_yen": 250000,
      "risk": 0.45,
      "cas": 0.82,
      "roi": 6.2,
      "recommendation": "include"
    }
  ],
  "pareto_frontier": [
    {"risk": 0.2, "profit": 150000},
    {"risk": 0.5, "profit": 500000}
  ]
}
```

---

### 7.7 Create Online Experiment

**Endpoint:** `POST /api/v2/experiments`

```bash
curl -X POST http://localhost:8000/api/v2/experiments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Email Subject Line Test",
    "metric": "open_rate",
    "arms": [
      {"arm_id": "control", "name": "Original Subject"},
      {"arm_id": "variant_a", "name": "Personalized Subject"},
      {"arm_id": "variant_b", "name": "Emoji Subject"}
    ],
    "allocation_strategy": "thompson_sampling"
  }'
```

**Python Example:**
```python
experiment_config = {
    "name": "Email Subject Line Test",
    "metric": "open_rate",
    "arms": [
        {"arm_id": "control", "name": "Original Subject"},
        {"arm_id": "variant_a", "name": "Personalized Subject"},
        {"arm_id": "variant_b", "name": "Emoji Subject"}
    ],
    "allocation_strategy": "thompson_sampling"
}

response = requests.post(
    f"{BASE_URL.replace('v1', 'v2')}/experiments",
    headers=headers,
    json=experiment_config
)
experiment_id = response.json()["experiment_id"]
```

---

### 7.8 Check Fairness Compliance

**Endpoint:** `POST /api/v2/governance/fairness`

```bash
curl -X POST http://localhost:8000/api/v2/governance/fairness \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "pol_001",
    "fairness_threshold": 5000,
    "sensitive_attributes": {
      "gender": ["male", "female"],
      "age_group": ["18-24", "25-34", "35-44", "45+"]
    },
    "uplift_data": [
      {"user_id": "u1", "delta_yen": 120, "gender": "male", "age_group": "25-34"},
      {"user_id": "u2", "delta_yen": 95, "gender": "female", "age_group": "25-34"}
    ]
  }'
```

**Response:**
```json
{
  "fairness_check": "PASSED",
  "disparities": {
    "gender": {
      "male": {"mean_delta_yen": 115, "count": 5000},
      "female": {"mean_delta_yen": 110, "count": 4800},
      "max_disparity": 5,
      "threshold": 5000
    }
  },
  "violations": [],
  "audit_log_id": "audit_12345"
}
```

---

### 7.9 WebSocket: Real-Time Analysis Progress

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analysis/analysis_abc123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.progress}% - ${data.stage}`);

  if (data.status === 'completed') {
    console.log('Analysis complete!', data.results);
  }
};
```

---

## 8. Security & Compliance

CQOx implements enterprise-grade security and compliance features to ensure data protection, access control, and regulatory adherence.

### 8.1 Authentication & Authorization

**JWT + OAuth2 Authentication**
- JSON Web Tokens (JWT) for stateless authentication
- OAuth2 integration for enterprise SSO (Google, Azure AD, Okta)
- Configurable token expiration (default: 1 hour access, 7 day refresh)
- Secure password hashing (bcrypt with salt)

**Role-Based Access Control (RBAC)**

| Role | Permissions |
|------|-------------|
| **Admin** | Full system access: manage users, datasets, policies, configurations, exports |
| **Analyst** | Read + analyze data, create policies, run experiments, export results |
| **Viewer** | Read-only access to dashboards, reports, and visualizations |

RBAC enforcement at:
- API Gateway (FastAPI dependencies)
- Database (PostgreSQL RLS policies)
- Frontend (UI component visibility)

### 8.2 Data Security

**Encryption**
- **In Transit**: TLS 1.3 for all client-server communication
- **At Rest**: PostgreSQL encryption for sensitive columns (PII, financial data)
- **API Tokens**: Encrypted storage, hashed comparison

**Multi-Tenancy & Data Isolation**
- Row-Level Security (RLS) in PostgreSQL ensures tenant data isolation
- Each API request authenticated with tenant_id in JWT
- Database automatically filters all queries by authenticated tenant
- Cross-tenant data leakage prevention via database policies

**Data Retention & Deletion**
- Configurable data retention policies
- Soft delete with audit trail
- GDPR/CCPA-compliant data deletion workflows
- Automatic PII redaction in logs

### 8.3 Governance & Compliance

**Audit Trails**
- All critical operations logged with:
  - User ID, role, timestamp
  - Action type (create, read, update, delete, export)
  - Resource ID (dataset, policy, experiment)
  - IP address, user agent
- Immutable audit logs (append-only)
- Audit log retention: 7 years (configurable)

**Fairness & Bias Detection**
- Automated fairness checks across sensitive attributes (gender, age, ethnicity, etc.)
- Statistical parity, equal opportunity, equalized odds metrics
- Configurable fairness thresholds per policy
- Violation alerts with automatic hold recommendations

**Frequency Caps & Exposure Limits**
- Per-user contact frequency limits (e.g., max 3 emails/week)
- Per-campaign exposure caps
- Channel-specific limits (Email, Push, SMS, etc.)
- Automatic compliance violations flagged in Governance Center

**Quality Gates**
- Minimum sample size requirements
- CAS threshold enforcement (e.g., block policies with CAS < 0.4)
- Data quality checks (missing values, outliers, data drift)
- Configurable severity levels: `info`, `warning`, `critical`
- Auto-block on critical violations

**Regulatory Compliance**
- **GDPR**: Right to access, right to deletion, data portability, consent management
- **CCPA**: Data disclosure, opt-out mechanisms, non-discrimination
- **SOC 2**: Security controls, access logs, encryption
- **HIPAA** (optional): PHI encryption, access controls (for healthcare clients)

### 8.4 Violation Logging & Alerts

**Violation Log Structure:**
```json
{
  "violation_id": "viol_12345",
  "type": "fairness",
  "severity": "critical",
  "policy_id": "pol_001",
  "details": "Gender disparity exceeds threshold: Δ¥ difference = ¥8,500 (threshold: ¥5,000)",
  "timestamp": "2025-11-27T10:30:00Z",
  "action_taken": "policy_blocked",
  "reviewer": null
}
```

**Alert Channels:**
- Email notifications to admins/analysts
- Slack/Teams integration (webhook)
- In-app notifications (bell icon)
- Dashboard alerts (Governance Center)

### 8.5 Security Best Practices

**Deployment Recommendations:**
1. **Production Environment**:
   - Use HTTPS only (Nginx with Let's Encrypt or corporate certs)
   - Enable firewall rules (allow only ports 80/443)
   - Isolate database on private network
   - Use secrets management (Vault, AWS Secrets Manager)

2. **Database Security**:
   - Strong passwords (16+ chars, rotated quarterly)
   - Disable public access (bind to localhost or private IP)
   - Enable PostgreSQL SSL connections
   - Regular backups (daily full + hourly incremental)

3. **API Security**:
   - Rate limiting (100 req/min per user, 1000 req/min per tenant)
   - CORS whitelist (restrict allowed origins)
   - Input validation (Pydantic schemas)
   - SQL injection prevention (parameterized queries only)

4. **Monitoring & Incident Response**:
   - Real-time alerts for failed login attempts (>5 in 10 min)
   - Anomaly detection (unusual data access patterns)
   - Incident response playbook
   - Regular security audits & penetration testing

---

## 9. Quickstart (example)

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

