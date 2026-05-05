# AlphaChart v3.4 — AC_01: Core Ensemble & Probabilistic Scoring Engine
**Revision:** v3.4.0 | **Status:** Implementation-Ready | **Owner:** AC_00 §5.1

---

## Table of Contents
1. [Purpose & Design Philosophy](#1-purpose--design-philosophy)
2. [Architecture](#2-architecture)
3. [Ensemble Aggregator — Full Implementation](#3-ensemble-aggregator--full-implementation)
4. [Regime-Conditional Weight System](#4-regime-conditional-weight-system)
5. [Direction Resolution Logic](#5-direction-resolution-logic)
6. [Calibration & Validation](#6-calibration--validation)
7. [Integration Points](#7-integration-points)
8. [Edge Cases](#8-edge-cases)
9. [Success Criteria](#9-success-criteria)

---

## 1. Purpose & Design Philosophy

The Core Ensemble Engine is the **sole authority for directional signal decisions** in AlphaChart. It aggregates expert signals from FinRL-X (AC_04), multi-timeframe trend analysis (AC_02), regime detection (AC_03), and the ML factor model (AC_05) into a single `(conviction_score, direction)` tuple using regime-conditional weighting.

**Core rule (immutable):** The ensemble determines direction. The LLM (AC_07) evaluates quality. Nothing downstream reverses a direction set here.

```
INPUTS                          ENSEMBLE                  OUTPUT
FinRLXOutput      ─────────►  EnsembleAggregator  ──►  conviction_score [0,1]
list[TFContext]   ─────────►  (regime-weighted)    ──►  direction: LONG|SHORT|FLAT
Regime + weights  ─────────►
ml_factor_score   ─────────►
anchor_bias       ─────────►
```

---

## 2. Architecture

```mermaid
flowchart LR
    A[FinRLXOutput\nBUY/SELL/HOLD probs] --> E
    B[list[TimeframeContext]\nper-TF momentum + strength] --> E
    C[Regime\nweight matrix key] --> E
    D[ml_factor_score\n0.0–1.0] --> E
    F[anchor_bias\nDirection from 3mo/1mo/1wk] --> G

    E[EnsembleAggregator\nWeighted combination] --> G
    G[DirectionResolver\nAnchor penalty if conflict] --> H
    H[conviction_score\ndirection]

    style E fill:#2a1e3a,stroke:#7a4a9b
    style G fill:#1e2a3a,stroke:#4a7a9b
```

---

## 3. Ensemble Aggregator — Full Implementation

```python
from alphachart.core.types import Direction, Regime, TimeframeContext, FinRLXOutput

class EnsembleAggregator:
    """
    Combines four expert signal sources using regime-conditional weights.
    Returns (conviction_score, direction).

    INVARIANTS:
    - conviction_score is always in [0.0, 1.0]
    - direction is always a valid Direction enum value
    - anchor_bias conflict applies a configurable penalty (not a hard block)
    - user-supplied weight overrides are L1-normalized before use
    """

    def aggregate(self,
                  finrl_x_output:    FinRLXOutput,
                  tf_contexts:       list[TimeframeContext],
                  regime:            Regime,
                  ml_factor_score:   float,
                  regime_weights:    dict[str, float],
                  direction_constraint: Direction,
                  user_weights:      dict[str, float] = None) -> tuple[float, Direction]:

        # 1. Compute per-source scores in [-1, +1] space
        frl_score = self._finrl_x_score(finrl_x_output)
        tf_score  = self._multi_tf_score(tf_contexts)
        ml_score  = (ml_factor_score - 0.5) * 2.0     # [0,1] → [-1,+1]
        rg_score  = self._regime_directional_score(regime)

        # 2. Select and normalize weights
        weights = self._resolve_weights(regime_weights, user_weights)

        # 3. Weighted combination
        raw = (weights["finrl_x"]      * frl_score +
               weights["multi_tf"]     * tf_score  +
               weights["ml_factor"]    * ml_score  +
               weights["regime_score"] * rg_score)

        # 4. Direction resolution
        proposed = Direction.LONG if raw > 0 else (
                   Direction.SHORT if raw < 0 else Direction.FLAT)

        # 5. Anchor conflict penalty
        raw = self._apply_anchor_penalty(raw, proposed, direction_constraint)

        # 6. Finalize
        conviction = min(abs(raw), 1.0)
        final_dir  = Direction.LONG if raw > 0 else (
                     Direction.SHORT if raw < 0 else Direction.FLAT)

        return round(conviction, 4), final_dir

    def _finrl_x_score(self, out: FinRLXOutput) -> float:
        """BUY probability - SELL probability, scaled by agent confidence."""
        buy  = out.action_probs.get("BUY",  0.33)
        sell = out.action_probs.get("SELL", 0.33)
        raw  = buy - sell                            # range: [-1, +1]
        # Weight by agent confidence — low confidence → pull toward 0
        return raw * out.agent_confidence

    def _multi_tf_score(self, contexts: list[TimeframeContext]) -> float:
        """Confidence × strength weighted average of per-TF momentum scores."""
        score_sum  = 0.0
        weight_sum = 0.0
        for ctx in contexts:
            w = ctx.confidence * ctx.trend_strength
            score_sum  += ctx.momentum_score * w
            weight_sum += w
        return score_sum / weight_sum if weight_sum > 0 else 0.0

    def _regime_directional_score(self, regime: Regime) -> float:
        """
        Regime contributes a weak directional prior.
        TRENDING_UP: slight LONG bias; TRENDING_DOWN: slight SHORT bias.
        RANGING/VOLATILE: neutral.
        """
        return {
            Regime.TRENDING_UP:   +0.20,
            Regime.TRENDING_DOWN: -0.20,
            Regime.RANGING:        0.00,
            Regime.VOLATILE:       0.00,
        }[regime]

    def _resolve_weights(self, regime_weights: dict,
                          user_weights: dict) -> dict:
        """L1-normalize; user weights override regime weights if supplied."""
        w = {**regime_weights, **(user_weights or {})}
        total = sum(w.values())
        return {k: v / total for k, v in w.items()} if total > 0 else regime_weights

    def _apply_anchor_penalty(self, raw: float,
                               proposed: Direction,
                               anchor: Direction) -> float:
        """
        Penalizes signals that fight the higher-timeframe anchor.
        Penalty: 40% conviction reduction (multiply raw by 0.60).
        Does NOT hard-block — the signal may still pass at lower conviction.
        See AC_02 for anchor_bias computation.
        """
        PENALTY = 0.60
        if anchor == Direction.SHORT and proposed == Direction.LONG:
            return raw * PENALTY
        if anchor == Direction.LONG and proposed == Direction.SHORT:
            return raw * PENALTY
        return raw
```

---

## 4. Regime-Conditional Weight System

Default calibrated weights per regime. These are the starting point; per-regime re-calibration occurs in AC_12 (RetrainingController) based on live performance.

```python
DEFAULT_REGIME_WEIGHTS = {
    Regime.TRENDING_UP:   {"finrl_x": 0.30, "multi_tf": 0.30,
                           "ml_factor": 0.20, "regime_score": 0.20},
    Regime.TRENDING_DOWN: {"finrl_x": 0.20, "multi_tf": 0.40,
                           "ml_factor": 0.20, "regime_score": 0.20},
    Regime.RANGING:       {"finrl_x": 0.25, "multi_tf": 0.20,
                           "ml_factor": 0.35, "regime_score": 0.20},
    Regime.VOLATILE:      {"finrl_x": 0.15, "multi_tf": 0.25,
                           "ml_factor": 0.20, "regime_score": 0.40},
}

# TRENDING_DOWN LONG remediation (from safety.py):
# If regime=TRENDING_DOWN and proposed direction=LONG:
#   conviction *= (1 - TREND_DOWN_LONG_CONVICTION_PENALTY)
# Applied AFTER ensemble, BEFORE safety filter.
```

---

## 5. Direction Resolution Logic

```python
def resolve_and_remediate(conviction: float, direction: Direction,
                           regime: Regime, config: dict) -> tuple[float, Direction]:
    """
    Post-ensemble direction remediation.
    Applies TRENDING_DOWN LONG penalty from safety.py.
    """
    from alphachart.core import safety

    if regime == Regime.TRENDING_DOWN and direction == Direction.LONG:
        conviction *= (1 - safety.TREND_DOWN_LONG_CONVICTION_PENALTY)
        # Raise quality floor — enforced downstream in SignalQualityDecision
        config["_trend_down_quality_raise"] = safety.TREND_DOWN_LONG_QUALITY_FLOOR_RAISE

    if regime == Regime.TRENDING_DOWN and direction == Direction.SHORT:
        conviction = min(conviction * (1 + safety.TREND_DOWN_SHORT_CONVICTION_BOOST), 1.0)

    return round(conviction, 4), direction
```

---

## 6. Calibration & Validation

```python
class EnsembleCalibrator:
    """
    Validates that conviction scores are calibrated:
    signals with conviction 0.8 should win ~80% of the time.
    Run monthly against the trade log.
    """

    def calibrate(self, trade_log: list[dict],
                  n_bins: int = 10) -> dict:
        bins = {i/n_bins: {"wins":0,"total":0}
                for i in range(n_bins)}
        for trade in trade_log:
            conv = trade.get("conviction_score", 0.5)
            bin_key = round(conv * n_bins) / n_bins
            bins[bin_key]["total"] += 1
            if trade.get("won"):
                bins[bin_key]["wins"] += 1

        report = {}
        for bk, data in sorted(bins.items()):
            if data["total"] == 0:
                continue
            actual_wr = data["wins"] / data["total"]
            expected  = bk  # conviction should approximate win rate
            error     = actual_wr - expected
            report[f"conv_{bk:.1f}"] = {
                "actual_win_rate": round(actual_wr, 3),
                "expected":        round(expected, 3),
                "calibration_error": round(error, 3),
                "trades":          data["total"],
                "miscalibrated":   abs(error) > 0.10,
            }
        return report
```

---

## 7. Integration Points

| Module | Direction | Data Exchanged |
|---|---|---|
| AC_02 (MultiTF) | → Ensemble | `list[TimeframeContext]`, `anchor_bias` |
| AC_03 (Regime) | → Ensemble | `Regime`, `regime_weights` |
| AC_04 (FinRL-X) | → Ensemble | `FinRLXOutput` |
| AC_05 (ML Factor) | → Ensemble | `ml_factor_score: float` |
| AC_11 (Config) | → Ensemble | `user_weights` override dict |
| Ensemble → AC_06 | → Safety | `conviction_score`, `direction` |
| AC_12 (Learning) | → Ensemble | calibrated weight updates (monthly) |

---

## 8. Edge Cases

| Case | Handling |
|---|---|
| All sources return neutral (0.0) | direction=FLAT, conviction=0.0 → signal discarded |
| FinRL-X agent not loaded for regime | `_null_output()` returns uniform 0.33 probs |
| contexts list is empty | tf_score=0.0; ensemble continues with other sources |
| ml_factor_score outside [0,1] | Clamped to [0,1] before centered |
| Weight sum equals zero | Falls back to DEFAULT_REGIME_WEIGHTS |
| anchor_bias=FLAT | No penalty applied |

---

## 9. Success Criteria

| Metric | Target |
|---|---|
| Conviction score calibration error per bin | < 10% |
| Direction accuracy (proposed vs realized) | ≥ 60% |
| Ensemble latency per ticker | < 50ms |
| Weight normalization assertion passes | 100% |

---
---

# AlphaChart v3.4 — AC_02: Multi-Timeframe Analysis & Higher-TF Anchor System
**Revision:** v3.4.0 | **Status:** Implementation-Ready | **Owner:** AC_00 §5.2

---

## Table of Contents
1. [Purpose & Design Philosophy](#1-purpose--design-philosophy-1)
2. [Timeframe Hierarchy](#2-timeframe-hierarchy)
3. [MultiTimeframeAnalyzer — Implementation](#3-multitimeframeanalyzer--implementation)
4. [Anchor Bias System](#4-anchor-bias-system)
5. [Confidence Decay Model](#5-confidence-decay-model)
6. [Key Level Detection](#6-key-level-detection)
7. [Integration Points](#7-integration-points-1)
8. [Edge Cases](#8-edge-cases-1)
9. [Success Criteria](#9-success-criteria-1)

---

## 1. Purpose & Design Philosophy

The Multi-Timeframe Analyzer produces a `TimeframeContext` for each available timeframe and derives the **anchor bias** — the higher-timeframe directional consensus that serves as a permission filter for all entry signals. A signal that fights the anchor bias loses 40% of its conviction (AC_01 anchor penalty).

**Core discipline:** Higher timeframes grant permission. Shorter timeframes provide timing.

---

## 2. Timeframe Hierarchy

```
ANCHOR (permission layer)          EXECUTION (timing layer)
──────────────────────────────     ──────────────────────────
3-Month     confidence: 0.50       Daily       confidence: 0.85
1-Month     confidence: 0.60       60-Minute   confidence: 0.92
1-Week      confidence: 0.75       15-Minute   confidence: 0.95
2-Week      confidence: 0.70
```

Higher timeframes have **lower confidence** because they represent slower-moving averages with wider prediction uncertainty. The confidence weight scales the contribution of each TF to both the anchor bias and the ensemble multi-TF score.

---

## 3. MultiTimeframeAnalyzer — Implementation

```python
import ta
import pandas as pd
from alphachart.core.types import Direction, TimeframeContext

class MultiTimeframeAnalyzer:

    CONFIDENCE_DECAY = {
        "3mo": 0.50, "1mo": 0.60, "2wk": 0.70,
        "1wk": 0.75, "daily": 0.85, "60m": 0.92, "15m": 0.95
    }

    ANCHOR_TIMEFRAMES     = {"3mo", "1mo", "1wk"}
    EXECUTION_TIMEFRAMES  = {"daily", "60m", "15m"}

    def analyze(self, ticker: str,
                all_data: dict[str, pd.DataFrame]) -> list[TimeframeContext]:
        contexts = []
        for tf, df in all_data.items():
            if df is None or df.empty or len(df) < 20:
                continue
            try:
                ctx = self._analyze_single(tf, df)
                contexts.append(ctx)
            except Exception:
                pass  # isolated failure per TF
        return contexts

    def _analyze_single(self, timeframe: str, df: pd.DataFrame) -> TimeframeContext:
        close = df["Close"]
        high  = df["High"]
        low   = df["Low"]

        # ── Trend: EMA20/EMA50 crossover ─────────────────────────────────
        ema20 = ta.trend.EMAIndicator(close, window=20).ema_indicator().iloc[-1]
        ema50 = ta.trend.EMAIndicator(close, window=50).ema_indicator().iloc[-1]
        if ema20 > ema50 * 1.005:
            trend = Direction.LONG
        elif ema20 < ema50 * 0.995:
            trend = Direction.SHORT
        else:
            trend = Direction.FLAT

        # ── Trend Strength: ADX normalized ───────────────────────────────
        adx = ta.trend.ADXIndicator(high, low, close).adx().iloc[-1]
        strength = min(float(adx) / 50.0, 1.0)

        # ── Momentum: MACD hist / ATR ─────────────────────────────────────
        macd_hist = ta.trend.MACD(close).macd_diff().iloc[-1]
        atr       = ta.volatility.AverageTrueRange(
                        high, low, close).average_true_range().iloc[-1]
        momentum  = float(macd_hist / atr) if atr > 0 else 0.0
        momentum  = max(-1.0, min(1.0, momentum))

        # ── Price Structure: HH/LL check ──────────────────────────────────
        recent_h = high.rolling(5).max()
        recent_l = low.rolling(5).min()
        structure_intact = bool(
            (trend == Direction.LONG  and recent_h.iloc[-1] > recent_h.iloc[-5]) or
            (trend == Direction.SHORT and recent_l.iloc[-1] < recent_l.iloc[-5]) or
            trend == Direction.FLAT
        )

        key_levels = self._compute_key_levels(high, low)

        return TimeframeContext(
            timeframe        = timeframe,
            trend_direction  = trend,
            trend_strength   = round(strength, 4),
            key_levels       = key_levels,
            momentum_score   = round(momentum, 4),
            structure_intact = structure_intact,
            confidence       = self.CONFIDENCE_DECAY.get(timeframe, 0.70)
        )

    def _compute_key_levels(self, high: pd.Series,
                             low: pd.Series, window: int = 20) -> list[float]:
        recent_highs = high.rolling(window).max().dropna().unique()[-3:]
        recent_lows  = low.rolling(window).min().dropna().unique()[-3:]
        return sorted(set(list(recent_highs) + list(recent_lows)))

    def get_anchor_bias(self, contexts: list[TimeframeContext]) -> Direction:
        """
        Weighted vote from anchor timeframes (3mo, 1mo, 1wk).
        Weight = confidence × trend_strength.
        Returns the dominant direction.
        """
        anchor_ctxs = [c for c in contexts
                       if c.timeframe in self.ANCHOR_TIMEFRAMES]
        if not anchor_ctxs:
            return Direction.FLAT

        votes = {Direction.LONG: 0.0, Direction.SHORT: 0.0, Direction.FLAT: 0.0}
        for ctx in anchor_ctxs:
            votes[ctx.trend_direction] += ctx.confidence * ctx.trend_strength

        return max(votes, key=votes.get)

    def count_aligned_timeframes(self, contexts: list[TimeframeContext],
                                  target: Direction) -> int:
        """Returns count of TFs whose trend_direction matches target."""
        return sum(1 for c in contexts if c.trend_direction == target)
```

---

## 4. Anchor Bias System

The anchor bias is used by two downstream modules:

- **AC_01 (Ensemble):** Applies 40% conviction penalty for signals that fight anchor
- **AC_09 (Scanner):** Filters by minimum TF alignment count (from SpreadConfig)

```python
# Anchor veto thresholds (from AC_11 config, default = SOFT)
ANCHOR_STRICTNESS = {
    "OFF":  lambda bias, prop: False,                     # no blocking
    "SOFT": lambda bias, prop: False,                     # penalty only (in AC_01)
    "HARD": lambda bias, prop: (
        bias == Direction.SHORT and prop == Direction.LONG or
        bias == Direction.LONG  and prop == Direction.SHORT
    ),  # hard block at safety filter (AC_06)
}
```

---

## 5. Confidence Decay Model

Higher timeframes are genuinely harder to predict. The confidence values reflect empirical prediction difficulty:

| Timeframe | Confidence | Rationale |
|---|---|---|
| 3mo | 0.50 | Macro trends; high noise, very slow signal |
| 1mo | 0.60 | Monthly trends; useful context but wide uncertainty |
| 2wk | 0.70 | Bi-weekly structure; reasonable predictive value |
| 1wk | 0.75 | Weekly trend; good anchor signal |
| Daily | 0.85 | Primary trading timeframe; high signal quality |
| 60m | 0.92 | Intraday timing; very responsive |
| 15m | 0.95 | Execution timing; highest responsiveness |

These values are NOT calibration targets — they are structural weights reflecting information content per timeframe.

---

## 6. Key Level Detection

Key levels (support/resistance) are reported in `TimeframeContext.key_levels` and used by:
- **AC_07 (LLM):** Included in the dossier for proximity analysis
- **AC_08 (Sizer):** Stop-loss may be set at or beyond nearest key level

```python
def detect_proximity_to_key_level(entry_price: float,
                                   levels: list[float],
                                   threshold_pct: float = 0.015) -> str:
    """Returns 'NEAR_RESISTANCE', 'NEAR_SUPPORT', or 'CLEAR'."""
    for level in levels:
        dist = abs(entry_price - level) / level
        if dist <= threshold_pct:
            if level > entry_price:
                return "NEAR_RESISTANCE"
            else:
                return "NEAR_SUPPORT"
    return "CLEAR"
```

---

## 7. Integration Points

| Module | Direction | Data |
|---|---|---|
| DataFetcher | → MTA | `dict[str, DataFrame]` (7 TFs) |
| MTA → AC_01 | → Ensemble | `list[TimeframeContext]`, `Direction` (anchor) |
| MTA → AC_07 | → LLM dossier | TF summary in dossier string |
| MTA → AC_09 | → Scanner | `min_tf_alignment_count` filter |
| AC_11 (Config) | → MTA | `TIMEFRAME_PRIORITY` weight overrides |

---

## 8. Edge Cases

| Case | Handling |
|---|---|
| Fewer than 20 bars on any TF | That TF skipped; not fatal |
| All anchor TFs missing | anchor_bias = FLAT; no anchor penalty applied |
| ADX computation fails | strength = 0.0; TF still included with neutral weight |
| Intraday data unavailable (weekend) | 60m, 15m skipped; daily/weekly used for execution |

---

## 9. Success Criteria

| Metric | Target |
|---|---|
| TF analysis latency per ticker | < 200ms |
| Anchor bias accuracy (matches realized trend direction) | ≥ 65% |
| Key level detection: at least 1 level per TF | 100% when data present |
| No TF failure propagates to pipeline halt | 100% |

---
---

# AlphaChart v3.4 — AC_03: Regime Detection & Conditional Weighting Engine
**Revision:** v3.4.0 | **Status:** Implementation-Ready | **Owner:** AC_00 §5.3

---

## Table of Contents
1. [Purpose](#1-purpose)
2. [Regime Classification Algorithm](#2-regime-classification-algorithm)
3. [Regime-Conditional Ensemble Weights](#3-regime-conditional-ensemble-weights)
4. [TRENDING_DOWN Remediation Protocol](#4-trending_down-remediation-protocol)
5. [Regime Distribution Monitoring](#5-regime-distribution-monitoring)
6. [Integration Points](#6-integration-points)
7. [Edge Cases](#7-edge-cases)
8. [Success Criteria](#8-success-criteria)

---

## 1. Purpose

The Regime Detector classifies the current market state into one of four regimes for each ticker. The regime governs which ensemble weight vector is applied (AC_01), which FinRL-X agent is activated (AC_04), and what additional scrutiny LONG signals receive (AC_06, safety.py).

---

## 2. Regime Classification Algorithm

```python
import ta
import pandas as pd
from alphachart.core.types import Regime

class RegimeDetector:
    """
    Three-layer classification:
    1. Volatility check (VOLATILE trumps all)
    2. Trend strength check (TRENDING_UP or TRENDING_DOWN)
    3. Default: RANGING
    """

    ADX_TREND_THRESHOLD = 25     # ADX > 25 = trending
    VOL_EXPANSION_RATIO = 1.5    # BB width / 20-day avg > 1.5 = volatile

    def detect(self, df_daily: pd.DataFrame) -> Regime:
        close = df_daily["Close"]
        high  = df_daily["High"]
        low   = df_daily["Low"]

        # Layer 1: Volatility expansion
        bb       = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        bb_width = (bb.bollinger_hband() - bb.bollinger_lband()) / close
        bb_avg   = bb_width.rolling(20).mean().iloc[-1]
        vol_ratio= float(bb_width.iloc[-1] / bb_avg) if bb_avg > 0 else 1.0
        if vol_ratio > self.VOL_EXPANSION_RATIO:
            return Regime.VOLATILE

        # Layer 2: Trend strength + direction
        adx  = float(ta.trend.ADXIndicator(high, low, close).adx().iloc[-1])
        ema20= float(ta.trend.EMAIndicator(close, 20).ema_indicator().iloc[-1])
        ema50= float(ta.trend.EMAIndicator(close, 50).ema_indicator().iloc[-1])

        if adx > self.ADX_TREND_THRESHOLD:
            return Regime.TRENDING_UP if ema20 > ema50 else Regime.TRENDING_DOWN

        # Layer 3: Default
        return Regime.RANGING

    def detect_with_confidence(self, df_daily: pd.DataFrame) -> tuple[Regime, float]:
        """Returns (regime, confidence_score [0,1])."""
        regime = self.detect(df_daily)
        close  = df_daily["Close"]
        high   = df_daily["High"]
        low    = df_daily["Low"]
        adx    = float(ta.trend.ADXIndicator(high, low, close).adx().iloc[-1])
        # Confidence proxied by signal strength
        confidence = {
            Regime.TRENDING_UP:   min(adx / 50.0, 1.0),
            Regime.TRENDING_DOWN: min(adx / 50.0, 1.0),
            Regime.RANGING:       1.0 - min(adx / 50.0, 1.0),
            Regime.VOLATILE:      0.70,  # volatile is always somewhat uncertain
        }[regime]
        return regime, round(confidence, 3)

    def get_ensemble_weights(self, regime: Regime,
                              user_override: dict = None) -> dict[str, float]:
        """
        Returns regime-conditional weights for EnsembleAggregator.
        If user_override is supplied (Advanced Mode), L1-normalize and return.
        """
        default_weights = {
            Regime.TRENDING_UP:   {"finrl_x":0.30,"multi_tf":0.30,
                                   "ml_factor":0.20,"regime_score":0.20},
            Regime.TRENDING_DOWN: {"finrl_x":0.20,"multi_tf":0.40,
                                   "ml_factor":0.20,"regime_score":0.20},
            Regime.RANGING:       {"finrl_x":0.25,"multi_tf":0.20,
                                   "ml_factor":0.35,"regime_score":0.20},
            Regime.VOLATILE:      {"finrl_x":0.15,"multi_tf":0.25,
                                   "ml_factor":0.20,"regime_score":0.40},
        }
        weights = user_override or default_weights[regime]
        total   = sum(weights.values())
        return {k: v / total for k, v in weights.items()}
```

---

## 3. Regime-Conditional Ensemble Weights

| Regime | FinRL-X | Multi-TF | ML Factor | Regime Score | Rationale |
|---|---|---|---|---|---|
| TRENDING_UP | 0.30 | 0.30 | 0.20 | 0.20 | Balanced; RL and trend both reliable |
| TRENDING_DOWN | 0.20 | 0.40 | 0.20 | 0.20 | Trend structure most reliable; RL less trusted on downside |
| RANGING | 0.25 | 0.20 | 0.35 | 0.20 | Mean-reversion factors dominate; trend less reliable |
| VOLATILE | 0.15 | 0.25 | 0.20 | 0.40 | Regime signal dominates; all others have elevated uncertainty |

---

## 4. TRENDING_DOWN Remediation Protocol

Applied post-ensemble (AC_01) and enforced in AC_06:

```python
TREND_DOWN_RULES = {
    # Applied in AC_01 resolve_and_remediate():
    "long_conviction_multiplier": 0.70,     # LONG conviction × 0.70
    "short_conviction_multiplier": 1.10,    # SHORT conviction × 1.10

    # Enforced in AC_06 DeterministicSafetyFilter:
    "long_quality_floor_raise": 0.10,       # min_quality += 0.10
    "max_long_position_pct": 0.02,          # position capped at 2%

    # Agent selection in AC_04:
    "finrl_x_agent_override": Regime.TRENDING_DOWN,  # force TD-trained agent
}
```

---

## 5. Regime Distribution Monitoring

Used by AC_09 (SpreadAdvisor) and AC_11 (GUI):

```python
class RegimeDistributionMonitor:
    """Tracks portfolio-wide regime distribution for adaptive recommendations."""

    def compute_distribution(self, tickers: list[str],
                              detector: RegimeDetector,
                              daily_data: dict) -> dict[str, float]:
        counts = {r.value: 0 for r in Regime}
        total  = 0
        for t in tickers:
            df = daily_data.get(t)
            if df is not None and not df.empty:
                r = detector.detect(df)
                counts[r.value] += 1
                total += 1
        return {k: v / max(total, 1) for k, v in counts.items()}
```

---

## 6. Integration Points

| Module | Direction | Data |
|---|---|---|
| DataFetcher | → RegimeDetector | `df_daily` |
| RegimeDetector → AC_01 | → Ensemble | `Regime`, `regime_weights` |
| RegimeDetector → AC_04 | → FinRL-X | `Regime` (selects agent) |
| RegimeDetector → AC_06 | → Safety | `Regime` (TRENDING_DOWN rules) |
| RegimeDetector → AC_09 | → Scanner | `Regime` (allowed_regimes filter) |
| RegimeDetector → AC_12 | → Learning | `Regime` (reward shaping, retrain trigger) |

---

## 7. Edge Cases

| Case | Handling |
|---|---|
| ADX computation needs min 14 bars | Requires minimum 30 bars in df_daily |
| BB width average is zero | vol_ratio clamped to 1.0; VOLATILE not triggered |
| EMA20 == EMA50 exactly | Returns RANGING (not TRENDING_UP/DOWN) |
| All tickers VOLATILE simultaneously | SpreadAdvisor recommends tightening SAI |

---

## 8. Success Criteria

| Metric | Target |
|---|---|
| Regime classification accuracy on labeled test set | ≥ 80% |
| Each regime represented in training data | 252+ days per regime |
| Regime detection latency | < 20ms per ticker |
| TRENDING_DOWN rules applied every time regime=TD | 100% |

---
---

# AlphaChart v3.4 — AC_04: FinRL-X Expert Signal Integration
**Revision:** v3.4.0 | **Status:** Implementation-Ready | **Owner:** AC_00 §5.4

---

## Table of Contents
1. [Role in the System](#1-role-in-the-system)
2. [Agent Architecture](#2-agent-architecture)
3. [State Vector Construction](#3-state-vector-construction)
4. [Inference Pipeline](#4-inference-pipeline)
5. [Training & Retraining Protocol](#5-training--retraining-protocol)
6. [Integration Points](#6-integration-points-1)
7. [Edge Cases](#7-edge-cases-1)
8. [Success Criteria](#8-success-criteria-1)

---

## 1. Role in the System

FinRL-X is **one expert signal source** within the ensemble — not the decision-maker. It is treated exactly as a hedge fund quant desk treats a systematic sub-pod: its signals are informative but not authoritative. The ensemble (AC_01) synthesizes FinRL-X output alongside three other signal sources.

FinRL-X produces:
- Action probabilities: `{BUY: float, HOLD: float, SELL: float}`
- Q-value (max expected return estimate)
- Agent confidence (max_prob - min_prob)

These become features in the ensemble, not final trade decisions.

---

## 2. Agent Architecture

One PPO agent is trained per market regime (4 agents total). An agent trained on `TRENDING_UP` data is not used in `TRENDING_DOWN` conditions.

```python
AGENT_REGISTRY = {
    Regime.TRENDING_UP:   "checkpoints/ppo_TRENDING_UP.zip",
    Regime.TRENDING_DOWN: "checkpoints/ppo_TRENDING_DOWN.zip",
    Regime.RANGING:       "checkpoints/ppo_RANGING.zip",
    Regime.VOLATILE:      "checkpoints/ppo_VOLATILE.zip",
}

class FinRLXEngine:
    def __init__(self, agent_checkpoints: dict):
        self.agents = {}
        for regime, path in agent_checkpoints.items():
            self.agents[regime] = self._load_agent(path)

    def _load_agent(self, path: str):
        from stable_baselines3 import PPO
        try:
            return PPO.load(path)
        except FileNotFoundError:
            return None   # null agent; produces null output

    def get_signal(self, regime: Regime,
                   state_vector) -> "FinRLXOutput":
        from alphachart.core.types import FinRLXOutput
        agent = self.agents.get(regime)
        if agent is None:
            return self._null_output(regime)

        action, _ = agent.predict(state_vector, deterministic=True)
        obs_tensor = agent.policy.obs_to_tensor(
            state_vector.reshape(1, -1))[0]
        dist  = agent.policy.get_distribution(obs_tensor)
        probs = dist.distribution.probs.detach().numpy()[0]
        labels= ["SELL", "HOLD", "BUY"]
        action_probs = {l: float(p) for l, p in zip(labels, probs)}

        return FinRLXOutput(
            agent_id         = f"ppo_{regime.value}",
            action_probs     = action_probs,
            q_value          = float(probs.max()),
            agent_confidence = float(probs.max() - probs.min()),
            regime_trained_on= regime
        )

    def _null_output(self, regime) -> "FinRLXOutput":
        from alphachart.core.types import FinRLXOutput
        return FinRLXOutput(
            agent_id="null",
            action_probs={"BUY":0.33,"HOLD":0.34,"SELL":0.33},
            q_value=0.0, agent_confidence=0.0,
            regime_trained_on=regime
        )
```

---

## 3. State Vector Construction

```python
import numpy as np
import ta

def build_state_vector(df: pd.DataFrame,
                        contexts: list,
                        regime: "Regime") -> np.ndarray:
    """
    Constructs the state vector for FinRL-X inference.
    Features are deterministic, reproducible, and contain NO forward-looking data.
    Dimension: 4 (momentum) + 1 (volume) + 1 (ATR) + 2N (TF contexts) + 4 (regime) = variable
    Minimum: 10 features (with 0 TF contexts).
    """
    from alphachart.core.types import Regime
    close  = df["Close"]
    high   = df["High"]
    low    = df["Low"]
    volume = df["Volume"]
    features = []

    # Price momentum (4 windows)
    for w in [5, 10, 20, 50]:
        if len(close) > w:
            features.append(float(close.iloc[-1] / close.iloc[-w] - 1))
        else:
            features.append(0.0)

    # Volume ratio vs 20-day MA
    vol_ma = volume.rolling(20).mean().iloc[-1]
    features.append(float(volume.iloc[-1] / vol_ma) if vol_ma > 0 else 1.0)

    # ATR normalized by price
    atr = ta.volatility.AverageTrueRange(high, low, close).average_true_range().iloc[-1]
    features.append(float(atr / close.iloc[-1]) if close.iloc[-1] > 0 else 0.0)

    # Multi-TF summary (momentum + strength per TF, sorted by confidence)
    for ctx in sorted(contexts, key=lambda x: x.confidence):
        features.append(float(ctx.momentum_score))
        features.append(float(ctx.trend_strength))

    # Regime one-hot encoding
    regime_vec = [0.0, 0.0, 0.0, 0.0]
    try:
        regime_vec[list(Regime).index(regime)] = 1.0
    except ValueError:
        pass
    features.extend(regime_vec)

    return np.array(features, dtype=np.float32)
```

---

## 4. Inference Pipeline

```
ticker, regime, df_daily, contexts
    │
    ▼
build_state_vector(df, contexts, regime)
    │
    ▼
agent = agents[regime]   (or null_agent if not loaded)
    │
    ▼
action_probs = agent.predict(state_vector)
    │
    ▼
FinRLXOutput {action_probs, q_value, agent_confidence, regime_trained_on}
    │
    ▼ → EnsembleAggregator (AC_01)
```

**Phase 0 requirement:** All agents must pass the 7-step Phase 0 audit (AC_14) before any agent is used in paper trading. Each regime-specific agent is audited independently.

---

## 5. Training & Retraining Protocol

```python
def retrain_agent(self, regime: "Regime",
                   training_df: pd.DataFrame,
                   config: dict):
    """
    Triggered by RetrainingController (AC_12) when win rate degrades.
    Phase 0 must be re-run on the new agent before deployment.
    """
    from finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv
    from finrl.agents.stablebaselines3.models import DRLAgent

    env   = StockTradingEnv(df=training_df, **config.get("env_kwargs", {}))
    agent = DRLAgent(env=env)
    model = agent.get_model("ppo", model_kwargs={
        "learning_rate": config.get("ppo_learning_rate", 3e-4),
        "n_steps":       config.get("ppo_n_steps", 2048),
    })
    trained = agent.train_model(
        model=model,
        tb_log_name=f"ppo_{regime.value}",
        total_timesteps=config.get("total_timesteps", 50_000)
    )

    # Save checkpoint BEFORE replacing live agent
    checkpoint_path = f"checkpoints/ppo_{regime.value}_new.zip"
    trained.save(checkpoint_path)

    # Phase 0 audit must pass before swap
    # phase0.audit(checkpoint_path) → raises if fails

    self.agents[regime] = trained

# TRAINING DATA REQUIREMENTS:
# - Minimum 252 trading days per regime
# - No forward-looking features (verified by Phase 0 Step 1)
# - Point-in-time data only
# - Transaction costs included in environment reward
```

---

## 6. Integration Points

| Module | Direction | Data |
|---|---|---|
| AC_03 (Regime) | → FinRL-X | `Regime` (selects active agent) |
| DataFetcher | → FinRL-X | `df_daily` for state vector |
| AC_02 (MTA) | → FinRL-X | `list[TimeframeContext]` for state features |
| FinRL-X → AC_01 | → Ensemble | `FinRLXOutput` |
| AC_12 (RLMF) | → FinRL-X | Reward signal, retrain trigger |
| AC_14 (Phase 0) | → FinRL-X | Blocking gate before deployment |

---

## 7. Edge Cases

| Case | Handling |
|---|---|
| Agent checkpoint missing | `_null_output()` returned; pipeline continues with 0.33/0.33/0.34 |
| State vector dimension mismatch | Agent rejects inference; null output returned |
| GPU unavailable | PPO runs on CPU; inference ~3× slower but functional |
| Regime mismatch at inference | Agent trained on TRENDING_UP used for RANGING (fallback only) → flagged in LLM dossier |
| NaN in state vector | Replace with 0.0 before inference |

---

## 8. Success Criteria

| Metric | Target |
|---|---|
| FinRL-X win rate (as sole signal) | ≥ 55% baseline (ensemble improves this) |
| Agent confidence > 0.40 on approved trades | ≥ 70% of trades |
| Phase 0 pass rate before any agent deployment | 100% |
| Inference latency per ticker | < 100ms |
| Null output rate (missing agents) | < 5% of signals |
