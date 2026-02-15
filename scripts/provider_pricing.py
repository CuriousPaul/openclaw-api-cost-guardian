#!/usr/bin/env python3
"""
Provider Pricing Information
Updated: 2026-02-15
"""

# Provider별 최신 가격 정보 (2026-02)
# 가격은 USD per token 단위
PRICING = {
    'anthropic': {
        'claude-opus-4-6': {
            'input': 0.000015,      # $15/M tokens
            'output': 0.000075,     # $75/M tokens
            'cache_read': 0.00000015,   # $0.15/M tokens
            'cache_write': 0.0000375    # $37.50/M tokens
        },
        'claude-sonnet-4-5': {
            'input': 0.000003,      # $3/M tokens
            'output': 0.000015,     # $15/M tokens
            'cache_read': 0.00000003,   # $0.03/M tokens
            'cache_write': 0.0000015    # $1.50/M tokens
        },
        'claude-sonnet-3-5': {
            'input': 0.000003,
            'output': 0.000015,
            'cache_read': 0.00000003,
            'cache_write': 0.0000015
        },
        'claude-haiku-3-5': {
            'input': 0.0000008,     # $0.80/M tokens
            'output': 0.000004,     # $4/M tokens
            'cache_read': 0.00000008,
            'cache_write': 0.0000004
        }
    },
    'openai': {
        'gpt-4o': {
            'input': 0.0000025,     # $2.50/M tokens
            'output': 0.00001,      # $10/M tokens
            'cache_read': 0.00000125,   # 50% discount
            'cache_write': 0.0000125    # 5x input cost
        },
        'gpt-4o-mini': {
            'input': 0.00000015,    # $0.15/M tokens
            'output': 0.0000006,    # $0.60/M tokens
            'cache_read': 0.000000075,
            'cache_write': 0.00000075
        },
        'gpt-4-turbo': {
            'input': 0.00001,       # $10/M tokens
            'output': 0.00003,      # $30/M tokens
        },
        'gpt-4': {
            'input': 0.00003,       # $30/M tokens
            'output': 0.00006       # $60/M tokens
        },
        'gpt-3.5-turbo': {
            'input': 0.0000005,     # $0.50/M tokens
            'output': 0.0000015     # $1.50/M tokens
        }
    },
    'google': {
        'gemini-2.5-flash': {
            'input': 0.00000015,    # $0.15/M tokens (무료 tier 있음)
            'output': 0.00000060,   # $0.60/M tokens
            'cache_read': 0.00000001875,  # $0.01875/M tokens
            'cache_write': 0.0000001875   # $0.1875/M tokens
        },
        'gemini-1.5-flash': {
            'input': 0.000000075,   # $0.075/M tokens
            'output': 0.0000003,    # $0.30/M tokens
            'cache_read': 0.00000001875,
            'cache_write': 0.0000001875
        },
        'gemini-1.5-pro': {
            'input': 0.00000125,    # $1.25/M tokens
            'output': 0.00000375,   # $3.75/M tokens
            'cache_read': 0.0000003125,
            'cache_write': 0.000003125
        },
        'gemini-pro': {
            'input': 0.0000005,     # $0.50/M tokens
            'output': 0.0000015     # $1.50/M tokens
        }
    },
    'zai': {
        'glm-5': {
            'input': 0.000001,      # 예상 $1/M tokens
            'output': 0.000003      # 예상 $3/M tokens
        },
        'glm-4.7': {
            'input': 0.0000008,     # 예상 $0.80/M tokens
            'output': 0.0000024     # 예상 $2.40/M tokens
        },
        'glm-4': {
            'input': 0.000001,
            'output': 0.000003
        }
    },
    'ollama': {
        # 로컬 모델 - 완전 무료
        '*': {
            'input': 0.0,
            'output': 0.0,
            'cache_read': 0.0,
            'cache_write': 0.0
        }
    }
}


def get_model_pricing(provider: str, model: str) -> dict:
    """
    특정 provider와 model의 가격 정보를 가져옴
    
    Args:
        provider: Provider 이름 (anthropic, openai, google, zai, ollama)
        model: 모델명 (전체 경로 또는 짧은 이름)
    
    Returns:
        dict: 가격 정보 (input, output, cache_read, cache_write)
              찾지 못한 경우 None
    """
    # Provider 정규화
    provider_lower = provider.lower()
    
    # Ollama는 모든 모델이 무료
    if provider_lower == 'ollama':
        return PRICING['ollama']['*']
    
    # Provider가 없으면 None
    if provider_lower not in PRICING:
        return None
    
    provider_pricing = PRICING[provider_lower]
    
    # 모델명에서 마지막 부분만 추출 (예: anthropic/claude-sonnet-4-5 -> claude-sonnet-4-5)
    model_short = model.split('/')[-1] if '/' in model else model
    model_lower = model_short.lower()
    
    # 정확히 일치하는 모델 찾기
    for model_key, pricing in provider_pricing.items():
        if model_key.lower() == model_lower or model_key.lower() in model_lower:
            return pricing
    
    # 부분 일치 시도 (예: claude-sonnet-4-5-20250929 -> claude-sonnet-4-5)
    for model_key, pricing in provider_pricing.items():
        if model_key.lower() in model_lower:
            return pricing
    
    return None


def calculate_cost(provider: str, model: str, usage: dict) -> float:
    """
    Usage 정보를 바탕으로 비용 계산
    
    Args:
        provider: Provider 이름
        model: 모델명
        usage: Usage 정보 (input, output, cacheRead, cacheWrite)
    
    Returns:
        float: 계산된 비용 (USD)
    """
    pricing = get_model_pricing(provider, model)
    
    if pricing is None:
        return 0.0
    
    cost = 0.0
    
    # Input tokens
    if 'input' in usage and usage['input'] > 0:
        cost += usage['input'] * pricing.get('input', 0.0)
    
    # Output tokens
    if 'output' in usage and usage['output'] > 0:
        cost += usage['output'] * pricing.get('output', 0.0)
    
    # Cache read tokens
    if 'cacheRead' in usage and usage['cacheRead'] > 0:
        cost += usage['cacheRead'] * pricing.get('cache_read', 0.0)
    
    # Cache write tokens
    if 'cacheWrite' in usage and usage['cacheWrite'] > 0:
        cost += usage['cacheWrite'] * pricing.get('cache_write', 0.0)
    
    return cost


def is_free_provider(provider: str) -> bool:
    """Provider가 무료인지 확인"""
    return provider.lower() == 'ollama'


def get_supported_providers() -> list:
    """지원하는 Provider 목록"""
    return list(PRICING.keys())


def get_provider_models(provider: str) -> list:
    """특정 Provider의 모델 목록"""
    provider_lower = provider.lower()
    if provider_lower not in PRICING:
        return []
    return list(PRICING[provider_lower].keys())


if __name__ == '__main__':
    # 테스트
    import json
    
    print("=== Supported Providers ===")
    for provider in get_supported_providers():
        models = get_provider_models(provider)
        print(f"\n{provider.upper()}: {len(models)} models")
        for model in models:
            pricing = get_model_pricing(provider, model)
            print(f"  • {model}")
            print(f"    Input: ${pricing['input']*1000000:.2f}/M | Output: ${pricing['output']*1000000:.2f}/M")
    
    print("\n\n=== Test Cost Calculation ===")
    test_cases = [
        ('anthropic', 'claude-sonnet-4-5', {'input': 1000, 'output': 500}),
        ('openai', 'gpt-4o', {'input': 1000, 'output': 500}),
        ('google', 'gemini-2.5-flash', {'input': 1000, 'output': 500}),
        ('ollama', 'llama3', {'input': 1000, 'output': 500}),
    ]
    
    for provider, model, usage in test_cases:
        cost = calculate_cost(provider, model, usage)
        print(f"{provider}/{model}: ${cost:.6f}")
