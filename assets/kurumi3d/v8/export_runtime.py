"""Export the existing v8 study to native SceneKit geometry, without rebuilding it.

Run with Blender: blender -b kurumi-head-study.blend --python export_runtime.py
Only the named head scene is exported; reference/comparison panels are excluded.
"""
from pathlib import Path
import hashlib
import gzip
import json
import math
import shutil

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / 'runtime'
ROOT = HERE.parents[2]


def material_spec(material):
    name = material.name if material else ''
    color = list(material.diffuse_color) if material else [.5, .5, .5, 1.]
    if name.startswith('Face |'):
        return dict(kind='face', color=[.92, .76, .65, 1.], texture='face.png')
    if name.startswith('Hair | painted'):
        return dict(kind='hair', color=[.033, .024, .028, 1.], texture='hair-albedo.png')
    if name.startswith('Ink |'):
        return dict(kind='ink', color=[.007, .0045, .006, 1.])
    return dict(kind='plain', color=color)


def export():
    scene = bpy.data.scenes.get('Kurumi | head study v8')
    if scene is None:
        raise RuntimeError('Open kurumi-head-study.blend before exporting')
    bpy.context.window.scene = scene
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    OUT.mkdir(exist_ok=True)
    records = []
    lower = np.array([math.inf] * 3)
    upper = -lower
    total_triangles = 0
    with (OUT / 'geometry.bin').open('wb') as stream:
        for obj in sorted(scene.objects, key=lambda o: o.name):
            if obj.type not in {'MESH', 'CURVE'} or obj.hide_render:
                continue
            evaluated = obj.evaluated_get(graph)
            mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=graph)
            try:
                mesh.calc_loop_triangles()
                if not mesh.loop_triangles:
                    continue
                count = len(mesh.loops)
                coordinates = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
                mesh.vertices.foreach_get('co', coordinates)
                coordinates = coordinates.reshape(-1, 3)
                matrix = np.array(evaluated.matrix_world, dtype=np.float32)
                coordinates = coordinates @ matrix[:3, :3].T + matrix[:3, 3]
                coordinates = coordinates[:, [0, 2, 1]] * [1, 1, -1]
                vertex_ids = np.empty(count, dtype=np.int32)
                mesh.loops.foreach_get('vertex_index', vertex_ids)
                normals = np.empty(count * 3, dtype=np.float32)
                mesh.corner_normals.foreach_get('vector', normals)
                normals = normals.reshape(-1, 3)
                normal_matrix = np.linalg.inv(matrix[:3, :3]).T
                normals = normals @ normal_matrix.T
                normals = normals[:, [0, 2, 1]] * [1, 1, -1]
                normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
                loops = np.empty((count, 8), dtype='<f4')
                loops[:, :3] = coordinates[vertex_ids]
                loops[:, 3:6] = normals
                uv_name = 'FaceUV' if any(m and m.name.startswith('Face |') for m in mesh.materials) else 'StrandUV'
                uv = mesh.uv_layers.get(uv_name)
                if uv:
                    values = np.empty(count * 2, dtype=np.float32)
                    uv.data.foreach_get('uv', values)
                    loops[:, 6:] = values.reshape(-1, 2)
                else:
                    loops[:, 6:] = 0
                if not np.isfinite(loops).all():
                    raise RuntimeError('Non-finite vertex data: ' + obj.name)
                triangles = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int32)
                mesh.loop_triangles.foreach_get('loops', triangles)
                triangles = triangles.reshape(-1, 3)
                slots = np.array([tri.material_index for tri in mesh.loop_triangles], dtype=np.int32)
                for slot in np.unique(slots):
                    corner_ids = triangles[slots == slot].ravel()
                    vertices, indices = np.unique(loops[corner_ids], axis=0, return_inverse=True)
                    vertices = np.ascontiguousarray(vertices, dtype='<f4')
                    indices = np.ascontiguousarray(indices, dtype='<u4')
                    mat = mesh.materials[int(slot)] if slot < len(mesh.materials) else None
                    record = dict(name=obj.name + (' / ' + str(slot) if len(np.unique(slots)) > 1 else ''),
                                  vertexOffset=stream.tell(), vertexCount=len(vertices))
                    stream.write(vertices.tobytes())
                    record.update(indexOffset=stream.tell(), indexCount=len(indices), material=material_spec(mat))
                    stream.write(indices.tobytes())
                    records.append(record)
                    lower = np.minimum(lower, vertices[:, :3].min(axis=0))
                    upper = np.maximum(upper, vertices[:, :3].max(axis=0))
                    total_triangles += len(indices) // 3
            finally:
                evaluated.to_mesh_clear()
    (OUT / 'geometry.bin.gz').write_bytes(gzip.compress((OUT / 'geometry.bin').read_bytes(), compresslevel=9, mtime=0))
    shutil.copy2(ROOT / 'assets/kurumi3d/v2/face.png', OUT / 'face.png')
    shutil.copy2(HERE / 'hair-albedo.png', OUT / 'hair-albedo.png')
    data = dict(version=1, model='kurumi-head-v8', bounds=dict(min=lower.tolist(), max=upper.tolist()), meshes=records)
    (OUT / 'scene.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    report = dict(source='assets/kurumi3d/v8/kurumi-head-study.blend',
                  sourceSHA256=hashlib.sha256((HERE / 'kurumi-head-study.blend').read_bytes()).hexdigest(),
                  meshParts=len(records), vertices=sum(m['vertexCount'] for m in records),
                  triangles=total_triangles, bytes=(OUT / 'geometry.bin').stat().st_size,
                  referencePanelsIncluded=False, animations=0, coordinateTransform='Blender (x,y,z) to SceneKit (x,z,-y)',
                  materialConversion='Face UV and alpha/front-normal mask; strand UV; linear material colors; inverted ink hulls')
    (OUT / 'export-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    export()
