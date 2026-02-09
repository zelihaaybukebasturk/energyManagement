# AI-Driven Building Energy Efficiency & Monitoring System

This project was developed during a 30-hour BTK Academy AI Hackathon with a focus on building-scale energy efficiency and AI-assisted decision support.

An intelligent energy efficiency monitoring and decision support system designed for building-scale applications, including schools, universities, hotels, and large residential complexes.

The system combines deterministic energy calculations, rule-based efficiency evaluation, and Retrieval-Augmented Generation (RAG) to transform raw technical data into clear, actionable insights for both technical experts and non-technical decision makers.

##  How It Works

1. **KPI Calculation**: System computes normalized energy metrics
2. **Efficiency Evaluation**: Rule-based engine classifies efficiency level
3. **Document Retrieval**: RAG system retrieves relevant technical documents
4. **AI Explanation**: System generates human-readable explanations and recommendations

## Architecture

### Backend Components

1. **KPI Calculator** (`backend/kpi_calculator.py`)
   - Calculates energy consumption per square meter
   - Computes energy per occupant
   - Normalizes by climate factors

2. **Efficiency Evaluator** (`backend/efficiency_evaluator.py`)
   - Rule-based efficiency classification
   - Building-type specific benchmarks
   - Efficiency scoring (efficient/moderately efficient/inefficient)

3. **RAG System** (`backend/rag_system.py`)
   - Retrieves relevant technical documents
   - Generates AI-powered explanations
   - Provides actionable recommendations

4. **API Server** (`backend/main.py`)
   - FastAPI-based REST API
   - `/analyze` endpoint for building analysis
   - `/benchmarks/{building_type}` endpoint for benchmark lookup

### Knowledge Base

The system includes a curated knowledge base (`knowledge_base/`) with:
- Energy efficiency standards
- HVAC best practices
- Lighting guidelines
- Retrofit strategies

### Frontend

Simple, modern web interface (`frontend/index.html`) for:
- Input building data
- View analysis results
- Display efficiency classification
- Show AI-generated explanations

Also included:
- **What-if Energy & KPI Simulation** (`frontend/simulation.html`) for LED / occupancy / operating-hours scenarios, with weather context and RAG-based interpretation.

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or navigate to the project directory**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ollama Kurulumu (AI açıklamaları için - İsteğe bağlı)**
   
   Sistem varsayılan olarak Ollama kullanmayı dener. Ollama kurmak için:
   
   **Windows:**
   ```bash
   setup_ollama.bat
   ```
   
   **Linux/Mac:**
   ```bash
   chmod +x setup_ollama.sh
   ./setup_ollama.sh
   ```

4. **Start the servers**
   
   **Start servers manually**
   
   Terminal 1 - Backend:
   ```bash
   python start_server.py
   ```
   
   Terminal 2 - Frontend:
   ```bash
   python serve_frontend.py
   ```
   
   **Access the application:**
   - Backend API: `http://localhost:8000`
   - Frontend: `http://localhost:8080`
   - API Documentation: `http://localhost:8000/docs`

  Pages:
  - Login: `http://localhost:8080/login.html`
  - Dashboard: `http://localhost:8080/dashboard.html`
  - What-if Simulation: `http://localhost:8080/simulation.html`

## Key Features

-  Transparent, deterministic calculations
-  Building-type specific benchmarks
-  Explainable AI reasoning
-  Regulation-aware recommendations
-  No large training datasets required
-  Easy to extend and customize

## LLM Integration

The system supports multiple LLM providers for AI-powered explanations:

### Setup LLM

**Ollama (Local, Free)**
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.2
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
```

## Future Enhancements

- Vector database for more sophisticated document retrieval
- Historical data tracking and trend analysis
- Multi-building comparison dashboard
- Export reports (PDF, Excel)
- Climate normalization improvements
- Fine-tuned models for energy efficiency domain

## Project Screenshots & Demo
<img width="861" height="586" alt="image" src="https://github.com/user-attachments/assets/3dac215c-bb12-44ae-9b2a-89c41246e3e0" />
<img width="854" height="788" alt="image" src="https://github.com/user-attachments/assets/9cdf5f05-5736-4d20-bc1f-3a6300e9429d" />
<img width="828" height="998" alt="image" src="https://github.com/user-attachments/assets/993a8899-6a3f-4f10-a5db-92b46a44c44d" />
<img width="1899" height="1033" alt="image" src="https://github.com/user-attachments/assets/4abb5bc0-8503-40c5-a57e-55aa02bbecf7" />
<img width="979" height="727" alt="image" src="https://github.com/user-attachments/assets/99963a1b-346f-4fdb-826d-e75b2f9974b5" />

**Built with:** Python, FastAPI, HTML/CSS/JavaScript

