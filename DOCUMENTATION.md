# CQOx Complete Documentation

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Installation](#installation)
3. [Data Upload & Column Mapping](#data-upload--column-mapping)
4. [Causal Inference](#causal-inference)
5. [Policy Management](#policy-management)
6. [Multi-Objective Optimization](#multi-objective-optimization)
7. [API Reference](#api-reference)
8. [Deployment](#deployment)

## Architecture Overview

CQOx consists of several layers:

### 1. Data Layer
- **Semantic Schema**: Canonical column definitions in `config/data_contract.yaml`
- **Column Mapping**: Automatic mapping with fail-fast validation
- **Feature Store**: RFM, behavioral, and treatment history features

### 2. Causal Engine
- **7 Estimators**: S/T/X/DR-Learner, Causal Forest, Uplift Forest
- **14 Diagnostics**: Balance, overlap, sensitivity, etc.
- **CAS Score**: Causal Assurance Score (0-1)

### 3. Policy Engine
- **Offline Evaluation**: IPS and DR estimators
- **Multi-Objective**: Pareto frontier optimization
- **Recourse**: Counterfactual recommendations
- **Export**: Target list generation

### 4. UI Layer
- React + Vite frontend
- TanStack Query for state management
- Responsive design

## Installation

### Prerequisites

```bash
# Python 3.11+
python --version

# Node.js 18+
node --version

# Wolfram ONE (optional, for visualizations)
wolframscript --version
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Data Upload & Column Mapping

### Workflow

1. **Upload File**
   ```bash
   POST /api/upload
   ```
   Returns suggested column mappings based on:
   - Exact alias matches
   - String similarity
   - Semantic column definitions

2. **Review Mapping**
   UI displays mapping table:
   - Left: Semantic columns (unit_id, time, treatment, y, X_*)
   - Right: Uploaded columns (dropdowns)
   - Highlights: Required columns in red if unmapped

3. **Apply Mapping**
   ```bash
   POST /api/upload/apply-mapping
   ```
   Performs:
   - Column renaming
   - Type conversion
   - Validation against data contract
   - Fail-fast on errors

4. **Save Profile** (optional)
   Save mapping for reuse with future uploads

### Data Contract

`config/data_contract.yaml` defines:

```yaml
semantic_columns:
  unit_id:
    description: "User/customer ID"
    type: string
    required: true
    aliases: [user_id, uid, customer_id]

  treatment:
    description: "Treatment assignment"
    type: categorical
    required: true
    aliases: [is_treated, campaign_flag]

  y:
    description: "Outcome variable"
    type: numeric
    required: true
    aliases: [revenue, purchase, conversion]
```

### Validation Rules

- Max 10% missing values for required columns
- Max 1% type conversion errors
- Fail-fast with detailed error messages

## Causal Inference

### Training Models

```python
from cqox.causal import SLearner, TLearner, DRLearner
from cqox.data.loader import DataLoader

# Load data
df = DataLoader.load_parquet("data/normalized.parquet")

X = df[[col for col in df.columns if col.startswith('X_')]]
treatment = df['treatment']
y = df['y']

# Train S-Learner
s_learner = SLearner()
s_learner.fit(X, treatment, y)

ate = s_learner.estimate_ate()
cate = s_learner.estimate_cate(X)

print(f"ATE: {ate:.2f}")
print(f"CATE mean: {cate.mean():.2f}, std: {cate.std():.2f}")
```

### Diagnostics

```python
from cqox.causal.diagnostics import covariate_balance_test, overlap_test

# Balance test
passed, report = covariate_balance_test(X, treatment)
print(f"Balance test: {'PASSED' if passed else 'FAILED'}")
print(f"Max SMD: {report['max_smd']:.3f}")

# Overlap test
passed, report = overlap_test(X, treatment)
print(f"Overlap test: {'PASSED' if passed else 'FAILED'}")
print(f"Violation rate: {report['violation_rate']:.2%}")
```

## Policy Management

### Policy YAML Structure

```yaml
id: "my_policy_v1"
name: "High-value retention campaign"
description: "Target high-value customers at risk of churn"

dataset_id: "dataset_2025Q1"
target_rule: "uplift >= 0.5 and X_rfm_monetary >= 1000 and churn_risk >= 0.3"

offer:
  type: "coupon"
  template_id: "20pct_off"
  discount_percentage: 20

channels:
  - "email"
  - "push"

frequency_cap: 2  # Max 2 treatments per user
budget_limit: 1000000  # Total budget limit

objectives:
  - name: "incremental_profit"
    weight: 1.0
  - name: "churn_rate"
    weight: -0.3  # Negative weight = minimize

risk_constraints:
  min_overlap: 0.6
  min_gamma: 1.3
  max_negative_cate_share: 0.05
```

### Offline Evaluation

```python
from cqox.causal.policy import OfflinePolicyEvaluator

evaluator = OfflinePolicyEvaluator()

# Estimate propensity scores
ps = evaluator.estimate_propensity_scores(X, treatment)

# Evaluate policy using DR estimator
result = evaluator.evaluate_policy(
    X, treatment, y, policy_treatment,
    method='dr'
)

print(f"Policy value: {result['value']:.2f} ± {result['std_error']:.2f}")
```

### Export Targets

```python
from cqox.export.targets import export_policy_targets

result = export_policy_targets(
    policy_id="my_policy_v1",
    dataset_id="dataset_2025Q1",
    output_format="csv"
)

print(f"Exported to: {result['output_path']}")
```

## Multi-Objective Optimization

```python
from cqox.causal.policy import MultiObjectiveOptimizer

optimizer = MultiObjectiveOptimizer(
    objectives=["incremental_profit", "risk_metric", "churn_rate"]
)

# Evaluate all policies
evaluations = optimizer.evaluate_policies(policies, objective_functions)

# Find Pareto frontier
pareto = optimizer.find_pareto_frontier(evaluations)

print(f"Found {len(pareto)} Pareto-optimal policies")

# Get 2D frontier for plotting
frontier_data = optimizer.get_frontier_2d(
    evaluations, "incremental_profit", "risk_metric"
)
```

## API Reference

### Upload Endpoints

- `POST /api/upload` - Upload file, get column mapping suggestions
- `POST /api/upload/apply-mapping` - Apply mapping and normalize
- `GET /api/upload/profiles` - List saved mapping profiles
- `GET /api/upload/profiles/{name}` - Get specific profile

### Dataset Endpoints

- `GET /api/datasets` - List datasets
- `GET /api/datasets/{id}` - Get dataset details
- `POST /api/datasets` - Register new dataset

### Policy Endpoints

- `GET /api/policies` - List policies
- `GET /api/policies/{id}` - Get policy details
- `POST /api/policies` - Create new policy
- `POST /api/policies/{id}/evaluate` - Run offline evaluation
- `POST /api/policies/{id}/export` - Export target list

### Causal Endpoints

- `POST /api/causal/train` - Train causal models
- `GET /api/causal/runs/{id}` - Get training run results

### Portfolio Endpoints

- `GET /api/portfolio/summary` - Portfolio summary
- `GET /api/portfolio/frontier` - Pareto frontier data

### Diagnostics Endpoints

- `GET /api/diagnostics/{run_id}` - Get diagnostics for model run

### Console Endpoints

- `GET /api/console/summary` - Decision Console summary

## Deployment

### Production Setup

1. **Database**
   ```bash
   # PostgreSQL for metadata
   createdb cqox
   ```

2. **Redis**
   ```bash
   # For Celery task queue
   redis-server
   ```

3. **Backend**
   ```bash
   cd backend
   gunicorn cqox.api.main:app \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8000
   ```

4. **Frontend**
   ```bash
   cd frontend
   npm run build
   # Serve with Nginx
   ```

5. **Celery Workers**
   ```bash
   celery -A cqox.tasks worker --loglevel=info
   ```

### CI/CD for Policy-as-Code

`.github/workflows/policy-gate.yml`:

```yaml
name: Policy Gate

on:
  pull_request:
    paths:
      - 'policies/**'

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Offline Policy Evaluation
        run: python scripts/evaluate_policies.py
      - name: Check Risk Constraints
        run: python scripts/check_constraints.py
```

### Environment Variables

```env
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/cqox
REDIS_URL=redis://localhost:6379/0
WOLFRAM_SCRIPT_PATH=wolframscript
DEBUG=false
```

## Best Practices

1. **Always use mapping profiles** for repeated uploads
2. **Version your policies** in Git
3. **Run diagnostics** before deploying policies
4. **Monitor CAS scores** - aim for >0.8
5. **Use multi-objective** to balance profit and risk
6. **Test with small budgets** before scaling

## Troubleshooting

### Column Mapping Fails

- Check `config/data_contract.yaml` for required columns
- Review type conversion errors in validation report
- Use mapping profiles for consistency

### Causal Estimates Seem Off

- Check diagnostics (balance, overlap)
- Review CAS score
- Try multiple estimators and compare
- Check for spillover effects

### Policy Export Empty

- Verify target_rule syntax
- Check if any users meet criteria
- Review budget/frequency caps

## Support

For issues or questions, contact the CQOx team.
