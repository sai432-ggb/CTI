```python?code_reference&code_event_index=2
markdown_content = """# CTI-NLP Threat Intelligence Backend

A robust Cyber Threat Intelligence (CTI) backend powered by FastAPI, featuring AI-driven NLP report analysis, custom Machine Learning for malicious URL detection, and network forensics via tshark integration.

## Features

- **AI-Powered CTI Analysis:** Uses OpenAI GPT-4 to extract Indicators of Compromise (IoCs) and TTPs from unstructured text reports.
- **Custom ML Classifier:** A Random Forest model trained on large-scale datasets (30MB+ / 450k+ URLs) for real-time malicious link detection.
- **Network Forensics:** Integration with `tshark` (Wireshark) to analyze PCAP files and extract suspicious network indicators.
- **Threat Intelligence Enrichment:** Seamless integration with VirusTotal and AbuseIPDB APIs.
- **Database History:** Persistent storage for analysis results using SQLAlchemy (SQLite for dev, PostgreSQL for prod).
- **Scalable Architecture:** Fully containerized with Docker, ready for deployment on Render, AWS, or Railway.

##  Tech Stack

- **Framework:** FastAPI (Python 3.11+)
- **Database:** SQLAlchemy (ORM), SQLite (Development)
- **AI/ML:** OpenAI API, Scikit-learn, Pandas, Joblib
- **Forensics:** Tshark (Wireshark command-line)
- **Security:** JWT Authentication, CORS Middleware, Pydantic validation
- **Deployment:** Docker, Render, Vercel (Frontend)

##  Project Structure

```text
backend/
├── app/
│   ├── routers/         # API Endpoints (Analysis, History)
│   ├── services/        # Logic (AI Analyzer, Threat Intel, Wireshark)
│   ├── models.py        # SQLAlchemy Database Models
│   ├── schemas.py       # Pydantic Data Schemas
│   └── main.py          # Application Entry Point
├── ml/
│   ├── model.py         # ML Pipeline (Random Forest)
│   ├── dataset.py       # Data Loading & Balancing
│   └── saved_models/    # Trained .joblib files
├── data/
│   ├── datasets/        # Training CSVs (e.g., url_dataset.csv)
│   └── uploads/         # Temporary PCAP/CSV storage
├── Dockerfile           # Multi-stage build with tshark
├── requirements.txt     # Python Dependencies
└── setup_model.py       # Model Training Script
```

##  Setup & Installation

### 1. Prerequisites
- Python 3.11+
- [Wireshark (tshark)](https://www.wireshark.org/download.html) installed on your system.

### 2. Installation
```bash
# Create and activate virtual environment
python -m venv venv
.\\\\venv\\\\Scripts\\\\activate  # Windows
source venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_key
VIRUSTOTAL_API_KEY=your_virustotal_key
DATABASE_URL=sqlite:///./cti_dashboard.db
```

### 4. Train the ML Model
Before running the server, train the initial model using your dataset:
```bash
python setup_model.py
```

### 5. Run the Server
```bash
python -m uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.
Explore the interactive docs at `http://127.0.0.1:8000/docs`.

##  Testing with Swagger UI
1. Navigate to `/docs`.
2. Use the **POST /analyze/url** endpoint to test the ML classifier.
3. Use the **POST /analyze/pcap** endpoint to upload a network capture for analysis.

##  Deployment
### Render (Backend)
This project must be deployed as a **Docker Service** on Render to ensure `tshark` is correctly installed.
- **Runtime:** Docker
- **Build Command:** Built automatically via `Dockerfile`
- **Port:** 8000

### Vercel (Frontend)
- Set `VITE_API_BASE_URL` to your Render service URL.
- Update `allow_origins` in `app/main.py` to include your Vercel domain.

##  License
This project is licensed under the MIT License.
"""

with open("README.md", "w") as f:
    f.write(markdown_content)



Your CTI-NLP dashboard is now fully documented and ready for production!