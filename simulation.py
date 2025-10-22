import math

# --- Simulation Parameters ---
# These can be tuned to adjust the simulation dynamics

# Nitrile conversion
BASE_NITRILE_CONVERSION_RATE = 0.1  # Base rate without any catalyst
IRON_CATALYST_FACTOR = 0.05         # Additional conversion rate per percentage point of iron
NITROGEN_PER_GRAM_NITRILE = 340     # ppm of Nitrogen produced per gram of Nitrile

# Plant growth
MAX_GROWTH_RATE = 0.9 # Max growth rate per step (e.g., 90% increase)
CARRYING_CAPACITY_DEFAULT = 120 # Default max sustainable biomass in grams
NITROGEN_GROWTH_FACTOR = 15000 # Nitrogen level (ppm) at which growth rate is half of max
WATER_GROWTH_SATURATION_G = 500.0    # Water amount at which growth factor ~0.5
OXYGEN_GROWTH_SATURATION_PPM = 20000 # Oxygen level at which growth factor ~0.5

# Nitrogen consumption
NITROGEN_PER_BIOMASS_GROWTH = 250 # ppm of Nitrogen consumed per gram of new biomass

def run_simulation_step(time, reactor_state, plant_state):
    """
    Runs a single step of the simulation with more realistic, gradual changes.
    Each step is assumed to be a 10-minute interval.
    """

    # 1. Gradual Nitrile to Nitrogen Conversion with Iron Catalyst
    iron_percent = reactor_state.get('regolith_iron_percent', 0.0)
    catalyst_eff = reactor_state.get('catalyst_efficiency_factor', 1.0)
    nitrile_conversion_rate = BASE_NITRILE_CONVERSION_RATE + (iron_percent * IRON_CATALYST_FACTOR * catalyst_eff)
    nitrile_conversion_rate = min(nitrile_conversion_rate, 0.95)

    converted_nitrile = reactor_state['nitrile_mass_g'] * nitrile_conversion_rate
    reactor_state['nitrile_mass_g'] -= converted_nitrile
    nitrogen_produced = converted_nitrile * NITROGEN_PER_GRAM_NITRILE
    reactor_state['nitrogen_concentration_ppm'] += nitrogen_produced

    # 2. Resource-dependent growth (Nitrogen, Water, Oxygen)
    nitrogen_ppm = reactor_state.get('nitrogen_concentration_ppm', 0.0)
    water_g = reactor_state.get('water_g', 0.0)
    oxygen_ppm = reactor_state.get('oxygen_ppm', 0.0)

    fn = nitrogen_ppm / (NITROGEN_GROWTH_FACTOR + nitrogen_ppm) if nitrogen_ppm > 0 else 0.0
    fw = water_g / (WATER_GROWTH_SATURATION_G + water_g) if water_g > 0 else 0.0
    fo = oxygen_ppm / (OXYGEN_GROWTH_SATURATION_PPM + oxygen_ppm) if oxygen_ppm > 0 else 0.0

    resource_limit = min(fn, fw, fo)  # Simple limiting factor
    growth_rate = MAX_GROWTH_RATE * resource_limit

    # 3. Logistic growth with carrying capacity
    biomass = plant_state['biomass_g']
    carrying_capacity = reactor_state.get('carrying_capacity_K', CARRYING_CAPACITY_DEFAULT)
    capacity_factor = (1 - biomass / carrying_capacity) if carrying_capacity > 0 else 1
    potential_growth = max(0, growth_rate * biomass * capacity_factor)

    # 4. Nitrogen consumption based on potential growth
    nitrogen_needed = potential_growth * NITROGEN_PER_BIOMASS_GROWTH

    # 5. Limit growth by available nitrogen
    if nitrogen_needed > nitrogen_ppm:
        actual_growth = (nitrogen_ppm / nitrogen_needed) * potential_growth if nitrogen_needed > 0 else 0
        nitrogen_consumed = nitrogen_ppm
    else:
        actual_growth = potential_growth
        nitrogen_consumed = nitrogen_needed

    # 6. Update State
    plant_state['biomass_g'] += actual_growth
    reactor_state['nitrogen_concentration_ppm'] -= nitrogen_consumed

    # Ensure values don't go below zero
    reactor_state['nitrile_mass_g'] = max(0, reactor_state['nitrile_mass_g'])
    reactor_state['nitrogen_concentration_ppm'] = max(0, reactor_state['nitrogen_concentration_ppm'])
    plant_state['biomass_g'] = max(0, plant_state['biomass_g'])

    return reactor_state, plant_state
