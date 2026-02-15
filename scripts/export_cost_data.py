#!/usr/bin/env python3
"""
API Cost Guardian - Data Export Tool
Export session cost data to CSV or JSON
"""

import json
import subprocess
import sys
import csv
from datetime import datetime, date, timedelta
from typing import Dict, List
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


def extract_cost_records(sessions: List[dict], days: int) -> List[dict]:
    """Extract all cost records from sessions"""
    records = []
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    period_start = datetime.combine(start_date, datetime.min.time()).timestamp() * 1000
    period_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time()).timestamp() * 1000
    
    for session in sessions:
        session_key = session.get('key', 'unknown')
        session_name = session.get('label') or session.get('displayName', 'unknown')
        
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
                dt = datetime.fromtimestamp(msg_timestamp / 1000)
                
                records.append({
                    'timestamp': dt.isoformat(),
                    'date': dt.date().isoformat(),
                    'time': dt.time().isoformat(),
                    'session_key': session_key,
                    'session_name': session_name,
                    'provider': msg.get('provider', 'unknown'),
                    'model': msg.get('model', 'unknown'),
                    'cost': round(cost, 4),
                    'input_tokens': usage.get('input', 0),
                    'output_tokens': usage.get('output', 0),
                    'total_tokens': usage.get('totalTokens', 0),
                    'cache_read_tokens': usage.get('cacheRead', 0),
                    'cache_write_tokens': usage.get('cacheWrite', 0)
                })
    
    return sorted(records, key=lambda x: x['timestamp'])


def export_to_csv(records: List[dict], output_file: str):
    """Export records to CSV"""
    if not records:
        print("No records to export", file=sys.stderr)
        return
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    
    print(f"✅ Exported {len(records)} records to {output_file}")


def export_to_json(records: List[dict], output_file: str):
    """Export records to JSON"""
    with open(output_file, 'w') as f:
        json.dump(records, f, indent=2)
    
    print(f"✅ Exported {len(records)} records to {output_file}")


def print_summary(records: List[dict]):
    """Print summary statistics"""
    if not records:
        print("No records found")
        return
    
    total_cost = sum(r['cost'] for r in records)
    total_tokens = sum(r['total_tokens'] for r in records)
    
    providers = {}
    models = {}
    
    for r in records:
        providers[r['provider']] = providers.get(r['provider'], 0) + r['cost']
        models[r['model']] = models.get(r['model'], 0) + r['cost']
    
    print("\n📊 Export Summary:")
    print(f"  Records: {len(records)}")
    print(f"  Total Cost: ${total_cost:.2f}")
    print(f"  Total Tokens: {total_tokens:,}")
    print(f"\n  Providers: {len(providers)}")
    print(f"  Models: {len(models)}")
    print(f"  Sessions: {len(set(r['session_key'] for r in records))}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export API cost data')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                        help='Export format (default: csv)')
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days to export (default: 7)')
    parser.add_argument('--output', type=str,
                        help='Output file path (default: auto-generated)')
    parser.add_argument('--summary', action='store_true',
                        help='Print summary only (no export)')
    
    args = parser.parse_args()
    
    sessions = get_sessions()
    
    if not sessions:
        print("No sessions found", file=sys.stderr)
        sys.exit(1)
    
    records = extract_cost_records(sessions, args.days)
    
    if not records:
        print(f"No cost records found in the past {args.days} days", file=sys.stderr)
        sys.exit(1)
    
    if args.summary:
        print_summary(records)
        return
    
    # Generate output filename if not specified
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = args.format
        output_file = f"api_costs_{timestamp}.{ext}"
    
    if args.format == 'csv':
        export_to_csv(records, output_file)
    else:
        export_to_json(records, output_file)
    
    print_summary(records)


if __name__ == '__main__':
    main()
