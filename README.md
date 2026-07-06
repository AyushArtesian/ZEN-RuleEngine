# 📋 Invoice Rule Engine

A no-code business rules engine for intelligent invoice routing and automation built with Python, Streamlit, and the ZEN Engine.

![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red?style=flat-square&logo=streamlit)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-CC342D?style=flat-square)
![ZEN-Engine](https://img.shields.io/badge/ZEN_Engine-0.18+-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## 🎯 Overview

The **Invoice Rule Engine** is a configurable decision-making system that automatically routes invoices based on user-defined business rules. Instead of code changes, stakeholders can create, modify, and manage rules through an intuitive web interface.

### Key Use Cases
- **Automatic Invoice Approval** — Bypass manual queue for low-risk invoices (trusted vendors, validated data)
- **Smart Routing** — Direct invoices to the appropriate queue (human review, blocked, auto-approved)
- **Compliance & Audit** — Complete audit trail of all routing decisions with full traceability
- **Dynamic Prioritization** — Reorder rule evaluation priority without deployment

## ✨ Features

### 🚀 No-Code Rule Management
- **Graphical Rule Builder** — Create rules via a web form without writing code
- **Dynamic Conditions** — Support for multiple fields (vendor, amount, store, validation status, etc.)
- **Rich Operators** — String operators (equals, contains, starts with, IN, etc.), numeric comparisons, boolean logic
- **Priority-Based Evaluation** — Rules evaluated in priority order; first match wins

### ⚡ Three Action Types
| Action | Description | Use Case |
|--------|-------------|----------|
| ✅ **Bypass Human Queue** | Post invoice directly | Pre-approved vendors, validated data |
| ⏳ **Send to Human Queue** | Route for manual review | Uncertain or high-value invoices |
| 🚫 **Block Posting** | Reject the invoice | Fraud, validation failures |

### 📊 Real-Time Dashboard
- KPI cards (total rules, active rules, evaluations)
- Decision breakdown by action type
- Recent evaluation history
- Active rules summary with conditions

### 🔍 Comprehensive Audit Trail
- Immutable logs of all invoice evaluations
- Decision path tracking
- Execution time metrics
- CSV export for compliance reporting

### 🛠️ Rule Management
- **Create** — Build new rules with multiple conditions
- **Read** — View all rules with detailed condition breakdown
- **Update** — Modify existing rules and conditions
- **Delete** — Soft-delete or permanently remove rules
- **Activate/Deactivate** — Toggle rules without deletion

### 🧪 Rule Testing
- Test rules against sample invoices
- View detailed decision path and execution metrics
- Validate rule behavior before deployment

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────┐
│        Streamlit Web UI                 │
│  (Dashboard, Rules, Test, Audit)        │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   Services Layer                        │
│  - Rule Service (CRUD)                  │
│  - Audit Service (logging, export)      │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   Engine Layer                          │
│  - Evaluator (orchestration)            │
│  - Rule Builder (ZEN model generation)  │
│  - ZEN Service (decision engine)        │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   Data Layer                            │
│  - SQLAlchemy ORM Models                │
│  - Repository Pattern                   │
│  - SQLite Database                      │
└─────────────────────────────────────────┘
```

### Decision Flow

```
Invoice Data Input
    ↓
Fetch Active Rules (sorted by priority)
    ↓
Build ZEN Decision Model
    ↓
Evaluate via ZEN Engine
    ↓
First Match → Return Action
    ↓
Log to Audit Trail
    ↓
Return Result (with decision path, timing)
```

## 🛠️ Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | Streamlit | 1.31.0+ |
| **Backend** | Python | 3.12+ |
| **ORM** | SQLAlchemy | 2.0.23+ |
| **Data Validation** | Pydantic | 2.5.0+ |
| **Decision Engine** | ZEN-Engine | 0.18.0+ |
| **Data Processing** | Pandas | 2.1.3+ |
| **Database** | SQLite | Built-in |
| **Environment** | python-dotenv | 1.0.0+ |
| **Testing** | pytest | 7.4.0+ |
| **Container** | Docker | 20.10+ |

## 📁 Project Structure

```
RuleEngine/
├── app.py                       # Main Streamlit app entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Container orchestration
├── .env                         # Environment variables (optional)
│
├── config/
│   ├── __init__.py
│   └── settings.py              # App configuration & paths
│
├── database/
│   ├── __init__.py
│   ├── db.py                    # SQLAlchemy engine & session
│   ├── models.py                # ORM models (Rule, RuleCondition, AuditLog)
│   └── repository.py            # Data access layer (CRUD helpers)
│
├── engine/
│   ├── __init__.py
│   ├── evaluator.py             # Core evaluation logic & result handling
│   ├── rule_builder.py          # Converts rules → ZEN decision models
│   └── zen_service.py           # Wrapper for ZEN Engine calls
│
├── services/
│   ├── __init__.py
│   ├── rule_service.py          # Business logic for rule CRUD
│   └── audit_service.py         # Audit log queries & CSV export
│
├── pages/                       # Streamlit multi-page apps
│   ├── 1_Dashboard.py           # Overview & KPIs
│   ├── 2_Create_Rule.py         # Rule creation form
│   ├── 3_Manage_Rules.py        # Edit/delete/toggle rules
│   ├── 4_Test_Rules.py          # Test rules against sample data
│   └── 5_Audit.py               # Audit log viewer & CSV export
│
├── data/                        # Runtime data directory
│   └── rule_engine.db           # SQLite database (auto-created)
│
├── decision_models/             # Generated ZEN decision models
│   └── invoice_rules.json       # Active rules as ZEN model
│
├── logs/                        # Application logs
│   └── app.log                  # Streamlit & app logs
│
└── sample_data/
    └── invoices/
        ├── sample_invoice_1.json
        └── sample_invoice_2.json
```

## 🗄️ Database Schema

### `rules` Table
```sql
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 100,
    action VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `rule_conditions` Table
```sql
CREATE TABLE rule_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL FOREIGN KEY,
    field_name VARCHAR(100) NOT NULL,
    operator VARCHAR(50) NOT NULL,
    value VARCHAR(500) NOT NULL,
    condition_order INTEGER DEFAULT 0
);
```

### `audit_logs` Table
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id VARCHAR(200),
    invoice_data TEXT,                  -- JSON snapshot
    matched_rule VARCHAR(200),
    decision VARCHAR(50) NOT NULL,      -- Action taken
    execution_time_ms FLOAT DEFAULT 0.0,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 Installation

### Prerequisites
- Python 3.12 or higher
- pip or conda
- SQLite (included with Python)
- Docker & Docker Compose (for containerized deployment)

### Local Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/RuleEngine.git
   cd RuleEngine
   ```

2. **Create Virtual Environment**
   ```bash
   # Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Or using conda
   conda create -n rule-engine python=3.12
   conda activate rule-engine
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` File** (Optional)
   ```env
   APP_NAME=Invoice Rule Engine
   LOG_LEVEL=INFO
   DEFAULT_ACTION=SEND_TO_HUMAN_QUEUE
   DATABASE_URL=sqlite:///./data/rule_engine.db
   ```

5. **Initialize Database**
   ```bash
   python -c "from database.db import init_db; init_db()"
   ```

6. **Run the Application**
   ```bash
   streamlit run app.py
   ```
   Access the app at `http://localhost:8501`

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f invoice-rule-engine

# Stop services
docker-compose down
```

The application will be available at `http://localhost:8501`

### Manual Docker Build

```bash
# Build the image
docker build -t invoice-rule-engine .

# Run the container
docker run -d \
  --name invoice-rule-engine \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/decision_models:/app/decision_models \
  invoice-rule-engine
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Invoice Rule Engine | Application display name |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DEFAULT_ACTION` | SEND_TO_HUMAN_QUEUE | Fallback action if no rules match |
| `DATABASE_URL` | sqlite:///./data/rule_engine.db | Database connection string |

### Supported Invoice Fields

The rule builder supports these invoice fields:

| Field | Type | Operators | Example |
|-------|------|-----------|---------|
| `vendor` | string | =, !=, Contains, Starts With, Ends With, IN, NOT IN | "Vendor A" |
| `amount` | number | =, !=, >, <, >=, <= | 5000 |
| `store` | string | =, !=, Contains, IN, NOT IN | "Store123" |
| `validationPassed` | boolean | = | true/false |
| `missingFields` | array | Contains, Not Contains | "invoice_number" |
| `currency` | string | =, !=, IN, NOT IN | "USD" |
| `country` | string | =, !=, IN, NOT IN | "US" |

### Actions

- **BYPASS_HUMAN_QUEUE** — Post invoice directly (green indicator)
- **SEND_TO_HUMAN_QUEUE** — Route for human review (orange indicator)
- **BLOCK_POSTING** — Reject/block the invoice (red indicator)

## 📖 Usage Guide

### 1️⃣ Create a Rule

1. Navigate to **"Create Rule"** page
2. Enter rule details:
   - **Name** — Unique rule identifier
   - **Priority** — Lower number = evaluated first (default: 100)
   - **Action** — Choose one of three actions
3. Add conditions using the form:
   - Select **Field** (vendor, amount, store, etc.)
   - Select **Operator** (=, >, contains, etc.)
   - Enter **Value**
4. Click **"Add Condition"** for AND logic
5. Click **"Create Rule"** to save

### 2️⃣ Manage Rules

1. Go to **"Manage Rules"** page
2. View all rules in a table with:
   - Name, description, priority, action, status
   - Detailed condition breakdown
3. **Edit** — Modify rule name, description, priority, action, or conditions
4. **Delete** — Remove the rule permanently
5. **Toggle** — Activate/deactivate rules without deletion

### 3️⃣ Test Rules

1. Navigate to **"Test Rules"** page
2. Select a **Sample Invoice** or paste custom JSON
3. Click **"Evaluate"** to run the engine
4. View results:
   - ✅ Action taken (with color indicator)
   - 📌 Matched rule name
   - ⏱️ Execution time (milliseconds)
   - 📊 Decision path (which rules were evaluated)

### 4️⃣ View Dashboard

1. Go to **"Dashboard"** page
2. See KPI metrics:
   - Total/active/disabled rules
   - Total evaluations
3. View **Decision Breakdown** by action type
4. Check **Recent Evaluations** (last 10 invoices)
5. Review **Active Rules** sorted by priority

### 5️⃣ Audit & Export

1. Navigate to **"Audit"** page
2. **View Audit Logs** with timestamps, decisions, execution times
3. **Filter by Decision** (Bypass, Send to Queue, Block)
4. **Download as CSV** for compliance reporting

## 🧪 Rule Examples

### Example 1: Bypass Trusted Vendors
```
Name:         Bypass Trusted Vendors
Priority:     1
Action:       BYPASS_HUMAN_QUEUE
Conditions:   
  - vendor = "Vendor A"
  AND
  - validationPassed = true
```

### Example 2: Block High-Risk Invoices
```
Name:         Block High-Risk
Priority:     10
Action:       BLOCK_POSTING
Conditions:
  - amount >= 10000
  AND
  - missingFields Contains "invoice_number"
```

### Example 3: Route by Country
```
Name:         International Review
Priority:     20
Action:       SEND_TO_HUMAN_QUEUE
Conditions:
  - country NOT IN "US,CA,MX"
```

## 🔌 API Reference

### Core Engine Functions

#### `evaluate_invoice(invoice_data: dict, invoice_id: Optional[str]) → EvaluationResult`

Evaluates an invoice against all active rules.

**Parameters:**
- `invoice_data` (dict) — Invoice data with fields matching SUPPORTED_FIELDS
- `invoice_id` (str, optional) — Unique invoice identifier for audit tracking

**Returns:**
- `EvaluationResult` dataclass with:
  - `action` — Routing action (BYPASS_HUMAN_QUEUE, SEND_TO_HUMAN_QUEUE, BLOCK_POSTING)
  - `matched_rule` — Name of matched rule (or None)
  - `execution_time_ms` — Time taken to evaluate
  - `decision_path` — List of evaluation steps
  - `error` — Error message (if any)
  - `raw_response` — Raw ZEN Engine response

**Example:**
```python
from engine.evaluator import evaluate_invoice

invoice = {
    "vendor": "Vendor A",
    "amount": 5000,
    "store": "Store123",
    "validationPassed": True,
    "currency": "USD",
    "country": "US"
}

result = evaluate_invoice(invoice, invoice_id="INV-2024-001")
print(result.action)              # → "BYPASS_HUMAN_QUEUE"
print(result.matched_rule)        # → "Bypass Trusted Vendors"
print(result.execution_time_ms)   # → 12.5
```

### Rule Service Functions

#### `create_rule(name, action, conditions, description, priority, created_by) → dict`
Create a new rule with conditions.

#### `get_all_rules(active_only=False) → list[dict]`
Retrieve all rules or only active rules.

#### `update_rule(rule_id, name, action, conditions, description, priority) → dict`
Update an existing rule.

#### `delete_rule(rule_id) → dict`
Delete a rule by ID.

#### `toggle_rule_active(rule_id, is_active) → dict`
Activate or deactivate a rule.

### Audit Service Functions

#### `get_audit_logs(limit=100, offset=0, decision_filter=None) → list[dict]`
Retrieve audit log entries with optional filtering.

#### `get_audit_stats() → dict`
Get aggregate statistics (total evaluations, by_decision breakdown).

#### `export_to_csv(logs) → str`
Export audit logs to CSV format.

## 🧑‍💻 Development

### Project Setup for Development

```bash
# Clone and setup
git clone https://github.com/yourusername/RuleEngine.git
cd RuleEngine

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run tests
pytest tests/ -v --cov=.
```

### Code Style

The project follows PEP 8. Use black for formatting:

```bash
black . --line-length=100
```

### Adding New Fields

To add support for a new invoice field:

1. **Update `SUPPORTED_FIELDS`** in [engine/rule_builder.py](engine/rule_builder.py)
   ```python
   SUPPORTED_FIELDS = {
       ...
       "newField": {"label": "New Field Label", "type": "string"},
   }
   ```

2. **Update `OPERATORS_BY_TYPE`** if needed
3. **Update sample invoices** in [sample_data/invoices/](sample_data/invoices/)
4. **Test rule creation** and evaluation with the new field

### Logging

The app logs to both console and file (`logs/app.log`):

```python
import logging
logger = logging.getLogger(__name__)
logger.info("Info message")
logger.error("Error message")
```

Configure log level via `LOG_LEVEL` environment variable.

## 🔒 Security Considerations

- **Database Encryption** — Recommended for production: Use SQL Alchemy with encrypted backends
- **Authentication** — Not built-in; implement Streamlit auth or reverse-proxy authentication
- **Input Validation** — All inputs validated via Pydantic models
- **Audit Trail** — All decisions logged immutably for compliance
- **SQL Injection** — Protected via SQLAlchemy ORM
- **CSRF/XSS** — Streamlit handles frame security

## 📊 Performance Tuning

- **Rule Evaluation** — Sorted by priority; O(n) where n = active rules
- **Typical Latency** — 10-50ms per evaluation (including DB operations)
- **Database Indexing** — Consider indexes on `rules.priority`, `rules.is_active`
- **Decision Model Caching** — Rebuild only when rules change

## 🐛 Troubleshooting

### Database Not Initializing
```bash
# Manually initialize
python -c "from database.db import init_db; init_db()"
```

### Port 8501 Already in Use
```bash
# Use alternative port
streamlit run app.py --server.port 8502
```

### Rules Not Matching
1. Check **Dashboard** → **Active Rules**
2. Use **Test Rules** to validate conditions
3. Verify field names match invoice structure
4. Check **Audit** logs for error messages

### High Evaluation Time
1. Check number of active rules
2. Review rule complexity and conditions
3. Check ZEN Engine logs in `logs/app.log`

## 📝 Sample Invoice Format

```json
{
  "vendor": "Vendor A",
  "amount": 5000.00,
  "store": "Store123",
  "validationPassed": true,
  "missingFields": [],
  "currency": "USD",
  "country": "US"
}
```

## 📚 Additional Resources

- **ZEN Engine Docs** — https://zenengine.io/
- **Streamlit Docs** — https://docs.streamlit.io/
- **SQLAlchemy ORM** — https://docs.sqlalchemy.org/
- **Pydantic Validation** — https://docs.pydantic.dev/

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes and test thoroughly
4. Commit with clear messages (`git commit -m 'Add AmazingFeature'`)
5. Push to your branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 🙋 Support & Contact

For questions, issues, or feature requests:
- **GitHub Issues** — https://github.com/yourusername/RuleEngine/issues
- **Email** — support@example.com

---

**Built with ❤️ by the Artesian Automation Team**

*Last Updated: July 6, 2024*
