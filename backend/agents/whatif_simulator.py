"""
What-If Simulator
Pure Python calculations for scenario analysis
No LLM needed — instant results
"""
from typing import Dict, Any


# Farm constants for demo (2-acre tomato farm)
BASE_YIELD_KG = 4200          # Base yield in kg
BASE_WATER_LITERS_WEEK = 3360  # Base weekly water usage (liters)
BASE_FERTILIZER_COST = 4200    # Base fertilizer cost (₹)
LABOR_COST = 8500              # Labor cost (₹)
OTHER_COSTS = 10500            # Seeds, pesticides, land prep, misc (₹)
BASE_PRICE_PER_KG = 30.0      # Current local market price


MARKET_PRICES = {
    "Local Market": {"price": 28.0, "transport": 500, "grading_required": False},
    "Nashik APMC": {"price": 32.0, "transport": 1200, "grading_required": False},
    "Pune APMC": {"price": 30.0, "transport": 5800, "grading_required": False},
    "Mumbai Wholesale": {"price": 35.0, "transport": 4500, "grading_required": True},
    "Online (eNAM)": {"price": 38.0, "transport": 0, "grading_required": True},
}


def calculate_whatif(
    irrigation_pct: float = 100.0,
    fertilizer_amount_pct: float = 100.0,
    harvest_days_offset: int = 0,
    selling_market: str = "Local Market",
    area_acres: float = 2.0
) -> Dict[str, Any]:
    """
    Calculate What-If scenario outcomes using pure Python math.
    
    Parameters:
    - irrigation_pct: Irrigation amount as % of baseline (0-150%)
    - fertilizer_amount_pct: Fertilizer as % of recommended dose (0-150%)
    - harvest_days_offset: Days early (-14) or late (+14) from optimal
    - selling_market: Which market to sell at
    - area_acres: Farm area
    """

    # === WATER CALCULATIONS ===
    irrigation_factor = irrigation_pct / 100.0
    weekly_water_used = BASE_WATER_LITERS_WEEK * irrigation_factor * (area_acres / 2.0)
    water_saved = BASE_WATER_LITERS_WEEK * (area_acres / 2.0) - weekly_water_used
    water_saved_pct = 100 - irrigation_pct

    # Water cost (₹3.5 per 1000L for drip irrigation)
    water_cost_baseline = BASE_WATER_LITERS_WEEK * (area_acres / 2.0) * 0.0035 * 12  # 12 weeks
    water_cost_scenario = weekly_water_used * 0.0035 * 12
    water_cost_saved = water_cost_baseline - water_cost_scenario

    # === YIELD IMPACT ===
    base_yield = BASE_YIELD_KG * (area_acres / 2.0)

    # Irrigation impact on yield
    if irrigation_pct < 50:
        yield_irrigation_factor = 0.65  # severe deficit
    elif irrigation_pct < 70:
        yield_irrigation_factor = 0.80  # moderate deficit
    elif irrigation_pct < 85:
        yield_irrigation_factor = 0.92  # mild deficit
    elif irrigation_pct <= 110:
        yield_irrigation_factor = 1.00  # optimal
    elif irrigation_pct <= 130:
        yield_irrigation_factor = 0.97  # slight over-irrigation
    else:
        yield_irrigation_factor = 0.90  # waterlogging risk

    # Fertilizer impact on yield
    fert_factor = fertilizer_amount_pct / 100.0
    if fert_factor < 0.5:
        yield_fert_factor = 0.70
    elif fert_factor < 0.75:
        yield_fert_factor = 0.87
    elif fert_factor <= 1.0:
        yield_fert_factor = 1.00
    elif fert_factor <= 1.25:
        yield_fert_factor = 1.05  # slight luxury consumption
    else:
        yield_fert_factor = 1.03  # diminishing returns

    # Harvest timing impact
    if harvest_days_offset < -10:
        yield_timing_factor = 0.75  # too early — immature
        price_timing_factor = 0.85
    elif harvest_days_offset < -5:
        yield_timing_factor = 0.88
        price_timing_factor = 0.92
    elif -5 <= harvest_days_offset <= 5:
        yield_timing_factor = 1.00  # optimal
        price_timing_factor = 1.00
    elif harvest_days_offset <= 10:
        yield_timing_factor = 0.93  # slight over-ripening
        price_timing_factor = 1.05  # late = higher prices sometimes
    else:
        yield_timing_factor = 0.78  # over-ripe, losses
        price_timing_factor = 0.90

    # Combined yield
    scenario_yield = base_yield * yield_irrigation_factor * yield_fert_factor * yield_timing_factor
    yield_change_pct = ((scenario_yield - base_yield) / base_yield) * 100

    # === COST CALCULATIONS ===
    fertilizer_cost = BASE_FERTILIZER_COST * (fertilizer_amount_pct / 100.0) * (area_acres / 2.0)
    fixed_costs = (LABOR_COST + OTHER_COSTS) * (area_acres / 2.0)
    total_cost = fertilizer_cost + water_cost_scenario + fixed_costs

    # === REVENUE AND PROFIT ===
    market_data = MARKET_PRICES.get(selling_market, MARKET_PRICES["Local Market"])
    price_per_kg = market_data["price"] * price_timing_factor
    transport_cost = market_data["transport"] * (area_acres / 2.0)

    # Grading premium/cost
    if market_data["grading_required"]:
        grading_cost = scenario_yield * 0.5  # ₹0.5/kg grading cost
        grade_a_yield = scenario_yield * 0.80  # 80% grade A after grading
    else:
        grading_cost = 0
        grade_a_yield = scenario_yield

    gross_revenue = grade_a_yield * price_per_kg
    total_expenses = total_cost + transport_cost + grading_cost
    net_profit = gross_revenue - total_expenses
    roi = ((net_profit / total_expenses) * 100) if total_expenses > 0 else 0

    # === SUSTAINABILITY SCORE ===
    sustainability = 50  # base

    # Water saving contribution
    if water_saved_pct > 0:
        sustainability += min(20, water_saved_pct * 0.4)
    elif water_saved_pct < -20:
        sustainability -= 15

    # Fertilizer efficiency
    if 80 <= fertilizer_amount_pct <= 110:
        sustainability += 15  # optimal use
    elif fertilizer_amount_pct > 130:
        sustainability -= 10  # excess = pollution risk
    elif fertilizer_amount_pct < 60:
        sustainability -= 5  # under-nutrition = poor efficiency

    # Market choice sustainability
    if "Online" in selling_market or "eNAM" in selling_market:
        sustainability += 10  # reduces transport emissions
    elif "Mumbai" in selling_market:
        sustainability -= 5  # long transport

    # Harvest timing
    if -3 <= harvest_days_offset <= 3:
        sustainability += 5  # optimal = less waste

    sustainability = max(0, min(100, int(sustainability)))

    # === COMPARISON TO BASELINE ===
    baseline_profit = base_yield * 0.75 * BASE_PRICE_PER_KG - (BASE_FERTILIZER_COST + LABOR_COST + OTHER_COSTS + water_cost_baseline) * (area_acres / 2.0)

    return {
        # Inputs (echoed back)
        "irrigation_pct": irrigation_pct,
        "fertilizer_amount_pct": fertilizer_amount_pct,
        "harvest_days_offset": harvest_days_offset,
        "selling_market": selling_market,
        "area_acres": area_acres,

        # Water
        "weekly_water_liters": round(weekly_water_used, 0),
        "water_saved_liters": round(water_saved, 0),
        "water_saved_pct": round(water_saved_pct, 1),
        "water_cost_saved": round(water_cost_saved, 2),

        # Yield
        "scenario_yield_kg": round(scenario_yield, 0),
        "baseline_yield_kg": base_yield,
        "yield_change_kg": round(scenario_yield - base_yield, 0),
        "yield_change_pct": round(yield_change_pct, 1),

        # Costs
        "fertilizer_cost": round(fertilizer_cost, 2),
        "water_cost": round(water_cost_scenario, 2),
        "labor_cost": round(fixed_costs * 0.45, 2),
        "transport_cost": round(transport_cost, 2),
        "grading_cost": round(grading_cost, 2),
        "total_cost": round(total_expenses, 2),

        # Revenue & Profit
        "price_per_kg": round(price_per_kg, 2),
        "gross_revenue": round(gross_revenue, 2),
        "net_profit": round(net_profit, 2),
        "profit_vs_baseline": round(net_profit - baseline_profit, 2),
        "profit_vs_baseline_pct": round(((net_profit - baseline_profit) / abs(baseline_profit)) * 100, 1) if baseline_profit != 0 else 0,
        "roi_pct": round(roi, 1),
        "profit_per_acre": round(net_profit / area_acres, 2),

        # Sustainability
        "sustainability_score": sustainability,

        # Analysis
        "recommendation": generate_recommendation(
            irrigation_pct, fertilizer_amount_pct, harvest_days_offset,
            selling_market, net_profit, baseline_profit, water_saved_pct
        ),
        "key_insights": generate_key_insights(
            irrigation_pct, fertilizer_amount_pct, harvest_days_offset,
            selling_market, net_profit, baseline_profit,
            water_saved_pct, yield_change_pct
        )
    }


def generate_recommendation(irr, fert, harvest_offset, market, profit, baseline, water_saved) -> str:
    tips = []

    if profit > baseline * 1.2:
        tips.append(f"✅ This scenario improves profit by {round(((profit-baseline)/abs(baseline))*100, 1)}% vs baseline")
    elif profit < baseline * 0.9:
        tips.append(f"⚠️ This scenario reduces profit — consider adjusting parameters")

    if irr < 80:
        tips.append("💧 Reduce irrigation below 80% risks yield loss — monitor soil moisture closely")
    elif irr > 120:
        tips.append("💧 Over-irrigation wastes water and may cause root diseases")

    if fert > 120:
        tips.append("🌱 Excess fertilizer beyond 120% has diminishing returns and raises costs")

    if "eNAM" in market or "Online" in market:
        tips.append("📊 Online market gives best price — register at enam.gov.in")

    if water_saved > 20:
        tips.append(f"🌊 {round(water_saved)}% water saved — excellent for sustainability!")

    return " | ".join(tips) if tips else "Scenario looks balanced — monitor results closely."


def generate_key_insights(irr, fert, harvest_offset, market, profit, baseline, water_saved_pct, yield_change_pct) -> list:
    insights = []

    # Yield insight
    if yield_change_pct > 0:
        insights.append({"icon": "📈", "text": f"Yield increases by {round(yield_change_pct, 1)}% in this scenario", "type": "positive"})
    elif yield_change_pct < -5:
        insights.append({"icon": "📉", "text": f"Yield drops by {abs(round(yield_change_pct, 1))}% — risk factor present", "type": "negative"})
    else:
        insights.append({"icon": "➡️", "text": "Yield stays near baseline — safe scenario", "type": "neutral"})

    # Water insight
    if water_saved_pct > 10:
        insights.append({"icon": "💧", "text": f"Saves {round(water_saved_pct)}% water — great for sustainability", "type": "positive"})
    elif water_saved_pct < -10:
        insights.append({"icon": "💧", "text": f"Uses {abs(round(water_saved_pct))}% more water than baseline", "type": "warning"})

    # Market insight
    market_price = MARKET_PRICES.get(market, {}).get("price", 28)
    if market_price >= 35:
        insights.append({"icon": "💰", "text": f"{market} offers premium pricing at ₹{market_price}/kg", "type": "positive"})

    # Profit vs baseline
    if profit > baseline:
        extra = round(profit - baseline, 0)
        insights.append({"icon": "🏆", "text": f"Extra profit of ₹{extra:,.0f} compared to baseline scenario", "type": "positive"})

    return insights
