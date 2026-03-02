# Caching

## Overview

The Caching module provides a powerful, decorator-based system for caching the results of asynchronous functions. It is designed to be highly resilient and performant, implementing several advanced caching strategies out-of-the-box.

### Key Features
-   **`@cache` Decorator**: The primary interface for caching function results.
-   **`@invalidate_cache` Decorator**: For declaratively invalidating cache keys.
-   **Resilient Fallback**: Can be configured with a fallback cache (e.g., in-memory) that is used if the primary cache (e.g., Redis) is unavailable.
-   **Single-Flight Caching**: Uses a distributed lock to prevent the "thundering herd" problem, where multiple concurrent requests for a missed key all trigger the expensive computation.
-   **Refresh-Ahead (Stale-While-Revalidate)**: Can serve stale data while a background task refreshes the cache, minimizing latency for users.

## Usage
```python
from nala.athomic.performance import cache, invalidate_cache

class ProductService:
    @cache(ttl=300, key_prefix="products") # Cache results for 5 minutes
    async def get_product_details(self, product_id: str) -> dict:
        # Expensive database call
        return await db.fetch_product(product_id)
        
    @invalidate_cache(key_prefix="products", key_resolver=lambda result, **kwargs: f"products:{kwargs['product_id']}")
    async def update_product_details(self, product_id: str, data: dict):
        # Update the product in the database
        # The cache for this product will be automatically invalidated.
        return await db.update_product(product_id, data)
```

For more details on the resilient provider, see the [**Fallback**](../resilience/fallback.md) documentation.

## API Reference
::: nala.athomic.performance.cache.decorators.cache
::: nala.athomic.performance.cache.decorators.invalidate_cache