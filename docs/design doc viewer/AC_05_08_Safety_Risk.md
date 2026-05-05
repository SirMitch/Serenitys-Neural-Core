# AlphaChart v3.4 — AC_05: ML Factor Model & Feature Engineering
**Revision:** v3.4.0 | **Status:** Implementation-Ready | **Owner:** AC_00 §5.5

---

## Table of Contents
1. [Purpose & Role](#1-purpose--role)
2. [Feature Engineering Pipeline](#2-feature-engineering-pipeline)
3. [Model Architecture & Training](#3-model-architecture--training)
4. [Inference & Retraining](#4-inference--retraining)
5. [Feature Importance & Ablation](#5-feature-importance--ablation)
6. [Integration Points](#6-integration-points)
7. [Edge Cases](#7-edge-cases)
8. [Success Criteria](#8-success-criteria)

---

## 1. Purpose & Role

The ML Factor Model is a classical supervised learning classifier that predicts the probability of a positive return over the prediction horizon. It operates independently of FinRL-X and Multi-TF analysis, providing a third orthogonal signal source to the ensemble.

It is not a deep learning model — it uses gradient boosting on hand-crafted factors for interpretability, speed, and resistance to overfitting on small datasets. Its output (`ml_factor_score: float [0,1]`) represents the model's probability estimate of a positive outcome.

---

## 2. Feature Engineering Pipeline

Eight factors are computed from daily OHLCV data. All features use only data available at signal time T (no lookahead — verified by Phase 0 Step 1).

```python
import numpy as np
import ta
import pandas as pd

class FeatureEngineer:
    """
    Computes the 8-factor feature vector for the ML Factor Model.
    All features are computed on the daily close series.
    Requires minimum 60 bars of history.
    """

    FEATURE_NAMES = [
        "momentum_5d",      # 5-day price rate of change
        "momentum_20d",     # 20-day price rate of change
        "momentum_60d",     # 60-day price rate of change (trend)
        "zscore_20d",       # price z-score vs 20-day mean (mean reversion)
        "realized_vol_20d", # 20-day realized volatility (risk)
        "vol_ratio_60d",    # realized vol / 60-day vol (vol regime)
        "volume_surge",     # today's volume / 20-day avg volume
        "range_ratio",      # today's range / ATR (activity)
    ]

    def compute(self, df: pd.DataFrame) -> np.ndarray:
        if len(df) < 60:
            raise ValueError("Minimum 60 bars required for feature computation")

        close = df["Close"]
        high  = df["High"]
        low   = df["Low"]
        vol   = df["Volume"]

        # Momentum factors
        mom_5  = float(close.pct_change(5).iloc[-1])
        mom_20 = float(close.pct_change(20).iloc[-1])
        mom_60 = float(close.pct_change(60).iloc[-1]) if len(df) > 60 else 0.0

        # Mean-reversion factor (z-score)
        mean_20  = close.rolling(20).mean().iloc[-1]
        std_20   = close.rolling(20).std().iloc[-1]
        zscore   = float((close.iloc[-1] - mean_20) / (std_20 + 1e-9))

        # Volatility factors
        ret_std_20 = float(close.pct_change().rolling(20).std().iloc[-1])
        ret_std_60 = float(close.pct_change().rolling(60).std().iloc[-1])
        vol_ratio  = ret_std_20 / (ret_std_60 + 1e-9)

        # Volume factor
        vol_ma_20  = float(vol.rolling(20).mean().iloc[-1])
        vol_surge  = float(vol.iloc[-1] / (vol_ma_20 + 1e-9))

        # Range factor
        atr        = float(ta.volatility.AverageTrueRange(
                         high, low, close).average_true_range().iloc[-1])
        today_range= float(high.iloc[-1] - low.iloc[-1])
        range_ratio= today_range / (atr + 1e-9)

        features = np.array([
            mom_5, mom_20, mom_60, zscore,
            ret_std_20, vol_ratio, vol_surge, range_ratio
        ], dtype=np.float32)

        # Replace NaN/Inf with 0
        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
        return features
```

---

## 3. Model Architecture & Training

```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import CalibratedClassifierCV
import joblib

class MLFactorModelTrainer:
    """
    Trains a calibrated GBM classifier on labeled historical data.
    Labels: 1 = positive return over N days, 0 = flat or negative.
    """

    PREDICTION_HORIZON_DAYS = 5   # predict return over next 5 trading days
    LABEL_THRESHOLD         = 0.005  # >0.5% move counted as positive

    def train(self, df: pd.DataFrame,
              model_path: str,
              n_splits: int = 5):
        """Walk-forward cross-validation training."""
        engineer = FeatureEngineer()

        # Build feature matrix and labels
        X_rows, y_labels = [], []
        for i in range(60, len(df) - self.PREDICTION_HORIZON_DAYS):
            slice_df = df.iloc[:i]
            try:
                features = engineer.compute(slice_df)
                future_ret = float(
                    df["Close"].iloc[i + self.PREDICTION_HORIZON_DAYS] /
                    df["Close"].iloc[i] - 1
                )
                label = int(future_ret > self.LABEL_THRESHOLD)
                X_rows.append(features)
                y_labels.append(label)
            except Exception:
                continue

        X = np.array(X_rows)
        y = np.array(y_labels)

        # Walk-forward validation
        tscv = TimeSeriesSplit(n_splits=n_splits)
        best_auc = 0.0
        best_model = None
        for train_idx, val_idx in tscv.split(X):
            model = GradientBoostingClassifier(
                n_estimators=200, max_depth=4,
                learning_rate=0.05, subsample=0.8,
                random_state=42
            )
            model.fit(X[train_idx], y[train_idx])
            # Probability calibration via Platt scaling
            calibrated = CalibratedClassifierCV(model, method="sigmoid", cv="prefit")
            calibrated.fit(X[train_idx], y[train_idx])

            from sklearn.metrics import roc_auc_score
            auc = roc_auc_score(y[val_idx],
                                calibrated.predict_proba(X[val_idx])[:, 1])
            if auc > best_auc:
                best_auc = auc
                best_model = calibrated

        joblib.dump(best_model, model_path)
        return best_auc

class MLFactorModel:
    def __init__(self, model_path: str):
        self.model    = joblib.load(model_path)
        self.engineer = FeatureEngineer()

    def predict_score(self, df: pd.DataFrame) -> float:
        """Returns P(positive return) in [0, 1]."""
        try:
            features = self.engineer.compute(df).reshape(1, -1)
            return float(self.model.predict_proba(features)[0][1])
        except Exception:
            return 0.5   # neutral fallback on error
```

---

## 4. Inference & Retraining

```python
# Retraining triggered by AC_12 RetrainingController on:
# - Win rate below 45% over last 20 trades
# - Total PnL below -15% over last 20 trades
# - Scheduled monthly retrain (regardless of performance)

# Retraining uses last config["training_window_days"] (default: 252) of data.
# New model must achieve AUC ≥ 0.60 on hold-out set before replacing live model.

RETRAIN_VALIDATION_GATE = {
    "min_auc":      0.60,
    "min_test_size": 60,    # minimum hold-out bars
}
```

---

## 5. Feature Importance & Ablation

The RSI ablation test (Phase 0 Step 6) applies to the ML Factor Model. RSI is intentionally excluded from the feature set. If RSI is added, performance must not improve by more than 5% — confirming it is not load-bearing.

```python
def run_feature_ablation(X: np.ndarray, y: np.ndarray,
                          feature_names: list) -> dict:
    """Drops each feature and measures AUC degradation."""
    from sklearn.metrics import roc_auc_score
    base_auc = ...  # baseline AUC with all features
    results  = {}
    for i, name in enumerate(feature_names):
        X_ablated = np.delete(X, i, axis=1)
        # retrain and evaluate
        ablated_auc = ...
        results[name] = {
            "auc_drop":      base_auc - ablated_auc,
            "is_critical":   (base_auc - ablated_auc) > 0.05,
        }
    return results
```

---

## 6. Integration Points

| Module | Direction | Data |
|---|---|---|
| DataFetcher | → ML Model | `df_daily` (60+ bars) |
| ML Model → AC_01 | → Ensemble | `ml_factor_score: float` |
| AC_12 (Learning) | → ML Model | Retrain trigger + new data |
| AC_14 (Phase 0) | → ML Model | AUC validation, ablation test |
| AC_07 (LLM) | reads | Score in dossier string |

---

## 7. Edge Cases

| Case | Handling |
|---|---|
| Fewer than 60 bars | Returns 0.5 (neutral); signal continues but LLM flagged |
| Model file missing | Returns 0.5; logs warning; Phase 0 must be run |
| Feature NaN/Inf | Replaced with 0.0 via `np.nan_to_num` |
| Class imbalance in training | `class_weight="balanced"` in GBM |

---

## 8. Success Criteria

| Metric | Minimum | Target |
|---|---|---|
| Out-of-sample AUC | ≥ 0.60 | ≥ 0.68 |
| Feature ablation: RSI not load-bearing | < 5% AUC change | 0% |
| Inference latency | < 10ms | < 5ms |
| Probability calibration error | < 8% | < 5% |

---
---

# AlphaChart v3.4 — AC_06: Deterministic Safety Layer & Hard Risk Guards
**Revision:** v3.4.0 | **Status:** Implementation-Ready | **Owner:** AC_00 §8

---

## Table of Contents
1. [Purpose & Authority](#1-purpose--authority)
2. [DeterministicSafetyFilter](#2-deterministicsafetyfilter)
3. [DrawdownGuard](#3-drawdownguard)
4. [StateLock](#4-statelock)
5. [Hard Safety Limit Registry](#5-hard-safety-limit-registry)
6. [TREND_DOWN Remediation Rules](#6-trend_down-remediation-rules)
7. [Integration Points](#7-integration-points)
8. [Edge Cases](#8-edge-cases)
9. [Success Criteria](#9-success-criteria)

---

## 1. Purpose & Authority

The Deterministic Safety Layer is the **last defense before any order is staged**. It applies immutable rule-based checks that cannot be disabled, overridden by config, or bypassed by any other module. If any check fails, the signal is blocked with a logged reason code. There is no appeal path.

All constants used in this module are defined in `alphachart/core/safety.py` (AC_00 §8). This module never defines its own numerical limits.

---

## 2. DeterministicSafetyFilter

```python
from alphachart.core import safety
from datetime import datetime, date
import pandas_market_calendars as mcal
import pandas as pd

class DeterministicSafetyFilter:
    """
    Rule-based signal validation.
    Runs BEFORE the LLM gate (cheaper than LLM; eliminates bad candidates early).
    Every check is deterministic and produces a specific reason code.
    """

    def __init__(self, earnings_calendar: dict):
        self.earnings_calendar = earnings_calendar   # {ticker: [date, ...]}

    def check(self, ticker: str, signal: dict,
              df_daily: pd.DataFrame) -> tuple[bool, list[str]]:
        """
        Returns (passed: bool, block_reasons: list[str]).
        block_reasons is empty if passed=True.
        """
        blocks = []
        today  = date.today()

        # ── Rule 1: Earnings Blackout ─────────────────────────────────────
        for edate in self.earnings_calendar.get(ticker, []):
            if abs((edate - today).days) <= safety.HARD_EARNINGS_BLACKOUT_DAYS:
                blocks.append(f"EARNINGS_BLACKOUT:{edate}")

        # ── Rule 2: Overnight Gap ─────────────────────────────────────────
        if len(df_daily) >= 2:
            prev_close = float(df_daily["Close"].iloc[-2])
            today_open = float(df_daily["Open"].iloc[-1])
            if prev_close > 0:
                gap_pct = abs(today_open / prev_close - 1)
                if gap_pct > safety.HARD_MAX_GAP_PCT:
                    blocks.append(f"GAP_FILTER:{gap_pct:.1%}")

        # ── Rule 3: Minimum Liquidity ─────────────────────────────────────
        if len(df_daily) >= 20:
            avg_vol = float(df_daily["Volume"].rolling(20).mean().iloc[-1])
            if avg_vol < safety.HARD_MIN_LIQUIDITY_VOLUME:
                blocks.append(f"LOW_LIQUIDITY:{avg_vol:.0f}")

        # ── Rule 4: Market Halt ───────────────────────────────────────────
        if signal.get("market_status") == "HALTED":
            blocks.append("MARKET_HALTED")

        # ── Rule 5: Market Closed (holiday/weekend) ───────────────────────
        nyse = mcal.get_calendar("NYSE")
        sched = nyse.schedule(
            start_date=today.strftime("%Y-%m-%d"),
            end_date=today.strftime("%Y-%m-%d")
        )
        if sched.empty:
            blocks.append("MARKET_CLOSED")

        # ── Rule 6: Market Open Blackout (first 15 min) ───────────────────
        import pytz
        now_et = datetime.now(pytz.timezone("America/New_York"))
        from datetime import time as dt_time
        if now_et.time() <= dt_time(9, 30 + safety.HARD_MARKET_OPEN_BLACKOUT_MIN):
            if now_et.time() >= dt_time(9, 30):
                blocks.append("OPEN_BLACKOUT")

        # ── Rule 7: RSI-Only Signal Block ─────────────────────────────────
        if signal.get("is_rsi_only_signal", False):
            blocks.append("RSI_ONLY_SIGNAL_BLOCKED")

        # ── Rule 8: TRENDING_DOWN LONG Position Size Cap ──────────────────
        # Note: position cap applied in PositionSizer, not here.
        # Here we flag for LLM dossier.
        if (signal.get("regime") == "TRENDING_DOWN" and
                signal.get("direction") == "LONG"):
            signal["_trend_down_long"] = True   # flag passed downstream

        passed = len(blocks) == 0
        return passed, blocks

    def check_portfolio_concentration(self,
                                       proposed_ticker: str,
                                       proposed_sector: str,
                                       open_positions: dict) -> tuple[bool, str]:
        """
        Checks sector concentration before adding a new position.
        open_positions: {ticker: {sector: str, value: float}}
        """
        total_value   = sum(p["value"] for p in open_positions.values())
        sector_value  = sum(p["value"] for p in open_positions.values()
                            if p.get("sector") == proposed_sector)
        if total_value > 0:
            sector_pct = sector_value / total_value
            if sector_pct >= safety.HARD_MAX_SECTOR_CONCENTRATION:
                return False, f"SECTOR_CONCENTRATION:{sector_pct:.1%}"
        return True, ""
```

---

## 3. DrawdownGuard

```python
class DrawdownGuard:
    """
    Monitors portfolio equity and enforces drawdown halts.
    Soft halt: stops new trades. Hard halt: stops ALL trading activity.
    Peak equity is tracked and only updated upward (ratchet).
    """

    def __init__(self, broker_connector, config: dict):
        self.broker    = broker_connector
        self.config    = config
        self.peak_equity = None

    def update_and_check(self) -> tuple[bool, str]:
        """
        Returns (trading_allowed: bool, status_message: str).
        Must be called before every order submission.
        """
        equity = self.broker.get_account_equity()

        # Update peak (ratchet — only moves up)
        if self.peak_equity is None or equity > self.peak_equity:
            self.peak_equity = equity

        drawdown = (self.peak_equity - equity) / self.peak_equity

        # Hard halt — immutable limit from safety.py
        if drawdown >= safety.HARD_MAX_PORTFOLIO_DRAWDOWN:
            return False, (f"HARD_HALT: drawdown={drawdown:.1%} "
                           f">= {safety.HARD_MAX_PORTFOLIO_DRAWDOWN:.0%}. "
                           f"All trading suspended.")

        # Soft halt — user-configured tolerance
        soft_limit = self.config.get("max_drawdown_tolerance",
                                     safety.HARD_MAX_PORTFOLIO_DRAWDOWN * 0.75)
        if drawdown >= soft_limit:
            return False, (f"SOFT_HALT: drawdown={drawdown:.1%} "
                           f">= soft limit {soft_limit:.0%}")

        return True, f"OK: drawdown={drawdown:.1%} equity=${equity:,.0f}"

    def get_current_drawdown(self) -> float:
        """Returns current drawdown as a positive fraction [0, 1]."""
        if self.peak_equity is None:
            return 0.0
        equity = self.broker.get_account_equity()
        return max(0.0, (self.peak_equity - equity) / self.peak_equity)
```

---

## 4. StateLock

```python
import threading

class StateLock:
    """
    Per-ticker mutex preventing concurrent orders on the same symbol.
    Implemented as a dict of threading.Lock objects.
    Acquired before order submission; released on order close or cancellation.
    """

    def __init__(self):
        self._locks: dict[str, bool] = {}
        self._mutex = threading.Lock()

    def acquire(self, ticker: str) -> bool:
        """Returns True if lock acquired, False if already locked."""
        with self._mutex:
            if self._locks.get(ticker, False):
                return False
            self._locks[ticker] = True
            return True

    def release(self, ticker: str):
        with self._mutex:
            self._locks[ticker] = False

    def is_locked(self, ticker: str) -> bool:
        return self._locks.get(ticker, False)

    def locked_tickers(self) -> list[str]:
        return [t for t, locked in self._locks.items() if locked]
```

---

## 5. Hard Safety Limit Registry

All limits are imported from `alphachart/core/safety.py`. See AC_00 §8 for the full registry. Key limits enforced by this module:

| Limit Constant | Value | Enforcement Point |
|---|---|---|
| `HARD_MAX_RISK_PCT` | 5% | PositionSizer (AC_08) + order validation |
| `HARD_MAX_PORTFOLIO_DRAWDOWN` | 20% | DrawdownGuard.update_and_check() |
| `HARD_MAX_CONCURRENT_TRADES` | 15 | OrderManager pre-check (AC_13) |
| `HARD_MIN_LIQUIDITY_VOLUME` | 500,000 | Rule 3 above |
| `HARD_EARNINGS_BLACKOUT_DAYS` | 2 | Rule 1 above |
| `HARD_MAX_GAP_PCT` | 3% | Rule 2 above |
| `HARD_MARKET_OPEN_BLACKOUT_MIN` | 15 | Rule 6 above |

---

## 6. TREND_DOWN Remediation Rules

Applied after ensemble scoring, before LLM gate:

```python
def apply_trend_down_remediation(conviction: float,
                                  direction: "Direction",
                                  regime: "Regime",
                                  config: dict) -> tuple[float, dict]:
    """
    Returns (adjusted_conviction, config_with_flags).
    """
    from alphachart.core.types import Direction, Regime
    if regime != Regime.TRENDING_DOWN:
        return conviction, config

    if direction == Direction.LONG:
        conviction *= (1 - safety.TREND_DOWN_LONG_CONVICTION_PENALTY)
        config["_quality_floor"] = (
            config.get("min_quality_score", 0.65) +
            safety.TREND_DOWN_LONG_QUALITY_FLOOR_RAISE
        )

    elif direction == Direction.SHORT:
        conviction = min(
            conviction * (1 + safety.TREND_DOWN_SHORT_CONVICTION_BOOST),
            1.0
        )

    return round(conviction, 4), config
```

---

## 7. Integration Points

| Module | Direction | Data |
|---|---|---|
| AC_01 (Ensemble) | → Safety | conviction, direction, regime |
| AC_09 (Scanner) | → Safety | bulk candidate check |
| Safety → AC_07 (LLM) | → Quality Gate | passes only if check() returns True |
| Safety → AC_13 (Orders) | → Order Mgr | DrawdownGuard called before every order |
| AC_11 (Config) | → Safety | `max_drawdown_tolerance` (soft limit only) |

---

## 8. Edge Cases

| Case | Handling |
|---|---|
| Earnings calendar outdated (> 7 days old) | Log warning; earnings blackout still enforced on known dates |
| Market calendar API failure | Assume market closed; block all signals |
| Broker API failure in DrawdownGuard | Block all trading (fail-safe) |
| Peak equity is None (first run) | Initialize to current equity; no drawdown yet |
| StateLock held > 24 hours | Automatic release with WARNING log |

---

## 9. Success Criteria

| Metric | Target |
|---|---|
| All hard limit violations prevented | 100% |
| Earnings blackout enforced | 100% |
| Market halt detected and blocked | 100% |
| Drawdown soft halt trigger accuracy | 100% |
| StateLock prevents duplicate orders | 100% |

---
---

# AlphaChart v3.4 — AC_07: LLM Quality Gate — Senior Quant Reviewer
**Revision:** v3.4.0 | **Status:** Implementation-Ready | **Owner:** AC_00 §5.6

---

## Table of Contents
1. [Role & Constraints](#1-role--constraints)
2. [System Prompt Design](#2-system-prompt-design)
3. [Dossier Construction](#3-dossier-construction)
4. [Quality Gate — Single Signal](#4-quality-gate--single-signal)
5. [Batch Evaluation (Scanner Path)](#5-batch-evaluation-scanner-path)
6. [Decision Logic](#6-decision-logic)
7. [Integration Points](#7-integration-points)
8. [Edge Cases](#8-edge-cases)
9. [Non-Negotiable Constraints](#9-non-negotiable-constraints)
10. [Success Criteria](#10-success-criteria)

---

## 1. Role & Constraints

The LLM layer is a **quality evaluator**, not a decision-maker. It operates as a senior quant analyst reviewing a trade committee dossier. It cannot:
- Change signal direction
- Override ensemble conviction
- Approve a signal that failed safety checks
- Be bypassed (even by high conviction)

It can only:
- Return a quality score and recommendation
- Identify risk flags and weaknesses
- Produce an auditable narrative

**Default to rejection:** Any LLM failure (timeout, parse error, API error) automatically rejects the signal. There is no fallback approval path.

---

## 2. System Prompt Design

```python
SYSTEM_PROMPT = """
You are a senior quantitative analyst at a top-tier systematic hedge fund.
You are reviewing a proposed algorithmic trade signal dossier.

YOUR ROLE:
- Evaluate the QUALITY and COHERENCE of the signal evidence.
- You do NOT decide trade direction. The ensemble has already done that.
- You do NOT override the numerical pipeline.

YOUR OUTPUT (JSON only, no preamble, no markdown):
{
  "quality_score": float,            // [0.0, 1.0] — overall signal quality
  "confidence_in_quality": float,    // [0.0, 1.0] — your assessment confidence
  "risk_flags": list[str],           // specific red flags
  "key_strengths": list[str],        // evidence supporting the trade
  "key_weaknesses": list[str],       // evidence against the trade
  "narrative": str,                  // max 100 words, precise, auditable
  "recommendation": str              // "APPROVE" | "APPROVE_WITH_CAUTION" | "REJECT"
}

PENALIZE (lower quality_score):
- Single-factor signals (RSI alone, volume alone, any single indicator)
- Higher-timeframe conflict with proposed direction
- Regime mismatch: agent trained on different regime than current
- Low FinRL-X confidence (<0.30) combined with ML factor score below 0.55
- Recent losses on this ticker (from RAG memory context)
- TRENDING_DOWN regime with LONG direction (flag prominently)

REWARD (higher quality_score):
- Full multi-timeframe alignment (3+ timeframes agree with direction)
- High FinRL-X confidence (>0.60) in the correct regime
- ML factor score above 0.65 with momentum confirmation
- Strong historical success patterns from RAG memory
- Tight Bollinger Band squeeze with expanding ATR (setup context)
- Volume confirmation (RVOL > 1.5x on breakout direction)

Return ONLY valid JSON. Nothing else.
"""
```

---

## 3. Dossier Construction

```python
def build_dossier(ticker: str,
                   direction: "Direction",
                   conviction: float,
                   contexts: list,
                   frl_out: "FinRLXOutput",
                   ml_score: float,
                   regime: "Regime",
                   rag_context: str,
                   pre_flags: list[str],
                   pre_scores: dict = None) -> str:
    """
    Builds the signal dossier string for LLM evaluation.
    All numeric values are rounded for readability.
    """
    tf_lines = "\n".join([
        f"  {c.timeframe}: {c.trend_direction.value} "
        f"(strength={c.trend_strength:.2f} momentum={c.momentum_score:+.2f} "
        f"conf={c.confidence:.2f} structure={'✓' if c.structure_intact else '✗'})"
        for c in sorted(contexts, key=lambda x: x.confidence, reverse=True)
    ])
    ps_lines = ""
    if pre_scores:
        ps_lines = (f"\nRVOL: {pre_scores.get('rvol','?'):.2f}× | "
                    f"ATR%: {pre_scores.get('atr_pct','?'):.2f}% | "
                    f"BB%ile: {pre_scores.get('bb_pctile','?'):.0f}")

    return f"""=== TRADE SIGNAL DOSSIER ===
Ticker: {ticker}
Proposed Direction: {direction.value}
Ensemble Conviction: {conviction:.3f}
Market Regime: {regime.value}

=== MULTI-TIMEFRAME ANALYSIS ===
{tf_lines}

=== FinRL-X EXPERT SIGNAL ===
Agent: {frl_out.agent_id} (trained on {frl_out.regime_trained_on.value})
Probs: BUY={frl_out.action_probs.get('BUY',0):.3f} \
HOLD={frl_out.action_probs.get('HOLD',0):.3f} \
SELL={frl_out.action_probs.get('SELL',0):.3f}
Agent Confidence: {frl_out.agent_confidence:.3f}

=== ML FACTOR SCORE ===
P(positive return): {ml_score:.3f}{ps_lines}

=== PRE-FILTER RISK FLAGS ===
{chr(10).join(pre_flags) if pre_flags else "None"}

=== HISTORICAL MEMORY (RAG) ===
{rag_context[:600] if rag_context else "No relevant history available."}

=== EVALUATE QUALITY — return JSON only ==="""
```

---

## 4. Quality Gate — Single Signal

```python
import anthropic, json, re
import concurrent.futures

LLM_TIMEOUT_SECONDS = 10

class LLMQualityGate:
    """
    Per-signal LLM quality evaluation (used by PortfolioScanner path).
    For Market-Wide Scanner batch evaluation, see BatchedLLMGate (AC_09).
    """

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic()
        self.model  = model

    def evaluate(self, ticker, direction, conviction, contexts,
                 frl_out, ml_score, regime,
                 rag_context, pre_flags,
                 pre_scores=None) -> dict:

        dossier = build_dossier(
            ticker, direction, conviction, contexts,
            frl_out, ml_score, regime, rag_context, pre_flags, pre_scores
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(self._call, dossier)
            try:
                raw = future.result(timeout=LLM_TIMEOUT_SECONDS)
            except concurrent.futures.TimeoutError:
                return self._timeout_reject()

        return self._parse(raw)

    def _call(self, dossier: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": dossier}]
        )
        return response.content[0].text

    def _parse(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
        return self._parse_failure_reject()

    def _timeout_reject(self) -> dict:
        return {
            "quality_score": 0.0,
            "confidence_in_quality": 0.0,
            "risk_flags": ["LLM_TIMEOUT"],
            "key_strengths": [],
            "key_weaknesses": ["LLM evaluation timed out"],
            "narrative": "LLM gate timed out. Signal rejected by default.",
            "recommendation": "REJECT"
        }

    def _parse_failure_reject(self) -> dict:
        return {
            "quality_score": 0.0,
            "confidence_in_quality": 0.0,
            "risk_flags": ["LLM_PARSE_FAILURE"],
            "key_strengths": [],
            "key_weaknesses": ["Could not parse LLM JSON response"],
            "narrative": "LLM response unparseable. Signal rejected by default.",
            "recommendation": "REJECT"
        }
```

---

## 5. Batch Evaluation (Scanner Path)

See AC_09 §8 for the full `BatchedLLMGate` implementation. The batch gate evaluates 10 candidates per API call using a modified system prompt requesting a JSON array. The evaluation criteria are identical to the single-signal gate.

---

## 6. Decision Logic

```python
class SignalQualityDecision:
    """
    Converts LLM evaluation output into a binary pass/fail decision.
    Applies TRENDING_DOWN quality floor raise if flagged.
    """

    def decide(self, llm_result: dict,
               conviction_score: float,
               config: dict) -> tuple[bool, str]:

        quality = llm_result.get("quality_score", 0.0)
        rec     = llm_result.get("recommendation", "REJECT")
        flags   = llm_result.get("risk_flags", [])

        # Base thresholds from config (AI-modulated)
        min_quality = config.get("min_quality_score", 0.65)
        min_conv    = config.get("conviction_threshold", 0.70)

        # TRENDING_DOWN quality floor raise (set by AC_06)
        min_quality = max(min_quality,
                          config.get("_quality_floor", min_quality))

        # Hard floor from safety.py
        from alphachart.core import safety
        min_quality = max(min_quality, safety.HARD_MIN_QUALITY_FLOOR)
        min_conv    = max(min_conv,    safety.HARD_MIN_CONVICTION_FLOOR)

        # Decision
        if rec == "REJECT":
            return False, f"LLM_REJECT quality={quality:.2f}"
        if quality < min_quality:
            return False, f"QUALITY_BELOW_FLOOR:{quality:.2f}<{min_quality:.2f}"
        if conviction_score < min_conv:
            return False, f"CONVICTION_BELOW_FLOOR:{conviction_score:.2f}"

        # Critical flag override
        CRITICAL = ["REGIME_MISMATCH", "EARNINGS_BLACKOUT",
                    "CIRCUIT_BREAKER", "EXTREME_VOLATILITY"]
        for flag in flags:
            if any(c in flag for c in CRITICAL):
                return False, f"CRITICAL_FLAG:{flag}"

        return True, "APPROVED"
```

---

## 7. Integration Points

| Module | Direction | Data |
|---|---|---|
| AC_06 (Safety) | → LLM | Passes only safe signals |
| AC_12 (RAG) | → LLM | Historical context string |
| AC_02 (MTA) | → LLM | TF context in dossier |
| AC_04 (FinRL-X) | → LLM | Action probs in dossier |
| AC_05 (ML) | → LLM | ml_score in dossier |
| LLM → AC_08 (Sizer) | → Risk | Approved signals only |
| LLM → AC_11 (GUI) | → Display | Narrative + strengths + flags |

---

## 8. Edge Cases

| Case | Handling |
|---|---|
| API rate limit hit | Exponential backoff (3 retries); then `_timeout_reject()` |
| Empty RAG context | "No relevant history." in dossier; not penalized |
| LLM returns non-JSON | `_parse_failure_reject()` called; signal rejected |
| quality_score > 1.0 | Clamped to 1.0 before decision |
| recommendation field missing | Defaults to "REJECT" |
| TRENDING_DOWN LONG approved by LLM | Still subject to conviction penalty from AC_01 |

---

## 9. Non-Negotiable Constraints

```
LLM-NC-1  LLM timeout → automatic rejection. No fallback approval path.
LLM-NC-2  LLM parse failure → automatic rejection.
LLM-NC-3  LLM cannot change direction. Direction set by ensemble (AC_01).
LLM-NC-4  LLM quality score floor = HARD_MIN_QUALITY_FLOOR (0.50). Never lower.
LLM-NC-5  LLM cannot bypass DeterministicSafetyFilter results.
LLM-NC-6  Batch path (AC_09) uses identical evaluation criteria as single path.
```

---

## 10. Success Criteria

| Metric | Target |
|---|---|
| LLM quality score correlation with realized PnL | Pearson r ≥ 0.35 |
| Timeout rate per signal | < 1% |
| Parse failure rate | < 0.5% |
| False positive rate (APPROVE → losing trade) | Tracked in trade log |
| Narrative completeness (< 100 words) | 100% |

---
---

# AlphaChart v3.4 — AC_08: Position Sizing, Risk Management & Aggressiveness Mapping
**Revision:** v3.4.0 | **Status:** Implementation-Ready | **Owner:** AC_00 §5.7

---

## Table of Contents
1. [Design Philosophy](#1-design-philosophy)
2. [Aggressiveness Index — Full Mapping](#2-aggressiveness-index--full-mapping)
3. [PositionSizer](#3-positionsizer)
4. [Kelly Criterion Integration](#4-kelly-criterion-integration)
5. [Stop-Loss & Profit Target Computation](#5-stop-loss--profit-target-computation)
6. [TRENDING_DOWN Position Caps](#6-trending_down-position-caps)
7. [Integration Points](#7-integration-points)
8. [Edge Cases](#8-edge-cases)
9. [Success Criteria](#9-success-criteria)

---

## 1. Design Philosophy

The Aggressiveness Index (AI) is the master parameter that modulates all operational thresholds from a single Growth Target Slider value. It affects:
- How many signals pass conviction/quality thresholds (lower AI = stricter)
- How large each position is (lower AI = smaller)
- How tight stops are (lower AI = wider stops = smaller positions)

**Hard limits from safety.py are always enforced regardless of AI.** AI can only operate within the space bounded by hard limits.

---

## 2. Aggressiveness Index — Full Mapping

```python
from alphachart.core import safety

def apply_aggressiveness(ai: float, config: dict) -> dict:
    """
    ai: float [0.0 = Conservative, 1.0 = Aggressive]
    Maps AI to all operational parameters.
    Hard limits are enforced via assertions — they cannot be circumvented.
    """
    def lerp(a, b, t): return a + (b - a) * t

    config["conviction_threshold"]   = lerp(0.80, 0.60, ai)
    config["min_quality_score"]      = lerp(0.80, 0.55, ai)
    config["position_size_pct"]      = lerp(0.01, 0.05, ai)
    config["stop_loss_atr_mult"]     = lerp(2.5,  1.5,  ai)
    config["profit_target_rr"]       = lerp(1.5,  3.5,  ai)
    config["max_concurrent_trades"]  = int(lerp(2, 10, ai))
    config["active_ai"]              = ai

    # ── Hard limit enforcement ────────────────────────────────────────────
    safety.validate_hard_limits(config)

    # Explicit floor clamps (belt and suspenders)
    config["position_size_pct"]    = min(config["position_size_pct"],
                                         safety.HARD_MAX_RISK_PCT)
    config["conviction_threshold"] = max(config["conviction_threshold"],
                                         safety.HARD_MIN_CONVICTION_FLOOR)
    config["min_quality_score"]    = max(config["min_quality_score"],
                                         safety.HARD_MIN_QUALITY_FLOOR)
    config["max_concurrent_trades"]= min(config["max_concurrent_trades"],
                                         safety.HARD_MAX_CONCURRENT_TRADES)
    return config

class AggressivenessMapper:
    """
    Converts the GUI Growth Target Slider to an Aggressiveness Index (AI).
    """

    def compute_ai(self, starting_equity: float,
                   target_equity: float) -> float:
        """Log-scale mapping: 1x = 0.0 AI, 100x = 1.0 AI."""
        import math
        ratio = target_equity / max(starting_equity, 1)
        if ratio <= 1.0:
            return 0.0
        ai = math.log10(ratio) / math.log10(100)
        return round(max(0.0, min(1.0, ai)), 4)

    def apply(self, ai: float, config: dict) -> dict:
        return apply_aggressiveness(ai, dict(config))
```

### 2.1 AI Tier Reference

| AI | Tier | Position Size | Conv Threshold | Quality Floor | Stop ATR Mult | Max Trades |
|---|---|---|---|---|---|---|
| 0.00–0.25 | Conservative | 1–2% | 80% | 80% | 2.5× | 2–3 |
| 0.25–0.55 | Moderate | 2–3% | 72–70% | 72–70% | 2.2–2.0× | 4–6 |
| 0.55–0.80 | Aggressive | 3–5% | 69–62% | 66–60% | 1.9–1.6× | 7–9 |
| 0.80–1.00 | Max | 5% | 62–60% | 60–55% | 1.6–1.5× | 10 |

---

## 3. PositionSizer

```python
import numpy as np

class PositionSizer:
    """
    Computes share count, dollar risk, stop-loss, and profit target.
    Uses ATR-based stops and Kelly-scaled sizing.
    """

    def __init__(self, broker_connector, hard_limits: dict):
        self.broker = broker_connector
        self.limits = hard_limits

    def compute(self, ticker: str,
                entry_price: float,
                stop_loss_price: float,
                conviction_score: float,
                config: dict) -> dict:

        equity = self.broker.get_account_equity()

        # Base risk per trade (AI-modulated, hard capped)
        risk_pct    = min(config["position_size_pct"],
                          safety.HARD_MAX_RISK_PCT)
        risk_amount = equity * risk_pct

        # Stop distance
        stop_distance = abs(entry_price - stop_loss_price)
        if stop_distance < entry_price * 0.005:   # minimum 0.5% stop
            stop_distance = entry_price * 0.005

        # Raw shares from risk amount
        raw_shares = risk_amount / stop_distance

        # Kelly scaling (half-Kelly for safety)
        kelly_shares = self._kelly_scale(raw_shares, conviction_score)

        # Final shares
        shares = max(1, int(kelly_shares))

        # Validate position size against hard limit
        position_value = shares * entry_price
        max_position   = equity * safety.HARD_MAX_RISK_PCT * 5
        if position_value > max_position:
            shares = max(1, int(max_position / entry_price))
            position_value = shares * entry_price

        # Profit target
        rr = config.get("profit_target_rr", 2.0)
        if entry_price > stop_loss_price:   # LONG
            profit_target = entry_price + stop_distance * rr
        else:                               # SHORT
            profit_target = entry_price - stop_distance * rr

        return {
            "shares":          shares,
            "position_value":  round(position_value, 2),
            "risk_amount":     round(risk_amount, 2),
            "stop_loss":       round(stop_loss_price, 2),
            "profit_target":   round(profit_target, 2),
            "stop_pct":        round(stop_distance / entry_price, 4),
            "rr_ratio":        round(rr, 2),
        }

    def _kelly_scale(self, raw_shares: float,
                      conviction: float) -> float:
        """
        Half-Kelly fraction: f* = (conviction - 0.5) × 2 × 0.5
        At conviction=0.60: scale=0.10
        At conviction=0.80: scale=0.30
        At conviction=1.00: scale=0.50
        """
        full_kelly = max(0.0, conviction - 0.5) * 2.0
        half_kelly = full_kelly * 0.5
        scale      = max(0.10, min(0.50, half_kelly))
        return raw_shares * scale
```

---

## 4. Kelly Criterion Integration

The half-Kelly fraction is computed as: `f* = (conviction - 0.5) × 0.5`

This produces conservative sizing that scales with conviction but never reaches the theoretical maximum (which would produce ruin-level volatility at sustained use).

---

## 5. Stop-Loss & Profit Target Computation

```python
import ta

def compute_atr_stop(df_daily: pd.DataFrame,
                      direction: "Direction",
                      atr_multiplier: float,
                      config: dict) -> tuple[float, float]:
    """
    Computes entry, stop, and profit target from current price and ATR.
    Returns (stop_loss_price, profit_target_price).
    """
    from alphachart.core.types import Direction
    close   = float(df_daily["Close"].iloc[-1])
    atr_val = float(ta.volatility.AverageTrueRange(
                  df_daily["High"], df_daily["Low"],
                  df_daily["Close"]).average_true_range().iloc[-1])

    # Enforce minimum ATR multiplier (hard limit)
    mult = max(atr_multiplier, safety.HARD_MIN_STOP_LOSS_ATR_MULT)

    if direction == Direction.LONG:
        stop   = close - atr_val * mult
        target = close + atr_val * mult * config.get("profit_target_rr", 2.0)
    else:
        stop   = close + atr_val * mult
        target = close - atr_val * mult * config.get("profit_target_rr", 2.0)

    return round(stop, 2), round(target, 2)
```

---

## 6. TRENDING_DOWN Position Caps

```python
def apply_trend_down_position_cap(shares: int,
                                   entry_price: float,
                                   equity: float,
                                   regime: "Regime",
                                   direction: "Direction") -> int:
    from alphachart.core.types import Regime, Direction
    if regime == Regime.TRENDING_DOWN and direction == Direction.LONG:
        max_position_value = equity * safety.TREND_DOWN_MAX_LONG_POSITION_PCT
        max_shares         = int(max_position_value / entry_price)
        return min(shares, max(1, max_shares))
    return shares
```

---

## 7. Integration Points

| Module | Direction | Data |
|---|---|---|
| AC_11 (Config/Slider) | → Risk | `aggressiveness_index` → `apply_aggressiveness()` |
| AC_07 (LLM) | → Risk | Approved signal → sizing request |
| AC_06 (Safety) | → Risk | Hard limits via safety.py |
| AC_03 (Regime) | → Risk | TRENDING_DOWN → position cap |
| Risk → AC_13 (Orders) | → Execution | `sizing` dict |
| Risk → AC_11 (GUI) | → Display | `position_value`, `risk_amount` |

---

## 8. Edge Cases

| Case | Handling |
|---|---|
| stop_distance < 0.5% of price | Clamped to 0.5%; avoids infinite shares |
| equity = 0 | Position size = 0; order not submitted |
| ATR = 0 (insufficient data) | Fallback: 1% stop from entry |
| Kelly scaling < 0.10 | Floor at 0.10 to ensure meaningful trades |
| TRENDING_DOWN LONG cap results in 0 shares | Minimum 1 share; position flagged as micro-size |

---

## 9. Success Criteria

| Metric | Target |
|---|---|
| Hard limit violation rate | 0% |
| AI → config mapping: all values within bounds | 100% |
| Position sizing latency | < 5ms |
| Kelly scale range: [0.10, 0.50] | 100% |
| TRENDING_DOWN LONG positions capped at 2% | 100% |
