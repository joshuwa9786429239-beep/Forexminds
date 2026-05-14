"""
ForexMind — Pair-Specific Configuration
Custom risk profiles and settings per currency pair
Optimized for GOLD (XAU_USD), GBP_USD, and other majors
"""

# Pair-specific parameters
PAIR_CONFIGS = {
    "XAU_USD": {
        "name": "Gold",
        "risk_multiplier": 0.8,  # Lower risk due to volatility
        "min_confidence": 65,  # Higher threshold for gold
        "min_rr_ratio": 2.0,  # Require better R:R
        "min_confluence": 4,  # Require 4/5 indicators aligned
        "stop_loss_pips": 60,  # Wider SL for volatility
        "take_profit_factor": 2.0,  # 2x SL for TP
        "max_position_size": 0.03,  # Smaller positions
        "volatility_adjustment": -10,  # Reduce confidence 10% in high vol
        "trading_times_best": ["London", "US"],
        "avoid_periods": ["Asian session"],  # Less predictable
        "reversal_prone": True,  # Gold reverses sharply
    },
    "GBP_USD": {
        "name": "British Pound",
        "risk_multiplier": 0.9,  # Normal-higher risk
        "min_confidence": 62,  # Slightly higher for GBP spreads
        "min_rr_ratio": 1.8,  # Better R:R needed
        "min_confluence": 3,  # 3+ indicators
        "stop_loss_pips": 50,
        "take_profit_factor": 1.8,
        "max_position_size": 0.04,
        "volatility_adjustment": -5,
        "trading_times_best": ["London", "US overlap"],
        "avoid_periods": ["Asian early session"],
        "reversal_prone": False,  # GBP trends
    },
    "EUR_USD": {
        "name": "Euro Dollar",
        "risk_multiplier": 1.0,  # Standard
        "min_confidence": 60,
        "min_rr_ratio": 1.5,
        "min_confluence": 3,
        "stop_loss_pips": 40,
        "take_profit_factor": 1.5,
        "max_position_size": 0.05,
        "volatility_adjustment": 0,
        "trading_times_best": ["London", "US"],
        "avoid_periods": ["Asian early"],
        "reversal_prone": False,
    },
    "USD_JPY": {
        "name": "Dollar Yen",
        "risk_multiplier": 1.0,
        "min_confidence": 60,
        "min_rr_ratio": 1.5,
        "min_confluence": 3,
        "stop_loss_pips": 45,
        "take_profit_factor": 1.5,
        "max_position_size": 0.05,
        "volatility_adjustment": 0,
        "trading_times_best": ["Asia", "US"],
        "avoid_periods": [],
        "reversal_prone": False,
    }
}

def get_pair_config(pair: str) -> dict:
    """
    Get configuration for a specific pair.
    Returns default if pair not in config.
    """
    return PAIR_CONFIGS.get(pair, {
        "name": pair,
        "risk_multiplier": 1.0,
        "min_confidence": 60,
        "min_rr_ratio": 1.5,
        "min_confluence": 3,
        "stop_loss_pips": 50,
        "take_profit_factor": 1.5,
        "max_position_size": 0.05,
        "volatility_adjustment": 0,
        "trading_times_best": [],
        "avoid_periods": [],
        "reversal_prone": False,
    })

def should_trade_pair(pair: str, current_hour: int, debate_confidence: int, confluence: int) -> tuple:
    """
    Determine if pair should be traded based on time and quality.
    Returns (should_trade: bool, reason: str)
    """
    config = get_pair_config(pair)
    
    # Check confidence
    if debate_confidence < config["min_confidence"]:
        return (False, f"Confidence {debate_confidence} below pair minimum {config['min_confidence']}")
    
    # Check confluence
    if confluence < config["min_confluence"]:
        return (False, f"Confluence {confluence}/5 below pair minimum {config['min_confluence']}")
    
    return (True, f"✓ OK for {pair} (Conf: {debate_confidence}%, Confluence: {confluence}/5)")
