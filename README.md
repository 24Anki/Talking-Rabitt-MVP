# 🐇 Talking Rabbitt

> **Conversational AI for Instant Business Insights**  
> Upload Data. Ask Questions. Get Answers.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/powered%20by-OpenAI-412991.svg)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: MVP](https://img.shields.io/badge/status-MVP-brightgreen.svg)]()

---

## ✨ What is Talking Rabbitt?

Talking Rabbitt is a **conversational analytics tool** that lets you upload any CSV and ask questions in plain English — getting instant text answers *and* automated visualizations. No SQL. No dashboards. No waiting for a data analyst.

**The Magic Moment:** In under 60 seconds, you go from a raw spreadsheet to a natural-language conversation with your data.

```
You:    "Which region had the highest revenue in Q1?"
🐇:     "The North region led Q1 with $587,420 in revenue,
         outperforming the next closest region (East) by 12%."
         [Bar chart auto-generated 📊]
```

---

## 🗂 Repository Structure

```
talking-rabbitt/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── secrets.toml.example  # API key configuration template
├── data/
│   └── sample_sales.csv      # Built-in sample dataset
├── tests/
│   └── test_queries.py       # Demo query regression tests
├── docs/
│   ├── architecture.md       # System design overview
│   └── api_integration.md    # CRM integration guide
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- An OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- pip package manager

### 1. Clone the Repository

```bash
git clone https://github.com/talkingrabbitt/mvp.git
cd mvp
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Your OpenAI API Key (Two Options)

**Option A — Environment Variable (Recommended for local dev):**

```bash
# macOS / Linux
export OPENAI_API_KEY="sk-your-key-here"

# Windows (Command Prompt)
set OPENAI_API_KEY=sk-your-key-here

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-key-here"
```

**Option B — Streamlit Secrets (Recommended for deployment):**

```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml and add your key:
```

```toml
# .streamlit/secrets.toml  ← NEVER commit this file!
OPENAI_API_KEY = "sk-your-key-here"
```

> ⚠️ **Security Note:** `.streamlit/secrets.toml` is listed in `.gitignore` by default.  
> Never commit API keys to version control. Use environment variables in CI/CD pipelines.

### 4. Run the App

```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501` — you're ready to ask questions!

---

## 🎮 Demo Mode (No API Key Required)

If you don't have an OpenAI API key, the app runs in **Demo Mode** with a built-in rule-based engine. Use the sample dataset and try these queries:

| Query | What You'll See |
|-------|----------------|
| `Which region had the highest revenue in Q1?` | Bar chart + top region callout |
| `Which product sold the most units in Q3?` | Bar chart + product ranking |
| `Show me revenue trends by quarter.` | Line chart with growth trend |
| `Compare revenue share by region.` | Pie chart with percentages |

---

## 📊 Sample Dataset

The built-in sample dataset contains **80 rows** across realistic business dimensions:

```
region     quarter    product        revenue    units_sold
North      Q1         AlphaWidget    142,350    923
North      Q1         BetaGadget     118,200    701
South      Q1         AlphaWidget    128,900    845
...
```

| Column | Type | Values |
|--------|------|--------|
| `region` | categorical | North, South, East, West, Central |
| `quarter` | categorical | Q1, Q2, Q3, Q4 |
| `product` | categorical | AlphaWidget, BetaGadget, GammaKit, DeltaTool |
| `revenue` | numeric | ~$50K–$200K per row |
| `units_sold` | numeric | ~400–1200 per row |

### Bring Your Own Data

Upload any CSV with your own column structure. The AI adapts automatically to your schema. Columns with numeric data become queryable metrics; categorical columns become filterable dimensions.

**Example custom queries for your own data:**
- `"What's the average deal size by sales rep this month?"`
- `"Which support category has the highest ticket volume?"`
- `"Show me churn rate trend over the last 6 months."`

---

## 🔑 API Key Security Best Practices

1. **Never hardcode keys** in source files
2. **Use `.env` files locally** with `python-dotenv` (not included by default)
3. **Rotate keys regularly** via the OpenAI dashboard
4. **Set usage limits** on your OpenAI account to prevent unexpected charges
5. **For production:** use a secrets manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault)

```python
# Safe key loading pattern used in app.py
import os
import streamlit as st

api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
```

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Frontend                  │
│  (Light-blue background, dark-brown text, branded)  │
└───────────────────┬─────────────────────────────────┘
                    │ User query + DataFrame
                    ▼
┌─────────────────────────────────────────────────────┐
│              Query Processing Layer                  │
│  • Schema extraction                                 │
│  • Pre-computed aggregations (accuracy boost)        │
│  • System prompt construction                        │
└───────────────────┬─────────────────────────────────┘
                    │ Augmented prompt
                    ▼
┌─────────────────────────────────────────────────────┐
│              OpenAI GPT-4o-mini                      │
│  • Natural language answer (2–4 sentences)           │
│  • Structured JSON chart specification               │
└───────────────────┬─────────────────────────────────┘
                    │ {text, chart_json}
                    ▼
┌─────────────────────────────────────────────────────┐
│              Visualization Layer                     │
│  • Matplotlib renderer (bar / line / pie)            │
│  • Brand color palette (#B85042, #3B1F0E, #7A9E7E)  │
│  • Embedded inline in chat thread                    │
└─────────────────────────────────────────────────────┘
```

---

## 🔌 CRM Integration (Roadmap)

Talking Rabbitt is designed to embed inside CRM platforms. The integration API (coming Q2 2025) will support:

```python
from talkingrabbitt import RabbittClient

client = RabbittClient(api_key="tr-your-key")

# Query your CRM data
result = client.ask(
    data_source="freshsales",      # or "hubspot", "salesforce"
    question="Which deals are most at risk this quarter?",
    crm_token="your-crm-oauth-token"
)

print(result.text)        # Natural language answer
print(result.chart_url)   # Hosted chart image URL
print(result.raw_data)    # Underlying DataFrame
```

See [`docs/api_integration.md`](docs/api_integration.md) for the full integration guide.

---

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest

# Run demo query regression tests
pytest tests/test_queries.py -v
```

---

## 📦 Deployment

### Deploy to Streamlit Community Cloud (Free)

1. Push your repo to GitHub (ensure `secrets.toml` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add `OPENAI_API_KEY` in the Secrets section of the dashboard
5. Deploy!

### Deploy to Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t talking-rabbitt .
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-your-key talking-rabbitt
```

---

## 🗺 Roadmap

| Milestone | Target | Status |
|-----------|--------|--------|
| CSV upload + NL queries | Q1 2025 | ✅ Complete |
| Auto-visualizations | Q1 2025 | ✅ Complete |
| HubSpot integration | Q2 2025 | 🔄 In Progress |
| Freshworks integration | Q2 2025 | 🔄 In Progress |
| Slack bot | Q3 2025 | 📋 Planned |
| Scheduled reports | Q3 2025 | 📋 Planned |
| White-label API | Q4 2025 | 📋 Planned |
| Custom LLM fine-tuning | Q4 2025 | 📋 Planned |

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-query`)
3. Commit your changes (`git commit -m 'Add amazing query type'`)
4. Push to the branch (`git push origin feature/amazing-query`)
5. Open a Pull Request



---

*Built with ❤️ and lots of ☕ by the Talking Rabbitt team.*  
*Ask your data anything. 🐇*

