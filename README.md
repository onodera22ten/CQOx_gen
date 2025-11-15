# CQOx - Causal Query Optimizer for Marketing Policy

Enterprise-grade causal inference platform for marketing policy optimization with Wolfram ONE visualization.

## 🎯 Features

### Causal Inference
- **7 Causal Estimators**: S-Learner, T-Learner, X-Learner, DR-Learner, Causal Forest, Uplift Forest, Doubly Robust Forest
- **14 Diagnostic Checks**: Balance, Overlap, Sensitivity, E-value, Qini curves, Calibration, Heterogeneity, Network/Temporal interference
- **CAS Score**: Integrated Causal Assurance Score (0-1) with quality levels

### Policy Optimization
- **Offline Policy Evaluation**: IPS and Doubly Robust methods
- **Multi-Objective Optimization**: Pareto frontier analysis
- **Experiment Design Recommender**: Sample size, stratification, duration recommendations
- **Risk-Sensitive RL**: CVaR-based reinforcement learning for risk-aware policies
- **Counterfactual Recourse**: Actionable recommendations

### Data Management
- **Semantic Schema Mapping**: Fail-fast column normalization with alias detection
- **Feature Store**: RFM, behavioral, and treatment history features
- **Multiple Format Support**: CSV, Parquet with auto-detection

### Visualization (Wolfram ONE)
- Pareto Frontier plots
- Love plots (covariate balance)
- Propensity score density
- CATE distribution histograms
- Qini curves
- Calibration plots
- Sensitivity analysis (Rosenbaum Gamma)

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Wolfram ONE (Engine無)

## 🚀 Quick Start

### 1. Database Setup

```bash
# Start PostgreSQL
sudo service postgresql start

# Initialize database
cd backend
chmod +x scripts/init_db.sh
./scripts/init_db.sh
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env.example .env
# Edit .env with your configuration

# Start API server
chmod +x scripts/start_api.sh
./scripts/start_api.sh
```

API will be available at http://localhost:8000

### 3. Celery Worker Setup

```bash
# In a new terminal
cd backend
source venv/bin/activate

# Start Redis
redis-server &

# Start Celery worker
chmod +x scripts/start_celery.sh
./scripts/start_celery.sh
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at http://localhost:3000

## 📚 API Documentation

Once the API server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Architecture

```
CQOx/
├── backend/
│   ├── cqox/
│   │   ├── api/              # FastAPI routes
│   │   ├── causal/           # Causal inference engine
│   │   │   ├── estimators/   # 7 causal estimators
│   │   │   ├── diagnostics/  # 14 diagnostic checks
│   │   │   └── policy/       # Policy optimization
│   │   ├── data/             # Data layer
│   │   ├── database/         # SQLAlchemy models
│   │   ├── export/           # Target export
│   │   └── tasks/            # Celery tasks
│   ├── alembic/              # Database migrations
│   └── scripts/              # Utility scripts
├── frontend/
│   └── src/
│       ├── pages/            # React pages
│       └── components/       # React components
├── wolfram/
│   └── visualizations/       # 7 Wolfram scripts
├── config/                   # Configuration files
├── policies/                 # Policy YAML definitions
└── tests/                    # Test suite
```

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=cqox --cov-report=html

# Run specific test file
pytest tests/unit/test_estimators.py
```

## 📊 Usage Example

### 1. Upload and Map Dataset

```python
import requests

# Upload CSV
files = {'file': open('marketing_data.csv', 'rb')}
response = requests.post('http://localhost:8000/api/upload', files=files)
dataset_id = response.json()['dataset_id']

# Suggest column mapping
response = requests.post('http://localhost:8000/api/upload/suggest-mapping', json={
    'upload_columns': ['customer_id', 'treatment_flag', 'revenue', 'age', 'gender']
})
mapping = response.json()['suggested_mapping']
```

### 2. Train Causal Models

```python
# Train multiple estimators
response = requests.post('http://localhost:8000/api/causal/train', json={
    'dataset_path': 'data/marketing_data.csv',
    'outcome': 'revenue',
    'treatment': 'treatment_flag',
    'features': ['age', 'gender', 'previous_purchases'],
    'estimators': ['s_learner', 't_learner', 'dr_learner', 'doubly_robust_forest'],
    'async_mode': True
})
task_id = response.json()['task_id']

# Check task status
response = requests.get(f'http://localhost:8000/api/causal/tasks/{task_id}')
print(response.json())
```

### 3. Run Diagnostics

```python
# Run all 14 diagnostic checks
response = requests.post('http://localhost:8000/api/diagnostics/run', json={
    'dataset_path': 'data/marketing_data.csv',
    'treatment_col': 'treatment_flag',
    'outcome_col': 'revenue',
    'feature_prefix': 'X_'
})

diagnostics = response.json()
print(f"CAS Score: {diagnostics['cas_score']}")
print(f"Quality: {diagnostics['quality_level']}")
```

### 4. Evaluate Policy

```python
# Offline policy evaluation
response = requests.post('http://localhost:8000/api/policies/evaluate', json={
    'policy_id': 'push_high_uplift_v1',
    'dataset_path': 'data/marketing_data.csv',
    'method': 'doubly_robust'
})

print(f"Policy Value: {response.json()['policy_value']}")
print(f"ROI: {response.json()['roi']}")
```

## 🔧 Configuration

### Database Migration

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Celery Tasks

View Celery tasks in `backend/cqox/tasks/`:
- `causal_tasks.py`: Model training, diagnostics
- `policy_tasks.py`: Policy evaluation, target export

## 🎨 Wolfram Visualizations

All 7 Wolfram scripts are available via API:

```python
# Generate Pareto frontier
response = requests.post('http://localhost:8000/api/visualizations/pareto-frontier', json={
    'policies': [
        {'name': 'Policy A', 'profit': 100000, 'risk': 0.2},
        {'name': 'Policy B', 'profit': 120000, 'risk': 0.35}
    ]
})
```

## 📦 Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Configure specific CORS origins
- [ ] Use production PostgreSQL instance
- [ ] Use production Redis instance
- [ ] Set `LOG_LEVEL=WARNING`
- [ ] Configure SSL/TLS
- [ ] Set up monitoring (Sentry, DataDog, etc.)
- [ ] Configure backup strategy

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

Proprietary - All rights reserved

## 🆘 Support

For issues and questions:
- GitHub Issues: https://github.com/onodera22ten/CQOx_gen/issues
- Documentation: http://localhost:8000/docs

## 🔄 Version History

### v1.0.0 (2025-11-15)
- Initial release
- 7 causal estimators
- 14 diagnostic checks
- Wolfram ONE visualization integration
- Full API and frontend implementation
