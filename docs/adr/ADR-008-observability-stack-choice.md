# ADR-008: Observability Stack Choice - Prometheus for Metrics, OpenTelemetry for Tracing

* **Status:** Partially Accepted (Metrics implemented, Tracing in progress)
* **Date:** 2025-04-13 (Placeholder)

## Context

* **Problem:** Operating complex, distributed systems like those built upon `athomic` requires deep visibility into their runtime behavior. Without adequate observability, diagnosing performance issues, debugging errors across components, and understanding system health under load becomes extremely difficult. We need ways to answer questions like "Why is this request slow?", "What component failed?", "Are we hitting resource limits?", "What's the error rate for service X?". This requires collecting different kinds of telemetry data.
* **Needs:**
    * **Metrics:** Aggregate numerical data over time (e.g., request counts, latencies, error rates, queue sizes, cache hit/miss ratios [source: 722, 967-969]) for monitoring overall health, identifying trends, setting alerts, and capacity planning.
    * **Traces:** Detailed, request-scoped information showing the path and timing of a request as it flows through different components or services (distributed tracing), essential for pinpointing bottlenecks and understanding complex interactions.
    * **Logs:** Contextual, event-based information (often textual) for specific points in time, primarily used for detailed error diagnosis and understanding specific events. (Logging itself is covered by ADR-004, but its integration with tracing is relevant here).
* **Goal:** Implement a comprehensive and standardized observability solution for `athomic`, leveraging industry-standard, preferably open-source, tools and protocols. This ensures interoperability with common monitoring ecosystems (like Prometheus Operator, Grafana, Jaeger) and avoids vendor lock-in where possible. [source: 279]
* **Alternatives Considered:**
    * **Proprietary APM Solutions (e.g., Datadog, New Relic, Dynatrace):** These offer integrated platforms for metrics, tracing, and logging, often with easy setup via agents. *Drawback:* Can lead to vendor lock-in, potentially higher costs depending on scale, and less control over the data format and collection mechanisms.
    * **Metrics Only (Prometheus):** Implementing only metrics collection using Prometheus. *Drawback:* While essential for monitoring and alerting, it lacks the detailed request-level visibility needed to diagnose complex latency issues or understand distributed workflows, which tracing provides.
    * **Tracing Only (e.g., Jaeger Client Libraries Directly):** Implementing only distributed tracing. *Drawback:* Lacks the high-level aggregated view and alerting capabilities provided by metrics. Can be harder to grasp overall system health trends just from traces.
    * **Logging-Centric Stack (e.g., ELK - Elasticsearch, Logstash, Kibana):** Primarily focused on log aggregation and analysis. Can be extended for metrics (Metricbeat) and tracing (Elastic APM). *Drawback:* Often more resource-intensive, setup can be complex, and Prometheus/OpenTelemetry are arguably more purpose-built and standard for metrics/tracing respectively in many cloud-native environments.
    * **Other Open Standards:** Using older standards like OpenCensus (now merged into OpenTelemetry) or focusing solely on OpenMetrics (a Prometheus exposition format standard). *Decision:* OpenTelemetry emerged as the leading open standard for tracing, integrating aspects of OpenTracing and OpenCensus. Prometheus remains the de facto standard for metrics scraping.

## Decision

* Adopt a **best-of-breed approach using industry-standard open specifications and tools**:
    * **Metrics: Prometheus.**
        * Utilize the official **`prometheus-client`** library [source: 5] for defining and exposing custom application metrics (Counters, Gauges, Histograms for requests, cache stats, secret access, auth events, etc.). [source: 967-969]
        * Leverage **`prometheus-fastapi-instrumentator`** [source: 5] and/or custom middleware (`RequestMetricsMiddleware` [source: 1131]) to automatically instrument FastAPI HTTP requests for standard metrics (count, latency, in-progress).
        * Expose all collected metrics via a standard **`/metrics` HTTP endpoint** [source: 1150] in the Prometheus exposition format, allowing a Prometheus server to scrape the data.
    * **Tracing: OpenTelemetry (OTel).** [source: 13, 187]
        * Standardize on **OpenTelemetry** as the vendor-neutral framework for generating, collecting, and exporting trace data. [source: 5]
        * Utilize **OTel instrumentation libraries** (e.g., `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-requests`, etc. [source: 5]) for automatic trace context propagation and span creation for supported libraries and frameworks. A basic setup exists in `src/nala/api/middleware/tracing.py`. [source: 1129]
        * Configure an **OTLP (OpenTelemetry Protocol) Exporter** [source: 1129] (specifically `OTLPSpanExporter` initially) to send trace data to a compatible backend (e.g., Jaeger, Grafana Tempo, SigNoz, or commercial APM tools). The backend endpoint, protocol (gRPC/HTTP), headers, and sampling rate will be configurable via `ObservabilitySettings`. [source: 815, 816]
        * Plan for **manual instrumentation** (creating spans explicitly) within critical sections of the `athomic` layer or complex business logic where auto-instrumentation doesn't provide sufficient detail (currently a TODO/roadmap item). [source: 187, 541]
    * **Logging Integration:** While handled by SafeLogger (ADR-004), ensure that trace context (Trace ID, Span ID) can be automatically injected into log records (a common OTel logging library integration pattern, *not yet explicitly shown* in the provided code but essential for correlating logs with traces).
* Centralize all observability configurations (enable/disable flags, exporter details, sampling rates) within the **`ObservabilitySettings`** Pydantic model [source: 813] managed by the central configuration system (ADR-001).

## Consequences

* **Positive:**
    * **Industry Standard & Interoperability:** Aligns `athomic` with widely adopted open standards, ensuring compatibility with a vast ecosystem of monitoring, alerting, and analysis tools (Grafana, Prometheus Operator, Jaeger, various OTel backends).
    * **Vendor Neutrality (especially for Tracing):** OpenTelemetry allows switching tracing backends without changing the application instrumentation code.
    * **Comprehensive Visibility:** The combination of metrics (aggregate view, alerting) and traces (deep request-level diagnosis) provides powerful observability.
    * **Rich Ecosystem & Community:** Benefits from the extensive tooling, documentation, and community support surrounding Prometheus and OpenTelemetry.
    * **Automation Potential:** OTel auto-instrumentation reduces the effort required for basic tracing coverage.
    * **Consistency:** Establishes a standardized approach for instrumenting code within the `athomic`.
* **Negative:**
    * **Operational Complexity:** Requires setting up and managing a potentially complex external stack (Prometheus server, OTel Collector (recommended), tracing storage/backend like Jaeger or Tempo, visualization tool like Grafana).
    * **Performance Overhead:** Collecting detailed metrics and traces inevitably introduces some performance overhead on the application, although tools are designed to minimize this. Trace sampling [source: 816] is often necessary in high-volume systems but means some requests won't be traced.
    * **Learning Curve:** Developers need to understand the core concepts of metrics (types, labels, cardinality) and distributed tracing (spans, context, propagation) to instrument code effectively and interpret the data.
    * **Incomplete Implementation (Current State):** While the foundation is laid and metrics are functional, the tracing implementation requires further work to be fully realized (completing OTel setup, adding manual instrumentation where needed, ensuring log correlation). [source: 13, 180, 194]
* **Neutral/Other:**
    * Effective monitoring requires careful dashboard design (e.g., in Grafana) and well-configured alerts based on the collected metrics.
    * The usefulness of tracing heavily depends on consistent context propagation across asynchronous tasks and service boundaries (if applicable), as well as sufficient instrumentation coverage (both automatic and manual).
    * Managing metric cardinality (the number of unique label combinations) is important to avoid overloading the Prometheus server.
    