# Product Requirements Document: The Lenny Growth Assistant

## Forward-deployment discovery brief

**Primary user and job:** Product managers, founders, and growth practitioners need to answer strategy questions from Lenny's Podcast/newsletter material and convert the findings into polished writing or lightweight UI artifacts. The product reduces manual transcript searching and makes evidence reusable.

**Success metrics:** (1) At least 90% of transcript-grounded claims in a manually reviewed test set cite a source. (2) A new evaluator can launch the stack and ask a question in under 10 minutes. (3) Median local response latency below 8 seconds for short prompts on reference hardware, measured rather than assumed.

**Assumptions:** The evaluator has Docker and Ollama; transcript files are supplied from an authorized source; the local model is the required demo default; this assessment is a local single-user prototype.

**Scope included:** FastAPI API, PostgreSQL persistence, independent sessions, Ollama and optional Anthropic provider, transcript ingestion/retrieval, source references, Ship 30 for 30 skill, Markdown/HTML artifacts, isolated artifact preview, health checks, and handoff documentation.

**Scope excluded:** Automatic scraping, authentication, multi-tenant permissions, advanced vector search, streaming responses, and production deployment. These can be added after validating core usefulness and operational constraints.

**Risks and trade-offs:** Retrieval may miss relevant evidence; source citations and abstention reduce but do not eliminate hallucination. Local models avoid per-token cloud fees and keep prompts on-device but may have lower quality or higher latency. Cloud models need keys and can incur cost. Transcript text may be copyrighted or private, so ingestion is manual and secrets/content are not logged. Generated HTML is untrusted and rendered in an iframe sandbox with scripts disabled. Production use needs auth, rate limits, migrations, retention controls, security testing, and evaluation datasets.
