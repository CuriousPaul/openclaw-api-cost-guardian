# Changelog

All notable changes to API Cost Guardian will be documented in this file.

## [1.1.0] - 2026-02-15

### Added
- **Weekly/Monthly Reports**: New `weekly_report.py` script for trend analysis
  - Analyze costs over 7 or 30 days
  - Calculate average, max, min, median costs
  - Detect cost trends (rising, falling, stable)
  - ASCII charts for visualization
  - Budget usage tracking

- **Data Export**: New `export_cost_data.py` script
  - Export to CSV or JSON format
  - Support for custom date ranges
  - Detailed session-level cost records
  - Summary statistics

- **Model Comparison**: New `model_comparison.py` script
  - Compare costs across different models
  - Cost efficiency metrics ($/call, $/1K tokens)
  - ASCII charts for cost and usage visualization
  - Automatic savings opportunity identification
  - High-cost model detection

### Changed
- Updated README.md with new features
- Added npm scripts for new tools

### Documentation
- Added comprehensive examples for new features
- Updated usage instructions
- Added cost optimization tips

## [1.0.0] - 2026-02-15

### Added
- Initial release
- Real-time cost tracking
- 3-tier alerting system (warning/urgent/critical)
- Provider and model-level cost breakdown
- Daily cost prediction
- Telegram notifications
- Cron automation support
- Cost reduction recommendations
