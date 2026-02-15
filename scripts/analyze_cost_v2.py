#!/usr/bin/env python3
"""
API Cost Guardian - Cost Analyzer (v2)
Uses sessions_list to calculate daily API costs
Multi-provider support with fallback pricing
"""

import json
import subprocess
import sys
from datetime import datetime, date, timedelta
from typing import Dict, List
from collections import defaultdict
from pathlib import Path

# Import provider pricing
try:
    from provider_pricing import calculate_cost, is_free_provider, get_model_pricing
except ImportError:
    # Fallback if module not found
    def calculate_cost(provider, model, usage):
        return 0.0
    def is_free_provider(provider):
        return False
    def get_model_pricing(provider, model):
        return None

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> dict:
    """Load configuration"""
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_sessions() -> List[dict]:
    """Get all sessions using OpenClaw CLI"""
    try:
        result = subprocess.run(
            ['openclaw', 'sessions', 'list', '--limit', '100', '--json'],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        return data.get('sessions', [])
    except Exception as e:
        print(f"Error getting sessions: {e}", file=sys.stderr)
        return []


def analyze_session_costs(sessions: List[dict], target_date: date) -> Dict:
    """Analyze costs from sessions for a specific date"""
    total_cost = 0.0
    provider_costs = defaultdict(float)
    model_costs = defaultdict(float)
    session_costs = []
    
    target_start = datetime.combine(target_date, datetime.min.time()).timestamp() * 1000
    target_end = datetime.combine(target_date + timedelta(days=1), datetime.min.time()).timestamp() * 1000
    
    for session in sessions:
        # Check if session has activity on target date
        updated_at = session.get('updatedAt', 0)
        
        if not (target_start <= updated_at < target_end):
            continue
        
        # Get last messages with usage info
        messages = session.get('messages', [])
        
        for msg in messages:
            if msg.get('role') != 'assistant':
                continue
            
            # Check timestamp
            msg_timestamp = msg.get('timestamp', 0)
            if not (target_start <= msg_timestamp < target_end):
                continue
            
            # Extract usage
            usage = msg.get('usage', {})
            cost_info = usage.get('cost', {})
            cost = cost_info.get('total', 0.0)
            
            provider = msg.get('provider', 'unknown')
            model = msg.get('model', 'unknown')
            
            # Fallback: calculate cost if not provided by OpenClaw
            if cost == 0.0 and usage.get('totalTokens', 0) > 0:
                calculated_cost = calculate_cost(provider, model, usage)
                if calculated_cost > 0:
                    cost = calculated_cost
            
            # Only include if there's actual cost or token usage
            if cost > 0 or usage.get('totalTokens', 0) > 0:
                total_cost += cost
                
                provider_costs[provider] += cost
                model_costs[model] += cost
                
                session_costs.append({
                    'session_key': session.get('key', 'unknown'),
                    'session_name': session.get('label') or session.get('displayName', 'unknown'),
                    'timestamp': datetime.fromtimestamp(msg_timestamp / 1000).isoformat(),
                    'provider': provider,
                    'model': model,
                    'cost': round(cost, 4),
                    'tokens': usage.get('totalTokens', 0),
                    'input': usage.get('input', 0),
                    'output': usage.get('output', 0),
                    'cache_read': usage.get('cacheRead', 0),
                    'cache_write': usage.get('cacheWrite', 0),
                    'is_free': is_free_provider(provider)
                })
    
    return {
        'total_cost': total_cost,
        'provider_costs': dict(provider_costs),
        'model_costs': dict(model_costs),
        'session_costs': sorted(session_costs, key=lambda x: x['timestamp'])
    }


def calculate_projected_cost(current_cost: float, current_hour: int) -> float:
    """Calculate projected daily cost"""
    if current_hour == 0:
        return current_cost
    
    hourly_rate = current_cost / current_hour if current_hour > 0 else 0
    projected_cost = current_cost + (hourly_rate * (24 - current_hour))
    
    return projected_cost


def generate_report(analysis: Dict, config: dict) -> dict:
    """Generate cost report"""
    current_hour = datetime.now().hour
    projected_cost = calculate_projected_cost(analysis['total_cost'], current_hour)
    
    thresholds = config['thresholds']
    alert_level = None
    
    if projected_cost >= thresholds['critical']:
        alert_level = 'critical'
    elif projected_cost >= thresholds['urgent']:
        alert_level = 'urgent'
    elif projected_cost >= thresholds['warning']:
        alert_level = 'warning'
    
    daily_budget = config['cost_tracking']['daily_budget']
    
    return {
        'date': date.today().isoformat(),
        'current_time': datetime.now().isoformat(),
        'current_hour': current_hour,
        'total_cost': round(analysis['total_cost'], 4),
        'projected_daily_cost': round(projected_cost, 4),
        'provider_costs': {k: round(v, 4) for k, v in analysis['provider_costs'].items()},
        'model_costs': {k: round(v, 4) for k, v in analysis['model_costs'].items()},
        'alert_level': alert_level,
        'thresholds': thresholds,
        'daily_budget': daily_budget,
        'budget_used_percent': round((projected_cost / daily_budget) * 100, 2),
        'usage_count': len(analysis['session_costs']),
        'top_sessions': sorted(
            [
                {
                    'session': s['session_name'],
                    'cost': s['cost'],
                    'model': s['model']
                }
                for s in analysis['session_costs']
            ],
            key=lambda x: x['cost'],
            reverse=True
        )[:10]
    }


def format_report(report: dict) -> str:
    """Format report as human-readable text with provider breakdown"""
    lines = []
    
    lines.append(f"📅 Date: {report['date']}")
    lines.append(f"⏰ Current Time: {report['current_time'][:19]}")
    lines.append("")
    lines.append(f"💰 Current Cost: ${report['total_cost']:.4f}")
    lines.append(f"📈 Projected Daily Cost: ${report['projected_daily_cost']:.4f}")
    lines.append(f"🎯 Daily Budget: ${report['daily_budget']:.2f}")
    lines.append(f"📊 Budget Used: {report['budget_used_percent']:.1f}%")
    lines.append("")
    
    # Provider별 비용 (유료 Provider만)
    paid_providers = {k: v for k, v in report['provider_costs'].items() if v > 0 and k.lower() != 'ollama'}
    free_providers = {k: v for k, v in report['provider_costs'].items() if k.lower() == 'ollama'}
    
    if paid_providers:
        lines.append("💳 Cost by Provider (Paid):")
        for provider, cost in sorted(paid_providers.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  • {provider.upper()}: ${cost:.4f}")
        lines.append("")
    
    if free_providers:
        lines.append("🆓 Free Providers:")
        for provider in free_providers:
            lines.append(f"  • {provider.upper()}: Local model (no cost)")
        lines.append("")
    
    # 모델별 TOP 5
    if report['model_costs']:
        lines.append("🤖 Top Models by Cost:")
        top_models = sorted(report['model_costs'].items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (model, cost) in enumerate(top_models, 1):
            model_short = model.split('/')[-1] if '/' in model else model
            if cost > 0:
                lines.append(f"  {i}. {model_short}: ${cost:.4f}")
            else:
                lines.append(f"  {i}. {model_short}: Free")
        lines.append("")
    
    if report['alert_level']:
        emoji = {'warning': '⚠️', 'urgent': '🔴', 'critical': '🚨'}[report['alert_level']]
        lines.append(f"{emoji} Alert Level: {report['alert_level'].upper()}")
        lines.append(f"  Threshold: ${report['thresholds'][report['alert_level']]:.2f}")
    else:
        lines.append("✅ No alerts")
    
    lines.append("")
    lines.append(f"📝 Total API Calls: {report['usage_count']}")
    
    if report['top_sessions']:
        lines.append("")
        lines.append("💸 Top Cost Sessions:")
        for i, session in enumerate(report['top_sessions'][:5], 1):
            lines.append(f"  {i}. {session['session']}: ${session['cost']:.2f} ({session['model'].split('/')[-1]})")
    
    return "\n".join(lines)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze OpenClaw API costs')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--telegram', action='store_true', help='Format for Telegram')
    
    args = parser.parse_args()
    
    config = load_config()
    sessions = get_sessions()
    
    if not sessions:
        print("No sessions found", file=sys.stderr)
        sys.exit(1)
    
    analysis = analyze_session_costs(sessions, date.today())
    report = generate_report(analysis, config)
    
    if args.json:
        print(json.dumps(report, indent=2))
    elif args.telegram:
        # Telegram-formatted output
        text = format_report(report)
        print(text)
    else:
        # Standard output
        print(format_report(report))
    
    # Exit code based on alert level
    if report['alert_level'] == 'critical':
        sys.exit(2)
    elif report['alert_level'] == 'urgent':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
