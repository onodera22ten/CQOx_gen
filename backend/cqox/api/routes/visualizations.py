"""
Wolfram visualization endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from loguru import logger
import subprocess
import json
import tempfile
from pathlib import Path

router = APIRouter()

WOLFRAM_SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent.parent / "wolfram" / "visualizations"


class ParetoFrontierRequest(BaseModel):
    """Request for Pareto frontier visualization"""
    policies: List[Dict[str, Any]]  # List of {name, profit, risk}


class BalancePlotRequest(BaseModel):
    """Request for balance plot (Love plot)"""
    variables: List[str]
    smd_values: List[float]
    threshold: float = 0.1


class OverlapDensityRequest(BaseModel):
    """Request for overlap density plot"""
    propensity_scores_treatment: List[float]
    propensity_scores_control: List[float]


class CATEDistributionRequest(BaseModel):
    """Request for CATE distribution"""
    cate_values: List[float]


class QiniCurveRequest(BaseModel):
    """Request for Qini curve"""
    uplift_scores: List[float]
    treatment: List[int]
    outcomes: List[float]


class CalibrationPlotRequest(BaseModel):
    """Request for calibration plot"""
    predicted_cate: List[float]
    observed_cate: List[float]


class SensitivityGammaRequest(BaseModel):
    """Request for sensitivity analysis plot"""
    gamma_values: List[float]
    p_values: List[float]


def run_wolfram_script(script_name: str, input_data: dict) -> dict:
    """
    Run a Wolfram script with input data

    Args:
        script_name: Name of .wl script (without path)
        input_data: Dictionary of input data

    Returns:
        Result from Wolfram script
    """
    script_path = WOLFRAM_SCRIPTS_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"Wolfram script not found: {script_path}")

    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        input_file = f.name

    try:
        # Run WolframScript
        cmd = [
            'wolframscript',
            '-file', str(script_path),
            '-args', input_file
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            logger.error(f"Wolfram script error: {result.stderr}")
            raise RuntimeError(f"Wolfram script failed: {result.stderr}")

        # Parse output
        output = json.loads(result.stdout)
        return output

    finally:
        # Clean up temp file
        Path(input_file).unlink(missing_ok=True)


@router.post("/pareto-frontier")
async def generate_pareto_frontier(request: ParetoFrontierRequest):
    """Generate Pareto frontier visualization"""
    try:
        logger.info("Generating Pareto frontier visualization")

        input_data = {
            "policies": request.policies
        }

        result = run_wolfram_script("pareto_frontier.wl", input_data)

        return {
            "status": "success",
            "visualization": result
        }

    except Exception as e:
        logger.error(f"Pareto frontier generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/balance-plot")
async def generate_balance_plot(request: BalancePlotRequest):
    """Generate Love plot (covariate balance)"""
    try:
        logger.info("Generating balance plot")

        input_data = {
            "variables": request.variables,
            "smd_values": request.smd_values,
            "threshold": request.threshold
        }

        result = run_wolfram_script("balance_plot.wl", input_data)

        return {
            "status": "success",
            "visualization": result
        }

    except Exception as e:
        logger.error(f"Balance plot generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/overlap-density")
async def generate_overlap_density(request: OverlapDensityRequest):
    """Generate propensity score density plot"""
    try:
        logger.info("Generating overlap density plot")

        input_data = {
            "propensity_scores_treatment": request.propensity_scores_treatment,
            "propensity_scores_control": request.propensity_scores_control
        }

        result = run_wolfram_script("overlap_density.wl", input_data)

        return {
            "status": "success",
            "visualization": result
        }

    except Exception as e:
        logger.error(f"Overlap density generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cate-distribution")
async def generate_cate_distribution(request: CATEDistributionRequest):
    """Generate CATE distribution histogram"""
    try:
        logger.info("Generating CATE distribution")

        input_data = {
            "cate_values": request.cate_values
        }

        result = run_wolfram_script("cate_distribution.wl", input_data)

        return {
            "status": "success",
            "visualization": result
        }

    except Exception as e:
        logger.error(f"CATE distribution generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qini-curve")
async def generate_qini_curve(request: QiniCurveRequest):
    """Generate Qini curve"""
    try:
        logger.info("Generating Qini curve")

        input_data = {
            "uplift_scores": request.uplift_scores,
            "treatment": request.treatment,
            "outcomes": request.outcomes
        }

        result = run_wolfram_script("qini_curve.wl", input_data)

        return {
            "status": "success",
            "visualization": result
        }

    except Exception as e:
        logger.error(f"Qini curve generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calibration-plot")
async def generate_calibration_plot(request: CalibrationPlotRequest):
    """Generate calibration plot"""
    try:
        logger.info("Generating calibration plot")

        input_data = {
            "predicted_cate": request.predicted_cate,
            "observed_cate": request.observed_cate
        }

        result = run_wolfram_script("calibration_plot.wl", input_data)

        return {
            "status": "success",
            "visualization": result
        }

    except Exception as e:
        logger.error(f"Calibration plot generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sensitivity-gamma")
async def generate_sensitivity_gamma(request: SensitivityGammaRequest):
    """Generate Rosenbaum sensitivity plot"""
    try:
        logger.info("Generating sensitivity gamma plot")

        input_data = {
            "gamma_values": request.gamma_values,
            "p_values": request.p_values
        }

        result = run_wolfram_script("sensitivity_gamma.wl", input_data)

        return {
            "status": "success",
            "visualization": result
        }

    except Exception as e:
        logger.error(f"Sensitivity gamma plot generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available")
async def list_available_visualizations():
    """List all available Wolfram visualizations"""
    try:
        scripts = list(WOLFRAM_SCRIPTS_DIR.glob("*.wl"))

        return {
            "visualizations": [s.stem for s in scripts],
            "total": len(scripts)
        }

    except Exception as e:
        logger.error(f"List visualizations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
