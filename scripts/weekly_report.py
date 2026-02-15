#!/usr/bin/env python3
"""
API Cost Guardian - Weekly/Monthly Report Generator
Analyzes cost trends over the past 7 or 30 days
"""

import json
import subprocess
import sys
from datetime import datetime, date, timedelta
from typing import Dict, List
from collections import defaultdict
from pathlib import Path
import statistics

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> dict:
    """Load configuration"""
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_sessions() -> List[dict]:
    """Get all sessions using OpenClaw CLI"""
    try:
        result = subprocess.run(
            ['openclaw', 'sessions', 'list', '--limit', '500', '--json'],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        return data.get('sessions', [])
    except Exception as e:
        print(f"Error getting sessions: {e}", file=sys.stderr)
        return []


def analyze_session_costs_for_date(sessions: List[dict], target_date: date) -> float:
    """Analyze total cost for a specific date"""
    total_cost = 0.0
    
    target_start = datetime.combine(target_date, datetime.min.time()).timestamp() * 1000
    target_end = datetime.combine(target_date + timedelta(days=1), datetime.min.time()).timestamp() * 1000
    
    for session in sessions:
        messages = session.get('messages', [])
        
        for msg in messages:
            if msg.get('role') != 'assistant':
                continue
            
            msg_timestamp = msg.get('timestamp', 0)
            if not (target_start <= msg_timestamp < target_end):
                continue
            
            usage = msg.get('usage', {})
            cost_info = usage.get('cost', {})
            cost = cost_info.get('total', 0.0)
            
            if cost > 0:
                total_cost += cost
    
    return total_cost


def analyze_period_costs(sessions: List[dict], days: int) -> Dict:
    """Analyze costs over a period of days"""
    daily_costs = {}
    provider_costs = defaultdict(float)
    model_costs = defaultdict(float)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    current_date = start_date
    while current_date <= end_date:
        cost = analyze_session_costs_for_date(sessions, current_date)
        daily_costs[current_date.isoformat()] = round(cost, 4)
        current_date += timedelta(days=1)
    
    # Analyze provider and model costs for the entire period
    period_start = datetime.combine(start_date, datetime.min.time()).timestamp() * 1000
    period_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time()).timestamp() * 1000
    
    for session in sessions:
        messages = session.get('messages', [])
        
        for msg in messages:
            if msg.get('role') != 'assistant':
                continue
            
            msg_timestamp = msg.get('timestamp', 0)
            if not (period_start <= msg_timestamp < period_end):
                continue
            
            usage = msg.get('usage', {})
            cost_info = usage.get('cost', {})
            cost = cost_info.get('total', 0.0)
            
            if cost > 0:
                provider = msg.get('provider', 'unknown')
                model = msg.get('model', 'unknown')
                
                provider_costs[provider] += cost
                model_costs[model] += cost
    
    costs_list = [c for c in daily_costs.values() if c > 0]
    
    return {
        'daily_costs': daily_costs,
        'total_cost': sum(daily_costs.values()),
        'average_cost': round(statistics.mean(costs_list), 4) if costs_list else 0.0,
        'max_cost': max(costs_list) if costs_list else 0.0,
        'min_cost': min(costs_list) if costs_list else 0.0,
        'median_cost': round(statistics.median(costs_list), 4) if costs_list else 0.0,
        'provider_costs': {k: round(v, 4) for k, v in provider_costs.items()},
        'model_costs': {k: round(v, 4) for k, v in model_costs.items()},
        'days_analyzed': days
    }


def calculate_trend(daily_costs: Dict[str, float]) -> str:
    """Calculate cost trend (rising, falling, stable)"""
    costs_list = list(daily_costs.values())
    
    if len(costs_list) < 3:
        return 'insufficient_data'
    
    # Compare first half vs second half
    mid = len(costs_list) // 2
    first_half_avg = statistics.mean(costs_list[:mid]) if costs_list[:mid] else 0
    second_half_avg = statistics.mean(costs_list[mid:]) if costs_list[mid:] else 0
    
    if second_half_avg > first_half_avg * 1.1:
        return 'rising'
    elif second_half_avg < first_half_avg * 0.9:
        return 'falling'
    else:
        return 'stable'


def generate_report(analysis: Dict, config: dict, period_name: str) -> dict:
    """Generate period report"""
    trend = calculate_trend(analysis['daily_costs'])
    daily_budget = config['cost_tracking']['daily_budget']
    period_budget = daily_budget * analysis['days_analyzed']
    
    return {
        'period': period_name,
        'days_analyzed': analysis['days_analyzed'],
        'total_cost': round(analysis['total_cost'], 4),
        'average_daily_cost': analysis['average_cost'],
        'max_daily_cost': analysis['max_cost'],
        'min_daily_cost': analysis['min_cost'],
        'median_daily_cost': analysis['median_cost'],
        'trend': trend,
        'daily_budget': daily_budget,
        'period_budget': period_budget,
        'budget_used_percent': round((analysis['total_cost'] / period_budget) * 100, 2),
        'provider_costs': analysis['provider_costs'],
        'model_costs': analysis['model_costs'],
        'daily_costs': analysis['daily_costs']
    }


def create_text_chart(daily_costs: Dict[str, float], width: int = 50) -> str:
    """Create ASCII bar chart of daily costs"""
    if not daily_costs:
        return "No data"
    
    max_cost = max(daily_costs.values()) if daily_costs.values() else 1
    if max_cost == 0:
        max_cost = 1
    
    lines = []
    for date_str, cost in sorted(daily_costs.items()):
        bar_length = int((cost / max_cost) * width)
        bar = '█' * bar_length
        lines.append(f"{date_str[-5:]} ${cost:6.2f} |{bar}")
    
    return '\n'.join(lines)


def format_report(report: dict) -> str:
    """Format report as human-readable text"""
    lines = []
    
    trend_emoji = {
        'rising': '📈',
        'falling': '📉',
        'stable': '➡️',
        'insufficient_data': '❓'
    }
    
    lines.append(f"{'='*60}")
    lines.append(f"📊 {report['period']} Cost Report")
    lines.append(f"{'='*60}")
    lines.append("")
    lines.append(f"📅 Period: {report['days_analyzed']} days")
    lines.append(f"💰 Total Cost: ${report['total_cost']:.2f}")
    lines.append(f"📊 Average Daily: ${report['average_daily_cost']:.2f}")
    lines.append(f"📈 Max Daily: ${report['max_daily_cost']:.2f}")
    lines.append(f"📉 Min Daily: ${report['min_daily_cost']:.2f}")
    lines.append(f"🎯 Median Daily: ${report['median_daily_cost']:.2f}")
    lines.append("")
    lines.append(f"{trend_emoji.get(report['trend'], '❓')} Trend: {report['trend'].upper()}")
    lines.append("")
    lines.append(f"💵 Period Budget: ${report['period_budget']:.2f}")
    lines.append(f"📊 Budget Used: {report['budget_used_percent']:.1f}%")
    lines.append("")
    
    if report['provider_costs']:
        lines.append("🔍 Cost by Provider:")
        for provider, cost in sorted(report['provider_costs'].items(), key=lambda x: x[1], reverse=True):
            pct = (cost / report['total_cost']) * 100
            lines.append(f"  • {provider}: ${cost:.2f} ({pct:.1f}%)")
        lines.append("")
    
    if report['model_costs']:
        lines.append("🤖 Cost by Model:")
        for model, cost in sorted(report['model_costs'].items(), key=lambda x: x[1], reverse=True):
            model_short = model.split('/')[-1] if '/' in model else model
            pct = (cost / report['total_cost']) * 100
            lines.append(f"  • {model_short}: ${cost:.2f} ({pct:.1f}%)")
        lines.append("")
    
    lines.append("📈 Daily Cost Chart:")
    lines.append("")
    lines.append(create_text_chart(report['daily_costs']))
    lines.append("")
    
    # Insights
    lines.append("💡 Insights:")
    if report['trend'] == 'rising':
        lines.append("  ⚠️ Costs are RISING - consider optimization!")
    elif report['trend'] == 'falling':
        lines.append("  ✅ Costs are FALLING - good progress!")
    elif report['trend'] == 'stable':
        lines.append("  ➡️ Costs are STABLE - predictable usage")
    
    if report['budget_used_percent'] > 90:
        lines.append("  🚨 Budget usage >90% - action needed!")
    elif report['budget_used_percent'] > 70:
        lines.append("  ⚠️ Budget usage >70% - monitor closely")
    
    return "\n".join(lines)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate weekly/monthly API cost report')
    parser.add_argument('--period', choices=['weekly', 'monthly'], default='weekly',
                        help='Report period (default: weekly)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    days = 7 if args.period == 'weekly' else 30
    period_name = "Weekly" if args.period == 'weekly' else "Monthly"
    
    config = load_config()
    sessions = get_sessions()
    
    if not sessions:
        print("No sessions found", file=sys.stderr)
        sys.exit(1)
    
    analysis = analyze_period_costs(sessions, days)
    report = generate_report(analysis, config, period_name)
    
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_report(report))


if __name__ == '__main__':
    main()
