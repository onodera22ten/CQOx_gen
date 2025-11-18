"""
Integration tests for column mapping workflow
"""
import pytest
import pandas as pd
import tempfile
from pathlib import Path
from cqox.data.column_mapping import (
    suggest_mapping,
    validate_mapping,
    apply_mapping,
    validate_normalized_data
)


def test_suggest_mapping():
    """Test column mapping suggestion"""
    upload_columns = ['user_id', 'event_time', 'revenue', 'campaign_flag']

    mapping = suggest_mapping(upload_columns)

    assert isinstance(mapping, dict)
    assert 'unit_id' in mapping
    assert 'time' in mapping
    assert mapping['unit_id'] == 'user_id'
    assert mapping['time'] == 'event_time'


def test_validate_mapping_success():
    """Test mapping validation (success case)"""
    mapping = {
        'unit_id': 'user_id',
        'time': 'timestamp',
        'treatment': 'campaign_flag',
        'y': 'revenue'
    }

    is_valid, missing = validate_mapping(mapping)

    assert is_valid
    assert len(missing) == 0


def test_validate_mapping_failure():
    """Test mapping validation (failure case)"""
    mapping = {
        'unit_id': 'user_id',
        'time': 'timestamp'
        # Missing required: treatment, y
    }

    is_valid, missing = validate_mapping(mapping)

    assert not is_valid
    assert 'treatment' in missing
    assert 'y' in missing


def test_apply_mapping():
    """Test applying column mapping"""
    df = pd.DataFrame({
        'user_id': [1, 2, 3],
        'timestamp': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'revenue': [100, 200, 300],
        'campaign_flag': [1, 0, 1]
    })

    mapping = {
        'unit_id': 'user_id',
        'time': 'timestamp',
        'y': 'revenue',
        'treatment': 'campaign_flag'
    }

    df_normalized = apply_mapping(df, mapping)

    assert 'unit_id' in df_normalized.columns
    assert 'time' in df_normalized.columns
    assert 'y' in df_normalized.columns
    assert 'treatment' in df_normalized.columns


def test_validate_normalized_data():
    """Test normalized data validation"""
    df_normalized = pd.DataFrame({
        'unit_id': ['u1', 'u2', 'u3'],
        'time': pd.to_datetime(['2025-01-01', '2025-01-02', '2025-01-03']),
        'treatment': [1, 0, 1],
        'y': [100.0, 200.0, 300.0]
    })

    passed, report = validate_normalized_data(df_normalized)

    assert passed
    assert report['passed']
    assert len(report['errors']) == 0
