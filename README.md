
## ⚡ Quick Start (5-Minute Local Setup)

Get the complete multi-service agentic engine running locally with a single command. 

### 1. Spin up the Stack
Ensure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

```bash
# Clone the repository
git clone [https://github.com/your-username/agent-native-engine.git](https://github.com/your-username/agent-native-engine.git)
cd agent-native-engine

# Start all services (Database, Redis, Go Core, Node Gateway, Python Workers)
docker-compose up --build -d


# Agent Native Asynchronous Orchestration Engine

A highly resilient, event-driven microservices architecture built to ingest, track, and execute cognitive agent workflows asynchronously.

## 🚀 Architecture Highlights
- **Ingress Gateway (Node.js / Express):** High-throughput entry point that validates schema contracts and safely registers transactions.
- **State Machine Orchestrator (Go):** Ultra-fast, highly concurrent transactional worker that manages the PostgreSQL ledger.
- **Cognitive Execution Mesh (Python):** Decoupled heavy-lifter designed to run resource-intensive AI, LLM, or data analysis pipelines.
- **Event Bus & Storage (Redis & PostgreSQL):** Uses Redis Pub/Sub for sub-millisecond inter-service communication and PostgreSQL for persistent state tracking.

## 🛠️ Tech Stack
- **Languages:** Node.js, Go (Golang), Python
- **Infrastructure:** Docker, Docker Compose
- **Data Layers:** PostgreSQL, Redis

## ⚡ Quick Start

1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/agent-native-engine.git](https://github.com/YOUR_USERNAME/agent-native-engine.git)
   cd agent-native-engine