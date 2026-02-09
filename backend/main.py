"""
Main API Server for AI-Driven Building Energy Efficiency System
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
import uvicorn
from datetime import datetime, timedelta

try:
    from jose import JWTError, jwt
    from passlib.context import CryptContext
    HAS_AUTH_LIBS = True
except ImportError:
    HAS_AUTH_LIBS = False
    print("Warning: python-jose and passlib not installed. Install with: pip install python-jose[cryptography] passlib[bcrypt]")

from kpi_calculator import KPICalculator
from efficiency_evaluator import EfficiencyEvaluator
from rag_system import RAGSystem
from whatif_simulator import SimulationInputs, simulate_whatif
from weather_client import fetch_weather_by_city, fetch_weather

try:
    from excel_dataset import load_excel_dataset, get_dataset_stats, get_records_for_rag
    EXCEL_DATASET_AVAILABLE = True
except ImportError:
    EXCEL_DATASET_AVAILABLE = False
    load_excel_dataset = lambda path=None: []
    get_dataset_stats = lambda rec: {"count": 0, "message": "Excel dataset module not available."}
    get_records_for_rag = lambda rec, bt, ep, lim=5: []


app = FastAPI(
    title="AI-Driven Building Energy Efficiency System",
    description="Energy efficiency monitoring and decision support system",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
kpi_calculator = KPICalculator()
efficiency_evaluator = EfficiencyEvaluator()

# Initialize RAG system with Ollama as default
import os
# Set Ollama as default if no other provider is configured
if not os.getenv("LLM_PROVIDER") and not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
    os.environ["LLM_PROVIDER"] = "ollama"
    os.environ["OLLAMA_BASE_URL"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    os.environ["OLLAMA_MODEL"] = os.getenv("OLLAMA_MODEL", "llama3.2")

rag_system = RAGSystem()  # Uses default path

# Authentication setup (if libraries available)
HAS_AUTH_LIBS_WORKING = False
if HAS_AUTH_LIBS:
    try:
        SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-3gen-energy-2024")
        ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        security = HTTPBearer()

        # Simple user database (in production, use a real database)
        USERS_DB = {
            "admin": {
                "username": "admin",
                "hashed_password": pwd_context.hash("admin123"),  # Change in production!
                "full_name": "System Administrator",
                "role": "admin"
            },
            "demo": {
                "username": "demo",
                "hashed_password": pwd_context.hash("demo123"),
                "full_name": "Demo User",
                "role": "user"
            }
        }
        HAS_AUTH_LIBS_WORKING = True
    except (ValueError, AttributeError) as e:
        print(f"Warning: passlib/bcrypt uyumluluk hatası, basit kimlik doğrulama kullanılıyor: {e}")
        HAS_AUTH_LIBS = False

if HAS_AUTH_LIBS and HAS_AUTH_LIBS_WORKING:

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current authenticated user from token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            token = credentials.credentials
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        if username not in USERS_DB:
            raise credentials_exception
        
        return USERS_DB[username]
else:
    # Fallback: simple token-based auth without JWT
    USERS_DB = {
        "admin": {"username": "admin", "password": "admin123", "full_name": "System Administrator", "role": "admin"},
        "demo": {"username": "demo", "password": "demo123", "full_name": "Demo User", "role": "user"}
    }
    security = HTTPBearer()
    
    def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Simple token check (fallback)."""
        token = credentials.credentials
        if token not in ["admin_token", "demo_token"]:
            raise HTTPException(status_code=401, detail="Invalid token")
        return USERS_DB.get("admin" if token == "admin_token" else "demo")


class BuildingAnalysisRequest(BaseModel):
    """Request model for building energy analysis."""
    total_energy_kwh: float = Field(..., description="Total energy consumption in kWh")
    building_area_m2: float = Field(..., description="Building area in square meters")
    building_type: str = Field(..., description="Building type (school, university, hotel, residential, office, hospital)")
    occupancy: Optional[int] = Field(None, description="Number of occupants")
    period_months: float = Field(12.0, description="Measurement period in months (default: 12 for annual)")

    # Optional weather/location context
    city: Optional[str] = Field(None, description="City name for weather context (e.g., Istanbul)")
    latitude: Optional[float] = Field(None, description="Latitude (optional)")
    longitude: Optional[float] = Field(None, description="Longitude (optional)")
    indoor_temp_c: Optional[float] = Field(22.0, description="Indoor setpoint temperature (°C) for context")

    # Optional cost / emissions (used for savings statements and per-person CO2 context)
    electricity_price_tl_per_kwh: float = Field(3.5, description="Electricity unit price (TL/kWh)")
    grid_emission_factor_kgco2_per_kwh: float = Field(0.42, description="Grid emission factor (kgCO2/kWh)")


class BuildingAnalysisResponse(BaseModel):
    """Response model for building energy analysis."""
    kpis: dict
    efficiency_evaluation: dict
    ai_explanation: dict


class WhatIfSimulationRequest(BaseModel):
    """Request model for room/zone scale what-if simulation."""
    scenario: str = Field(..., description='One of: "led", "occupancy_down_20", "hours_shorter"')
    room_m2: float = Field(..., description="Room area in square meters")
    people_count: int = Field(..., description="Number of people in the room/zone")
    electricity_kwh: float = Field(..., description="Electricity consumption (kWh) for the selected period")
    period_months: float = Field(1.0, description="Period length in months (default: 1)")
    room_temp_c: float = Field(22.0, description="Indoor setpoint temperature (°C)")

    building_type: str = Field("office", description="Building type for default load shares")
    baseline_hours_per_day: float = Field(9.0, description="Baseline operating hours per day")
    new_hours_per_day: Optional[float] = Field(None, description="New operating hours per day (for hours_shorter)")

    electricity_price_tl_per_kwh: float = Field(3.5, description="Electricity unit price (TL/kWh)")
    grid_emission_factor_kgco2_per_kwh: float = Field(0.42, description="Grid emission factor (kgCO2/kWh)")

    # Weather / location (optional)
    city: Optional[str] = Field(None, description="City name for weather context (e.g., Istanbul)")
    latitude: Optional[float] = Field(None, description="Latitude (optional)")
    longitude: Optional[float] = Field(None, description="Longitude (optional)")


class WhatIfSimulationResponse(BaseModel):
    """Response model for what-if simulation."""
    simulation: dict
    ai_explanation: dict
    weather: Optional[dict] = None


class BuildingWhatIfRequest(BuildingAnalysisRequest):
    """Building-scale what-if based on completed baseline analysis inputs."""
    scenario: str = Field(..., description='One of: "led", "occupancy_down_20", "hours_shorter"')
    baseline_hours_per_day: float = Field(9.0, description="Baseline operating hours per day")
    new_hours_per_day: Optional[float] = Field(None, description="New operating hours per day (for hours_shorter)")


class BuildingWhatIfResponse(BaseModel):
    """Response for building what-if re-analysis."""
    baseline: dict
    whatif: dict
    whatif_simulation: dict
    whatif_commentary: dict
    weather: Optional[dict] = None


def _fetch_weather_payload(city: Optional[str], latitude: Optional[float], longitude: Optional[float]) -> Optional[Dict[str, Any]]:
    weather_payload = None
    if latitude is not None and longitude is not None:
        w = fetch_weather(latitude, longitude)
        if w:
            weather_payload = {"location": {"latitude": latitude, "longitude": longitude}, "weather": w}
    elif city:
        weather_payload = fetch_weather_by_city(city)
    return weather_payload


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI-Driven Building Energy Efficiency System API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth/login - POST endpoint for authentication",
            "analyze": "/analyze - POST endpoint for building energy analysis"
        }
    }


# Authentication endpoints
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    full_name: str

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return JWT token."""
    if not HAS_AUTH_LIBS:
        # Simple fallback authentication
        user = USERS_DB.get(login_data.username)
        if not user or user.get("password") != login_data.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
        # Return simple token
        token = f"{login_data.username}_token"
        return TokenResponse(
            access_token=token,
            username=user["username"],
            full_name=user["full_name"]
        )
    
    user = USERS_DB.get(login_data.username)
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        username=user["username"],
        full_name=user["full_name"]
    )

@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return {
        "username": current_user["username"],
        "full_name": current_user["full_name"],
        "role": current_user["role"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# --- Excel dataset (auxiliary) endpoints ---

@app.get("/dataset/stats")
async def dataset_stats():
    """
    Get statistics from the auxiliary Excel dataset.
    Used for benchmarking and validation only; does not change KPI formulas.
    """
    if not EXCEL_DATASET_AVAILABLE:
        return {"available": False, "message": "Install pandas and openpyxl; set EXCEL_DATASET_PATH to Excel file."}
    import os
    path = os.getenv("EXCEL_DATASET_PATH")
    records = load_excel_dataset(path)
    stats = get_dataset_stats(records)
    return {"available": True, "records_loaded": len(records), "stats": stats}


@app.get("/dataset/validate")
async def dataset_validate(total_energy_kwh: float, building_area_m2: float, building_type: str = "hospital"):
    """
    Compare given inputs to dataset distribution (min/mean/max energy per m²).
    For validation only; core logic unchanged.
    """
    if not EXCEL_DATASET_AVAILABLE:
        return {"available": False}
    import os
    path = os.getenv("EXCEL_DATASET_PATH")
    records = load_excel_dataset(path)
    stats = get_dataset_stats(records)
    energy_per_sqm = total_energy_kwh / building_area_m2 if building_area_m2 > 0 else 0
    ds = (stats.get("energy_per_sqm_kwh") or {})
    return {
        "available": True,
        "your_energy_per_sqm_kwh": round(energy_per_sqm, 2),
        "dataset_stats": ds,
        "within_dataset_range": (ds.get("min", 0) <= energy_per_sqm <= ds.get("max", 1e9)) if ds else None,
    }


@app.get("/benchmarks/{building_type}")
async def get_benchmarks(building_type: str):
    """Get benchmark values for a building type."""
    try:
        benchmarks = efficiency_evaluator.get_benchmark_info(building_type)
        return {
            "building_type": building_type,
            "benchmarks": benchmarks
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/analyze", response_model=BuildingAnalysisResponse)
async def analyze_building(request: BuildingAnalysisRequest):
    """
    Analyze building energy efficiency.
    
    This endpoint:
    1. Calculates energy KPIs
    2. Evaluates efficiency using rule-based benchmarks
    3. Generates AI-powered explanations and recommendations using RAG
    """
    try:
        weather_payload = _fetch_weather_payload(request.city, request.latitude, request.longitude)

        # Step 1: Calculate KPIs
        kpis = kpi_calculator.calculate_kpis(
            total_energy_kwh=request.total_energy_kwh,
            building_area_m2=request.building_area_m2,
            occupancy=request.occupancy
        )
        # Add context fields for LLM
        kpis["indoor_temp_c"] = request.indoor_temp_c
        kpis["electricity_price_tl_per_kwh"] = request.electricity_price_tl_per_kwh
        kpis["grid_emission_factor_kgco2_per_kwh"] = request.grid_emission_factor_kgco2_per_kwh
        
        # Step 2: Evaluate efficiency
        efficiency_result = efficiency_evaluator.evaluate_efficiency(
            energy_per_sqm_kwh=kpis["energy_per_sqm_kwh"],
            building_type=request.building_type,
            period_months=request.period_months
        )
        
        # Step 3: Retrieve relevant documents and generate AI explanation
        relevant_docs = rag_system.retrieve_relevant_documents(
            building_type=efficiency_result["building_type"],
            efficiency_level=efficiency_result["efficiency_level"],
            energy_per_sqm=efficiency_result["annual_energy_per_sqm"]
        )
        
        # Optional: enrich RAG with auxiliary Excel dataset (similar buildings)
        dataset_context = None
        if EXCEL_DATASET_AVAILABLE:
            import os
            excel_records = load_excel_dataset(os.getenv("EXCEL_DATASET_PATH"))
            similar = get_records_for_rag(
                excel_records,
                efficiency_result["building_type"],
                efficiency_result["annual_energy_per_sqm"],
                limit=5
            )
            if similar:
                dataset_context = "Similar buildings in reference dataset (year, total kWh, area m², kWh/m²):\n" + "\n".join(
                    f"  {r}" for r in similar
                )
        
        ai_explanation = rag_system.generate_explanation(
            kpis=kpis,
            efficiency_result=efficiency_result,
            relevant_docs=relevant_docs,
            dataset_context=dataset_context,
            weather_payload=weather_payload,
        )
        # Include weather payload for frontend display (if any)
        ai_explanation["weather"] = weather_payload
        
        # Include period in response so frontend can clarify "period" vs "annual"
        efficiency_result_with_period = {**efficiency_result, "period_months": request.period_months}
        kpis_with_period = {**kpis, "period_months": request.period_months}

        return BuildingAnalysisResponse(
            kpis=kpis_with_period,
            efficiency_evaluation=efficiency_result_with_period,
            ai_explanation=ai_explanation
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.post("/simulate/whatif", response_model=WhatIfSimulationResponse)
async def simulate_whatif_endpoint(request: WhatIfSimulationRequest):
    """
    Interactive what-if simulation endpoint.

    - Recalculates KPIs for selected scenario
    - Adds weather context (Open-Meteo) when location provided
    - Uses RAG + LLM to provide contextual interpretation in Turkish
    """
    try:
        weather_payload = None
        outdoor_temp_c = None

        if request.latitude is not None and request.longitude is not None:
            w = fetch_weather(request.latitude, request.longitude)
            if w:
                weather_payload = {"location": {"latitude": request.latitude, "longitude": request.longitude}, "weather": w}
                outdoor_temp_c = w.get("outdoor_temp_c")
        elif request.city:
            weather_payload = fetch_weather_by_city(request.city)
            if weather_payload and weather_payload.get("weather"):
                outdoor_temp_c = (weather_payload["weather"] or {}).get("outdoor_temp_c")

        sim_inputs = SimulationInputs(
            room_m2=request.room_m2,
            people_count=request.people_count,
            electricity_kwh=request.electricity_kwh,
            period_months=request.period_months,
            room_temp_c=request.room_temp_c,
            building_type=request.building_type,
            baseline_hours_per_day=request.baseline_hours_per_day,
            new_hours_per_day=request.new_hours_per_day,
            electricity_price_tl_per_kwh=request.electricity_price_tl_per_kwh,
            grid_emission_factor_kgco2_per_kwh=request.grid_emission_factor_kgco2_per_kwh,
            outdoor_temp_c=outdoor_temp_c,
        )

        simulation = simulate_whatif(sim_inputs, scenario=request.scenario)
        relevant_docs = rag_system.retrieve_relevant_documents_for_whatif(simulation.get("scenario"))
        ai_explanation = rag_system.generate_whatif_explanation(
            scenario=simulation.get("scenario"),
            simulation_result=simulation,
            relevant_docs=relevant_docs,
            weather_payload=weather_payload,
        )

        return WhatIfSimulationResponse(simulation=simulation, ai_explanation=ai_explanation, weather=weather_payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if simulation error: {str(e)}")


@app.post("/analyze/whatif", response_model=BuildingWhatIfResponse)
async def analyze_building_with_whatif(request: BuildingWhatIfRequest):
    """
    Run a baseline analysis, then apply a selected what-if scenario and re-run analysis.

    Intended for dashboard use: user finishes analysis -> selects a scenario -> gets updated KPIs + interpretation.
    """
    try:
        if request.scenario == "occupancy_down_20" and (request.occupancy is None or request.occupancy <= 0):
            raise HTTPException(status_code=400, detail='Bu senaryo için "Kullanıcı Sayısı (occupancy)" gereklidir.')

        weather_payload = _fetch_weather_payload(request.city, request.latitude, request.longitude)
        outdoor_temp_c = None
        try:
            if weather_payload and weather_payload.get("weather"):
                outdoor_temp_c = (weather_payload["weather"] or {}).get("outdoor_temp_c")
        except Exception:
            outdoor_temp_c = None

        # --- Baseline analysis (reuse same logic as /analyze) ---
        base_kpis = kpi_calculator.calculate_kpis(
            total_energy_kwh=request.total_energy_kwh,
            building_area_m2=request.building_area_m2,
            occupancy=request.occupancy
        )
        base_kpis["indoor_temp_c"] = request.indoor_temp_c
        base_kpis["electricity_price_tl_per_kwh"] = request.electricity_price_tl_per_kwh
        base_kpis["grid_emission_factor_kgco2_per_kwh"] = request.grid_emission_factor_kgco2_per_kwh

        base_eff = efficiency_evaluator.evaluate_efficiency(
            energy_per_sqm_kwh=base_kpis["energy_per_sqm_kwh"],
            building_type=request.building_type,
            period_months=request.period_months
        )

        base_docs = rag_system.retrieve_relevant_documents(
            building_type=base_eff["building_type"],
            efficiency_level=base_eff["efficiency_level"],
            energy_per_sqm=base_eff["annual_energy_per_sqm"]
        )
        base_ai = rag_system.generate_explanation(
            kpis={**base_kpis, "period_months": request.period_months},
            efficiency_result={**base_eff, "period_months": request.period_months},
            relevant_docs=base_docs,
            dataset_context=None,
            weather_payload=weather_payload,
        )
        # Attach weather into AI payload for frontend display
        base_ai["weather"] = weather_payload
        baseline = {
            "kpis": {**base_kpis, "period_months": request.period_months},
            "efficiency_evaluation": {**base_eff, "period_months": request.period_months},
            "ai_explanation": base_ai,
        }

        # --- Apply what-if (using the same engine but mapped to building scale) ---
        # Map: building_area_m2 -> room_m2, occupancy -> people_count, total_energy_kwh -> electricity_kwh
        sim_inputs = SimulationInputs(
            room_m2=request.building_area_m2,
            people_count=int(request.occupancy or 0),
            electricity_kwh=request.total_energy_kwh,
            period_months=request.period_months,
            room_temp_c=float(request.indoor_temp_c or 22.0),
            building_type=request.building_type,
            baseline_hours_per_day=request.baseline_hours_per_day,
            new_hours_per_day=request.new_hours_per_day,
            electricity_price_tl_per_kwh=request.electricity_price_tl_per_kwh,
            grid_emission_factor_kgco2_per_kwh=request.grid_emission_factor_kgco2_per_kwh,
            outdoor_temp_c=outdoor_temp_c,
        )
        whatif_simulation = simulate_whatif(sim_inputs, scenario=request.scenario)

        adj_total = float((whatif_simulation.get("whatif") or {}).get("total_kwh") or request.total_energy_kwh)
        adj_occ = (whatif_simulation.get("whatif") or {}).get("people_count")
        adj_occ = int(adj_occ) if adj_occ else request.occupancy

        # --- What-if analysis (same evaluator/benchmarks, new totals) ---
        w_kpis = kpi_calculator.calculate_kpis(
            total_energy_kwh=adj_total,
            building_area_m2=request.building_area_m2,
            occupancy=adj_occ
        )
        w_kpis["indoor_temp_c"] = request.indoor_temp_c
        w_kpis["electricity_price_tl_per_kwh"] = request.electricity_price_tl_per_kwh
        w_kpis["grid_emission_factor_kgco2_per_kwh"] = request.grid_emission_factor_kgco2_per_kwh

        w_eff = efficiency_evaluator.evaluate_efficiency(
            energy_per_sqm_kwh=w_kpis["energy_per_sqm_kwh"],
            building_type=request.building_type,
            period_months=request.period_months
        )

        w_docs = rag_system.retrieve_relevant_documents(
            building_type=w_eff["building_type"],
            efficiency_level=w_eff["efficiency_level"],
            energy_per_sqm=w_eff["annual_energy_per_sqm"]
        )
        w_ai = rag_system.generate_explanation(
            kpis={**w_kpis, "period_months": request.period_months},
            efficiency_result={**w_eff, "period_months": request.period_months},
            relevant_docs=w_docs,
            dataset_context=None,
            weather_payload=weather_payload,
        )
        w_ai["weather"] = weather_payload
        whatif = {
            "kpis": {**w_kpis, "period_months": request.period_months},
            "efficiency_evaluation": {**w_eff, "period_months": request.period_months},
            "ai_explanation": w_ai,
        }

        # --- RAG what-if commentary (3 scenarios + summary sentence) ---
        rel = rag_system.retrieve_relevant_documents_for_whatif(whatif_simulation.get("scenario"))
        whatif_commentary = rag_system.generate_whatif_explanation(
            scenario=whatif_simulation.get("scenario"),
            simulation_result=whatif_simulation,
            relevant_docs=rel,
            weather_payload=weather_payload,
        )

        return BuildingWhatIfResponse(
            baseline=baseline,
            whatif=whatif,
            whatif_simulation=whatif_simulation,
            whatif_commentary=whatif_commentary,
            weather=weather_payload,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if analyze error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

