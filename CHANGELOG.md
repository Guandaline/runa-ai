# CHANGELOG

<!-- version list -->

## v3.40.0 (2026-02-19)

### Features

- **ai/rag**: Implement Hybrid GraphRAG and polymorphic retrieval factory
  ([#229](https://github.com/test-nala/athomic/pull/229),
  [`3663efc`](https://github.com/test-nala/athomic/commit/3663efc518cae2e83c9d7cc2feb3e6abdc8df4f1))


## v3.39.0 (2026-02-10)

### Features

- **ai/graph**: Finalize persistence layer and update RAG docs
  ([#228](https://github.com/test-nala/athomic/pull/228),
  [`a68f866`](https://github.com/test-nala/athomic/commit/a68f8668547d3fa5650fa757d35a88a9aed3ec40))


## v3.38.0 (2026-01-20)

### Features

- **ai/graph**: Implement entity and relation extraction pipeline
  ([#227](https://github.com/test-nala/athomic/pull/227),
  [`93a4553`](https://github.com/test-nala/athomic/commit/93a4553accc4f06ddab25219aa243756accaf027))


## v3.37.0 (2026-01-19)

### Features

- **database**: Implement neo4j provider, migrations backend, and multi-tenancy wrappers
  ([#226](https://github.com/test-nala/athomic/pull/226),
  [`f4c3438`](https://github.com/test-nala/athomic/commit/f4c343860436a27886ec18ffa66f468be466cafc))


## v3.36.0 (2026-01-19)

### Features

- **observability**: Implement AgentTracing for automated agent telemetry
  ([#225](https://github.com/test-nala/athomic/pull/225),
  [`a5ff260`](https://github.com/test-nala/athomic/commit/a5ff26018a686514219d79615e7a2c9bd9f39d6d))


## v3.35.0 (2026-01-19)

### Chores

- **deps**: Bump pyasn1 from 0.6.1 to 0.6.2
  ([#222](https://github.com/test-nala/athomic/pull/222),
  [`9add31c`](https://github.com/test-nala/athomic/commit/9add31cbeb0d023c6e5ec597ccfc555964d19f06))

### Features

- **workflow**: Introduce Universal Workflow Orchestration architecture (ADR-130)
  ([#224](https://github.com/test-nala/athomic/pull/224),
  [`2f650c6`](https://github.com/test-nala/athomic/commit/2f650c6238260f7a49132c73e4691445a413ed38))


## v3.34.0 (2026-01-16)

### Features

- **ai**: Implement RAG context compression and token optimization
  ([#223](https://github.com/test-nala/athomic/pull/223),
  [`3a212ad`](https://github.com/test-nala/athomic/commit/3a212ad7d3c04264d33b8607d288f22a7a59bc2f))


## v3.33.0 (2026-01-09)

### Features

- **ai**: Implementa Otimização de Janela de Contexto e Orçamento Dinâmico de Tokens
  ([#221](https://github.com/test-nala/athomic/pull/221),
  [`bcfbc4c`](https://github.com/test-nala/athomic/commit/bcfbc4c81566933711601de6355b9ae2ebeef440))


## v3.32.0 (2026-01-07)

### Features

- **ai**: Implement cognitive intent engine with robust llm provider
  ([#220](https://github.com/test-nala/athomic/pull/220),
  [`6065814`](https://github.com/test-nala/athomic/commit/6065814a64a4c621d7cc415c6042f7dc127e268b))


## v3.31.0 (2026-01-06)

### Chores

- **deps**: Bump aiohttp from 3.13.2 to 3.13.3
  ([#217](https://github.com/test-nala/athomic/pull/217),
  [`d404148`](https://github.com/test-nala/athomic/commit/d404148df06e4086c839e40f2ac14931add1d9e8))

### Documentation

- **architecture**: Clarify runtime EventBus vs messaging vs outbox boundaries
  ([#215](https://github.com/test-nala/athomic/pull/215),
  [`acae081`](https://github.com/test-nala/athomic/commit/acae081bf90cbb4ab4e49bf4c5d6b99e460e194b))

### Features

- **rag**: Upgrade pipeline with HyDE, Re-ranking, and integration tests
  ([#219](https://github.com/test-nala/athomic/pull/219),
  [`876f00d`](https://github.com/test-nala/athomic/commit/876f00ddaad95034c2f2dda36c1e2ce9f6fe5997))

### Refactoring

- **redis**: Centralize Lua script management and decouple providers
  ([#218](https://github.com/test-nala/athomic/pull/218),
  [`fbfcf31`](https://github.com/test-nala/athomic/commit/fbfcf31c21df5875b45abe0be9f97bb907f2992a))

- **storage**: Migrate GCS provider to async gcloud-aio with session management
  ([#216](https://github.com/test-nala/athomic/pull/216),
  [`ad89dbf`](https://github.com/test-nala/athomic/commit/ad89dbf16341dc87c562e001970cf2da7af55034))


## v3.30.0 (2026-01-05)

### Features

- **ai/documents**: Implement strategy pattern for text splitters
  ([#214](https://github.com/test-nala/athomic/pull/214),
  [`58238bd`](https://github.com/test-nala/athomic/commit/58238bd2a8a0ee59c45db1088652568ab526598c))


## v3.29.0 (2026-01-03)

### Features

- **ai**: Implement secure Sandbox Service and Code Interpreter tool
  ([#213](https://github.com/test-nala/athomic/pull/213),
  [`1bdc863`](https://github.com/test-nala/athomic/commit/1bdc863884b854a40996bbea9d85b72cb5b091c1))


## v3.28.0 (2026-01-02)

### Features

- **execution**: Integrate usage reporting and refactor emitter factory
  ([#212](https://github.com/test-nala/athomic/pull/212),
  [`08e4c1d`](https://github.com/test-nala/athomic/commit/08e4c1d203a21a7db8f6669aa7378af9939e4392))

### Refactoring

- **athomic**: Enhance execution manager and messaging emitter reliability
  ([#211](https://github.com/test-nala/athomic/pull/211),
  [`343396c`](https://github.com/test-nala/athomic/commit/343396c08be9163baa2a3b7fcdafb2af6d7108a1))


## v3.27.0 (2025-12-28)

### Chores

- Fix import bug ([#210](https://github.com/test-nala/athomic/pull/210),
  [`c694f07`](https://github.com/test-nala/athomic/commit/c694f07b59a17803df1700a3f6a3c156c8da8b44))

### Features

- **usage**: Implement messaging-based usage emission backend
  ([#210](https://github.com/test-nala/athomic/pull/210),
  [`c694f07`](https://github.com/test-nala/athomic/commit/c694f07b59a17803df1700a3f6a3c156c8da8b44))


## v3.26.0 (2025-12-25)

### Features

- **execution**: Implement transversal execution domain (ADR-122)
  ([#209](https://github.com/test-nala/athomic/pull/209),
  [`11182d6`](https://github.com/test-nala/athomic/commit/11182d6c232760ef454b5f6206a2403ffff9e231))


## v3.25.0 (2025-12-23)

### Features

- **messaging,lifecycle,registry**: Harden service shutdown, registry semantics and Kafka consumer
  lifecycle ([#208](https://github.com/test-nala/athomic/pull/208),
  [`81b2294`](https://github.com/test-nala/athomic/commit/81b22947b83554fe2813f5b49a230369c48a55b5))

- **session**: Introduce generic async session leasing and lifecycle management
  ([#208](https://github.com/test-nala/athomic/pull/208),
  [`81b2294`](https://github.com/test-nala/athomic/commit/81b22947b83554fe2813f5b49a230369c48a55b5))


## v3.24.0 (2025-12-19)

### Features

- **ai**: Implement knowledge graph module for GraphRAG
  ([#207](https://github.com/test-nala/athomic/pull/207),
  [`56d6e29`](https://github.com/test-nala/athomic/commit/56d6e29ed2bb3dafe63d6ac428fe6fbbd1f1647d))


## v3.23.0 (2025-12-19)

### Features

- **ai/qa**: Implement AI evaluation harness and QA service
  ([#206](https://github.com/test-nala/athomic/pull/206),
  [`3e27121`](https://github.com/test-nala/athomic/commit/3e27121fe56b7b2c28b85d429d2395cae90a40d1))


## v3.22.0 (2025-12-16)

### Features

- **ai/agents**: Integrate state persistence into runtime and factory
  ([#205](https://github.com/test-nala/athomic/pull/205),
  [`b6fa0e0`](https://github.com/test-nala/athomic/commit/b6fa0e09bd04c61077bd935384a9bfce444b56a8))


## v3.21.0 (2025-12-16)

### Features

- **ai**: Implement semantic cache for LLM optimization
  ([#204](https://github.com/test-nala/athomic/pull/204),
  [`5b4d5e2`](https://github.com/test-nala/athomic/commit/5b4d5e268deb67024c914ec29f1907d3acb8edcf))


## v3.20.0 (2025-12-14)

### Features

- **ai**: Implement standardized LLM streaming, governance, and RAG v2 pipeline
  ([#203](https://github.com/test-nala/athomic/pull/203),
  [`2a6a6cb`](https://github.com/test-nala/athomic/commit/2a6a6cbd6ff2e2d407edb884a2119c12de90f292))


## v3.19.0 (2025-12-13)

### Features

- **ai/governance**: Implement Guard Pipeline and Centralize LLM Governance
  ([#202](https://github.com/test-nala/athomic/pull/202),
  [`7c3c8be`](https://github.com/test-nala/athomic/commit/7c3c8bef3b3e3988f4a1a62a20e4d0ffabd9477c))


## v3.18.0 (2025-12-13)

### Features

- **ai**: Implement RAG Core Service and Strategy Pattern
  ([#201](https://github.com/test-nala/athomic/pull/201),
  [`add548e`](https://github.com/test-nala/athomic/commit/add548e6af2a3cc35fbeea7d5fb735bffc765389))


## v3.17.0 (2025-12-12)

### Features

- **ai**: Implement EvalOps architecture and stabilize Google GenAI integration
  ([#200](https://github.com/test-nala/athomic/pull/200),
  [`5e7c298`](https://github.com/test-nala/athomic/commit/5e7c298e69dedd270418f5727d1964d5448e829d))


## v3.16.0 (2025-12-11)

### Features

- **ai**: Implement modular Document Ingestion pipeline and Embedding Manager
  ([#199](https://github.com/test-nala/athomic/pull/199),
  [`dd32b3b`](https://github.com/test-nala/athomic/commit/dd32b3bb809f73387b017b809caee84c4ad675e5))


## v3.15.0 (2025-12-10)

### Features

- **ai**: Implement modular Agent architecture and refactor migration tests
  ([#198](https://github.com/test-nala/athomic/pull/198),
  [`1c3105c`](https://github.com/test-nala/athomic/commit/1c3105cea9ef774ca66696f8fc99622df0e0d280))


## v3.14.0 (2025-12-08)

### Features

- **ai**: Implement decoupled prompt management system
  ([#197](https://github.com/test-nala/athomic/pull/197),
  [`3c784e1`](https://github.com/test-nala/athomic/commit/3c784e1130503bf00c6cb183484802dc2f553999))


## v3.13.0 (2025-12-08)

### Features

- **ai**: Upgrade Google GenAI SDK and refactor OpenAI/Ollama providers
  ([#196](https://github.com/test-nala/athomic/pull/196),
  [`6b10330`](https://github.com/test-nala/athomic/commit/6b103304d5659d85a94259eb4816133002a71970))


## v3.12.0 (2025-12-05)

### Features

- **ai**: Implement tools layer with schema generation and registry
  ([#195](https://github.com/test-nala/athomic/pull/195),
  [`1d1b33d`](https://github.com/test-nala/athomic/commit/1d1b33d202d11b864f50d9e2f39df78812191ace))

### Refactoring

- **ai**: Implement lazy initialization for VertexAIProvider
  ([#194](https://github.com/test-nala/athomic/pull/194),
  [`aee446d`](https://github.com/test-nala/athomic/commit/aee446d8fd81b0772549afcc1a831099b71ce0f3))


## v3.11.0 (2025-12-05)

### Chores

- **depend**: Fix dependencies for torch on mac
  ([#192](https://github.com/test-nala/athomic/pull/192),
  [`3318f50`](https://github.com/test-nala/athomic/commit/3318f500aac681cc124025a3adf98f96cf4a8163))

### Features

- **migrations**: Add distributed locking to prevent race conditions
  ([#193](https://github.com/test-nala/athomic/pull/193),
  [`a805e29`](https://github.com/test-nala/athomic/commit/a805e29368c5cc314dd8f372f4b0d1277d9d1b97))


## v3.10.0 (2025-12-05)

### Features

- **ai**: Implement comprehensive AI module with LLMs, Embeddings, and Memory
  ([#191](https://github.com/test-nala/athomic/pull/191),
  [`d4b86b1`](https://github.com/test-nala/athomic/commit/d4b86b111f0586a8f5207171148a7f7915a61c09))

- **vector**: Finalize implementation, fix factory logic, and add documentation
  ([#191](https://github.com/test-nala/athomic/pull/191),
  [`d4b86b1`](https://github.com/test-nala/athomic/commit/d4b86b111f0586a8f5207171148a7f7915a61c09))

- **vector**: Finalize implementation, fix factory logic, and add doc…
  ([#191](https://github.com/test-nala/athomic/pull/191),
  [`d4b86b1`](https://github.com/test-nala/athomic/commit/d4b86b111f0586a8f5207171148a7f7915a61c09))


## v3.9.0 (2025-12-01)

### Features

- **lineage**: Refactor architecture to provider-collector pattern with composite storage
  ([#190](https://github.com/test-nala/athomic/pull/190),
  [`e3d88c7`](https://github.com/test-nala/athomic/commit/e3d88c775d486c67d1c678408156ddf2e7e81e68))


## v3.8.0 (2025-11-28)

### Chores

- **deps**: Bump actions/checkout in the github-actions group
  ([#186](https://github.com/test-nala/athomic/pull/186),
  [`9b12912`](https://github.com/test-nala/athomic/commit/9b12912c878499615b219e3382e22a1eef68531b))

### Features

- **database**: Implement Neo4j graph database infrastructure
  ([#189](https://github.com/test-nala/athomic/pull/189),
  [`2ffb8d1`](https://github.com/test-nala/athomic/commit/2ffb8d1a692699d0303b394c15b3174e6ccf7ba7))


## v3.7.0 (2025-11-28)

### Features

- **athomic**: Implement Service Mesh readiness mode
  ([#188](https://github.com/test-nala/athomic/pull/188),
  [`5cc4591`](https://github.com/test-nala/athomic/commit/5cc4591fbda246a11e3144b110744f03d1047fc9))


## v3.6.0 (2025-11-26)

### Features

- **workflows**: Implement agnostic Durable Workflow module with Temporal and Local providers
  ([#187](https://github.com/test-nala/athomic/pull/187),
  [`b314395`](https://github.com/test-nala/athomic/commit/b314395365f4bc028addcacf301067a89545a288))


## v3.5.0 (2025-11-16)

### Features

- **messaging**: Implement batch idempotency and standardize key generation
  ([#185](https://github.com/test-nala/athomic/pull/185),
  [`a7782a7`](https://github.com/test-nala/athomic/commit/a7782a778aac1454cd3dff7aa5dd200d86b2dc96))

### Refactoring

- **resilience**: Make idempotency handler protocol-agnostic and fix tests
  ([#184](https://github.com/test-nala/athomic/pull/184),
  [`c038f60`](https://github.com/test-nala/athomic/commit/c038f60ec1e7080a1f2824c0a0c01116796fcd0a))


## v3.4.0 (2025-11-12)

### Chores

- **deps**: Bump the poetry-dependencies group across 1 directory with 45 updates
  ([#177](https://github.com/test-nala/athomic/pull/177),
  [`1c75a8d`](https://github.com/test-nala/athomic/commit/1c75a8dcb106a0df5a766d86e2b6f406126d5142))

### Features

- **messaging**: Implement Causal Consistency and refactor Consumer architecture
  ([#180](https://github.com/test-nala/athomic/pull/180),
  [`da8e6dd`](https://github.com/test-nala/athomic/commit/da8e6dd2e26a7c467c4171dd1f1fe90330cf0479))


## v3.3.0 (2025-11-07)

### Chores

- **deps**: Bump the github-actions group with 2 updates
  ([#172](https://github.com/test-nala/athomic/pull/172),
  [`e76dbb8`](https://github.com/test-nala/athomic/commit/e76dbb8975cb2898890e4cdfb369254c495ba6ba))

- **deps**: Bump the poetry-dependencies group with 23 updates
  ([#173](https://github.com/test-nala/athomic/pull/173),
  [`d0a3129`](https://github.com/test-nala/athomic/commit/d0a312986b439927aa0221efcdb39baea96b81d1))

### Features

- **core, streaming**: Add stateful streaming/windowing engine and implement ADR-097
  ([#178](https://github.com/test-nala/athomic/pull/178),
  [`d194d33`](https://github.com/test-nala/athomic/commit/d194d33a2ab6ae48d46680f75bd52a09fa9bea6e))

### Refactoring

- **core**: Implement explicit Dependency Injection pattern (ADR-094)
  ([#176](https://github.com/test-nala/athomic/pull/176),
  [`afe8a58`](https://github.com/test-nala/athomic/commit/afe8a582cdcd620f253a4f5c3d434ffda8e77e24))

- **migrations**: Centralize dynamic module loading utility
  ([`aabdded`](https://github.com/test-nala/athomic/commit/aabdded562012570cd116d4fb2120780f8a4d793))


## v3.2.0 (2025-10-02)

### Features

- **messaging**: Implement Priority Queues and Concurrency Control
  ([#174](https://github.com/test-nala/athomic/pull/174),
  [`45c7913`](https://github.com/test-nala/athomic/commit/45c7913907b6f7f826ee3636ef846f5d6b097c7a))


## v3.1.0 (2025-09-28)

### Chores

- **docs**: Clear docs ([#171](https://github.com/test-nala/athomic/pull/171),
  [`2dbaf81`](https://github.com/test-nala/athomic/commit/2dbaf81f645657a24bae51e1ad6018a0274e3939))

- **reademe**: Add readme content ([#171](https://github.com/test-nala/athomic/pull/171),
  [`2dbaf81`](https://github.com/test-nala/athomic/commit/2dbaf81f645657a24bae51e1ad6018a0274e3939))

### Documentation

- **config**: Add docstrings on config files
  ([#169](https://github.com/test-nala/athomic/pull/169),
  [`8ed78ca`](https://github.com/test-nala/athomic/commit/8ed78ca7179d7df6bf40937cf167989cfb300ac9))

- **athomic**: Adding docstring part 1 ([#169](https://github.com/test-nala/athomic/pull/169),
  [`8ed78ca`](https://github.com/test-nala/athomic/commit/8ed78ca7179d7df6bf40937cf167989cfb300ac9))

- **athomic**: Adding docstrings ([#170](https://github.com/test-nala/athomic/pull/170),
  [`4094dba`](https://github.com/test-nala/athomic/commit/4094dba681e09819e4d6e1284272d9bf9a835174))

- **lifecycle**: Add docstring ([#169](https://github.com/test-nala/athomic/pull/169),
  [`8ed78ca`](https://github.com/test-nala/athomic/commit/8ed78ca7179d7df6bf40937cf167989cfb300ac9))

- **service**: Add docstring ([#169](https://github.com/test-nala/athomic/pull/169),
  [`8ed78ca`](https://github.com/test-nala/athomic/commit/8ed78ca7179d7df6bf40937cf167989cfb300ac9))

### Features

- **docs**: Implement documentation site with MkDocs and CI/CD
  ([#171](https://github.com/test-nala/athomic/pull/171),
  [`2dbaf81`](https://github.com/test-nala/athomic/commit/2dbaf81f645657a24bae51e1ad6018a0274e3939))


## v3.0.0 (2025-09-25)

### Chores

- **deps**: Bump the poetry-dependencies group with 32 updates
  ([#167](https://github.com/test-nala/athomic/pull/167),
  [`18395bf`](https://github.com/test-nala/athomic/commit/18395bf96a17bd99c2eab84452a648fac55e2bd8))

- **infra**: Locust infrastructure and test API route
  ([#168](https://github.com/test-nala/athomic/pull/168),
  [`3e3c0ec`](https://github.com/test-nala/athomic/commit/3e3c0eca5c90b0f837b243be912e07bd760fb1d6))

### Features

- **messaging**: Implement Optimistic Ordered Consumer using the Strategy Pattern
  ([#168](https://github.com/test-nala/athomic/pull/168),
  [`3e3c0ec`](https://github.com/test-nala/athomic/commit/3e3c0eca5c90b0f837b243be912e07bd760fb1d6))

### Breaking Changes

- **messaging**: The `MessageProcessor` class has been removed and its logic distributed among the new strategy layers (`OrchestrationStrategy`, `ExecutionStrategy`) and the new `BaseMessageProcessor` (single and batch). Any component that previously depended directly on the old `MessageProcessor` must be refactored to use the new `ConsumerFactory` and strategy protocols.


## v2.16.0 (2025-09-19)

### Features

- **outbox**: Implement FIFO Ordering and Hot Aggregate Observability
  ([#166](https://github.com/test-nala/athomic/pull/166),
  [`8a0098b`](https://github.com/test-nala/athomic/commit/8a0098b760d2e18ab3532a042d3e5aba11c4138a))


## v2.15.0 (2025-09-19)

### Chores

- **deps**: Bump actions/setup-python in the github-actions group
  ([#160](https://github.com/test-nala/athomic/pull/160),
  [`368d82b`](https://github.com/test-nala/athomic/commit/368d82b9bf299df755109bce896bdc2d6aa61335))

- **deps**: Bump the poetry-dependencies group across 1 directory with 33 updates
  ([#163](https://github.com/test-nala/athomic/pull/163),
  [`155e58d`](https://github.com/test-nala/athomic/commit/155e58d76d92f5a02f9f4064301bef352676e9dd))

### Features

- **resilience**: Implement distributed backpressure mechanism
  ([#165](https://github.com/test-nala/athomic/pull/165),
  [`b4c89ad`](https://github.com/test-nala/athomic/commit/b4c89adceb8abaa1382dc5c4ee8be50c6af54a2d))

### Refactoring

- **core**: Introduce ConnectionManager & Migration Module
  ([#164](https://github.com/test-nala/athomic/pull/164),
  [`2433658`](https://github.com/test-nala/athomic/commit/24336587ac3ed4634d01f23c3f39143a9d7d7a8d))


## v2.14.0 (2025-09-11)

### Features

- **devops**: Implement dockerized environment and Kafka IaC
  ([#162](https://github.com/test-nala/athomic/pull/162),
  [`8821bbc`](https://github.com/test-nala/athomic/commit/8821bbcf299c0bd339ad89094bb861f704aa5b72))


## v2.13.0 (2025-09-07)

### Chores

- **metrics**: Add metrics to outbox releasing
  ([#159](https://github.com/test-nala/athomic/pull/159),
  [`a949cf2`](https://github.com/test-nala/athomic/commit/a949cf228fec0e60d0dfdcef099f415cba077a07))

### Features

- **resilience**: Introduce generic sharding service and apply to outbox
  ([#159](https://github.com/test-nala/athomic/pull/159),
  [`a949cf2`](https://github.com/test-nala/athomic/commit/a949cf228fec0e60d0dfdcef099f415cba077a07))


## v2.12.0 (2025-09-06)

### Features

- **leasing**: Add distributed leasing module with Redis provider
  ([#157](https://github.com/test-nala/athomic/pull/157),
  [`22bb59f`](https://github.com/test-nala/athomic/commit/22bb59fa46238c57ce41ea696e185ae4b413cfd9))


## v2.11.0 (2025-09-06)

### Features

- Implement FIFO ordering guarantee for the Outbox pattern
  ([#156](https://github.com/test-nala/athomic/pull/156),
  [`0298858`](https://github.com/test-nala/athomic/commit/0298858a2603b6fd89bee6322fa95881e7978ff6))


## v2.10.0 (2025-09-04)

### Features

- **integration**: New messaging broker for local tests
  ([#155](https://github.com/test-nala/athomic/pull/155),
  [`12b46af`](https://github.com/test-nala/athomic/commit/12b46af96fcde51d70e03c74568287a010e42647))

- **messaging**: Implement in-memory provider and refactor settings
  ([#155](https://github.com/test-nala/athomic/pull/155),
  [`12b46af`](https://github.com/test-nala/athomic/commit/12b46af96fcde51d70e03c74568287a010e42647))


## v2.9.0 (2025-09-03)

### Chores

- **deps**: Bump the poetry-dependencies group with 23 updates
  ([#150](https://github.com/test-nala/athomic/pull/150),
  [`05a9ff0`](https://github.com/test-nala/athomic/commit/05a9ff0112eff7954431b8686852e17a58bb2c22))

### Features

- **athomic/lineage**: Introduce data lineage module using OpenLineage standard
  ([#154](https://github.com/test-nala/athomic/pull/154),
  [`9f0cce8`](https://github.com/test-nala/athomic/commit/9f0cce81c8dd9275680085bcfa9c2ad48ed11e5b))


## v2.8.0 (2025-09-02)

### Features

- **messaging**: Implement Claim Check pattern for large messages
  ([#153](https://github.com/test-nala/athomic/pull/153),
  [`d731bfa`](https://github.com/test-nala/athomic/commit/d731bfa05b7cdd5ce7db8cef350eb4569bddca81))


## v2.7.0 (2025-09-02)

### Chores

- Improve code quality and align test suite with guidelines
  ([`f910be5`](https://github.com/test-nala/athomic/commit/f910be5911a3b2aeb8ddf0f04f8e2b4a7c5075b3))

### Features

- **storage**: Implement Storage module and enhance Plugin system
  ([#152](https://github.com/test-nala/athomic/pull/152),
  [`0e2f203`](https://github.com/test-nala/athomic/commit/0e2f2038b399490d09aa22f51188bb065f9c8372))


## v2.6.0 (2025-08-23)

### Features

- Add field-level message encryption serializer
  ([#149](https://github.com/test-nala/athomic/pull/149),
  [`6daa230`](https://github.com/test-nala/athomic/commit/6daa230e8fd47bb2b3c2a24d0910ea12cadb414e))


## v2.5.0 (2025-08-22)

### Features

- **resilience**: Add Saga pattern and Idempotency modules
  ([#148](https://github.com/test-nala/athomic/pull/148),
  [`152d1d3`](https://github.com/test-nala/athomic/commit/152d1d36fcbc3ad194c8326a00babe6a13faf13d))


## v2.4.0 (2025-08-22)

### Features

- **resilience**: Implement framework-agnostic Idempotency module
  ([#147](https://github.com/test-nala/athomic/pull/147),
  [`fbe2e5e`](https://github.com/test-nala/athomic/commit/fbe2e5e6fa2a4d8bceea3f163e818fbaeee10536))


## v2.3.0 (2025-08-22)

### Bug Fixes

- **messaging**: Make batch accumulator robust to optional message attributes
  ([#146](https://github.com/test-nala/athomic/pull/146),
  [`99c52fe`](https://github.com/test-nala/athomic/commit/99c52febae169f22274de997460c1270f0cbe3c8))

- **messaging**: Pass async __call__ as callback in delay setup
  ([#146](https://github.com/test-nala/athomic/pull/146),
  [`99c52fe`](https://github.com/test-nala/athomic/commit/99c52febae169f22274de997460c1270f0cbe3c8))

### Chores

- Fix lost code ([#145](https://github.com/test-nala/athomic/pull/145),
  [`596785a`](https://github.com/test-nala/athomic/commit/596785ae1f11d61e2db31f2ecc1fecc565e96543))

### Features

- **messaging**: Implement log sampling for DLQ poison pills
  ([#146](https://github.com/test-nala/athomic/pull/146),
  [`99c52fe`](https://github.com/test-nala/athomic/commit/99c52febae169f22274de997460c1270f0cbe3c8))


## v2.2.0 (2025-08-19)

### Chores

- **devx**: Convenient commit command ([#143](https://github.com/test-nala/athomic/pull/143),
  [`8565a0a`](https://github.com/test-nala/athomic/commit/8565a0a15d0fe24a031c96be9a0192a07b5d9891))

- **tests**: Fix test timeout ([#143](https://github.com/test-nala/athomic/pull/143),
  [`8565a0a`](https://github.com/test-nala/athomic/commit/8565a0a15d0fe24a031c96be9a0192a07b5d9891))

### Features

- **messaging**: Add batch consumption settings and integration test
  ([#143](https://github.com/test-nala/athomic/pull/143),
  [`8565a0a`](https://github.com/test-nala/athomic/commit/8565a0a15d0fe24a031c96be9a0192a07b5d9891))

- **messaging**: Harden retry/delay handlers and add unit tests
  ([#143](https://github.com/test-nala/athomic/pull/143),
  [`8565a0a`](https://github.com/test-nala/athomic/commit/8565a0a15d0fe24a031c96be9a0192a07b5d9891))

### Refactoring

- **messaging**: Adopt ProcessingOutcome for DLQ and fix strategy tests
  ([#143](https://github.com/test-nala/athomic/pull/143),
  [`8565a0a`](https://github.com/test-nala/athomic/commit/8565a0a15d0fe24a031c96be9a0192a07b5d9891))

- **messaging**: Decouple DLQ and improve lifecycle management
  ([#143](https://github.com/test-nala/athomic/pull/143),
  [`8565a0a`](https://github.com/test-nala/athomic/commit/8565a0a15d0fe24a031c96be9a0192a07b5d9891))

- **messaging**: Use Dependency Injection for DelayedMessageHandler
  ([#143](https://github.com/test-nala/athomic/pull/143),
  [`8565a0a`](https://github.com/test-nala/athomic/commit/8565a0a15d0fe24a031c96be9a0192a07b5d9891))


## v2.1.0 (2025-08-18)

### Chores

- **devx**: Convenient commit command ([#142](https://github.com/test-nala/athomic/pull/142),
  [`49de177`](https://github.com/test-nala/athomic/commit/49de1772e739b6bdb38a8f0d5666d0bce423e861))

- **tests**: Fix test timeout ([#142](https://github.com/test-nala/athomic/pull/142),
  [`49de177`](https://github.com/test-nala/athomic/commit/49de1772e739b6bdb38a8f0d5666d0bce423e861))

### Features

- **messaging**: Add batch consumption settings and integration test
  ([#142](https://github.com/test-nala/athomic/pull/142),
  [`49de177`](https://github.com/test-nala/athomic/commit/49de1772e739b6bdb38a8f0d5666d0bce423e861))

- **messaging**: Harden retry/delay handlers and add unit tests
  ([#142](https://github.com/test-nala/athomic/pull/142),
  [`49de177`](https://github.com/test-nala/athomic/commit/49de1772e739b6bdb38a8f0d5666d0bce423e861))

### Refactoring

- **messaging**: Decouple DLQ and improve lifecycle management
  ([#142](https://github.com/test-nala/athomic/pull/142),
  [`49de177`](https://github.com/test-nala/athomic/commit/49de1772e739b6bdb38a8f0d5666d0bce423e861))

- **messaging**: Use Dependency Injection for DelayedMessageHandler
  ([#142](https://github.com/test-nala/athomic/pull/142),
  [`49de177`](https://github.com/test-nala/athomic/commit/49de1772e739b6bdb38a8f0d5666d0bce423e861))


## v2.0.0 (2025-08-17)

### Bug Fixes

- **messaging**: Improved error handling in the republish task
  ([`20890e0`](https://github.com/test-nala/athomic/commit/20890e05d640bddcd073cd7696cdd1dd14e116e6))

### Features

- **messaging**: Made DLQ consumer group_id configurable
  ([`20890e0`](https://github.com/test-nala/athomic/commit/20890e05d640bddcd073cd7696cdd1dd14e116e6))

### Refactoring

- **messaging**: Clarified and simplified the exception hierarchy
  ([`20890e0`](https://github.com/test-nala/athomic/commit/20890e05d640bddcd073cd7696cdd1dd14e116e6))

- **messaging**: Improved dependency injection, validation, and batch error handling
  ([`20890e0`](https://github.com/test-nala/athomic/commit/20890e05d640bddcd073cd7696cdd1dd14e116e6))


## v1.0.0 (2025-05-27)
### Bug Fixes

- **messaging**: DLQ fixes and integration test
  ([`5c41dee`](https://github.com/test-nala/athomic/commit/5c41deed3abdf37737b7d38f957e53b0b0d46b02))

- **tests**: Integration tests with flags
  ([#71](https://github.com/test-nala/athomic/pull/71),
  [`9b406d8`](https://github.com/test-nala/athomic/commit/9b406d832b031d27bf39fcde38aaaab8be707302))

### Chores

- **backlog**: Update backlog for task-004 in progress and task-003 completed
  ([`c5b78f1`](https://github.com/test-nala/athomic/commit/c5b78f17038cb3abc64c49c26a70edadd215c98a))

- **deps**: Bump poetry-dependencies group with 14 updates
  ([#72](https://github.com/test-nala/athomic/pull/72),
  [`15f631e`](https://github.com/test-nala/athomic/commit/15f631e59b87e2de00ee2f5baba7135c26f7efb2))

- **deps**: Bump poetry-dependencies group with 14 updates
  ([#68](https://github.com/test-nala/athomic/pull/68),
  [`42d2109`](https://github.com/test-nala/athomic/commit/42d210917fb348cca5e3bc58be10552fe6c8241e))

- **deps**: Bump poetry-dependencies group with 20 updates
  ([#74](https://github.com/test-nala/athomic/pull/74),
  [`812ced4`](https://github.com/test-nala/athomic/commit/812ced4f7cb7ada49a4362c84eaf824cd3c45674))

- **doc**: ADR file name prefix
  ([`f3b0d23`](https://github.com/test-nala/athomic/commit/f3b0d23b0e1a6e0d50aa1e018cdf339c631fa447))

- **doc**: Messaging and DLQ documentation
  ([`5c41dee`](https://github.com/test-nala/athomic/commit/5c41deed3abdf37737b7d38f957e53b0b0d46b02))

- **doc**: Serializer documentation ([#75](https://github.com/test-nala/athomic/pull/75),
  [`0e231d5`](https://github.com/test-nala/athomic/commit/0e231d5141d386a2aad525df6ec6c66f025413ff))

- **doc**: Update documentation ([#75](https://github.com/test-nala/athomic/pull/75),
  [`0e231d5`](https://github.com/test-nala/athomic/commit/0e231d5141d386a2aad525df6ec6c66f025413ff))

- **docs**: Update backlog and docs
  ([`c642250`](https://github.com/test-nala/athomic/commit/c6422504bb9026e0cae6adaab4da8cfe4274d13b))

- **refact**: Refactor config schema directory
  ([`44a59fa`](https://github.com/test-nala/athomic/commit/44a59fa4be8c3301a4913fbd41e9f6b2c3391cf3))

- **test**: Outbox decorator integration tests
  ([#69](https://github.com/test-nala/athomic/pull/69),
  [`1b90c32`](https://github.com/test-nala/athomic/commit/1b90c324babbf6156ef14ca766b5788703a39e03))

- **tests**: Fix outbox unit tests ([#71](https://github.com/test-nala/athomic/pull/71),
  [`9b406d8`](https://github.com/test-nala/athomic/commit/9b406d832b031d27bf39fcde38aaaab8be707302))

- **tests**: Outbox integration test ([#71](https://github.com/test-nala/athomic/pull/71),
  [`9b406d8`](https://github.com/test-nala/athomic/commit/9b406d832b031d27bf39fcde38aaaab8be707302))

### Continuous Integration

- Update quality report
  ([`4028a5c`](https://github.com/test-nala/athomic/commit/4028a5c7fc2a02d5177388493f9c7c880bb3e1fe))

- Update quality report
  ([`8ac9e80`](https://github.com/test-nala/athomic/commit/8ac9e80530b5b04b641ad9827f3358cfa8c6038f))

- Update quality report
  ([`f481a1b`](https://github.com/test-nala/athomic/commit/f481a1be7ad828507ef61b7f00d2e8a7bed028cd))

- Update quality report
  ([`75aeeb1`](https://github.com/test-nala/athomic/commit/75aeeb1cfb8c5da48eee8cbdc629ded2274e56d5))

- Update quality report
  ([`9cac580`](https://github.com/test-nala/athomic/commit/9cac58010de52301b360d6cca40529ecfbf30411))

### Features

- **messaging**: Add protobuf serializer provider
  ([#75](https://github.com/test-nala/athomic/pull/75),
  [`0e231d5`](https://github.com/test-nala/athomic/commit/0e231d5141d386a2aad525df6ec6c66f025413ff))

- **messaging**: DLQ and serializer with structural refactor
  ([`5c41dee`](https://github.com/test-nala/athomic/commit/5c41deed3abdf37737b7d38f957e53b0b0d46b02))

- **messaging**: Improve messaging serializer
  ([#75](https://github.com/test-nala/athomic/pull/75),
  [`0e231d5`](https://github.com/test-nala/athomic/commit/0e231d5141d386a2aad525df6ec6c66f025413ff))

- **messaging**: Improve serializer with target_model
  ([#75](https://github.com/test-nala/athomic/pull/75),
  [`0e231d5`](https://github.com/test-nala/athomic/commit/0e231d5141d386a2aad525df6ec6c66f025413ff))

- **outbox**: Outbox is now fully agnostic and works with any process type
  ([`44a59fa`](https://github.com/test-nala/athomic/commit/44a59fa4be8c3301a4913fbd41e9f6b2c3391cf3))
