"""Import the STEP into Fluent meshing and print the object / label names it creates."""
import os
import ansys.fluent.core as pf

HERE = os.path.dirname(os.path.abspath(__file__))
m = pf.launch_fluent(mode="meshing", precision="double", processor_count=4, ui_mode="no_gui", cwd=HERE, start_timeout=300)
m.workflow.InitializeWorkflow(WorkflowType="Watertight Geometry")
imp = m.workflow.TaskObject["Import Geometry"]
imp.Arguments.set_state({"FileName": os.path.join(HERE, "hotend_cfd_domain.step"), "LengthUnit": "mm"})
imp.Execute()
print("=== objects ===", flush=True)
m.tui.objects.list()
mu = m.meshing_utilities
print("PY objects:", m.scheme_eval.scheme_eval("(map (lambda (o) (symbol->string (get-obj-name o))) (get-all-objects))"))
for o in ("nozzlebody", "heatbreak", "heatsink", "air_fan", "air_main"):
    try:
        print(o, "labels:", mu.get_labels(object_name=o))
    except Exception as e:
        print(o, "err:", str(e)[:120])
m.exit()
