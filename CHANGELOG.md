# Changelog

All notable changes to API Cost Guardian will be documented in this file.

## [1.2.0] - 2026-02-15

### Added
- **Multi-Provider Support**: Full support for all major AI providers
  - ✅ Anthropic (Claude Opus, Sonnet, Haiku)
  - ✅ OpenAI (GPT-4o, GPT-4, GPT-3.5)
  - ✅ Google (Gemini Flash, Pro)
  - ✅ ZAI (GLM-5, GLM-4.7)
  - ✅ Ollama (local models - completely FREE)

- **Provider Pricing Module**: New `provider_pricing.py`
  - Up-to-date pricing for all supported providers
  - Automatic cost calculation when OpenClaw data is missing
  - Cache token pricing support (cache_read, cache_write)
  - Helper functions: `get_model_pricing()`, `calculate_cost()`, `is_free_provider()`

- **Enhanced Reporting**: Improved cost reports with provider breakdown
  - Separate sections for paid vs free providers
  - Provider-level TOP 5 models
  - Free models clearly marked
  - Better formatting for multi-provider scenarios

### Changed
- `analyze_cost_v2.py` now uses `provider_pricing.py` for fallback cost calculation
- Report format improved to distinguish paid/free providers
- Cost calculation more robust with fallback logic

### Documentation
- Updated README.md with full provider support table
- Updated SKILL.md with provider-specific examples
- Added pricing examples and free provider highlights

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
