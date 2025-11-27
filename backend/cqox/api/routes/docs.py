"""
【日本語サマリ】このモジュールは twin.pdf などの設計資料を配信する API を提供する。
- なぜ必要か: Digital Twin 画面から PDF の最新版を直接参照できるようにし、ドキュメントの単一ソース化を保つため
- 何をするか: twin.pdf を FileResponse で返却し、存在しない場合は 404 を返す
- どう検証するか: /docs/twin を curl し、HTTP 200 で PDF がダウンロードできることを確認
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse

router = APIRouter(prefix="/docs", tags=["docs"])

REPO_ROOT = Path(__file__).resolve().parents[3]
TWIN_PDF_PATH = REPO_ROOT / "twin.pdf"


@router.get("/twin", response_class=FileResponse, summary="Digital Twin Spec PDF")
async def get_twin_pdf():
    """
    twin.pdf を返却する。存在しない場合は 404。
    """
    if not TWIN_PDF_PATH.exists():
        raise HTTPException(status_code=404, detail="twin.pdf not found at repository root")

    return FileResponse(
        TWIN_PDF_PATH,
        media_type="application/pdf",
        filename="twin.pdf",
    )


@router.head("/twin", summary="Digital Twin Spec PDF (HEAD)")
async def head_twin_pdf() -> Response:
    """
    HEAD endpoint so frontend can verify availability without downloading the entire file.
    """
    if not TWIN_PDF_PATH.exists():
        raise HTTPException(status_code=404, detail="twin.pdf not found at repository root")
    return Response(status_code=200)

