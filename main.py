import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from simulation import run_simulation_step, NITROGEN_PER_GRAM_NITRILE, NITROGEN_PER_BIOMASS_GROWTH, CARRYING_CAPACITY_DEFAULT

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimulationParams(BaseModel):
    initial_nitrile_mass_g: float = 100.0
    regolith_iron_percent: float = 5.0
    catalyst_efficiency_factor: float = 1.0  # Multiplier on iron-catalyzed conversion
    water_available_g: float = 500.0         # Lunar resource: water available (g)
    oxygen_available_ppm: float = 20000.0    # Lunar resource: oxygen concentration (ppm)
    simulation_duration_h: float = 5.0

@app.post("/run_simulation")
def run_simulation_endpoint(params: SimulationParams):
    # Auto-compute carrying capacity from nitrogen supply (scientific heuristic)
    # K_N = (total nitrogen available) / (nitrogen required per gram biomass)
    K_n = (params.initial_nitrile_mass_g * NITROGEN_PER_GRAM_NITRILE) / NITROGEN_PER_BIOMASS_GROWTH
    SAFETY_FACTOR = 0.9  # avoid extreme edge saturation
    carrying_capacity_K = min(CARRYING_CAPACITY_DEFAULT, K_n * SAFETY_FACTOR)

    reactor_state = {
        'nitrile_mass_g': params.initial_nitrile_mass_g,
        'nitrogen_concentration_ppm': 0.0,
        'regolith_iron_percent': params.regolith_iron_percent,
        'catalyst_efficiency_factor': params.catalyst_efficiency_factor,
        'water_g': params.water_available_g,
        'oxygen_ppm': params.oxygen_available_ppm,
        'carrying_capacity_K': carrying_capacity_K,
    }
    plant_state = {'biomass_g': 0.1}
    
    # Convert duration from hours to minutes for simulation steps
    simulation_duration_min = int(params.simulation_duration_h * 60)
    time_step = 10  # Each step is 10 minutes
    
    raw_results = []
    raw_results.append({
        "time": 0,
        "reactor_state": reactor_state.copy(),
        "plant_state": plant_state.copy()
    })

    time_points = range(time_step, simulation_duration_min + 1, time_step)
    for time in time_points:
        reactor_state, plant_state = run_simulation_step(time, reactor_state.copy(), plant_state.copy())
        raw_results.append({
            "time": time,
            "reactor_state": reactor_state,
            "plant_state": plant_state
        })
        
    # Process results into the format expected by the frontend
    time_points_out = [res['time'] for res in raw_results]
    biomass_history = [res['plant_state']['biomass_g'] for res in raw_results]
    nitrile_history = [res['reactor_state']['nitrile_mass_g'] for res in raw_results]
    nitrogen_history = [res['reactor_state']['nitrogen_concentration_ppm'] for res in raw_results]

    return {
        "time_points": time_points_out,
        "biomass_history": biomass_history,
        "nitrile_history": nitrile_history,
        "nitrogen_history": nitrogen_history,
    }

# --- Static File Serving ---
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

# Mount the frontend directory under the path "/static"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# Serve favicon.ico at the path browsers request by default
FAVICON_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'favicon.ico')
FAVICON_PATH = os.path.abspath(FAVICON_PATH)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    if os.path.exists(FAVICON_PATH):
        return FileResponse(FAVICON_PATH)
    # Fallback: return a 204 No Content to silence the error if file is missing
    from fastapi import Response
    return Response(status_code=204)

# Serve the index.html file for the root URL ('/') and for '/index.html'
@app.get("/", response_class=FileResponse)
@app.get("/index.html", response_class=FileResponse)
async def read_index():
    return os.path.join(FRONTEND_DIR, "index.html")

# Serve the help.html file
@app.get("/help.html", response_class=FileResponse)
async def read_help():
    return os.path.join(FRONTEND_DIR, "help.html")