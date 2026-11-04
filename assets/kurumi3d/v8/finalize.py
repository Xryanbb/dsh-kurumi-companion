"""Rebuild, render a fair comparison, and open the independent head study."""
import bpy, runpy, json, math
from pathlib import Path
from mathutils import Vector
out=Path(__file__).resolve().parent
runpy.run_path(str(out/'build.py'),run_name='__main__')
runpy.run_path(str(out/'compare.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(out/'kurumi-head-study.blend'),load_ui=False,use_scripts=False)
# Run open_model_view.py in a fresh console call after Blender loads the file.
