# athomic

![Coverage](https://github.com/test-nala/athomic/blob/coverage-badges/coverage.svg)

# Teste Nala: Athomic

**The IDP for Resilient, Observable, and High-Performance Python Microservices.**

Build robust services in record time, focusing on what truly matters: your business logic.

[![CI Status](https://img.shields.io/github/actions/workflow/status/test-nala/athomic/ci.yml?branch=main&style=for-the-badge)](https://github.com/test-nala/athomic/actions)
[![Release](https://img.shields.io/github/v/release/test-nala/athomic?style=for-the-badge)](https://github.com/test-nala/athomic/releases)
[![Commitizen friendly](https://img.shields.io/badge/Commitizen-friendly-brightgreen.svg?style=for-the-badge)](http://commitizen.github.io/cz-cli/)
[![License](https://img.shields.io/github/license/test-nala/athomic?style=for-the-badge)](https://github.com/test-nala/athomic/blob/main/LICENSE)

---

## 🔥 The Problem: The Hidden Complexity of Microservices

Building microservices goes far beyond writing business logic. Engineering teams spend precious time repeatedly solving the same infrastructure challenges:
- How to ensure that communication between services is **resilient to failures**?
- How to gain **complete visibility** (Logs, Metrics, Traces) into what's happening in production?
- How to maintain code **quality, consistency, and security** as the team grows?
- How to ensure the **developer experience (DevEx)** is simple and productive?

Solving these problems from scratch for every new service is inefficient, expensive, and risky.

## ✨ The Solution: The Athomic Layer

**Teste Nala** (internally named **Athomic**) is an opinionated and extensible IDP that solves these challenges once and for all. It provides a solid, production-ready foundation, allowing your developers to focus exclusively on delivering value.

We abstract away the infrastructure complexity so you don't have to.

---

## 🚀 Value Proposition & Key Features

With Athomic, your team gains superpowers to build world-class services.

### 🛡️ Native Resilience (Bulletproof Services)
Build self-healing systems that handle failures gracefully.
- **Circuit Breaker:** Automatically isolates failing components.
- **Smart Retries:** Configures retry mechanisms with exponential backoff.
- **Rate Limiter:** Protects your services against traffic spikes.
- **Fallback:** Defines alternative behaviors in case of an error.

### 🔭 Autopilot Observability (The 3 Pillars)
Gain deep insights into your application's behavior effortlessly.
- **Structured Logging:** JSON logs, ready to be ingested by any platform.
- **Prometheus Metrics:** Export performance and business metrics in a standardized way.
- **Distributed Tracing (OpenTelemetry):** Trace requests across multiple services with a unified context.

### 💻 Superior Developer Experience (Superior DevEx)
A modern tool ecosystem that ensures quality and productivity from day one.
- **Dependency Management with Poetry:** A reproducible and deterministic development environment.
- **Automated Code Quality:** `black`, `ruff`, and `mypy` ensure clean, error-free code, enforced with `pre-commit` hooks.
- **One-Command Local Environment:** `docker-compose` to spin up all necessary infrastructure (Kafka, Redis, Vault, etc.).

### 🏗️ Solid & Extensible Architecture
A decoupled and explicit codebase that promotes the best engineering practices.
- **Simplified Dependency Injection:** A clear application lifecycle that facilitates testing and maintenance.
- **Proven Design Patterns:** Use of Factory, Facade, and Registry for a clean architecture.
- **Easy to Extend:** Add new infrastructure integrations (e.g., a new database, a new message broker) without altering the core.

---

## 🤝 Contributing

This is a project that thrives on collaboration. If you wish to contribute, please read our `CONTRIBUTING.md` to learn about our development process and our `CODE_OF_CONDUCT.md` to understand our community standards.

---

Made with ❤️ by the Guandaline for Test Nala

>© test-nala 2025
