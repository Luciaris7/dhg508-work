"""Build the bridge of the Californian in Blender, render it, and export the
hotspot geometry the web viewer needs.

    blender --background --factory-startup --python scene/build_bridge.py -- [--quick] [--glb]

Everything is modelled here, in code, so the scene can be rebuilt and audited.
The historical basis is in research/parts-table.md: the report and the Day 7
minutes describe a bridge, a chart room, a speaking tube, a Morse lamp and a
compass.  The sizes and arrangement are inferred from photographs of comparable
1900s merchant steamers; that inference is marked in the same table.

Coordinates: +X forward (bow), +Y to port, +Z up.  Bridge deck is z = 0, the
water line is z = -11.
"""

import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
OUT.mkdir(parents=True, exist_ok=True)

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
QUICK = "--quick" in ARGS
WANT_GLB = "--glb" in ARGS
HI = "--hi" in ARGS
ONLY = [ARGS[ARGS.index("--only") + 1]] if "--only" in ARGS else []
NO_STILLS = "--no-stills" in ARGS

DECK_FRONT = 2.3        # forward edge of the bridge deck
CHART_DOOR_X = -6.9

M = {}


def material(name, color, rough=0.5, metal=0.0, emission=None, strength=0.0,
             bump=0.0, bump_scale=40.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    if bump:
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = bump_scale
        noise.inputs["Detail"].default_value = 6.0
        bump_node = nodes.new("ShaderNodeBump")
        bump_node.inputs["Strength"].default_value = bump
        links.new(noise.outputs["Fac"], bump_node.inputs["Height"])
        links.new(bump_node.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def plank_material():
    """Teak deck: bands of plank along Y, with caulking lines between them."""
    mat = bpy.data.materials.new("teak planks")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    coord = nodes.new("ShaderNodeTexCoord")
    wave = nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Y"
    wave.inputs["Scale"].default_value = 22.0
    wave.inputs["Distortion"].default_value = 0.12
    wave.inputs["Detail"].default_value = 1.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.028, 0.017, 0.010, 1)
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = (0.102, 0.066, 0.039, 1)
    links.new(coord.outputs["Object"], wave.inputs["Vector"])
    links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.58
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 140.0
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def build_materials():
    M["deck"] = plank_material()
    M["deck_edge"] = material("deck edge", (0.13, 0.092, 0.062), rough=0.65)
    M["white"] = material("painted white", (0.50, 0.50, 0.47), rough=0.45,
                          bump=0.08, bump_scale=60)
    M["white_dirty"] = material("painted white, weathered", (0.38, 0.38, 0.36),
                                rough=0.55, bump=0.12, bump_scale=50)
    M["black"] = material("black paint", (0.028, 0.028, 0.032), rough=0.5)
    M["brass"] = material("brass", (0.52, 0.34, 0.11), rough=0.30, metal=1.0)
    M["glass"] = material("window glass", (0.015, 0.022, 0.03), rough=0.07)
    M["canvas"] = material("canvas dodger", (0.46, 0.44, 0.37), rough=0.92,
                           bump=0.2, bump_scale=120)
    M["lamp"] = material("oil lamp glass", (1.0, 0.72, 0.38), rough=0.2,
                         emission=(1.0, 0.62, 0.28), strength=22.0)
    M["lamp_cool"] = material("chart lamp glass", (1.0, 0.82, 0.58), rough=0.2,
                              emission=(1.0, 0.72, 0.42), strength=14.0)
    M["sea"] = material("sea", (0.004, 0.008, 0.014), rough=0.05,
                        bump=0.06, bump_scale=200)
    M["ice"] = material("field ice", (0.70, 0.78, 0.86), rough=0.30,
                        bump=0.3, bump_scale=12)
    M["ice_near"] = material("ice, close", (0.62, 0.72, 0.82), rough=0.22,
                             bump=0.4, bump_scale=8)
    M["uniform"] = material("officer's uniform", (0.065, 0.070, 0.090), rough=0.85)
    M["skin"] = material("skin", (0.30, 0.22, 0.18), rough=0.6)
    M["paper"] = material("chart paper", (0.34, 0.30, 0.22), rough=0.8)
    M["window_lit"] = material("lit window", (0.06, 0.05, 0.04), rough=0.4,
                               emission=(1.0, 0.58, 0.24), strength=0.60)
    M["metal_dark"] = material("dark metal", (0.07, 0.07, 0.08), rough=0.42, metal=0.9)
    M["star"] = material("star", (1, 1, 1), rough=1.0,
                         emission=(0.85, 0.90, 1.0), strength=40.0)
    M["moon"] = material("moon", (1, 0.97, 0.9), rough=1.0,
                         emission=(1.0, 0.96, 0.86), strength=14.0)


# ----------------------------------------------------------------- geometry


def box(name, size, loc, rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    if mat:
        obj.data.materials.append(mat)
    return obj


def cyl(name, radius, depth, loc, rot=(0, 0, 0), mat=None, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc,
                                        rotation=rot, vertices=verts)
    obj = bpy.context.object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return obj


def sphere(name, radius, loc, mat=None, seg=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=seg,
                                        ring_count=rings)
    obj = bpy.context.object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return obj


def room(name, x0, x1, y0, y1, z0, z1, thick=0.10, mat=None, open_side=None,
         opening=None):
    """Four walls, a floor and a ceiling; one wall may have a doorway cut out."""
    mat = mat or M["white"]
    w, d, h = x1 - x0, y1 - y0, z1 - z0
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    box(name + " floor", (w, d, thick), (cx, cy, z0 - thick / 2), mat=M["deck_edge"])
    box(name + " ceiling", (w, d, thick), (cx, cy, z1 + thick / 2), mat=mat)
    # forward / aft walls
    box(name + " wall fwd", (thick, d, h), (x1 + thick / 2, cy, cz), mat=mat)
    box(name + " wall aft", (thick, d, h), (x0 - thick / 2, cy, cz), mat=mat)
    # side walls, possibly with a doorway
    for side, yw in ((1, y1), (-1, y0)):
        wall = "%s wall %s" % (name, "port" if side > 0 else "stbd")
        if opening and side == open_side:
            ox0, ox1, oz1 = opening
            box(wall + " a", (ox0 - x0, thick, h), ((x0 + ox0) / 2, yw, cz), mat=mat)
            box(wall + " b", (x1 - ox1, thick, h), ((ox1 + x1) / 2, yw, cz), mat=mat)
            box(wall + " head", (ox1 - ox0, thick, h - oz1),
                ((ox0 + ox1) / 2, yw, z0 + oz1 + (h - oz1) / 2), mat=mat)
        else:
            box(wall, (w, thick, h), (cx, yw, cz), mat=mat)


def rail(name, x0, y0, x1, y1, z, posts=6, height=1.05, mat=None):
    mat = mat or M["white_dirty"]
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    angle = math.atan2(dy, dx)
    for i in range(posts + 1):
        t = i / posts
        cyl(name + "_post%d" % i, 0.022, height,
            (x0 + dx * t, y0 + dy * t, z + height / 2), mat=mat, verts=8)
    for zz in (z + height, z + height * 0.62, z + height * 0.32):
        cyl(name + "_wire%.2f" % zz, 0.011, length,
            ((x0 + x1) / 2, (y0 + y1) / 2, zz),
            rot=(0, math.pi / 2, angle), mat=M["metal_dark"], verts=6)


# ----------------------------------------------------------------- the ship


def build_ship():
    # hull, deck house, foredeck
    box("hull", (30.0, 11.0, 7.6), (2.0, 0, -7.8), mat=M["black"])
    box("bow wedge", (6.0, 7.0, 7.6), (18.0, 0, -7.8), rot=(0, 0, math.radians(45)),
        mat=M["black"])
    box("deck house", (11.6, 6.8, 3.8), (-2.9, 0, -2.1), mat=M["white_dirty"])
    box("foredeck", (13.0, 7.2, 0.16), (9.0, 0, -4.08), mat=M["deck"])
    box("fore bulwark", (0.10, 7.2, 1.15), (15.4, 0, -3.45), mat=M["white_dirty"])
    for side in (1, -1):
        box("fore bulwark %d" % side, (13.0, 0.10, 1.15), (9.0, side * 3.55, -3.45),
            mat=M["white_dirty"])
    box("fwd hatch", (1.5, 1.7, 0.30), (10.9, -1.1, -3.95), mat=M["deck_edge"])
    for side in (1, -1):
        cyl("bitt %d" % side, 0.09, 0.55, (7.4, side * 1.1, -3.75), mat=M["metal_dark"],
            verts=10)
    box("bitt base", (0.9, 2.6, 0.10), (7.4, 0, -4.02), mat=M["deck_edge"])
    cyl("fore mast", 0.12, 12.0, (11.0, 0, 1.8), mat=M["white_dirty"], verts=12)
    cyl("funnel", 0.95, 6.0, (-10.4, 0, 0.0), mat=M["black"], verts=28)
    cyl("funnel cap", 1.02, 0.25, (-10.4, 0, 3.05), mat=M["black"], verts=28)
    box("after house", (5.0, 6.0, 3.0), (-13.5, 0, -2.5), mat=M["white_dirty"])

    # bridge deck
    box("bridge deck", (11.2, 6.6, 0.14), (-3.3, 0, -0.07), mat=M["deck"])
    # forward bulwark: a low steel plate, canvas dodger above it
    box("bridge fwd plate", (0.10, 6.6, 0.85), (DECK_FRONT, 0, 0.425),
        mat=M["white_dirty"])
    box("bridge fwd dodger", (0.05, 6.4, 0.52), (DECK_FRONT + 0.02, 0, 1.11),
        mat=M["canvas"])
    box("bridge fwd cap", (0.20, 6.6, 0.05), (DECK_FRONT, 0, 0.86), mat=M["deck_edge"])
    # side wings: low plate and an open rail above it, which is what a bridge
    # wing actually looks like, and which leaves the view open
    for side in (1, -1):
        box("wing plate %d" % side, (11.2, 0.10, 0.55), (-3.3, side * 3.3, 0.275),
            mat=M["white_dirty"])
        box("wing cap %d" % side, (11.2, 0.18, 0.05), (-3.3, side * 3.3, 0.57),
            mat=M["deck_edge"])
        rail("wing rail %d" % side, DECK_FRONT, side * 3.3, -8.8, side * 3.3,
             0.55, posts=8, height=0.52)
    # weather cloth along the port wing only (the wind is from the port side)
    box("wing dodger", (8.4, 0.04, 0.42), (-4.2, 3.32, 0.95), mat=M["canvas"])

    # ---- wheelhouse (solid; the camera never goes inside)
    box("wheelhouse", (3.0, 5.0, 2.35), (-3.1, 0, 1.175), mat=M["white"])
    box("wheelhouse roof", (3.3, 5.3, 0.12), (-3.1, 0, 2.41), mat=M["white_dirty"])
    box("wh window band", (0.06, 4.7, 0.70), (-1.58, 0, 1.66), mat=M["glass"])
    for i in range(6):
        box("wh mullion f%d" % i, (0.09, 0.06, 0.70), (-1.56, -2.1 + i * 0.84, 1.66),
            mat=M["white_dirty"])
    for side in (1, -1):
        box("wh window side %d" % side, (2.6, 0.06, 0.62), (-3.1, side * 2.52, 1.66),
            mat=M["glass"])
        for i in range(3):
            box("wh mullion %d%d" % (side, i), (0.06, 0.09, 0.62),
                (-4.1 + i * 1.0, side * 2.52, 1.66), mat=M["white_dirty"])
    box("wh door", (0.06, 0.74, 1.96), (-4.62, -1.55, 0.98), mat=M["black"])
    box("wh door frame", (0.09, 0.88, 2.06), (-4.64, -1.55, 1.03), mat=M["white_dirty"])
    # the wheelhouse clock, on the aft bulkhead, facing the bridge
    box("clock bracket", (0.10, 0.06, 0.06), (-4.66, 0.95, 1.86), mat=M["brass"])
    box("clock case", (0.06, 0.28, 0.28), (-4.70, 0.95, 1.86), mat=M["brass"])
    cyl("clock face", 0.115, 0.02, (-4.74, 0.95, 1.86), rot=(0, math.pi / 2, 0),
        mat=M["paper"], verts=20)

    # ---- chart house: hollow, with a half-open door on the starboard wall
    room("chart house", -8.6, -5.2, -1.9, 2.3, 0.0, 2.15, mat=M["white"],
         open_side=-1, opening=(-7.35, -6.45, 1.95))
    box("chart roof", (3.6, 4.4, 0.12), (-6.9, 0.2, 2.21), mat=M["white_dirty"])
    door_angle = math.radians(-38)
    hinge = (-7.35, -1.96)
    leaf = 0.90
    cx = hinge[0] + leaf / 2 * math.cos(door_angle)
    cy = hinge[1] + leaf / 2 * math.sin(door_angle)
    box("chart door", (leaf, 0.06, 1.92), (cx, cy, 0.96),
        rot=(0, 0, door_angle), mat=M["black"])
    cyl("door knob", 0.035, 0.06,
        (hinge[0] + leaf * 0.92 * math.cos(door_angle) - 0.05,
         hinge[1] + leaf * 0.92 * math.sin(door_angle), 1.02),
        rot=(0, math.pi / 2, door_angle), mat=M["brass"], verts=10)
    # a porthole aft, and a window on the starboard side of the chart house
    cyl("porthole ring", 0.23, 0.07, (-8.63, 0.55, 1.74),
        rot=(0, math.pi / 2, 0), mat=M["brass"], verts=20)
    cyl("porthole glass", 0.185, 0.08, (-8.62, 0.55, 1.74),
        rot=(0, math.pi / 2, 0), mat=M["glass"], verts=20)
    box("chart window", (0.62, 0.07, 0.50), (-6.05, -1.92, 1.74), mat=M["window_lit"])
    box("chart window frame", (0.72, 0.05, 0.60), (-6.05, -1.94, 1.74),
        mat=M["white_dirty"])

    # a ship's bell on the forward bulwark, an inside dodger, a coil of rope
    box("bell bracket", (0.10, 0.10, 0.30), (2.24, -1.05, 1.02), mat=M["metal_dark"])
    cyl("bell", 0.13, 0.20, (2.12, -1.05, 1.14), mat=M["brass"], verts=18)

    # ---- instruments on the bridge
    cyl("binnacle base", 0.30, 0.85, (0.55, 0.35, 0.42), mat=M["white_dirty"], verts=18)
    cyl("binnacle collar", 0.31, 0.10, (0.55, 0.35, 0.88), mat=M["brass"], verts=18)
    sphere("compass dome", 0.20, (0.55, 0.35, 1.02), mat=M["glass"])
    for side in (1, -1):
        cyl("telegraph %d" % side, 0.16, 0.95, (-0.55, side * 1.15, 0.47),
            mat=M["brass"], verts=16)
        box("telegraph face %d" % side, (0.20, 0.22, 0.10), (-0.55, side * 1.15, 1.0),
            mat=M["brass"])
    cyl("speaking tube", 0.05, 0.58, (-4.48, 1.55, 1.06),
        rot=(0, math.radians(10), 0), mat=M["brass"], verts=12)
    cyl("tube mouth", 0.09, 0.10, (-4.45, 1.55, 1.32), mat=M["brass"], verts=12)
    # Morse lamp, starboard forward corner of the bridge
    cyl("morse pedestal", 0.06, 1.05, (1.75, -2.85, 0.52), mat=M["metal_dark"], verts=10)
    cyl("morse housing", 0.17, 0.26, (1.75, -2.85, 1.15), mat=M["metal_dark"], verts=16)
    cyl("morse lens", 0.13, 0.03, (1.75, -2.85, 1.30), mat=M["brass"], verts=16)
    # glasses on a bracket on the starboard cap rail
    box("glass bracket", (0.14, 0.10, 0.05), (1.15, -3.10, 0.62), mat=M["brass"])
    for side in (1, -1):
        cyl("binocular %d" % side, 0.045, 0.30, (1.15, -3.10 + side * 0.05, 0.74),
            rot=(0, math.radians(72), 0), mat=M["black"], verts=12)
    # oil lamp on the wheelhouse front
    box("lamp bracket", (0.30, 0.08, 0.08), (-1.55, -1.35, 2.22), mat=M["metal_dark"])
    cyl("lamp housing", 0.15, 0.34, (-1.45, -1.35, 2.38), mat=M["metal_dark"], verts=14)
    sphere("lamp glass", 0.115, (-1.45, -1.35, 2.38), mat=M["lamp"])
    # the scrap log, on the chart-house roof edge beside the bridge
    box("log box", (0.38, 0.28, 0.26), (0.0, -2.62, 0.13), mat=M["deck_edge"])
    box("scrap log", (0.26, 0.19, 0.04), (0.0, -2.62, 0.28), mat=M["paper"])
    cyl("pencil", 0.010, 0.14, (0.10, -2.59, 0.31), rot=(0, math.radians(20), 0),
        mat=M["metal_dark"], verts=6)
    # a lifebuoy on the port rail, for scale
    cyl("lifebuoy", 0.30, 0.10, (0.2, 3.28, 0.95), rot=(math.pi / 2, 0, 0),
        mat=M["canvas"], verts=24)
    cyl("lifebuoy hole", 0.20, 0.12, (0.2, 3.28, 0.95), rot=(math.pi / 2, 0, 0),
        mat=M["black"], verts=24)

    # ---- people
    officer("stone", (1.72, -2.96, 0.0), facing=math.radians(-96))
    seated_master("master", (-8.10, 0.82, 0.0))
    sphere("binnacle flame", 0.05, (0.55, 0.35, 0.95), mat=M["lamp"], seg=12, rings=8)
    draw_rigging()
    draw_winch()

    # ---- chart room interior
    box("chart table", (1.55, 0.95, 0.09), (-7.05, 0.82, 0.88), mat=M["deck"])
    for dx in (-0.75, 0.75):
        for dy in (-0.40, 0.40):
            box("table leg %.2f %.2f" % (dx, dy), (0.07, 0.07, 0.84),
                (-7.15 + dx, 0.75 + dy, 0.42), mat=M["deck_edge"])
    box("chart sheet", (1.00, 0.66, 0.01), (-7.15, 0.75, 0.93), mat=M["paper"])
    box("spare chart", (0.55, 0.40, 0.02), (-7.55, 1.15, 0.95), mat=M["paper"])
    # a bench along the port wall, a coat on a hook by the door
    box("bench", (1.4, 0.38, 0.07), (-7.0, 2.05, 0.44), mat=M["deck_edge"])
    for dx in (-0.6, 0.6):
        box("bench leg %.2f" % dx, (0.06, 0.30, 0.42), (-7.0 + dx, 2.05, 0.21),
            mat=M["deck_edge"])
    box("coat hook", (0.05, 0.05, 0.05), (-5.45, -1.70, 1.72), mat=M["brass"])
    box("coat", (0.16, 0.34, 0.72), (-5.42, -1.70, 1.32), mat=M["uniform"])
    # a framed chart on the forward wall
    box("wall chart", (0.04, 0.70, 0.50), (-5.42, 0.60, 1.55), mat=M["paper"])
    box("wall chart frame", (0.05, 0.78, 0.58), (-5.44, 0.60, 1.55),
        mat=M["deck_edge"])
    cyl("chart lamp base", 0.09, 0.05, (-6.70, 1.42, 0.93), mat=M["brass"], verts=12)
    cyl("chart lamp stem", 0.02, 0.34, (-6.70, 1.42, 1.10), mat=M["brass"], verts=8)
    sphere("chart lamp globe", 0.10, (-6.70, 1.42, 1.29), mat=M["lamp_cool"])
    box("chart clock", (0.06, 0.26, 0.26), (-8.52, 1.55, 1.62), mat=M["brass"])
    cyl("chart clock face", 0.11, 0.02, (-8.58, 1.55, 1.62), rot=(0, math.pi / 2, 0),
        mat=M["paper"], verts=20)


def officer(name, loc, facing=0.0):
    """A low-poly man in a heavy coat and a peaked cap, 1.76 m."""
    x, y, z = loc
    cos_f, sin_f = math.cos(facing), math.sin(facing)
    cyl(name + "_legs", 0.125, 0.90, (x, y, z + 0.45), mat=M["uniform"], verts=12)
    torso = cyl(name + "_torso", 0.185, 0.66, (x, y, z + 1.20), mat=M["uniform"], verts=14)
    torso.scale = (1.0, 0.66, 1.0)
    # shoulders and collar, so the silhouette reads as a person and not a pipe
    box(name + "_shoulders", (0.33, 0.34, 0.11), (x, y, z + 1.50),
        rot=(0, 0, facing + math.pi / 2), mat=M["uniform"])
    cyl(name + "_neck", 0.06, 0.08, (x, y, z + 1.56), mat=M["skin"], verts=8)
    sphere(name + "_head", 0.105, (x, y, z + 1.64), mat=M["skin"], seg=16, rings=10)
    cyl(name + "_cap", 0.115, 0.07, (x, y, z + 1.73), mat=M["uniform"], verts=14)
    box(name + "_peak", (0.13, 0.05, 0.018),
        (x + cos_f * 0.10, y + sin_f * 0.10, z + 1.70),
        rot=(0, 0, facing), mat=M["black"])
    for side in (1, -1):
        cyl("%s_arm%d" % (name, side), 0.05, 0.62,
            (x + math.cos(facing - side * 1.35) * 0.18,
             y + math.sin(facing - side * 1.35) * 0.18, z + 1.18),
            rot=(math.radians(6), 0, facing), mat=M["uniform"], verts=10)
    # a hand at the end of the starboard arm
    sphere(name + "_hand", 0.05,
           (x + math.cos(facing - 1.35) * 0.18 + cos_f * 0.02,
            y + math.sin(facing - 1.35) * 0.18 + sin_f * 0.02, z + 0.88),
           mat=M["skin"], seg=10, rings=8)


def seated_master(name, loc):
    """Seated in the chair, leaning back, cap still on: 1.35 m to the crown."""
    x, y, z = loc
    box(name + "_chair seat", (0.52, 0.54, 0.09), (x - 0.28, y, z + 0.44),
        mat=M["deck_edge"])
    box(name + "_chair back", (0.09, 0.54, 0.62), (x - 0.52, y, z + 0.86),
        mat=M["deck_edge"])
    for side in (1, -1):
        box("%s_chair arm%d" % (name, side), (0.42, 0.06, 0.05),
            (x - 0.28, y + side * 0.26, z + 0.66), mat=M["deck_edge"])
    cyl(name + "_thighs", 0.16, 0.42, (x + 0.02, y, z + 0.52), mat=M["uniform"], verts=12)
    box(name + "_thighs box", (0.34, 0.34, 0.16), (x + 0.10, y, z + 0.52),
        mat=M["uniform"])
    torso = cyl(name + "_torso", 0.18, 0.52, (x - 0.06, y, z + 0.95),
                mat=M["uniform"], verts=14)
    torso.scale = (1.0, 0.72, 1.0)
    box(name + "_shoulders", (0.10, 0.36, 0.24), (x - 0.10, y, z + 1.16),
        mat=M["uniform"])
    cyl(name + "_neck", 0.055, 0.08, (x - 0.06, y, z + 1.24), mat=M["skin"], verts=8)
    sphere(name + "_head", 0.105, (x - 0.04, y, z + 1.31), mat=M["skin"], seg=16,
           rings=10)
    cyl(name + "_cap", 0.115, 0.07, (x - 0.04, y, z + 1.40), mat=M["uniform"], verts=14)
    box(name + "_peak", (0.13, 0.05, 0.018), (x + 0.06, y, z + 1.37),
        rot=(0, 0, 0), mat=M["black"])
    sphere(name + "_hand", 0.05, (x + 0.16, y - 0.20, z + 0.72), mat=M["skin"],
           seg=10, rings=8)


def rod_between(name, a, b, radius=0.015, mat=None):
    """A thin cylinder from point a to point b (stays, shrouds, rails)."""
    import mathutils
    a_v, b_v = mathutils.Vector(a), mathutils.Vector(b)
    mid = (a_v + b_v) / 2
    direction = b_v - a_v
    length = direction.length
    cyl(name, radius, length, tuple(mid), mat=mat or M["metal_dark"], verts=6)
    obj = bpy.context.object
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")


def draw_rigging():
    top = (11.0, 0.0, 7.4)
    for i, (x, y, z) in enumerate(((-2.4, 0.0, 1.2), (-2.4, 3.0, 1.2),
                                   (-2.4, -3.0, 1.2), (15.2, 0.0, -3.4),
                                   (2.0, 4.4, -3.4), (2.0, -4.4, -3.4))):
        rod_between("stay%d" % i, top, (x, y, z), 0.012, M["metal_dark"])
    # a couple of halyards down the foremast
    rod_between("halyard", (11.0, 0.25, 7.0), (11.0, 0.25, -3.8), 0.010)


def draw_winch():
    cyl("winch drum", 0.26, 0.9, (6.6, 1.9, -3.55),
        rot=(0, math.pi / 2, 0), mat=M["metal_dark"], verts=16)
    for side in (1, -1):
        box("winch frame %d" % side, (0.12, 0.35, 0.55), (6.6, 1.9 + side * 0.5, -3.8),
            mat=M["white_dirty"])
    box("winch base", (1.4, 1.3, 0.12), (6.6, 1.9, -3.98), mat=M["deck_edge"])


# ----------------------------------------------------------------- night


def build_night():
    box("sea", (6000, 6000, 0.2), (0, 0, -11.1), mat=M["sea"])
    random.seed(11)
    # field ice: dense close to the ship, thinning to the horizon
    for i in range(240):
        r = 14 + (i * 2.6) ** 1.22
        if r > 520:
            break
        ang = math.radians(-40 + random.uniform(-95, 95))
        x = math.cos(ang) * r
        y = math.sin(ang) * r
        near = r < 90
        w = random.uniform(5, 14) if near else random.uniform(12, 34)
        d = random.uniform(4, 11) if near else random.uniform(8, 24)
        h = random.uniform(0.4, 1.1) if near else random.uniform(0.3, 0.9)
        box("floe%03d" % i, (w, d, h), (x, y, -10.75 + h / 2),
            rot=(random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03),
                 ang + random.uniform(-0.5, 0.5)),
            mat=M["ice_near"] if near else M["ice"])
    # a continuous belt at the horizon, so it reads as ice and not open sea
    for i in range(40):
        x = 26 + i * 2.4 + random.uniform(-4, 4)
        y = random.uniform(-34, 34)
        box("ahead floe%02d" % i,
            (random.uniform(8, 22), random.uniform(6, 16), random.uniform(0.6, 1.8)),
            (x, y, -10.7), rot=(0, 0, random.uniform(0, 3.14)),
            mat=M["ice_near"] if i % 2 else M["ice"])
    for i in range(70):
        ang = math.radians(random.uniform(0, 360))
        r = random.uniform(260, 520)
        box("distant ice %02d" % i,
            (random.uniform(40, 120), random.uniform(30, 80), 0.3),
            (math.cos(ang) * r, math.sin(ang) * r, -10.88),
            rot=(0, 0, ang + random.uniform(-0.5, 0.5)), mat=M["ice"])
    build_stars()
    build_moon_and_lamps()


def build_stars():
    """One mesh, a few hundred tiny quads on a sphere."""
    verts, faces = [], []
    random.seed(3)
    for _ in range(260):
        theta = random.uniform(0, 2 * math.pi)
        z = random.uniform(0.02, 0.75)
        r = 700.0
        rxy = math.sqrt(max(0.0, 1 - z * z))
        direction = Vector((rxy * math.cos(theta), rxy * math.sin(theta), z))
        center = direction * r
        up = Vector((0, 0, 1))
        if abs(direction.dot(up)) > 0.95:
            up = Vector((1, 0, 0))
        right = direction.cross(up).normalized()
        up2 = right.cross(direction).normalized()
        size = random.uniform(0.22, 0.62)
        base = len(verts)
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            verts.append(tuple(center + right * sx * size + up2 * sy * size))
        faces.append((base, base + 1, base + 2, base + 3))
    mesh = bpy.data.meshes.new("stars")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("stars", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(M["star"])


def build_moon_and_lamps():
    moon = bpy.data.lights.new("moonlight", type="SUN")
    moon.energy = 1.5
    moon.angle = math.radians(5.0)
    moon.color = (0.55, 0.68, 1.0)
    obj = bpy.data.objects.new("moonlight", moon)
    bpy.context.collection.objects.link(obj)
    obj.rotation_euler = (math.radians(62), 0, math.radians(135))

    # a very faint cool fill, so nothing is pure black
    fill = bpy.data.lights.new("sky fill", type="SUN")
    fill.energy = 0.10
    fill.angle = math.radians(60.0)
    fill.color = (0.45, 0.55, 0.85)
    obj = bpy.data.objects.new("sky fill", fill)
    bpy.context.collection.objects.link(obj)
    obj.rotation_euler = (math.radians(18), 0, math.radians(-40))

    bpy.ops.mesh.primitive_uv_sphere_add(radius=16.0, location=(-420, 380, 300),
                                         segments=24, ring_count=16)
    disc = bpy.context.object
    disc.name = "moon disc"
    disc.data.materials.append(M["moon"])

    for name, loc, energy, radius, color in (
            ("bridge lamp light", (-1.45, -1.35, 2.38), 26, 0.22, (1.0, 0.64, 0.32)),
            ("binnacle light", (0.55, 0.35, 1.05), 4.0, 0.10, (1.0, 0.72, 0.40)),
            ("chart lamp light", (-6.70, 1.42, 1.30), 9.0, 0.12, (1.0, 0.72, 0.42)),
            ("wheelhouse glow", (-3.1, 0.0, 1.7), 5.0, 0.6, (1.0, 0.74, 0.5)),
            ("chart room rim", (-7.55, 1.9, 1.95), 2.5, 0.15, (1.0, 0.78, 0.52))):
        lamp = bpy.data.lights.new(name, type="POINT")
        lamp.energy = energy
        lamp.shadow_soft_size = radius
        lamp.color = color
        item = bpy.data.objects.new(name, lamp)
        item.location = loc
        bpy.context.collection.objects.link(item)

    world = bpy.data.worlds[0] if bpy.data.worlds else bpy.data.worlds.new("night")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.004, 0.007, 0.016, 1)
    bg.inputs["Strength"].default_value = 1.0


# ----------------------------------------------------------------- cameras


NODES = {
    "bridge": {
        "loc": (-0.55, -2.50, 1.66),
        "look_at": (-2.20, -10.5, 0.35),
        "hotspots": {
            "light": (0.0, -1500.0, -8.6),
            "morse": (1.75, -2.85, 1.20),
            "glasses": (1.15, -3.10, 0.76),
            "clock": (-4.72, 0.95, 1.86),
            "tube": (-4.45, 1.55, 1.30),
            "stone": (1.72, -2.96, 1.35),
            "log": (0.0, -2.62, 0.33),
            "ice": (60.0, -300.0, -10.7),
            "door": (-7.20, -2.10, 1.10),
        },
    },
    "foredeck": {
        "loc": (9.4, 1.0, -2.30),
        "look_at": (34.0, -9.0, -7.5),
        "hotspots": {
            "light": (0.0, -1500.0, -8.6),
            "ice": (24.0, -90.0, -10.7),
            "gear": (6.6, 1.9, -3.5),
            "ladder": (2.6, 1.2, -2.4),
        },
    },
    "chart_room": {
        "loc": (-5.80, -1.05, 1.60),
        "look_at": (-8.00, 0.80, 1.10),
        "hotspots": {
            "master": (-8.10, 0.82, 1.28),
            "chart": (-7.05, 0.82, 0.95),
            "clock": (-8.52, 1.55, 1.62),
            "door": (-7.05, -2.20, 1.05),
        },
    },
}


def look_rotation(loc, target):
    dx, dy, dz = target[0] - loc[0], target[1] - loc[1], target[2] - loc[2]
    dist = math.hypot(dx, dy)
    yaw = math.atan2(-dx, dy)
    pitch = math.atan2(dist, -dz)
    return (pitch, 0.0, yaw)


def make_camera(name, node):
    cam_data = bpy.data.cameras.new("cam_" + name)
    cam_data.type = "PANO"
    cam_data.panorama_type = "EQUIRECTANGULAR"
    cam = bpy.data.objects.new("cam_" + name, cam_data)
    cam.location = node["loc"]
    cam.rotation_euler = look_rotation(node["loc"], node["look_at"])
    bpy.context.collection.objects.link(cam)
    return cam


def hotspot_angles(node):
    loc = node["loc"]
    rot = look_rotation(loc, node["look_at"])
    inv = Euler(rot, "XYZ").to_matrix().inverted()
    out = {}
    for key, point in node["hotspots"].items():
        d = inv @ Vector((point[0] - loc[0], point[1] - loc[1], point[2] - loc[2]))
        d.normalize()
        out[key] = {"yaw": round(math.degrees(math.atan2(d.x, -d.z)), 2),
                    "pitch": round(math.degrees(math.asin(max(-1.0, min(1.0, d.y)))), 2)}
    return {"loc": list(loc), "look_at": list(node["look_at"]),
            "hotspots": out}


# ----------------------------------------------------------------- render


def setup_cycles():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24 if QUICK else 160
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.device = "GPU"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == "OPTIX"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 1.4
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90


EXPOSURE = {"bridge": 1.40, "foredeck": 1.55, "chart_room": 1.85}


def render_pano(name, node):
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["cam_" + name]
    scene.view_settings.exposure = EXPOSURE.get(name, 1.4)
    scene.render.resolution_x = 1536 if QUICK else (6144 if HI else 3072)
    scene.render.resolution_y = scene.render.resolution_x // 2
    path = OUT / ("pano_%s.jpg" % name)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print("PANO", name, path.name, path.stat().st_size // 1024, "KB")


STILLS = {
    "exterior": {"loc": (13.0, -19.0, -5.5), "look_at": (-3.0, 0.5, 1.6), "lens": 32,
                 "exposure": 1.85},
    "chart_room": {"loc": (-6.05, -1.05, 1.56), "look_at": (-7.95, 0.75, 1.10),
                   "lens": 24, "exposure": 1.85},
}


def render_still(name, spec, res=(1760, 990)):
    scene = bpy.context.scene
    data = bpy.data.cameras.new("still_" + name)
    data.lens = spec["lens"]
    cam = bpy.data.objects.new("still_" + name, data)
    cam.location = spec["loc"]
    cam.rotation_euler = look_rotation(spec["loc"], spec["look_at"])
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    scene.view_settings.exposure = spec["exposure"]
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.image_settings.file_format = "PNG"
    path = OUT / ("still_%s.png" % name)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print("STILL", name, path.name, path.stat().st_size // 1024, "KB")


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build_materials()
    build_ship()
    build_night()
    setup_cycles()
    for name, node in NODES.items():
        make_camera(name, node)
    bpy.context.view_layer.update()

    data = {name: hotspot_angles(node) for name, node in NODES.items()}
    (OUT / "hotspots.json").write_text(json.dumps(data, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    print("HOTSPOTS written")

    for name in NODES:
        if ONLY and name not in ONLY:
            continue
        render_pano(name, NODES[name])
    if not QUICK and not NO_STILLS:
        for name, spec in STILLS.items():
            render_still(name, spec)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "bridge.blend"))
    if WANT_GLB:
        bpy.ops.export_scene.gltf(filepath=str(OUT / "bridge.glb"),
                                  export_format="GLB", export_cameras=False)
        print("GLB", (OUT / "bridge.glb").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
