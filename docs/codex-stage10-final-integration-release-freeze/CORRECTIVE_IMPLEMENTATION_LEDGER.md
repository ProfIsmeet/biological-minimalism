# Corrective Implementation Ledger

Implementation checkpoint: `4acc4d3109295d4d3da1ece023e5eb86d1d3a032`.

- Backend Digital Twin schema/engine/route now carry conceptual metadata and a literal untrained/unvalidated status only.
- Mission Timeline no longer requests the legacy state; frontend API/types no longer expose it.
- PDD current-state/API/route descriptions match the implementation.
- Regression checks reject score fields, percentages, legacy consumers, and unsupported language.
- SHAP capacity matches the two intended independent targets; existing per-explainer locks remain intact.
- Explanation panels wait for confirmed REST source identity before fetching.
- One concurrent endpoint regression was added; backend count rose from 364 to 365 passes.
- Historical local paths were sanitized; evidence-name collisions were corrected before evidence commit.
- NumPy 2.5.3, scikit-learn 1.9.1, and SHAP 0.52.0 are pinned to the versions exercised by the clean-clone matrix.
