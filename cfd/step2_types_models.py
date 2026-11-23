"""Fix zone types, enable physics, and print the settings layout for the fan BC and the fixed nozzle temperature."""
import json
from fl import connect

FAN_FACE = "air_fan-air_main"                    # x = 19.25 ring, outlet side of the fan
FAN_INLET_RING = "air_fan-air_main_1"            # x = 29.25 ring, intake side
FAN_WALLS = ["air_fan-fanhub", "air_fan-fanframe"]
BOX = "airmain-1-air_main:40909:49022"

s = connect()
st = s.settings.setup
bc = st.boundary_conditions
bc.set_zone_type(zone_list=FAN_WALLS, new_type="wall")
bc.set_zone_type(zone_list=[FAN_INLET_RING], new_type="interior")
bc.set_zone_type(zone_list=[BOX], new_type="pressure-outlet")
print("fan zones now:", list(bc.fan.keys()), "| outlets:", list(bc.pressure_outlet.keys()))

st.models.energy.enabled = True
st.models.viscous.model = "k-omega"
st.models.viscous.k_omega_model = "sst"
og = st.general.operating_conditions
print("operating conditions:", json.dumps(og.get_state(), default=str)[:600])
print("FAN state:", json.dumps(bc.fan[FAN_FACE].get_state(), default=str)[:2500])
cz = st.cell_zone_conditions.solid["nozzlebody"]
cz.fixed_values.enable = True
print("FIXED VALUES state:", json.dumps(cz.fixed_values.get_state(), default=str)[:1500])
print("OUTLET state:", json.dumps(bc.pressure_outlet[BOX].get_state(), default=str)[:1500])
print("MATERIALS solid:", list(st.materials.solid.keys()), "fluid:", list(st.materials.fluid.keys()))
print("AIR density:", json.dumps(st.materials.fluid["air"].density.get_state(), default=str))
