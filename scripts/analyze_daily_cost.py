#!/usr/bin/env python3
"""
API Cost Guardian - Daily Cost Analyzer
Analyzes OpenClaw session logs to calculate daily API costs
"""

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Configuration
WORKSPACE_PATH = Path(os.path.expanduser("~/.openclaw/workspace"))
CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> dict:
    """Load configuration from config.json"""
    with open(CONFIG_PATH) as f:
        return json.load(f)


def find_session_logs() -> List[Path]:
    """Find all session log files (*.jsonl)"""
    return list(WORKSPACE_PATH.glob("*.jsonl"))


def parse_log_file(log_file: Path, target_date: date) -> Tuple[float, Dict[str, float], List[dict]]:
    """
    Parse a JSONL log file and extract cost information for target date
    
    Returns:
        (total_cost, provider_costs, usage_details)
    """
    total_cost = 0.0
    provider_costs = defaultdict(float)
    usage_details = []
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    
                    # Check if entry has timestamp
                    if 'timestamp' not in entry:
                        continue
                    
                    # Parse timestamp (in milliseconds)
                    timestamp_ms = entry['timestamp']
                    entry_date = datetime.fromtimestamp(timestamp_ms / 1000).date()
                    
                    # Only process entries from target date
                    if entry_date != target_date:
                        continue
                    
                    # Extract usage and cost info
                    if 'usage' in entry and 'cost' in entry['usage']:
                        cost_info = entry['usage']['cost']
                        cost = cost_info.get('total', 0.0)
                        
                        if cost > 0:
                            total_cost += cost
                            
                            # Get provider from entry
                            provider = entry.get('provider', 'unknown')
                            model = entry.get('model', 'unknown')
                            
                            provider_costs[provider] += cost
                            
                            # Store usage detail
                            usage_details.append({
                                'timestamp': datetime.fromtimestamp(timestamp_ms / 1000).isoformat(),
                                'provider': provider,
                                'model': model,
                                'cost': cost,
                                'tokens': entry['usage'].get('totalTokens', 0),
                                'input': entry['usage'].get('input', 0),
                                'output': entry['usage'].get('output', 0)
                            })
                            
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Warning: Error parsing line: {e}", file=sys.stderr)
                    continue
                    
    except Exception as e:
        print(f"Error reading {log_file}: {e}", file=sys.stderr)
        
    return total_cost, dict(provider_costs), usage_details


def calculate_projected_cost(current_cost: float, current_hour: int) -> float:
    """
    Calculate projected daily cost based on current cost and time
    
    Args:
        current_cost: Total cost so far today
        current_hour: Current hour (0-23)
    
    Returns:
        Projected total cost for the day
    """
    if current_hour == 0:
        return current_cost
    
    # Simple linear projection
    hours_elapsed = current_hour
    hours_remaining = 24 - current_hour
    
    hourly_rate = current_cost / hours_elapsed
    projected_cost = current_cost + (hourly_rate * hours_remaining)
    
    return projected_cost


def analyze_daily_cost(target_date: date = None) -> dict:
    """
    Analyze all session logs for a given date
    
    Args:
        target_date: Date to analyze (default: today)
    
    Returns:
        Dictionary with cost analysis results
    """
    if target_date is None:
        target_date = date.today()
    
    config = load_config()
    log_files = find_session_logs()
    
    total_cost = 0.0
    provider_costs = defaultdict(float)
    all_usage_details = []
    
    # Process all log files
    for log_file in log_files:
        file_cost, file_providers, file_details = parse_log_file(log_file, target_date)
        total_cost += file_cost
        
        for provider, cost in file_providers.items():
            provider_costs[provider] += cost
        
        all_usage_details.extend(file_details)
    
    # Sort usage details by timestamp
    all_usage_details.sort(key=lambda x: x['timestamp'])
    
    # Calculate projected cost
    current_hour = datetime.now().hour
    projected_cost = calculate_projected_cost(total_cost, current_hour)
    
    # Determine alert level
    thresholds = config['thresholds']
    alert_level = None
    if projected_cost >= thresholds['critical']:
        alert_level = 'critical'
    elif projected_cost >= thresholds['urgent']:
        alert_level = 'urgent'
    elif projected_cost >= thresholds['warning']:
        alert_level = 'warning'
    
    # Build result
    result = {
        'date': target_date.isoformat(),
        'current_time': datetime.now().isoformat(),
        'current_hour': current_hour,
        'total_cost': round(total_cost, 4),
        'projected_daily_cost': round(projected_cost, 4),
        'provider_costs': {k: round(v, 4) for k, v in provider_costs.items()},
        'alert_level': alert_level,
        'thresholds': thresholds,
        'daily_budget': config['cost_tracking']['daily_budget'],
        'budget_used_percent': round((projected_cost / config['cost_tracking']['daily_budget']) * 100, 2),
        'usage_count': len(all_usage_details),
        'usage_details': all_usage_details[-10:] if len(all_usage_details) > 10 else all_usage_details  # Last 10
    }
    
    return result


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze OpenClaw API costs')
    parser.add_argument('--date', type=str, help='Date to analyze (YYYY-MM-DD), default: today')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Parse date
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        target_date = date.today()
    
    # Analyze
    result = analyze_daily_cost(target_date)
    
    # Output
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        print(f"📅 Date: {result['date']}")
        print(f"⏰ Current Time: {result['current_time'][:19]}")
        print()
        print(f"💰 Current Cost: ${result['total_cost']:.2f}")
        print(f"📈 Projected Daily Cost: ${result['projected_daily_cost']:.2f}")
        print(f"🎯 Daily Budget: ${result['daily_budget']:.2f}")
        print(f"📊 Budget Used: {result['budget_used_percent']:.1f}%")
        print()
        
        if result['provider_costs']:
            print("🔍 Cost by Provider:")
            for provider, cost in sorted(result['provider_costs'].items(), key=lambda x: x[1], reverse=True):
                print(f"  • {provider}: ${cost:.2f}")
            print()
        
        if result['alert_level']:
            emoji = {'warning': '⚠️', 'urgent': '🔴', 'critical': '🚨'}[result['alert_level']]
            print(f"{emoji} Alert Level: {result['alert_level'].upper()}")
            print(f"  Threshold: ${result['thresholds'][result['alert_level']]:.2f}")
        else:
            print("✅ No alerts")
        
        print()
        print(f"📝 Usage Count: {result['usage_count']} API calls")
    
    # Exit code based on alert level
    if result['alert_level'] == 'critical':
        sys.exit(2)
    elif result['alert_level'] == 'urgent':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
