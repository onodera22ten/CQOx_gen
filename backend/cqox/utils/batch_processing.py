"""
【日本語サマリ】このモジュールは大規模データ（100万行以上）をバッチ処理するためのユーティリティを提供する。
- なぜ必要か: 100万行レベルのデータを一度にメモリに載せるとOOMが発生するため
- 何をするか: チャンク分割、並列処理、ストリーミング処理
- どう検証するか: メモリ使用量監視、処理時間計測、結果の整合性チェック

【Inputs】
- DataFrame or file path: 大規模データセット
- chunk_size: チャンクサイズ（デフォルト: 100K行）

【Outputs】
- Generator of DataFrames: チャンク単位で処理されたデータ
"""

import pandas as pd
import numpy as np
from typing import Iterator, Callable, Any, Optional, Dict, List
from pathlib import Path
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from cqox.config.settings import settings

logger = logging.getLogger(__name__)


def read_csv_in_chunks(
    file_path: Path | str,
    chunk_size: Optional[int] = None,
    **read_csv_kwargs
) -> Iterator[pd.DataFrame]:
    """
    CSVファイルをチャンク単位で読み込む（ストリーミング処理）
    
    Args:
        file_path: CSVファイルパス
        chunk_size: チャンクサイズ（行数）。Noneの場合は設定から取得
        **read_csv_kwargs: pd.read_csvに渡す追加引数
    
    Yields:
        pd.DataFrame: チャンク単位のデータフレーム
        
    Example:
        for chunk in read_csv_in_chunks('large_data.csv', chunk_size=100_000):
            process_chunk(chunk)
    """
    chunk_size = chunk_size or settings.batch_chunk_size
    
    logger.info(f"Reading CSV in chunks: {file_path} (chunk_size={chunk_size:,})")
    
    try:
        chunk_iterator = pd.read_csv(file_path, chunksize=chunk_size, **read_csv_kwargs)
        
        for i, chunk in enumerate(chunk_iterator):
            logger.debug(f"Processing chunk {i+1} ({len(chunk):,} rows)")
            yield chunk
            
    except Exception as e:
        logger.error(f"Error reading CSV in chunks: {e}")
        raise


def process_dataframe_in_chunks(
    df: pd.DataFrame,
    process_func: Callable[[pd.DataFrame], pd.DataFrame],
    chunk_size: Optional[int] = None,
    parallel: bool = False,
    max_workers: Optional[int] = None
) -> pd.DataFrame:
    """
    DataFrameをチャンク単位で処理し、結果を結合
    
    Args:
        df: 処理対象のDataFrame
        process_func: チャンク処理関数 (df_chunk -> df_result)
        chunk_size: チャンクサイズ（行数）
        parallel: 並列処理を有効化（CPUバウンドな処理向け）
        max_workers: 並列ワーカー数（Noneの場合は設定から取得）
    
    Returns:
        pd.DataFrame: 処理済みDataFrame
        
    Example:
        def compute_cate(chunk):
            chunk['cate'] = chunk['y1'] - chunk['y0']
            return chunk
        
        result = process_dataframe_in_chunks(df, compute_cate, parallel=True)
    """
    chunk_size = chunk_size or settings.batch_chunk_size
    max_workers = max_workers or settings.parallel_workers
    
    total_rows = len(df)
    
    if total_rows <= chunk_size:
        # Small dataset: process directly
        logger.info(f"Processing small dataset directly ({total_rows:,} rows)")
        return process_func(df)
    
    # Large dataset: process in chunks
    logger.info(f"Processing large dataset in chunks ({total_rows:,} rows, chunk_size={chunk_size:,}, parallel={parallel})")
    
    chunks = [df.iloc[i:i+chunk_size].copy() for i in range(0, total_rows, chunk_size)]
    
    if parallel and len(chunks) > 1:
        # Parallel processing (for CPU-bound tasks)
        logger.info(f"Using parallel processing with {max_workers} workers")
        
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {executor.submit(process_func, chunk): i for i, chunk in enumerate(chunks)}
            
            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    result = future.result()
                    results.append((chunk_idx, result))
                    logger.debug(f"Chunk {chunk_idx+1}/{len(chunks)} completed")
                except Exception as e:
                    logger.error(f"Chunk {chunk_idx} failed: {e}")
                    raise
        
        # Sort by chunk index and concatenate
        results.sort(key=lambda x: x[0])
        processed_chunks = [r[1] for r in results]
    else:
        # Sequential processing (for I/O-bound tasks or small datasets)
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
            processed_chunks.append(process_func(chunk))
    
    # Concatenate results
    result = pd.concat(processed_chunks, axis=0, ignore_index=True)
    logger.info(f"Batch processing completed: {len(result):,} rows")
    
    return result


def estimate_memory_usage(df: pd.DataFrame) -> Dict[str, float]:
    """
    DataFrameのメモリ使用量を推定
    
    Args:
        df: DataFrame
    
    Returns:
        Dict with memory stats (MB):
            - total: 総メモリ使用量
            - per_row: 行あたりのメモリ使用量
            - estimated_peak: ピーク時の推定メモリ（コピーやソートを考慮）
    """
    memory_bytes = df.memory_usage(deep=True).sum()
    memory_mb = memory_bytes / (1024 ** 2)
    per_row_mb = memory_mb / len(df) if len(df) > 0 else 0
    
    # Assume 3x memory for peak usage (copies, sorting, temporary objects)
    estimated_peak_mb = memory_mb * 3
    
    return {
        "total_mb": round(memory_mb, 2),
        "per_row_mb": round(per_row_mb, 6),
        "estimated_peak_mb": round(estimated_peak_mb, 2),
        "rows": len(df),
        "columns": len(df.columns)
    }


def check_memory_limit(df: pd.DataFrame, max_memory_mb: Optional[int] = None) -> bool:
    """
    DataFrameがメモリ制限内に収まるかチェック
    
    Args:
        df: DataFrame
        max_memory_mb: 最大メモリ制限（MB）。Noneの場合は設定から取得
    
    Returns:
        bool: True if within limit
    
    Raises:
        MemoryError: メモリ制限を超えた場合
    """
    max_memory_mb = max_memory_mb or settings.max_memory_per_worker_mb
    
    stats = estimate_memory_usage(df)
    
    if stats['estimated_peak_mb'] > max_memory_mb:
        msg = (
            f"Estimated memory usage ({stats['estimated_peak_mb']:.1f} MB) "
            f"exceeds limit ({max_memory_mb} MB). "
            f"Dataset: {stats['rows']:,} rows × {stats['columns']} cols. "
            f"Consider using batch processing with smaller chunk_size."
        )
        logger.error(msg)
        raise MemoryError(msg)
    
    logger.info(f"Memory check passed: {stats['estimated_peak_mb']:.1f} MB / {max_memory_mb} MB")
    return True


def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameのdtypeを最適化してメモリ使用量を削減
    
    Args:
        df: DataFrame
    
    Returns:
        pd.DataFrame: 最適化されたDataFrame
    """
    original_size = df.memory_usage(deep=True).sum() / (1024 ** 2)
    
    df_opt = df.copy()
    
    # Optimize numeric columns
    for col in df_opt.select_dtypes(include=['int64']).columns:
        df_opt[col] = pd.to_numeric(df_opt[col], downcast='integer')
    
    for col in df_opt.select_dtypes(include=['float64']).columns:
        df_opt[col] = pd.to_numeric(df_opt[col], downcast='float')
    
    # Convert object columns to category if cardinality is low
    for col in df_opt.select_dtypes(include=['object']).columns:
        num_unique = df_opt[col].nunique()
        num_total = len(df_opt[col])
        
        # Convert to category if < 50% unique values
        if num_unique / num_total < 0.5:
            df_opt[col] = df_opt[col].astype('category')
    
    optimized_size = df_opt.memory_usage(deep=True).sum() / (1024 ** 2)
    reduction = ((original_size - optimized_size) / original_size) * 100
    
    logger.info(f"Memory optimization: {original_size:.1f} MB → {optimized_size:.1f} MB ({reduction:.1f}% reduction)")
    
    return df_opt


def split_dataframe_for_parallel(
    df: pd.DataFrame,
    n_splits: Optional[int] = None
) -> List[pd.DataFrame]:
    """
    DataFrameを並列処理用に分割
    
    Args:
        df: DataFrame
        n_splits: 分割数（Noneの場合は設定から取得）
    
    Returns:
        List[pd.DataFrame]: 分割されたDataFrameリスト
    """
    n_splits = n_splits or settings.parallel_workers
    
    split_size = len(df) // n_splits
    splits = []
    
    for i in range(n_splits):
        start_idx = i * split_size
        end_idx = start_idx + split_size if i < n_splits - 1 else len(df)
        splits.append(df.iloc[start_idx:end_idx].copy())
    
    logger.info(f"Split DataFrame into {n_splits} parts ({[len(s) for s in splits]} rows each)")
    
    return splits


# Example usage for causal inference tasks
def process_cate_estimation_in_batches(
    df: pd.DataFrame,
    estimator_func: Callable[[pd.DataFrame], np.ndarray],
    chunk_size: Optional[int] = None
) -> np.ndarray:
    """
    CATE推定をバッチ処理で実行
    
    Args:
        df: 特徴量データ
        estimator_func: CATE推定関数（df -> cate_array）
        chunk_size: チャンクサイズ
    
    Returns:
        np.ndarray: CATE推定値
        
    Example:
        def estimate_cate(df_chunk):
            return model.predict(df_chunk[features])
        
        cate = process_cate_estimation_in_batches(df, estimate_cate)
    """
    chunk_size = chunk_size or settings.batch_chunk_size
    total_rows = len(df)
    
    if total_rows <= chunk_size:
        return estimator_func(df)
    
    logger.info(f"Processing CATE estimation in batches ({total_rows:,} rows, chunk_size={chunk_size:,})")
    
    results = []
    for i in range(0, total_rows, chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        logger.debug(f"CATE batch {i//chunk_size + 1}/{(total_rows + chunk_size - 1)//chunk_size}")
        cate_chunk = estimator_func(chunk)
        results.append(cate_chunk)
    
    return np.concatenate(results)


if __name__ == "__main__":
    # Demo: メモリ最適化とバッチ処理のテスト
    print("=== Batch Processing Utilities Demo ===\n")
    
    # Generate large synthetic dataset
    n_rows = 1_000_000
    print(f"Generating {n_rows:,} rows...")
    
    df = pd.DataFrame({
        'x1': np.random.randn(n_rows),
        'x2': np.random.randn(n_rows),
        'treatment': np.random.binomial(1, 0.5, n_rows),
        'outcome': np.random.randn(n_rows),
        'category': np.random.choice(['A', 'B', 'C'], n_rows)
    })
    
    # Check memory
    stats = estimate_memory_usage(df)
    print(f"\nMemory usage:")
    print(f"  Total: {stats['total_mb']:.1f} MB")
    print(f"  Per row: {stats['per_row_mb']:.6f} MB")
    print(f"  Estimated peak: {stats['estimated_peak_mb']:.1f} MB")
    
    # Optimize dtypes
    df_opt = optimize_dtypes(df)
    
    # Batch processing example
    def compute_cate(chunk: pd.DataFrame) -> pd.DataFrame:
        chunk['cate'] = chunk['x1'] * 0.5 + chunk['x2'] * 0.3
        return chunk
    
    print(f"\nBatch processing with chunk_size=100,000...")
    result = process_dataframe_in_chunks(df_opt, compute_cate, chunk_size=100_000, parallel=False)
    print(f"Result shape: {result.shape}")
    
    print("\n✅ Demo completed!")

