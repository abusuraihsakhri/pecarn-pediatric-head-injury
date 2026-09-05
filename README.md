# PECARN Pediatric Head Injury

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** PECARN Guidelines, CAP / CLSI / ISO Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

PECARN Pediatric Head Injury Rule implementation for ruling out clinically important traumatic brain injury (ciTBI) in children <2y and >=2y. This zero-dependency Python implementation provides single and batch evaluation capabilities with enterprise-grade security features.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_metrics()`** — Core PECARN scoring algorithm that computes risk scores and classifications.
- **`process_single()`** — Evaluates a single patient case with provided parameters.
- **`process_batch()`** — Processes CSV files containing multiple patient records.
- **`main()`** — CLI entry point for single and batch operations.

### 🏗️ Enterprise Agent Suite

- **`agents/supervisor.py`** — Multi-worker orchestrator coordinating QC, safety, and protocol evaluations.
- **`agents/workers.py`** — Specialized workers: InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker.
- **`agents/base.py`** — PHI guard, HMAC-SHA256 audit trail, and security utilities.
- **`agents/api.py`** — FastAPI REST server with health, metrics, audit, and chat endpoints.

---

## 📐 PECARN Scoring Algorithm

The core algorithm computes a weighted score from input parameters:

```text
score = primary_val + Σ(secondary_val_i * (1.0 / i))  for i = 2, 3, ...
rounded_score = round(score, 2)
```

Classification tiers:
- **Low / Standard** (score < 10.0): Standard monitoring or negative cutoff
- **Moderate / Intermediate** (10.0 ≤ score < 25.0): Close observation or secondary evaluation
- **High / Severe** (score ≥ 25.0): Urgent clinical intervention or primary positive finding

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/pecarn-pediatric-head-injury.git
cd pecarn-pediatric-head-injury

# Install core dependencies
pip install pydantic>=2.0

# Install with web server support
pip install -e ".[web]"

# Install with all dependencies (including test)
pip install -e ".[all]"
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Case Evaluation
```bash
python cli.py single --v1 12.0 --v2 4.0 --v3 2.0
```

### 2. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 3. Enterprise Agent Audit
```bash
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2 --critical
```

### 4. Interactive Chat
```bash
python cli.py chat "Explain PECARN criteria for children under 2"
```

### 5. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 6. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--v1` | Primary parameter | 10.0 |
| `--v2` | Secondary parameter | 5.0 |
| `--v3` | Tertiary parameter | 2.0 |
| `-i, --input` | Input CSV file path | Required |
| `-o, --output` | Output CSV file path | results.csv |

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary measurement | Required |
| `v2` | Secondary measurement | Required |
| `v3` | Tertiary measurement | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable in production for persistent audit integrity:

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-secure-random-key-here"

# Windows
set AUDIT_SECRET_KEY=your-secure-random-key-here
```

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

Run the enrichment module tests:

```bash
python -m pytest tests/ -v
```

---

## 🐳 Container Deployment

```bash
docker build -t pecarn-pediatric-head-injury .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key pecarn-pediatric-head-injury
```

Or using Docker Compose:

```bash
docker-compose up -d
```

---

## 📁 Project Structure

```
pecarn-pediatric-head-injury/
├── agents/                 # Enterprise agent suite
│   ├── __init__.py
│   ├── api.py             # FastAPI REST server
│   ├── base.py            # PHI guard, audit trail, security
│   ├── learning.py        # Bayesian calibration engine
│   ├── llm_factory.py     # LLM provider factory
│   ├── metrics.py         # Prometheus metrics collector
│   ├── models.py          # Pydantic data models
│   ├── streamer.py        # WebSocket telemetry broadcaster
│   ├── supervisor.py      # Multi-worker orchestrator
│   └── workers.py         # Specialized evaluation workers
├── tests/                 # Test suite
│   ├── test_enrichment.py
│   └── test_pecarn_pediatric_head_injury.py
├── web/                   # Web dashboard
│   └── index.html
├── cli.py                 # CLI entry point
├── pecarn_rule.py         # Core PECARN algorithm
├── enrichment.py          # Clinical enrichment features
├── simulator.py           # High-throughput simulation
├── pyproject.toml         # Package configuration
├── Dockerfile             # Container build
├── docker-compose.yml     # Container orchestration
├── sample.csv             # Sample input data
├── benchmark_dataset.json # Benchmark test cases
└── README.md
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
