#!/usr/bin/env python3
"""
API Cost Guardian - Model Comparison Tool
Compare cost and usage across different models
"""

import json
import subprocess
import sys
from datetime import datetime, date, timedelta
from typing import Dict, List
from collections import defaultdict
from pathlib import Path

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


def analyze_model_usage(sessions: List[dict], days: int) -> Dict:
    """Analyze usage and costs per model"""
    model_stats = defaultdict(lambda: {
        'cost': 0.0,
        'count': 0,
        'input_tokens': 0,
        'output_tokens': 0,
        'total_tokens': 0,
        'cache_read_tokens': 0,
        'cache_write_tokens': 0
    })
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
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
                model = msg.get('model', 'unknown')
                
                model_stats[model]['cost'] += cost
                model_stats[model]['count'] += 1
                model_stats[model]['input_tokens'] += usage.get('input', 0)
                model_stats[model]['output_tokens'] += usage.get('output', 0)
                model_stats[model]['total_tokens'] += usage.get('totalTokens', 0)
                model_stats[model]['cache_read_tokens'] += usage.get('cacheRead', 0)
                model_stats[model]['cache_write_tokens'] += usage.get('cacheWrite', 0)
    
    # Calculate averages and cost per 1K tokens
    for model, stats in model_stats.items():
        stats['avg_cost_per_call'] = stats['cost'] / stats['count'] if stats['count'] > 0 else 0
        stats['cost_per_1k_tokens'] = (stats['cost'] / stats['total_tokens']) * 1000 if stats['total_tokens'] > 0 else 0
    
    return dict(model_stats)


def create_cost_bar_chart(model_stats: Dict, width: int = 50) -> str:
    """Create ASCII bar chart of model costs"""
    if not model_stats:
        return "No data"
    
    max_cost = max(stats['cost'] for stats in model_stats.values())
    if max_cost == 0:
        max_cost = 1
    
    lines = []
    sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['cost'], reverse=True)
    
    for model, stats in sorted_models:
        model_short = model.split('/')[-1] if '/' in model else model
        bar_length = int((stats['cost'] / max_cost) * width)
        bar = '█' * bar_length
        lines.append(f"{model_short:30} ${stats['cost']:7.2f} |{bar}")
    
    return '\n'.join(lines)


def create_usage_bar_chart(model_stats: Dict, width: int = 50) -> str:
    """Create ASCII bar chart of model usage (call count)"""
    if not model_stats:
        return "No data"
    
    max_count = max(stats['count'] for stats in model_stats.values())
    if max_count == 0:
        max_count = 1
    
    lines = []
    sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for model, stats in sorted_models:
        model_short = model.split('/')[-1] if '/' in model else model
        bar_length = int((stats['count'] / max_count) * width)
        bar = '█' * bar_length
        lines.append(f"{model_short:30} {stats['count']:5} calls |{bar}")
    
    return '\n'.join(lines)


def format_report(model_stats: Dict, days: int) -> str:
    """Format model comparison report"""
    lines = []
    
    total_cost = sum(stats['cost'] for stats in model_stats.values())
    total_calls = sum(stats['count'] for stats in model_stats.values())
    
    lines.append(f"{'='*70}")
    lines.append(f"🤖 Model Comparison Report ({days} days)")
    lines.append(f"{'='*70}")
    lines.append("")
    lines.append(f"📊 Total Models: {len(model_stats)}")
    lines.append(f"💰 Total Cost: ${total_cost:.2f}")
    lines.append(f"📞 Total Calls: {total_calls}")
    lines.append("")
    
    # Cost Chart
    lines.append("💰 Cost by Model:")
    lines.append("")
    lines.append(create_cost_bar_chart(model_stats))
    lines.append("")
    
    # Usage Chart
    lines.append("📊 Usage by Model (Call Count):")
    lines.append("")
    lines.append(create_usage_bar_chart(model_stats))
    lines.append("")
    
    # Detailed Stats Table
    lines.append("📋 Detailed Stats:")
    lines.append("")
    lines.append(f"{'Model':<30} {'Cost':>10} {'Calls':>7} {'$/Call':>10} {'$/1K tok':>10}")
    lines.append("-" * 70)
    
    sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['cost'], reverse=True)
    
    for model, stats in sorted_models:
        model_short = model.split('/')[-1] if '/' in model else model
        lines.append(
            f"{model_short:<30} "
            f"${stats['cost']:>9.2f} "
            f"{stats['count']:>7} "
            f"${stats['avg_cost_per_call']:>9.4f} "
            f"${stats['cost_per_1k_tokens']:>9.4f}"
        )
    
    lines.append("")
    
    # Cost Savings Analysis
    lines.append("💡 Cost Optimization Insights:")
    lines.append("")
    
    # Find most expensive model
    most_expensive = max(model_stats.items(), key=lambda x: x[1]['cost'])
    most_expensive_name = most_expensive[0].split('/')[-1] if '/' in most_expensive[0] else most_expensive[0]
    
    # Find cheapest model with usage
    cheapest = min(
        ((k, v) for k, v in model_stats.items() if v['count'] > 0),
        key=lambda x: x[1]['cost_per_1k_tokens'],
        default=None
    )
    
    lines.append(f"  📈 Most expensive: {most_expensive_name} (${most_expensive[1]['cost']:.2f})")
    
    if cheapest:
        cheapest_name = cheapest[0].split('/')[-1] if '/' in cheapest[0] else cheapest[0]
        lines.append(f"  📉 Cheapest: {cheapest_name} (${cheapest[1]['cost_per_1k_tokens']:.4f}/1K tokens)")
        
        # Calculate potential savings
        expensive_tokens = most_expensive[1]['total_tokens']
        current_cost = most_expensive[1]['cost']
        potential_cost = (expensive_tokens / 1000) * cheapest[1]['cost_per_1k_tokens']
        savings = current_cost - potential_cost
        
        if savings > 0:
            lines.append("")
            lines.append(f"  💰 Potential savings if {most_expensive_name} → {cheapest_name}:")
            lines.append(f"     Current: ${current_cost:.2f}")
            lines.append(f"     Potential: ${potential_cost:.2f}")
            lines.append(f"     Savings: ${savings:.2f} ({(savings/current_cost)*100:.1f}%)")
    
    # Find models with high cost per call
    high_cost_models = [
        (k, v) for k, v in sorted_models
        if v['avg_cost_per_call'] > 0.1  # $0.10 per call threshold
    ]
    
    if high_cost_models:
        lines.append("")
        lines.append("  ⚠️ High cost per call models:")
        for model, stats in high_cost_models[:3]:
            model_short = model.split('/')[-1] if '/' in model else model
            lines.append(f"     • {model_short}: ${stats['avg_cost_per_call']:.4f}/call")
    
    return "\n".join(lines)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare API costs across models')
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days to analyze (default: 7)')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON')
    
    args = parser.parse_args()
    
    sessions = get_sessions()
    
    if not sessions:
        print("No sessions found", file=sys.stderr)
        sys.exit(1)
    
    model_stats = analyze_model_usage(sessions, args.days)
    
    if not model_stats:
        print(f"No model usage found in the past {args.days} days", file=sys.stderr)
        sys.exit(1)
    
    if args.json:
        print(json.dumps(model_stats, indent=2))
    else:
        print(format_report(model_stats, args.days))


if __name__ == '__main__':
    main()
