"""
Demo mode API endpoints

Generate synthetic datasets and run quick analyses
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from pathlib import Path
from datetime import datetime
import uuid
from loguru import logger

from cqox.demo.data_generator import DemoDataGenerator
from cqox.data.loader import DatasetRegistry, DataLoader
from cqox.config import settings

router = APIRouter()


class DatasetGenerateRequest(BaseModel):
    """Request to generate a demo dataset"""
    type: Literal['rct', 'observational', 'panel'] = Field(
        ...,
        description="Type of dataset to generate"
    )
    name: Optional[str] = Field(
        None,
        description="Custom name for the dataset (auto-generated if not provided)"
    )
    description: Optional[str] = Field(
        None,
        description="Description of the dataset"
    )

    # Common parameters
    seed: Optional[int] = Field(
        None,
        description="Random seed for reproducibility"
    )

    # RCT parameters
    n_samples: Optional[int] = Field(
        10000,
        description="Number of samples (for RCT and observational)"
    )
    treatment_effect: Optional[float] = Field(
        50.0,
        description="True treatment effect"
    )
    noise_std: Optional[float] = Field(
        None,
        description="Standard deviation of outcome noise"
    )

    # Observational parameters
    selection_strength: Optional[float] = Field(
        2.0,
        description="Strength of selection bias (observational only)"
    )

    # Panel parameters
    n_units: Optional[int] = Field(
        1000,
        description="Number of units (panel data only)"
    )
    n_periods: Optional[int] = Field(
        12,
        description="Number of time periods (panel data only)"
    )
    treatment_start: Optional[int] = Field(
        6,
        description="Period when treatment starts (panel data only)"
    )


class QuickAnalysisRequest(BaseModel):
    """Request to run quick analysis on a dataset"""
    dataset_id: str = Field(
        ...,
        description="ID of the dataset to analyze"
    )
    estimator: Literal['s_learner', 't_learner', 'x_learner', 'dr_learner'] = Field(
        't_learner',
        description="Causal estimator to use"
    )


@router.post("/generate")
async def generate_demo_dataset(request: DatasetGenerateRequest):
    """
    Generate a synthetic dataset for demo purposes

    Supports three types:
    - **RCT**: Randomized controlled trial with perfect randomization
    - **Observational**: Observational study with selection bias and confounding
    - **Panel**: Panel data for difference-in-differences analysis

    The generated dataset is automatically saved and registered in the dataset registry.

    Returns:
        - dataset_id: Unique identifier for the generated dataset
        - file_path: Path where the dataset is saved
        - info: Summary statistics about the dataset
    """
    try:
        # Generate dataset ID
        dataset_id = f"demo_{request.type}_{uuid.uuid4().hex[:8]}"

        # Create name if not provided
        if request.name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            request.name = f"Demo {request.type.upper()} Dataset ({timestamp})"

        # Initialize generator
        generator = DemoDataGenerator(seed=request.seed)

        # Prepare parameters based on dataset type
        params = {}
        if request.type == 'rct':
            params = {
                'n_samples': request.n_samples,
                'treatment_effect': request.treatment_effect,
            }
            if request.noise_std is not None:
                params['noise_std'] = request.noise_std

        elif request.type == 'observational':
            params = {
                'n_samples': request.n_samples,
                'true_treatment_effect': request.treatment_effect,
                'selection_strength': request.selection_strength,
            }
            if request.noise_std is not None:
                params['noise_std'] = request.noise_std

        elif request.type == 'panel':
            params = {
                'n_units': request.n_units,
                'n_periods': request.n_periods,
                'treatment_start': request.treatment_start,
                'treatment_effect': request.treatment_effect,
            }
            if request.noise_std is not None:
                params['noise_std'] = request.noise_std

        # Generate dataset
        logger.info(f"Generating {request.type} dataset with params: {params}")
        df = generator.generate_dataset(request.type, **params)

        # Save dataset
        demo_dir = settings.data_dir / "demo"
        demo_dir.mkdir(parents=True, exist_ok=True)

        file_path = demo_dir / f"{dataset_id}.csv"
        generator.save_dataset(df, file_path, format='csv')

        # Register dataset
        registry = DatasetRegistry()
        metadata = {
            "name": request.name,
            "description": request.description or f"Demo {request.type} dataset",
            "file_path": str(file_path),
            "dataset_type": request.type,
            "generated_at": datetime.now().isoformat(),
            "params": params,
            "is_demo": True
        }
        registry.register_dataset(dataset_id, metadata)

        # Get dataset info
        info = generator.get_dataset_info(df)

        logger.info(f"Successfully generated dataset: {dataset_id}")

        return {
            "success": True,
            "dataset_id": dataset_id,
            "name": request.name,
            "file_path": str(file_path),
            "type": request.type,
            "info": info,
            "metadata": metadata
        }

    except Exception as e:
        logger.error(f"Failed to generate dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Dataset generation failed: {str(e)}")


@router.get("/datasets")
async def list_demo_datasets():
    """
    List all demo datasets

    Returns all datasets that were generated in demo mode.
    """
    try:
        registry = DatasetRegistry()
        all_datasets = registry.list_datasets()

        # Filter for demo datasets only
        demo_datasets = {
            dataset_id: metadata
            for dataset_id, metadata in all_datasets.items()
            if metadata.get('is_demo', False)
        }

        return {
            "success": True,
            "count": len(demo_datasets),
            "datasets": demo_datasets
        }

    except Exception as e:
        logger.error(f"Failed to list demo datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}")
async def get_demo_dataset(dataset_id: str):
    """
    Get details about a specific demo dataset

    Returns metadata and summary statistics for the dataset.
    """
    try:
        registry = DatasetRegistry()
        metadata = registry.get_dataset(dataset_id)

        # Verify it's a demo dataset
        if not metadata.get('is_demo', False):
            raise HTTPException(
                status_code=400,
                detail="This is not a demo dataset"
            )

        # Load dataset to get current info
        file_path = metadata.get('file_path')
        if file_path and Path(file_path).exists():
            df = DataLoader.load_csv(file_path)
            info = DemoDataGenerator.get_dataset_info(df)
            metadata['current_info'] = info

        return {
            "success": True,
            "dataset_id": dataset_id,
            "metadata": metadata
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get demo dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/datasets/{dataset_id}")
async def delete_demo_dataset(dataset_id: str):
    """
    Delete a demo dataset

    Removes the dataset file and its registry entry.
    """
    try:
        registry = DatasetRegistry()
        metadata = registry.get_dataset(dataset_id)

        # Verify it's a demo dataset
        if not metadata.get('is_demo', False):
            raise HTTPException(
                status_code=400,
                detail="Can only delete demo datasets through this endpoint"
            )

        # Delete file if exists
        file_path = metadata.get('file_path')
        if file_path:
            file_path = Path(file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")

        # Remove from registry
        import yaml
        registry_file = registry.registry_file
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                datasets = yaml.safe_load(f) or {}

            if dataset_id in datasets:
                del datasets[dataset_id]

                with open(registry_file, 'w') as f:
                    yaml.dump(datasets, f, default_flow_style=False)

                logger.info(f"Removed from registry: {dataset_id}")

        return {
            "success": True,
            "message": f"Dataset {dataset_id} deleted successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete demo dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-analysis")
async def quick_analysis(request: QuickAnalysisRequest):
    """
    Run a quick causal analysis on a demo dataset

    Performs a basic causal inference analysis using the specified estimator.
    This is a simplified analysis for demonstration purposes.

    Returns:
        - estimated_ate: Estimated average treatment effect
        - true_ate: True treatment effect (if known from demo data)
        - bias: Difference between estimated and true effect
        - ci_lower, ci_upper: 95% confidence interval
    """
    try:
        # Load dataset
        registry = DatasetRegistry()
        metadata = registry.get_dataset(request.dataset_id)

        file_path = metadata.get('file_path')
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Dataset file not found")

        df = DataLoader.load_csv(file_path)

        # Verify required columns
        if 'treatment' not in df.columns or 'outcome' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Dataset must have 'treatment' and 'outcome' columns"
            )

        # Simple analysis based on estimator type
        from sklearn.linear_model import LinearRegression
        from sklearn.ensemble import RandomForestRegressor
        import numpy as np

        # Prepare data
        X_cols = [col for col in df.columns if col not in ['treatment', 'outcome', 'true_ate', 'true_cate', 'propensity_score', 'baseline_outcome', 'unit_id', 'period', 'treated_unit', 'post_period']]

        # Handle categorical variables
        df_encoded = df.copy()
        for col in X_cols:
            if df_encoded[col].dtype == 'object':
                df_encoded = pd.get_dummies(df_encoded, columns=[col], drop_first=True)

        # Update X_cols after encoding
        X_cols_encoded = [col for col in df_encoded.columns if col not in ['treatment', 'outcome', 'true_ate', 'true_cate', 'propensity_score', 'baseline_outcome', 'unit_id', 'period', 'treated_unit', 'post_period']]

        X = df_encoded[X_cols_encoded].values
        T = df['treatment'].values
        Y = df['outcome'].values

        # Run estimator
        if request.estimator == 's_learner':
            # S-learner: Single model with treatment as feature
            X_with_t = np.column_stack([X, T])
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_with_t, Y)

            # Predict counterfactuals
            X_t1 = np.column_stack([X, np.ones(len(X))])
            X_t0 = np.column_stack([X, np.zeros(len(X))])

            Y1_pred = model.predict(X_t1)
            Y0_pred = model.predict(X_t0)
            cate = Y1_pred - Y0_pred
            ate = cate.mean()

        elif request.estimator == 't_learner':
            # T-learner: Separate models for treatment and control
            model_t1 = RandomForestRegressor(n_estimators=100, random_state=42)
            model_t0 = RandomForestRegressor(n_estimators=100, random_state=42)

            model_t1.fit(X[T == 1], Y[T == 1])
            model_t0.fit(X[T == 0], Y[T == 0])

            Y1_pred = model_t1.predict(X)
            Y0_pred = model_t0.predict(X)
            cate = Y1_pred - Y0_pred
            ate = cate.mean()

        elif request.estimator == 'x_learner':
            # Simplified X-learner
            model_t1 = RandomForestRegressor(n_estimators=100, random_state=42)
            model_t0 = RandomForestRegressor(n_estimators=100, random_state=42)

            model_t1.fit(X[T == 1], Y[T == 1])
            model_t0.fit(X[T == 0], Y[T == 0])

            # Impute counterfactuals
            D1 = Y[T == 1] - model_t0.predict(X[T == 1])
            D0 = model_t1.predict(X[T == 0]) - Y[T == 0]

            # Train on imputed effects
            model_tau1 = RandomForestRegressor(n_estimators=100, random_state=42)
            model_tau0 = RandomForestRegressor(n_estimators=100, random_state=42)

            model_tau1.fit(X[T == 1], D1)
            model_tau0.fit(X[T == 0], D0)

            # Combine predictions
            tau1 = model_tau1.predict(X)
            tau0 = model_tau0.predict(X)
            cate = 0.5 * (tau1 + tau0)
            ate = cate.mean()

        elif request.estimator == 'dr_learner':
            # Simplified doubly robust learner
            # Estimate propensity score
            from sklearn.linear_model import LogisticRegression
            ps_model = LogisticRegression(max_iter=1000)
            ps_model.fit(X, T)
            ps = ps_model.predict_proba(X)[:, 1]

            # Outcome models
            model_t1 = RandomForestRegressor(n_estimators=100, random_state=42)
            model_t0 = RandomForestRegressor(n_estimators=100, random_state=42)

            model_t1.fit(X[T == 1], Y[T == 1])
            model_t0.fit(X[T == 0], Y[T == 0])

            Y1_pred = model_t1.predict(X)
            Y0_pred = model_t0.predict(X)

            # Doubly robust estimation
            dr_t1 = Y1_pred + (T / ps) * (Y - Y1_pred)
            dr_t0 = Y0_pred + ((1 - T) / (1 - ps)) * (Y - Y0_pred)
            cate = dr_t1 - dr_t0
            ate = cate.mean()

        else:
            raise HTTPException(status_code=400, detail=f"Unknown estimator: {request.estimator}")

        # Bootstrap confidence intervals
        n_bootstrap = 100
        bootstrap_ates = []
        for _ in range(n_bootstrap):
            idx = np.random.choice(len(df), size=len(df), replace=True)
            df_boot = df.iloc[idx]
            T_boot = df_boot['treatment'].values
            Y_boot = df_boot['outcome'].values
            ate_boot = Y_boot[T_boot == 1].mean() - Y_boot[T_boot == 0].mean()
            bootstrap_ates.append(ate_boot)

        ci_lower = np.percentile(bootstrap_ates, 2.5)
        ci_upper = np.percentile(bootstrap_ates, 97.5)

        # Get true ATE if available
        true_ate = None
        bias = None
        if 'true_ate' in df.columns:
            true_ate = float(df['true_ate'].iloc[0])
            bias = ate - true_ate

        # Naive estimate (for comparison)
        naive_ate = Y[T == 1].mean() - Y[T == 0].mean()

        result = {
            "success": True,
            "dataset_id": request.dataset_id,
            "estimator": request.estimator,
            "results": {
                "estimated_ate": float(ate),
                "ci_lower": float(ci_lower),
                "ci_upper": float(ci_upper),
                "naive_ate": float(naive_ate),
                "true_ate": true_ate,
                "bias": bias,
                "cate_stats": {
                    "mean": float(cate.mean()),
                    "std": float(cate.std()),
                    "min": float(cate.min()),
                    "max": float(cate.max())
                }
            },
            "sample_info": {
                "n_samples": len(df),
                "n_treated": int(T.sum()),
                "n_control": int((1 - T).sum())
            }
        }

        logger.info(f"Quick analysis completed: {request.estimator} on {request.dataset_id}")

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Quick analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/")
async def demo_info():
    """
    Get information about demo mode capabilities

    Returns available dataset types, estimators, and example configurations.
    """
    return {
        "success": True,
        "demo_mode": "active",
        "dataset_types": {
            "rct": {
                "name": "Randomized Controlled Trial",
                "description": "Perfect randomization with known treatment effect",
                "parameters": ["n_samples", "treatment_effect", "noise_std"],
                "default_params": {
                    "n_samples": 10000,
                    "treatment_effect": 50.0,
                    "noise_std": 100.0
                }
            },
            "observational": {
                "name": "Observational Study",
                "description": "Selection bias and confounding requiring adjustment",
                "parameters": ["n_samples", "treatment_effect", "selection_strength", "noise_std"],
                "default_params": {
                    "n_samples": 50000,
                    "treatment_effect": 40.0,
                    "selection_strength": 2.0,
                    "noise_std": 120.0
                }
            },
            "panel": {
                "name": "Panel Data (DiD)",
                "description": "Time-series cross-section for difference-in-differences",
                "parameters": ["n_units", "n_periods", "treatment_start", "treatment_effect", "noise_std"],
                "default_params": {
                    "n_units": 1000,
                    "n_periods": 12,
                    "treatment_start": 6,
                    "treatment_effect": 30.0,
                    "noise_std": 50.0
                }
            }
        },
        "estimators": ["s_learner", "t_learner", "x_learner", "dr_learner"],
        "endpoints": {
            "generate": "POST /api/demo/generate - Generate a new dataset",
            "list": "GET /api/demo/datasets - List all demo datasets",
            "get": "GET /api/demo/datasets/{dataset_id} - Get dataset details",
            "delete": "DELETE /api/demo/datasets/{dataset_id} - Delete a dataset",
            "analyze": "POST /api/demo/quick-analysis - Run quick analysis"
        }
    }
