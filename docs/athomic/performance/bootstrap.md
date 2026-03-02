# Performance Bootstrap (uvloop)

## Overview

The `athomic.performance.bootstrap` module contains utilities that should be run at the very beginning of the application's lifecycle to apply performance optimizations.

## `install_uvloop_if_available()`

The primary utility is `install_uvloop_if_available()`. **uvloop** is a high-performance, drop-in replacement for Python's default `asyncio` event loop. It is implemented in Cython and built on top of `libuv`, the same library that powers Node.js.

By using uvloop, your application can achieve significant performance improvements for I/O-bound operations, often seeing a 2-4x increase in throughput.

### How It Works
This function is called in your application's entrypoint (e.g., `main.py`) **before** any other code runs. It attempts to import `uvloop`.
-   If the `uvloop` package is installed in the environment, it sets it as the global asyncio event loop policy.
-   If it's not installed, it does nothing, and the application gracefully falls back to using the standard asyncio event loop.

This allows `uvloop` to be an optional, production-only dependency.