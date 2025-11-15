# CQOx: Causal Query Optimizer for Marketing Policy

CQOx is a comprehensive platform for optimizing marketing policies using causal inference, offline policy learning, and multi-objective optimization.

## Features

### Core Capabilities

- **Semantic Schema & Column Mapping**: Automatic mapping of uploaded data to canonical schema with fail-fast validation
- **7 Causal Estimators**: S-Learner, T-Learner, X-Learner, DR-Learner, Causal Forest, and more
- **14 Diagnostics**: Comprehensive causal quality checks including balance, overlap, sensitivity analysis
- **Offline Policy Evaluation**: IPS and Doubly Robust estimators for pre-deployment policy assessment
- **Multi-Objective Optimization**: Pareto frontier analysis for profit vs risk tradeoffs
- **Counterfactual Recourse**: Recommendations for improving policy outcomes
- **Digital Twin**: Customer behavior simulation under policy sequences (v2)
- **Policy-as-Code**: Git-versioned YAML policies with CI/CD integration

### UI Components

- **Decision Console**: Executive dashboard with recommended policies and KPIs
- **Policy Lab**: Policy creation, editing, and evaluation interface
- **Causal Design & Evaluation**: Model training and causal inference workflows
- **Portfolio & ROI**: Multi-channel portfolio view with Pareto frontier
- **Diagnostics & Audit**: Complete diagnostic suite with CAS (Causal Assurance Score)

## Quick Start

### Backend Setup

```bash
cd /home/hirokionodeara/CQOx_gen/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m cqox.api.main
```

### Frontend Setup

```bash
cd /home/hirokionodeara/CQOx_gen/frontend
npm install
npm run dev
```

## Documentation

See full documentation in the README file for:
- Architecture details
- Column mapping workflow
- Policy creation guide
- API reference
- Deployment instructions