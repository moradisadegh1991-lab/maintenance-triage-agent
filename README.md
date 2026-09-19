# 🏭 Maintenance Triage Agent
### LangGraph ReAct Agent for Petrochemical Equipment Failure Analysis

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0-purple.svg)](https://github.com/langchain-ai/langgraph)
[![Claude](https://img.shields.io/badge/Model-Claude%20Sonnet%204.6-orange.svg)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An **agentic AI system** that autonomously triages equipment failure reports at petrochemical plants. Given a plain-text report from an operator, the agent pulls CMMS history, checks sensor thresholds, and creates a prioritized Work Order — all without human intervention.

---

## 🎯 Problem Statement

A pump shows **94°C temperature** and **5.2 mm/s vibration**.

Traditional rule engines: `IF temperature > 85 → trigger alert` ❌ (misses context)

This agent: reasons across **sensor data + failure history + asset criticality** simultaneously, exactly like a senior maintenance engineer. ✅

---

## 🏗️ Architecture

```
START → llm_call → [tool_calls?] → tool_node ──┐
            ↑                                    │
            └────────────────────────────────────┘
                         ↓ (no more tool calls)
                        END
```

**ReAct Loop (LangGraph Graph API):**

1. `llm_call` node — Claude decides which tools to invoke based on the report
2. `tool_node` node — executes the requested tools and returns `ToolMessage` results
3. `should_continue` — conditional edge: loop back if more tool calls needed, else `END`

![Architecture Diagram](images/01_architecture.svg)

---

## 🔧 Tools

| Tool | Description | Real-world equivalent |
|---|---|---|
| `get_equipment_history` | Retrieves MTBF, MTTR, last failure from CMMS | FmWeb / SAP PM / Maximo API |
| `check_sensor_threshold` | Compares sensor readings against safety limits (SI units) | DCS historian / OSIsoft PI |
| `create_work_order` | Creates a prioritized maintenance Work Order | CMMS POST request |

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/maintenance-triage-agent.git
cd maintenance-triage-agent
```

### 2. Create virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API key

```bash
cp .env.example .env
# Open .env and add your Anthropic API key
```

Get your API key at [platform.claude.com](https://platform.claude.com) → API Keys

> ⚠️ **Important:** This requires an Anthropic Console API key with billing enabled.
> A Claude.ai Pro/Max chat subscription does **not** include API access.

### 5. Run the agent

```bash
python maintenance_triage_agent.py
```

---

## 📊 Sample Output

```
=== Maintenance Triage Agent ===
Report: پمپ P-204 خط آب دریا الان دمای 94 درجه سانتی‌گراد و ویبراسیون 5.2 mm/s

[Tool Call 1] get_equipment_history(equipment_id="P-204")
→ MTBF=92 days, MTTR=6h, last failure: 2026-03-11 (seawater seal leak)

[Tool Call 2] check_sensor_threshold(parameter="temperature_c", value=94.0)
→ 🚨 CRITICAL: 94°C exceeds threshold 85°C (+10.6% over limit)

[Tool Call 3] check_sensor_threshold(parameter="vibration_mm_s", value=5.2)
→ 🚨 CRITICAL: 5.2 mm/s exceeds threshold 4.5 mm/s (+15.6% over limit)

[Tool Call 4] create_work_order(equipment_id="P-204", priority="URGENT", ...)
→ ✅ Work Order registered: WO-P-204-3847

Final Summary:
تجهیز P-204 در وضعیت بحرانی قرار دارد. دو پارامتر حیاتی از آستانه عبور کرده‌اند.
با توجه به سابقه نشت آب‌بند دریایی در ۳.۵ ماه پیش (کمتر از MTBF ۹۲ روز)،
یک Work Order با اولویت URGENT ثبت شد. توقف فوری تجهیز توصیه می‌شود.

llm_calls: 3
```

---

## 🗂️ Project Structure

```
maintenance-triage-agent/
├── maintenance_triage_agent.py   # Main agent (LangGraph ReAct)
├── test_api_key.py               # Standalone API key validator
├── requirements.txt
├── requirements-dev.txt          # Dev tooling (SkillSpector security scanner)
├── Makefile                      # install / install-dev / scan targets
├── .env.example
├── images/
│   ├── 01_architecture.svg       # Agent architecture diagram
│   ├── 02_execution_trace.svg    # Agent reasoning trace
│   └── 03_results_card.svg       # Sample results card
└── README.md
```

---

## 🔌 Connecting to Real Systems

Replace the mock dictionaries with actual CMMS/DCS calls:

```python
# Instead of:
record = CMMS_HISTORY.get(equipment_id)

# Use your real CMMS API:
record = fmweb_client.get_equipment(equipment_id)       # FmWeb
record = sap_pm_client.get_equipment_history(equipment_id)  # SAP PM
record = maximo_client.get_asset(equipment_id)          # IBM Maximo

# For sensor thresholds from DCS historian:
value = osipi_client.get_current_value(tag_name)        # OSIsoft PI
```

The LangGraph graph structure stays **identical** — only tool implementations change.

---

## 📐 Extending the Agent

Add a new tool in 3 steps:

```python
@tool
def get_spare_parts_availability(equipment_id: str, part_code: str) -> str:
    """Check if spare parts are available in warehouse for this equipment.
    
    Args:
        equipment_id: Equipment tag (e.g., P-204)
        part_code: Part number from CMMS catalog
    """
    # your warehouse API call here
    return f"Part {part_code}: 3 units in stock, location W-12-B"

# Add to the tools list — graph auto-discovers it
tools = [get_equipment_history, check_sensor_threshold, create_work_order, get_spare_parts_availability]
```

---

## 🛡️ Security Scanning with SkillSpector

This project uses [SkillSpector](https://github.com/NVIDIA/SkillSpector) as a
development tool to scan any external AI agent skill/tool before it's
integrated into this codebase. It statically analyzes code for prompt
injection, data exfiltration, supply-chain risks, and dangerous execution
patterns, then reports a risk score.

```bash
# Install (requires Python >=3.12,<3.15; separate from requirements.txt)
pip install -r requirements-dev.txt
# or: make install-dev

# Scan a directory or file before trusting it (static analysis, no API key needed)
make scan SKILL=./path/to/skill
# or directly:
skillspector scan ./path/to/skill --no-llm
```

For the deeper LLM-based semantic pass, drop `--no-llm` and configure an LLM
provider key (e.g. `OPENAI_API_KEY`) as described in the
[SkillSpector docs](https://github.com/NVIDIA/SkillSpector).

---

## 🔑 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | ✅ Yes |

---

## 📦 Requirements

```
langgraph>=1.0
langchain>=0.3
langchain-anthropic>=0.3
python-dotenv>=1.0
```

---

## 👤 Author

**Sadegh Moradi**  
Senior Data & Maintenance Engineer | Predictive Analytics Lead  
Kavian Petrochemical Company — South Pars / Asalouyeh, Iran

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com)

---

## 📄 License

MIT — feel free to adapt for your own plant/CMMS system.
