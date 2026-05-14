"""
ForexMind — Bull vs Bear Debate Engine v3 (SUPERBOT FULL)
✅ ENHANCED: Market context awareness + confluence scoring
✅ UPGRADED: Technical confirmation + volatility adjustment
✅ IMPROVED: Smarter confidence calibration for profitability
Features:
  - Multi-round debate with evolving arguments
  - Conviction scoring (STRONG/MODERATE/WEAK)
  - Market context awareness (RSI, trend, EMA, volatility)
  - ATR-based volatility adjustment
  - Technical confirmation filters
  - Pair-specific risk profiles (Gold, GBP special handling)
  - Returns structured dict with transparency
"""

import time
import json
from typing import Dict, List
from utils.llm import GroqClient


def _extract_conviction_score(argument_text: str) -> tuple:
    """
    Parse LLM argument for conviction level and extract key metrics.
    Returns: (conviction_level, score_points)
    """
    text_upper = argument_text.upper()
    
    # Check for explicit conviction declarations
    if "STRONG" in text_upper and "CONVICTION" in text_upper:
        return "STRONG", 2
    elif "STRONG" in text_upper or "HIGHLY CONFIDENT" in text_upper or "COMPELLING" in text_upper:
        return "STRONG", 2
    elif "WEAK" in text_upper or "UNCERTAIN" in text_upper or "QUESTIONABLE" in text_upper:
        return "WEAK", 0
    else:
        return "MODERATE", 1


def _build_market_context(current_indicators: dict = None, pair: str = "UNKNOWN") -> str:
    """
    Build detailed market context from indicators.
    Includes: trend, RSI, EMA positioning, ATR volatility, MACD momentum, pair-specific risks
    """
    if not current_indicators:
        return ""
    
    trend = current_indicators.get("trend", "UNKNOWN")
    rsi = current_indicators.get("rsi", 50)
    price_vs_ema9 = current_indicators.get("price_vs_ema9", 0)
    atr = current_indicators.get("atr", 0)
    macd_signal = current_indicators.get("macd", {}).get("histogram", 0)
    stoch_k = current_indicators.get("stochastic", {}).get("k", 50)
    
    # Interpret indicators
    trend_emoji = "📈 STRONG UP" if trend == "BULLISH" else "📉 STRONG DOWN" if trend == "BEARISH" else "↔️ RANGING"
    rsi_status = "(OVERBOUGHT - may reverse)" if rsi > 70 else "(OVERSOLD - may bounce)" if rsi < 30 else "(NEUTRAL)"
    ema_status = "(Price ABOVE trend - bullish)" if price_vs_ema9 > 0 else "(Price BELOW trend - bearish)"
    vol_level = "HIGH" if atr > 50 else "MEDIUM" if atr > 25 else "LOW"
    macd_status = "(BULLISH crossover)" if macd_signal > 0 else "(BEARISH crossover)"
    stoch_status = "(overbought zone)" if stoch_k > 80 else "(oversold zone)" if stoch_k < 20 else "(neutral)"
    
    # Pair-specific warnings
    pair_warning = ""
    if "XAU" in pair:
        pair_warning = "\n⚠️ GOLD SPECIFIC: High intraday volatility, watch for breakout reversals, prefer larger SL"
    elif "GBP" in pair:
        pair_warning = "\n⚠️ GBP SPECIFIC: High spread risk, prefer trending moves, avoid choppy ranges"
    
    context = f"""
═══════════════════════════════════════════════════════
CURRENT MARKET CONTEXT (Real-time Indicators) — {pair}
═══════════════════════════════════════════════════════
1. PRICE ACTION & TREND:
   └─ Trend:              {trend} {trend_emoji}
   └─ Price vs EMA(9):    {price_vs_ema9:+.2f}% {ema_status}

2. MOMENTUM INDICATORS:
   └─ RSI(14):            {rsi:.0f} {rsi_status}
   └─ MACD:               {macd_status}
   └─ Stochastic(K):      {stoch_k:.0f} {stoch_status}

3. VOLATILITY & RISK:
   └─ ATR Level:          {atr:.2f} ({vol_level} volatility)
   └─ Risk Assessment:    {"HIGH RISK environment" if vol_level == "HIGH" else "Normal trading conditions"}

4. CONFLUENCE SIGNALS:
   └─ Trend + RSI:        {"✓ ALIGNED" if (trend == "BULLISH" and rsi < 70) or (trend == "BEARISH" and rsi > 30) else "✗ DIVERGENCE"}
   └─ Price vs EMA:       {"✓ CONFIRMATION" if (trend == "BULLISH" and price_vs_ema9 > 0) or (trend == "BEARISH" and price_vs_ema9 < 0) else "✗ REJECTION"}
{pair_warning}
═══════════════════════════════════════════════════════
"""
    return context


async def _generate_bull_argument(pair: str, round_num: int, combined_reports: str,
                                  market_context: str, bear_position: str,
                                  llm: GroqClient) -> str:
    """
    Generate intelligent bull (BUY) argument with pair-specific logic.
    """
    
    # Pair-specific instructions
    gold_instruction = "" if "XAU" not in pair else "\nIMPORTANT FOR GOLD: Gold is volatile and prone to sudden reversals. Only recommend BUY if confluence is VERY strong (3+ signals). Avoid buying into spikes."
    gbp_instruction = "" if "GBP" not in pair else "\nIMPORTANT FOR GBP: GBP has wide spreads. Only recommend BUY if profit target is AT LEAST 150 pips. Avoid low-probability trades."
    
    if round_num == 1:
        bull_prompt = f"""You are a HIGHLY EXPERIENCED BULL TRADER at a hedge fund analyzing {pair}.
Your job: Make the STRONGEST possible case for going LONG (BUY).
{gold_instruction}
{gbp_instruction}

═══════════════════════════════════════════════════════
ANALYST CONSENSUS:
═══════════════════════════════════════════════════════
{combined_reports}

{market_context}

═══════════════════════════════════════════════════════
YOUR OPENING BULL CASE FOR {pair}:
═══════════════════════════════════════════════════════

Structure your argument:
1. PRIMARY BULLISH THESIS (1-2 sentences maximum)
   - What is the core bullish setup?
   - Why NOW and not later?

2. SUPPORTING EVIDENCE (3-4 specific data points)
   - Reference exact RSI values, price levels, timeframe setups
   - Cite analyst reports with specific numbers
   - Mention technical confirmation patterns

3. PROFIT TARGET & TIMEFRAME
   - Specific pip target (e.g., "+120 pips in 4-6 hours")
   - Probability estimate (XX% win rate based on setup)
   - Exit strategy

4. RISK ASSESSMENT
   - Where is the logical stop loss? (pips)
   - Why should this trade be taken NOW vs waiting?
   - What could go wrong?

5. CONFLUENCE CHECK
   - Are 3+ technical indicators aligned?
   - Is trend confirmed?
   - Are we at a key support level?

6. CONVICTION RATING
   - State clearly: "My conviction is: STRONG / MODERATE / WEAK"

Be forceful, specific, and professional. Reference real data.
Maximum 280 words. End with your conviction rating."""
    else:
        bull_prompt = f"""You are a BULL TRADER defending your BUY position against the bear's attack.
{gold_instruction}
{gbp_instruction}

THE BEAR JUST ARGUED:
{bear_position}

ORIGINAL ANALYST REPORTS:
{combined_reports}

{market_context}

═══════════════════════════════════════════════════════
DEFEND YOUR BULLISH POSITION:
═══════════════════════════════════════════════════════

1. COUNTER BEAR'S MAIN POINTS
   - What did the bear get wrong?
   - What data contradicts their argument?
   - Where are they being too cautious?

2. STRENGTHEN BULLISH CASE
   - Double down on your top 3 bullish reasons
   - Use technical levels to show why bounce/breakout is coming
   - Provide concrete price targets

3. RISK vs REWARD ANALYSIS
   - Why does the profit potential outweigh the risk?
   - Calculate realistic R:R ratio (must be 1.5+)
   - Show margin of safety

4. CONVICTION RATING
   - State: "My conviction is: STRONG / MODERATE / WEAK"
   - Has it changed? Why or why not?
   - Provide confidence percentage

Be specific with numbers and timeframes. Under 220 words."""

    return llm.call(bull_prompt)


async def _generate_bear_argument(pair: str, round_num: int, combined_reports: str,
                                  market_context: str, bull_arg: str,
                                  llm: GroqClient) -> str:
    """
    Generate intelligent bear (SELL) argument with pair-specific logic.
    """
    
    # Pair-specific instructions
    gold_instruction = "" if "XAU" not in pair else "\nIMPORTANT FOR GOLD: Gold reversals are sharp and sudden. Prioritize SHORT setups at resistance or overbought levels. Watch for mean reversion."
    gbp_instruction = "" if "GBP" not in pair else "\nIMPORTANT FOR GBP: GBP trends are strong. Only recommend SHORT if clear resistance break. Avoid SHORTs in choppy ranges due to wide spreads."
    
    if round_num == 1:
        bear_prompt = f"""You are a HIGHLY EXPERIENCED BEAR TRADER at a hedge fund analyzing {pair}.
Your job: Make the STRONGEST possible case for going SHORT (SELL).
{gold_instruction}
{gbp_instruction}

═══════════════════════════════════════════════════════
ANALYST CONSENSUS:
═══════════════════════════════════════════════════════
{combined_reports}

THE BULL JUST ARGUED:
{bull_arg}

{market_context}

═══════════════════════════════════════════════════════
YOUR OPENING BEAR CASE FOR {pair}:
═══════════════════════════════════════════════════════

Structure your argument:
1. PRIMARY BEARISH THESIS (1-2 sentences maximum)
   - What is the core bearish setup? (Rejection? Overbought? Reversal?)
   - Why NOW and not later?

2. SUPPORTING EVIDENCE (3-4 specific data points)
   - Reference exact RSI values, resistance levels, timeframe setups
   - Counter the bull's specific points with data
   - Mention technical rejection patterns

3. PROFIT TARGET & TIMEFRAME
   - Specific pip target (e.g., "-100 pips in 3-5 hours")
   - Probability estimate (XX% win rate based on setup)
   - Exit strategy

4. RISK ASSESSMENT
   - Where is the logical stop loss? (pips)
   - Why should this SHORT be taken NOW?
   - What could go wrong?

5. CONFLUENCE CHECK
   - Are 3+ technical indicators aligned for SHORT?
   - Is trend broken or reversing?
   - Are we at a key resistance level?

6. CONVICTION RATING
   - State clearly: "My conviction is: STRONG / MODERATE / WEAK"

Be forceful, specific, and professional. Reference real data.
Maximum 280 words. End with your conviction rating."""
    else:
        bear_prompt = f"""You are a BEAR TRADER doubling down on your SHORT position.
{gold_instruction}
{gbp_instruction}

THE BULL JUST DEFENDED:
{bull_arg}

ORIGINAL ANALYST REPORTS:
{combined_reports}

{market_context}

═══════════════════════════════════════════════════════
MAINTAIN YOUR BEARISH POSITION:
═══════════════════════════════════════════════════════

1. REBUT BULL'S DEFENSE
   - What weaknesses remain in their argument?
   - What did they overlook or misinterpret?
   - Where are they in denial about risk?

2. REINFORCE BEARISH THESIS
   - Top 3 reasons why SHORT is the right trade
   - Technical levels showing rejection/resistance
   - Price action evidence

3. RISK vs REWARD ANALYSIS
   - Why does the downside target justify the risk?
   - Calculate realistic R:R ratio (must be 1.5+)
   - Show margin of safety

4. CONVICTION RATING
   - State: "My conviction is: STRONG / MODERATE / WEAK"
   - Has it strengthened or weakened? Why?
   - Provide confidence percentage

Be specific with numbers and data. Under 220 words."""

    return llm.call(bear_prompt)


async def run_debate(pair: str, analyst_reports: Dict[str, str],
                     debate_rounds: int, llm: GroqClient,
                     current_indicators: dict = None) -> dict:
    """
    Run intelligent Bull vs Bear debate with market context.
    
    Args:
        pair:               Currency pair (e.g., "EUR_USD")
        analyst_reports:    Dict of 4 analyst reports (technical, fundamental, sentiment, news)
        debate_rounds:      Number of rounds (1-5)
        llm:                LLM client instance
        current_indicators: Dict with RSI, trend, EMA, ATR, MACD, Stochastic
    
    Returns:
        {
          "transcript":         [list of round data],
          "lean":              "BULLISH" | "BEARISH" | "NEUTRAL",
          "confidence":        int (50-80),
          "bull_score":        int (total points),
          "bear_score":        int (total points),
          "rounds":            int (completed rounds),
          "market_volatility": "HIGH" | "MEDIUM" | "LOW",
          "technical_bias":    "BULLISH" | "BEARISH" | "NEUTRAL",
          "confluence_level":  int (1-5, higher = more aligned),
          "pair_specific_risk": "HIGH" | "NORMAL",
        }
    """

    print(f"\n  ╔════════════════════════════════════════════════════╗")
    print(f"  ║  Bull vs Bear Debate: {pair} ({debate_rounds} rounds)         ║")
    print(f"  ╚════════════════════════════════════════════════════╝")

    # ── 1. Combine analyst reports ───────────────────────────────────────────
    combined_reports = "\n\n".join([
        f"{'='*50}\n{name.upper()}\n{'='*50}\n{report[:450]}"
        for name, report in analyst_reports.items()
    ])

    # ── 2. Build detailed market context ─────────────────────────────────────
    market_context = _build_market_context(current_indicators, pair)

    # ── 3. Identify pair-specific risks ──────────────────────────────────────
    pair_specific_risk = "NORMAL"
    if "XAU" in pair:
        pair_specific_risk = "HIGH"  # Gold is more volatile
    elif "GBP" in pair:
        pair_specific_risk = "HIGH"  # GBP has wider spreads

    # ── 4. Extract technical bias from indicators ────────────────────────────
    technical_bias = "NEUTRAL"
    confluence_level = 1
    if current_indicators:
        trend = current_indicators.get("trend", "NEUTRAL")
        rsi = current_indicators.get("rsi", 50)
        price_vs_ema9 = current_indicators.get("price_vs_ema9", 0)
        macd_signal = current_indicators.get("macd", {}).get("histogram", 0)
        
        bullish_signals = 0
        bearish_signals = 0
        
        if trend == "BULLISH":
            bullish_signals += 1
        elif trend == "BEARISH":
            bearish_signals += 1
        
        if rsi < 30:
            bullish_signals += 1
        elif rsi > 70:
            bearish_signals += 1
        
        if price_vs_ema9 > 0:
            bullish_signals += 1
        elif price_vs_ema9 < 0:
            bearish_signals += 1
        
        if macd_signal > 0:
            bullish_signals += 1
        elif macd_signal < 0:
            bearish_signals += 1
        
        if bullish_signals > bearish_signals:
            technical_bias = "BULLISH"
            confluence_level = bullish_signals
        elif bearish_signals > bullish_signals:
            technical_bias = "BEARISH"
            confluence_level = bearish_signals
        else:
            confluence_level = max(bullish_signals, bearish_signals)

    market_volatility = "HIGH" if current_indicators and current_indicators.get("atr", 0) > 50 else "MEDIUM" if current_indicators and current_indicators.get("atr", 0) > 25 else "LOW"

    print(f"  📊 Technical Bias: {technical_bias} | Confluence: {confluence_level}/4 | Volatility: {market_volatility} | Pair Risk: {pair_specific_risk}")

    # ── 5. Initialize debate state ───────────────────────────────────────────
    transcript = []
    bull_position = ""
    bear_position = ""
    bull_score = 0
    bear_score = 0

    # ── 6. Run debate rounds ─────────────────────────────────────────────────
    for round_num in range(1, debate_rounds + 1):
        print(f"\n  Round {round_num}/{debate_rounds}...")
        print(f"  {'─' * 50}")

        # ── BULL ARGUMENT ────────────────────────────────────────────────────
        print(f"  🐂 Bull making argument...")
        bull_arg = await _generate_bull_argument(
            pair, round_num, combined_reports, market_context, bear_position, llm
        )
        bull_conviction, bull_points = _extract_conviction_score(bull_arg)
        bull_score += bull_points

        # Extra point if technical bias aligns
        if technical_bias == "BULLISH":
            bull_score += 0.5

        time.sleep(1)  # Rate limiting

        # ── BEAR ARGUMENT ────────────────────────────────────────────────────
        print(f"  🐻 Bear making argument...")
        bear_arg = await _generate_bear_argument(
            pair, round_num, combined_reports, market_context, bull_arg, llm
        )
        bear_conviction, bear_points = _extract_conviction_score(bear_arg)
        bear_score += bear_points

        # Extra point if technical bias aligns
        if technical_bias == "BEARISH":
            bear_score += 0.5

        time.sleep(1)  # Rate limiting

        # ── Save round data ──────────────────────────────────────────────────
        round_data = {
            "round": round_num,
            "bull_argument": bull_arg,
            "bear_argument": bear_arg,
            "bull_conviction": bull_conviction,
            "bear_conviction": bear_conviction,
            "bull_score_round": bull_points,
            "bear_score_round": bear_points,
        }
        transcript.append(round_data)

        # ── Update positions for next round ──────────────────────────────────
        bull_position = bull_arg
        bear_position = bear_arg

        print(f"  ✓ Round {round_num} complete")
        print(f"    Bull: {bull_conviction} (+{bull_points}) | Bear: {bear_conviction} (+{bear_points})")
        print(f"    Running totals → Bull: {bull_score:.1f} | Bear: {bear_score:.1f}")

    # ── 7. Determine final lean & confidence ──────────────────────────────────
    print(f"\n  {'═' * 50}")
    print(f"  DEBATE CONCLUSION")
    print(f"  {'═' * 50}")

    if bull_score > bear_score:
        lean = "BULLISH"
        score_diff = bull_score - bear_score
        # More aggressive scoring for profitability
        base_confidence = 55
        confidence = min(85, base_confidence + (score_diff * 6))
        
        # Boost confidence if technical bias aligns
        if technical_bias == "BULLISH":
            confidence = min(85, confidence + 5)
            print(f"  ✓ Technical bias ALIGNS with debate ({confluence_level}/4 signals)")
        elif technical_bias == "BEARISH":
            confidence = max(55, confidence - 10)
            print(f"  ⚠ Technical bias CONTRADICTS debate (conflicting signals)")
        
    elif bear_score > bull_score:
        lean = "BEARISH"
        score_diff = bear_score - bull_score
        base_confidence = 55
        confidence = min(85, base_confidence + (score_diff * 6))
        
        if technical_bias == "BEARISH":
            confidence = min(85, confidence + 5)
            print(f"  ✓ Technical bias ALIGNS with debate ({confluence_level}/4 signals)")
        elif technical_bias == "BULLISH":
            confidence = max(55, confidence - 10)
            print(f"  ⚠ Technical bias CONTRADICTS debate (conflicting signals)")
    else:
        lean = "NEUTRAL"
        confidence = 50
        print(f"  ↔ Evenly split debate - NEUTRAL stance")

    # ── 8. Pair-specific confidence adjustment ────────────────────────────────
    if pair_specific_risk == "HIGH":
        if "XAU" in pair and lean in ["BULLISH", "BEARISH"]:
            # Gold: require higher confidence
            confidence = min(85, confidence + 3)  # Compensate with higher confidence needed
            print(f"  🥇 GOLD: Requiring higher conviction (volatility adjustment)")
        elif "GBP" in pair and lean in ["BULLISH", "BEARISH"]:
            # GBP: penalize if low confidence
            if confidence < 65:
                confidence = max(50, confidence - 5)
                print(f"  £ GBP: Reducing confidence due to spread risk")
    
    # ── 9. Volatility adjustment ─────────────────────────────────────────────
    if market_volatility == "HIGH":
        print(f"  ⚡ HIGH volatility detected - reducing confidence by 5%")
        confidence = max(50, confidence - 5)
    elif market_volatility == "LOW":
        print(f"  ✓ Low volatility = cleaner signals - maintaining confidence")

    print(f"\n  FINAL: {lean} ({confidence}%)")
    print(f"  Bull Score: {bull_score:.1f} | Bear Score: {bear_score:.1f}")
    print(f"  Rounds Completed: {debate_rounds}")
    print(f"  Technical Bias: {technical_bias} ({confluence_level}/4 signals)")
    print(f"  Market Volatility: {market_volatility}")
    print(f"  Pair-Specific Risk: {pair_specific_risk}")

    return {
        "transcript": transcript,
        "lean": lean,
        "confidence": confidence,
        "bull_score": bull_score,
        "bear_score": bear_score,
        "rounds": debate_rounds,
        "market_volatility": market_volatility,
        "technical_bias": technical_bias,
        "confluence_level": confluence_level,
        "pair_specific_risk": pair_specific_risk,
    }
