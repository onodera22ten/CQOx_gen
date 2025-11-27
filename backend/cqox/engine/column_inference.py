"""
Column role inference utilities
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd


@dataclass
class ColumnSuggestion:
    """Suggested role for a column."""
    role: str  # treatment | outcome | id | sensitive
    column: str
    score: float
    reason: str


KEYWORDS = {
    "treatment": ["treatment", "treat", "arm", "variant", "group", "segment", "policy", "campaign"],
    "outcome": ["delta_yen", "revenue", "sales", "ltv", "profit", "y", "conversion", "converted"],
    "id": ["user_id", "customer_id", "member_id", "account_id", "id"],
    "sensitive": ["gender", "sex", "age", "age_group", "prefecture", "region"],
}


def infer_column_roles(df: pd.DataFrame) -> Dict[str, List[ColumnSuggestion]]:
    """
    Infer likely column roles from a pandas DataFrame.
    """
    suggestions: Dict[str, List[ColumnSuggestion]] = {
        "treatment": [],
        "outcome": [],
        "id": [],
        "sensitive": [],
    }

    if df.empty:
        return suggestions

    nunique = df.nunique(dropna=True)

    for col in df.columns:
        lname = col.lower()
        nuniq = int(nunique.get(col, 0))

        # ID candidates: unique values and name keywords
        if nuniq == len(df) and any(k in lname for k in KEYWORDS["id"]):
            suggestions["id"].append(
                ColumnSuggestion(
                    role="id",
                    column=col,
                    score=0.9,
                    reason=f"unique values ({nuniq}) and name matches ID keyword",
                )
            )

        # Treatment candidates: low cardinality + keyword
        if nuniq <= 10 and any(k in lname for k in KEYWORDS["treatment"]):
            score = 0.8 if nuniq <= 3 else 0.6
            suggestions["treatment"].append(
                ColumnSuggestion(
                    role="treatment",
                    column=col,
                    score=score,
                    reason=f"{nuniq} unique values and name matches treatment keyword",
                )
            )

        # Outcome candidates: keyword match
        if any(k in lname for k in KEYWORDS["outcome"]):
            suggestions["outcome"].append(
                ColumnSuggestion(
                    role="outcome",
                    column=col,
                    score=0.8,
                    reason="name matches outcome keyword",
                )
            )

        # Sensitive candidates: low cardinality + keyword
        if nuniq <= 20 and any(k in lname for k in KEYWORDS["sensitive"]):
            suggestions["sensitive"].append(
                ColumnSuggestion(
                    role="sensitive",
                    column=col,
                    score=0.7,
                    reason=f"{nuniq} unique values and name matches sensitive keyword",
                )
            )

    return suggestions
