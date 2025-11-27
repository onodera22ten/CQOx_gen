import pandas as pd

from cqox.engine.column_inference import infer_column_roles


def test_infer_simple_case():
    df = pd.DataFrame(
        {
            "user_id": [1, 2, 3],
            "treatment_arm": [0, 1, 1],
            "delta_yen": [100, 200, -50],
            "gender": ["male", "female", "male"],
        }
    )

    suggestions = infer_column_roles(df)

    assert any(s.column == "treatment_arm" for s in suggestions["treatment"])
    assert any(s.column == "delta_yen" for s in suggestions["outcome"])
    assert any(s.column == "gender" for s in suggestions["sensitive"])
    assert any(s.column == "user_id" for s in suggestions["id"])
