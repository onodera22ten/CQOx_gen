"""
Column mapping functionality: Semantic schema + Mapping profiles + Fail-fast validation
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml
import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from loguru import logger

from cqox.config import settings


class ColumnMappingError(Exception):
    """Column mapping related errors"""
    pass


class SemanticSchema:
    """Semantic schema (canonical schema) definition"""

    def __init__(self, contract_path: Optional[Path] = None):
        if contract_path is None:
            contract_path = settings.config_dir / "data_contract.yaml"

        with open(contract_path, 'r', encoding='utf-8') as f:
            self.contract = yaml.safe_load(f)

        self.semantic_columns = self.contract['semantic_columns']
        self.type_rules = self.contract['type_rules']
        self.validation_rules = self.contract['validation']

    def get_required_columns(self) -> List[str]:
        """Get list of required semantic columns"""
        return [
            col_name
            for col_name, col_def in self.semantic_columns.items()
            if col_def.get('required', False)
        ]

    def get_all_columns(self) -> List[str]:
        """Get list of all semantic columns"""
        return list(self.semantic_columns.keys())

    def get_aliases(self, semantic_column: str) -> List[str]:
        """Get aliases for a semantic column"""
        col_def = self.semantic_columns.get(semantic_column, {})
        return col_def.get('aliases', [])

    def get_expected_type(self, semantic_column: str) -> str:
        """Get expected type for a semantic column"""
        col_def = self.semantic_columns.get(semantic_column, {})
        return col_def.get('type', 'unknown')


class ColumnAliasManager:
    """Manage column aliases"""

    def __init__(self, aliases_path: Optional[Path] = None):
        if aliases_path is None:
            aliases_path = settings.config_dir / "column_aliases.yaml"

        with open(aliases_path, 'r', encoding='utf-8') as f:
            self.aliases = yaml.safe_load(f)

    def get_aliases(self, semantic_column: str) -> List[str]:
        """Get aliases for a semantic column"""
        # Remove unit_id -> user_id mapping, use direct semantic name
        semantic_key = semantic_column.replace('unit_id', 'user_id')
        return self.aliases.get(semantic_key, [])


def similarity_score(s1: str, s2: str) -> float:
    """Calculate similarity score between two strings"""
    # Normalize: lowercase, remove underscores
    s1_norm = s1.lower().replace('_', '').replace('-', '')
    s2_norm = s2.lower().replace('_', '').replace('-', '')

    # Exact match after normalization
    if s1_norm == s2_norm:
        return 1.0

    # Partial match (one contains the other)
    if s1_norm in s2_norm or s2_norm in s1_norm:
        return 0.9

    # Sequence matcher
    return SequenceMatcher(None, s1_norm, s2_norm).ratio()


def suggest_mapping(
    upload_columns: List[str],
    schema: Optional[SemanticSchema] = None,
    alias_manager: Optional[ColumnAliasManager] = None,
    similarity_threshold: float = 0.7
) -> Dict[str, Optional[str]]:
    """
    Suggest mapping from upload columns to semantic columns

    Args:
        upload_columns: List of column names from uploaded file
        schema: Semantic schema definition
        alias_manager: Alias manager
        similarity_threshold: Minimum similarity score for auto-suggestion

    Returns:
        Dict mapping semantic_column -> upload_column (or None if no good match)
    """
    if schema is None:
        schema = SemanticSchema()
    if alias_manager is None:
        alias_manager = ColumnAliasManager()

    mapping = {}
    used_upload_columns = set()

    for semantic_col in schema.get_all_columns():
        best_match = None
        best_score = 0.0

        # Get all possible aliases
        aliases_from_schema = schema.get_aliases(semantic_col)
        aliases_from_manager = alias_manager.get_aliases(semantic_col)
        all_aliases = set(aliases_from_schema + aliases_from_manager)

        # Check exact matches first
        for upload_col in upload_columns:
            if upload_col in used_upload_columns:
                continue

            # Exact match with aliases
            if upload_col in all_aliases or upload_col == semantic_col:
                best_match = upload_col
                best_score = 1.0
                break

            # Calculate similarity
            score = max([
                similarity_score(upload_col, alias)
                for alias in all_aliases
            ] + [similarity_score(upload_col, semantic_col)])

            if score > best_score:
                best_score = score
                best_match = upload_col

        # Only suggest if score is above threshold
        if best_score >= similarity_threshold:
            mapping[semantic_col] = best_match
            if best_match:
                used_upload_columns.add(best_match)
        else:
            mapping[semantic_col] = None

    return mapping


def validate_mapping(
    mapping: Dict[str, Optional[str]],
    schema: Optional[SemanticSchema] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that all required semantic columns are mapped

    Args:
        mapping: Mapping dict (semantic_column -> upload_column)
        schema: Semantic schema definition

    Returns:
        (is_valid, list_of_missing_required_columns)
    """
    if schema is None:
        schema = SemanticSchema()

    required_columns = schema.get_required_columns()
    missing_columns = [
        col for col in required_columns
        if mapping.get(col) is None
    ]

    is_valid = len(missing_columns) == 0
    return is_valid, missing_columns


def apply_mapping(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    schema: Optional[SemanticSchema] = None
) -> pd.DataFrame:
    """
    Apply column mapping to rename columns to semantic names

    Args:
        df: DataFrame with upload column names
        mapping: Mapping dict (semantic_column -> upload_column)
        schema: Semantic schema definition

    Returns:
        DataFrame with semantic column names
    """
    if schema is None:
        schema = SemanticSchema()

    # Create reverse mapping (upload_column -> semantic_column)
    reverse_mapping = {
        upload_col: semantic_col
        for semantic_col, upload_col in mapping.items()
        if upload_col is not None
    }

    # Rename columns
    df_normalized = df.rename(columns=reverse_mapping)

    # Type conversion
    for semantic_col in df_normalized.columns:
        if semantic_col not in schema.semantic_columns:
            continue

        expected_type = schema.get_expected_type(semantic_col)

        try:
            if expected_type == 'numeric':
                df_normalized[semantic_col] = pd.to_numeric(
                    df_normalized[semantic_col],
                    errors='coerce'
                )
            elif expected_type == 'datetime':
                df_normalized[semantic_col] = pd.to_datetime(
                    df_normalized[semantic_col],
                    errors='coerce'
                )
            elif expected_type == 'categorical':
                df_normalized[semantic_col] = df_normalized[semantic_col].astype(str)
        except Exception as e:
            logger.warning(f"Type conversion warning for {semantic_col}: {e}")

    return df_normalized


def validate_normalized_data(
    df: pd.DataFrame,
    schema: Optional[SemanticSchema] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate normalized DataFrame against schema rules

    Args:
        df: Normalized DataFrame
        schema: Semantic schema definition

    Returns:
        (is_valid, validation_report)
    """
    if schema is None:
        schema = SemanticSchema()

    validation_report = {
        'passed': True,
        'errors': [],
        'warnings': []
    }

    max_missing_rate = schema.validation_rules['max_missing_rate']
    max_type_error_rate = schema.validation_rules['max_type_error_rate']

    # Check required columns
    required_cols = schema.get_required_columns()
    for col in required_cols:
        if col not in df.columns:
            validation_report['errors'].append(
                f"Required column '{col}' is missing after mapping"
            )
            validation_report['passed'] = False
            continue

        # Check missing values
        missing_rate = df[col].isna().sum() / len(df)
        if missing_rate > max_missing_rate:
            validation_report['errors'].append(
                f"Column '{col}' has {missing_rate:.1%} missing values "
                f"(max allowed: {max_missing_rate:.1%})"
            )
            validation_report['passed'] = False

    # Check type conversion errors (NaN introduced by coercion)
    for col in df.columns:
        if col not in schema.semantic_columns:
            continue

        expected_type = schema.get_expected_type(col)

        if expected_type == 'numeric':
            # Count how many values became NaN after to_numeric
            if df[col].dtype == 'object':
                validation_report['warnings'].append(
                    f"Column '{col}' expected to be numeric but has object type"
                )

        elif expected_type == 'datetime':
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                validation_report['warnings'].append(
                    f"Column '{col}' expected to be datetime but has {df[col].dtype} type"
                )

    return validation_report['passed'], validation_report


class MappingProfileManager:
    """Manage mapping profiles (saved mappings for reuse)"""

    def __init__(self, profiles_dir: Optional[Path] = None):
        if profiles_dir is None:
            profiles_dir = settings.config_dir / "column_mappings"

        self.profiles_dir = profiles_dir
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def save_profile(
        self,
        profile_name: str,
        mapping: Dict[str, str],
        metadata: Optional[Dict] = None
    ):
        """Save a mapping profile"""
        profile_data = {
            'name': profile_name,
            'mapping': mapping,
            'metadata': metadata or {}
        }

        profile_path = self.profiles_dir / f"{profile_name}.yaml"
        with open(profile_path, 'w', encoding='utf-8') as f:
            yaml.dump(profile_data, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Saved mapping profile: {profile_name}")

    def load_profile(self, profile_name: str) -> Dict[str, str]:
        """Load a mapping profile"""
        profile_path = self.profiles_dir / f"{profile_name}.yaml"

        if not profile_path.exists():
            raise ColumnMappingError(f"Profile '{profile_name}' not found")

        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = yaml.safe_load(f)

        return profile_data['mapping']

    def list_profiles(self) -> List[str]:
        """List all available profiles"""
        return [
            p.stem for p in self.profiles_dir.glob("*.yaml")
        ]

    def detect_profile_diff(
        self,
        upload_columns: List[str],
        profile_name: str
    ) -> Dict[str, Any]:
        """
        Detect differences between upload columns and saved profile

        Returns:
            Dict with 'new_columns', 'missing_columns', 'unchanged_columns'
        """
        profile_mapping = self.load_profile(profile_name)
        profile_upload_cols = set(profile_mapping.values())

        upload_cols_set = set(upload_columns)

        return {
            'new_columns': list(upload_cols_set - profile_upload_cols),
            'missing_columns': list(profile_upload_cols - upload_cols_set),
            'unchanged_columns': list(upload_cols_set & profile_upload_cols)
        }
