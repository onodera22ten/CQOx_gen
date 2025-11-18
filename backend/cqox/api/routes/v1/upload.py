"""
【日本語サマリ】データセットアップロードAPI
- なぜ必要か: ユーザーがCSVファイルをアップロードしてデータセットを作成する
- 何をするか: ファイルアップロード、検証、S3/ローカルストレージへの保存、メタデータの記録
- どう検証するか: ファイル形式チェック、サイズ制限、エラーハンドリング

【Inputs】
- CSV file via multipart/form-data
- name: データセット名
- description: 説明

【Outputs】
- dataset_id: 作成されたデータセットID
- message: 成功メッセージ
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import uuid
import pandas as pd
import io
import json
from pathlib import Path

from cqox.database.connection import get_db
from cqox.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/upload", tags=["upload"])

# アップロード用ディレクトリ
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/dataset")
async def upload_dataset(
    file: UploadFile = File(..., description="CSV file to upload"),
    name: str = Form(..., description="Dataset name"),
    description: str = Form("", description="Dataset description"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    CSVファイルをアップロードしてデータセットを作成
    
    - ファイル形式: CSV (カンマ区切り)
    - 最大サイズ: 100MB
    - エンコーディング: UTF-8推奨
    """
    
    # ファイル形式チェック
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="CSVファイルのみアップロード可能です"
        )
    
    try:
        # ファイル内容を読み込み
        contents = await file.read()
        
        # サイズチェック (100MB制限)
        if len(contents) > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="ファイルサイズが100MBを超えています"
            )
        
        # pandasで読み込んで検証
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"CSVファイルの読み込みに失敗しました: {str(e)}"
            )

        # スキーマ情報を生成（データ型を文字列に変換）
        schema_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}

        # データセットIDを生成（UUIDオブジェクトとして）
        dataset_id_uuid = uuid.uuid4()
        dataset_id_str = str(dataset_id_uuid)
        
        # ファイル保存
        file_path = UPLOAD_DIR / f"{dataset_id_str}.csv"
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # データベースに登録
        tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        now = datetime.utcnow()
        
        # datasetsテーブルがない場合は作成
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS datasets (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                file_path VARCHAR(500),
                row_count INTEGER,
                column_count INTEGER,
                columns JSONB,
                tenant_id UUID,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        
        # メタデータを保存（同じUUIDを使用）
        await db.execute(
            text("""
                INSERT INTO datasets (id, name, description, file_path, row_count, column_count, columns, schema, tenant_id, created_at, updated_at)
                VALUES (:id, :name, :description, :file_path, :row_count, :column_count, :columns, :schema, :tenant_id, :created_at, :updated_at)
            """),
            {
                "id": dataset_id_uuid,  # UUIDオブジェクトをそのまま使用
                "name": name,
                "description": description,
                "file_path": str(file_path),
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": json.dumps(df.columns.tolist()),
                "schema": json.dumps(schema_dict),
                "tenant_id": tenant_id,
                "created_at": now,
                "updated_at": now
            }
        )
        
        await db.commit()
        
        return {
            "dataset_id": dataset_id_str,  # 文字列として返す
            "name": name,
            "message": "データセットを正常にアップロードしました",
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "file_size_mb": len(contents) / (1024 * 1024)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"アップロード処理中にエラーが発生しました: {str(e)}"
        )


@router.get("/datasets")
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    アップロード済みデータセット一覧を取得
    """
    try:
        result = await db.execute(
            text("""
                SELECT id, name, description, row_count, column_count, created_at
                FROM datasets
                ORDER BY created_at DESC
            """)
        )
        
        datasets = []
        for row in result:
            datasets.append({
                "id": str(row[0]),
                "name": row[1],
                "description": row[2],
                "row_count": row[3],
                "column_count": row[4],
                "created_at": row[5].isoformat() if row[5] else None
            })
        
        return datasets
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"データセット一覧の取得に失敗しました: {str(e)}"
        )


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    データセットを削除
    """
    try:
        # ファイルパスを取得
        result = await db.execute(
            text("SELECT file_path FROM datasets WHERE id = :dataset_id"),
            {"dataset_id": uuid.UUID(dataset_id)}
        )
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="データセットが見つかりません")
        
        file_path = Path(row[0])
        
        # データベースから削除
        await db.execute(
            text("DELETE FROM datasets WHERE id = :dataset_id"),
            {"dataset_id": uuid.UUID(dataset_id)}
        )
        await db.commit()
        
        # ファイルを削除
        if file_path.exists():
            file_path.unlink()
        
        return {"message": "データセットを削除しました"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"削除処理中にエラーが発生しました: {str(e)}"
        )

