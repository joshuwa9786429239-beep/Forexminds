````markdown name=INTEGRATION_GUIDE.md
# ForexMind v2 — Integration Guide

## Overview
This guide explains how to integrate the new Enhancement modules into your ForexMind trading bot.

---

## 🎯 Enhancement 1: Debate Output Format
**Status:** ✅ Already Correct

The `researchers.py` already returns the correct format. No changes needed.

```python
# Already returns this format:
{
    "lean": "BULLISH" | "BEARISH" | "NEUTRAL",
    "confidence": 50-85,
    "transcript": [...],
    "bull_score": float,
    "bear_score": float,
    "technical_bias": "BULLISH" | "BEARISH" | "NEUTRAL",
    "confluence_level": 1-5,
}
```

---

## 🔄 Enhancement 2: Multi-Timeframe Confluence Scoring

**File:** `data/confluence.py`

### Integration in `main.py`

Add after step 3 (indicators calculation):

```python
# -- Step 3b: Calculate confluence score ----
from data.confluence import get_confluence_info

confluence_info = get_confluence_info(indicators)
print(f"\n  Confluence Score: {confluence_info['confluence_score']}/100")
print(f"  Alignment: {confluence_info['trend_alignment']}")
print(confluence_info['analysis'])

confluence_multiplier = confluence_info['position_multiplier']
```

### Use in Step 7 (Execution Pipeline)

Adjust position size based on confluence:

```python
# -- Step 7: Execution pipeline (modified) ----
try:
    decision = await run_execution_pipeline(pair, analysis, debate_result, history, llm)
    
    # Apply confluence multiplier
    base_size = decision.get("position_size", DEFAULT_LOT_SIZE)
    adjusted_size = base_size * confluence_multiplier
    decision["position_size"] = adjusted_size
    
    print(f"    Position: {base_size} lots → {adjusted_size:.3f} lots (confluence adjusted)")
except Exception as e:
    print(f"  [Main] Execution error: {e}")
    decision = {"action": "HOLD", "confidence": 0, "position_size": 0}
```

---

## 🌍 Enhancement 3: Session-Aware Trading

**File:** `utils/session.py`

### Integration in `main.py`

Add at the start of `analyze_pair()`:

```python
# -- Step 0: Check session suitability ----
from utils.session import SessionManager

session, session_info = SessionManager.get_current_session()
print(f"\n  📍 Session: {session.upper()} ({session_info['quality']})")

if not SessionManager.should_trade_in_session(session):
    print(f"  ⛔ Low-liquidity session. Skipping {pair}.")
    return None
```

### Integration in `run_auto.py`

Replace the loop:

```python
# -- Enhanced version with session awareness ----
from utils.session import SessionManager

session, session_info = SessionManager.get_current_session()
print(f"\n  📍 Current Session: {session.upper()}")
print(f"     Quality: {session_info['quality']}")
print(f"     Position Multiplier: {session_info['position_multiplier']:.0%}")

if not SessionManager.should_trade_in_session(session):
    print(f"  ⛔ Trading disabled in {session} session")
    time.sleep(INTERVAL)
    continue

for pair in PAIRS:
    optimal = "✓" if SessionManager.is_pair_optimal_for_session(pair, session) else "⚠"
    print(f"\n  {optimal} Running {pair}...")
    subprocess.run(["python", "main.py", "--pair", pair, "--rounds", "2"])
    time.sleep(10)
```

---

## 📅 Enhancement 4: Economic Calendar Filter

**File:** `utils/calendar.py`

### Integration in `main.py` (Step 1)

Add before fetching data:

```python
# -- Step 1b: Check for economic events ----
from utils.calendar import EconomicCalendar

should_skip, reason, mins = EconomicCalendar.should_skip_trade(pair)
if should_skip:
    print(f"  📅 SKIPPING: {reason}")
    EconomicCalendar.send_calendar_alert(pair, True, reason, telegram)
    return None

# Also show upcoming events
upcoming = EconomicCalendar.get_upcoming_events(pair, hours_ahead=24)
if upcoming:
    print(f"  📅 Upcoming events for {pair}:")
    for evt in upcoming:
        print(f"     • {evt['event']} ({evt['impact']}) in {evt['hours_until']:.1f}h")
```

---

## 📊 Enhancement 6: ATR-Based Trailing Stop

**File:** `trailing_stop_atr.py`

### Run as Background Process

```bash
# Terminal 1 - Main bot
python run_auto_enhanced.py

# Terminal 2 - ATR trailing stop monitor
python trailing_stop_atr.py
```

### Key Improvements Over Fixed Trailing

| Feature | Fixed (20 pips) | ATR-Based (1.5x) |
|---------|-----------------|------------------|
| EUR/USD Volatility | 20 pips always | ~30-50 pips (adapts) |
| USD/JPY Volatility | 20 pips always | ~20-30 pips (adapts) |
| XAU/USD (Gold) | 20 pips always | ~40-80 pips (adapts to spike swings) |
| Breakeven Lock | 15 pips | 15 pips (same) |

---

## 🌙 Enhancement 7: Auto Close at Day End

**File:** `run_auto_enhanced.py`

### Features

- ✅ Automatically closes all positions at **21:00 GMT** (before daily rollover)
- ✅ Avoids overnight swap charges
- ✅ Resumes trading at **8:30 GMT** (London open)
- ✅ Respects session-aware trading rules
- ✅ Sends Telegram alerts

### Usage

```bash
# Use enhanced version instead of run_auto.py
python run_auto_enhanced.py
```

**Console Output:**
```
[14:30 GMT] AUTO RUN #45
📍 CURRENT SESSION: OVERLAP
     Quality: OPTIMAL
     Position Multiplier: 100%
✓ Trading enabled in overlap session

[21:05 GMT] AUTO RUN #61
⏰ TIME TO CLOSE (21:00+ GMT) — Closing all positions...
✓ All positions closed for the day
⏳ Waiting for London open (8:30 GMT)...
```

---

## 📊 Enhancement 8: Backtesting Module

**File:** `backtest/run_backtest.py`

### Test Strategy Before Trading

```bash
# Single pair
python backtest/run_backtest.py --pair EUR_USD --days 30

# Different pair
python backtest/run_backtest.py --pair GBP_USD --days 60
```

### Expected Output

```
============================================================
  BACKTEST RESULTS: EUR_USD
  Period: 30 days
============================================================

  Trades:              142
  Wins / Losses:       98 / 44
  Win Rate:            69.0%
  Total Pips:          1245.5
  Avg Pips/Trade:      8.8

  Starting Equity:     $1000.00
  Ending Equity:       $2450.00
  Total P&L:           $1450.00
  Return:              145.0%

  Max Drawdown:        $325.00 (13.2%)
  Sharpe Ratio:        1.85

============================================================
```

---

## 🎯 Enhancement 9: Confidence Calibration

**File:** `memory/calibrator.py`

### Track Trade Accuracy

After each closed trade, record result:

```python
from memory.calibrator import ConfidenceCalibrator

calibrator = ConfidenceCalibrator()

# Record a closed trade
calibrator.add_trade_result(
    pair="EUR_USD",
    predicted_confidence=72,
    actual_result="WIN",  # or "LOSS"
    pnl=50.0  # in dollars
)
```

### Generate Calibration Report

```bash
python memory/calibrator.py
```

### Report Example

```
CONFIDENCE CALIBRATION REPORT
================================================================

  EUR_USD:
  ─────────────────────────────────────────────────────────────
    Trades Analyzed:        20
    Actual Win Rate:        68.5%
    Avg Predicted Conf:     71.2%
    Total P&L:              $425.50

    CALIBRATION ACCURACY:
      Status:               WELL_CALIBRATED
      Avg Error:           4.2%

    CONFIDENCE BUCKETS:
      50-55%  :  48.0% win rate (6 trades)
      55-60%  :  66.7% win rate (12 trades)
      60-65%  :  75.0% win rate (8 trades)
      70-75%  :  83.3% win rate (12 trades)

    RECOMMENDATIONS:
      ✓ Calibration is good. No adjustments needed.

================================================================
```

---

## 📋 Integration Checklist

### Phase 1: Core Enhancements (Week 1)
- [ ] Deploy `data/confluence.py` (Enhancement 2)
- [ ] Test confluence scoring in demo mode
- [ ] Verify position sizing adjustments

### Phase 2: Risk Management (Week 2)
- [ ] Deploy `utils/session.py` (Enhancement 3)
- [ ] Deploy `utils/calendar.py` (Enhancement 4)
- [ ] Deploy `trailing_stop_atr.py` (Enhancement 6)
- [ ] Test with demo account

### Phase 3: Automation (Week 3)
- [ ] Deploy `run_auto_enhanced.py` (Enhancement 7)
- [ ] Verify day-end close functionality
- [ ] Monitor for 7 days in demo

### Phase 4: Analytics (Week 4)
- [ ] Deploy `backtest/run_backtest.py` (Enhancement 8)
- [ ] Deploy `memory/calibrator.py` (Enhancement 9)
- [ ] Run initial backtest on 30 days of data
- [ ] Track confidence accuracy for 50+ trades

---

## 🧪 Testing Workflow

### 1. Demo Mode Testing

```bash
# Terminal 1: Run enhanced auto-runner
python run_auto_enhanced.py

# Terminal 2: Monitor trailing stops (separate terminal)
python trailing_stop_atr.py

# Terminal 3: Monitor calibration (separate terminal)
# Update memory/calibrator.py with real results
watch -n 300 'python memory/calibrator.py'
```

### 2. Verify Integrations

```bash
# Check confluence scoring works
python -c "from data.confluence import confluence_score; print('✓ Confluence OK')"

# Check session detection
python -c "from utils.session import SessionManager; SessionManager.print_session_info()"

# Check calendar events
python -c "from utils.calendar import EconomicCalendar; EconomicCalendar.print_calendar()"
```

### 3. Backtest Before Live

```bash
# Always backtest new parameters
python backtest/run_backtest.py --pair EUR_USD --days 60
```

---

## ⚙️ Configuration

### config/settings.py - Add Session Config

```python
# ── Trading Sessions ──────────────────────────────────────
PREFERRED_SESSIONS = ["london", "newyork", "overlap"]
AVOID_SESSIONS = ["asian"]
POSITION_MULTIPLIER_ENABLED = True

# ── Economic Calendar ──────────────────────────────────────
SKIP_TRADES_BEFORE_NEWS = 30  # minutes
SKIP_TRADES_AFTER_NEWS = 30   # minutes

# ── ATR Trailing Stop ──────────────────────────────────────
ATR_TRAILING_ENABLED = True
ATR_MULTIPLIER = 1.5
BREAKEVEN_AFTER_PIPS = 15
```

---

## 🐛 Troubleshooting

### Issue: Confluence Score Always 50
**Solution:** Check that `indicators_by_timeframe` is being passed correctly with both H1 and H4 data.

### Issue: Session Detection Not Working
**Solution:** Verify `datetime.utcnow()` returns correct UTC time. Check system time zone.

### Issue: Economic Events Not Blocking
**Solution:** Economic calendar currently uses simulated events. For production, integrate forexfactory.com API.

### Issue: ATR Trailing Not Moving SL
**Solution:** Ensure MT5 is running and connected. Check MAGIC_NUMBER matches in both `mt5_executor.py` and `trailing_stop_atr.py` (both 234000).

---

## 📚 Full Integration Example

**Complete `main.py` modifications:**

```python
# Add imports at top
from data.confluence import get_confluence_info
from utils.session import SessionManager
from utils.calendar import EconomicCalendar

async def analyze_pair(pair, rounds, llm, fetcher, executor, telegram, memory):
    """Full analysis with all enhancements."""
    
    print_separator(f"Analyzing {pair}")
    
    # -- ENHANCEMENT 3: Session Check ----
    session, session_info = SessionManager.get_current_session()
    if not SessionManager.should_trade_in_session(session):
        print(f"  [Main] {session} session - skipping {pair}")
        return None
    
    # -- ENHANCEMENT 4: Economic Calendar ----
    should_skip, reason, mins = EconomicCalendar.should_skip_trade(pair)
    if should_skip:
        print(f"  [Main] SKIPPING: {reason}")
        telegram.send_signal(pair, "HOLD", 0, f"Economic event: {reason}")
        return None
    
    # ... existing steps 1-3 ...
    
    # -- ENHANCEMENT 2: Confluence Scoring ----
    confluence_info = get_confluence_info(indicators)
    confluence_mult = confluence_info['position_multiplier']
    print(f"  [Main] Confluence: {confluence_info['confluence_score']}/100 ({confluence_mult:.0%} size)")
    
    # ... existing steps 4-6 ...
    
    # -- ENHANCEMENT 2: Apply confluence to position size ----
    try:
        decision = await run_execution_pipeline(pair, analysis, debate_result, history, llm)
        base_size = decision.get("position_size", DEFAULT_LOT_SIZE)
        adjusted_size = base_size * confluence_mult
        decision["position_size"] = adjusted_size
    except Exception as e:
        print(f"  [Main] Execution error: {e}")
        decision = {"action": "HOLD", "confidence": 0, "position_size": 0}
    
    # ... rest of main.py unchanged ...
```

---

## 📞 Support

For issues or questions about integrations:
1. Check the troubleshooting section above
2. Review the enhancement files' inline documentation
3. Run test scripts in isolation to diagnose

---

**Last Updated:** 2026-05-14
**Version:** v2.0 (All 10 Enhancements)
````
