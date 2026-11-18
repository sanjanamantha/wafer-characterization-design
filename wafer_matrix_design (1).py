"""
Wafer Matrix -- Full Characterization Die, repeated across a 4 inch wafer
----------------------------------------------------------------------------
Builds the full expanded characterization die (everything from v3: shape
matrix, line/space matrix, trench ruler, microloading arrays, square
ruler, open windows, alignment crosses) as ONE reusable cell, then steps
and repeats it across a 100mm (4 inch) wafer, similar to how a real fab
steps a reticle -- as many complete, non-overlapping copies as fit inside
the usable wafer area.

Also draws a thin wafer outline (with major/minor flats) as a reference
layer, so you can visually confirm the fill looks right.

Saves to your Desktop.
"""

import pya
import math
import os

# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------

layout = pya.Layout()
dbu = 0.001
layout.dbu = dbu

layer_index = layout.layer(1, 0)
wafer_outline_layer = layout.layer(99, 0)


# ---------------------------------------------------------------------------
# BASIC SHAPE HELPERS
# ---------------------------------------------------------------------------

def draw_rectangle(cell, layer, center_x, center_y, width, height):
    left = center_x - width / 2
    right = center_x + width / 2
    bottom = center_y - height / 2
    top_edge = center_y + height / 2
    box = pya.DBox(left, bottom, right, top_edge)
    cell.shapes(layer).insert(box)


def make_circle_points(center_x, center_y, diameter, num_points=64):
    radius = diameter / 2
    points = []
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        points.append(pya.DPoint(x, y))
    return points


def draw_circle(cell, layer, center_x, center_y, diameter):
    points = make_circle_points(center_x, center_y, diameter)
    cell.shapes(layer).insert(pya.DPolygon(points))


def draw_ring(cell, layer, center_x, center_y, outer_diameter, wall_thickness):
    outer_points = make_circle_points(center_x, center_y, outer_diameter)
    inner_diameter = outer_diameter - 2 * wall_thickness
    inner_points = make_circle_points(center_x, center_y, inner_diameter)
    ring_polygon = pya.DPolygon(outer_points)
    ring_polygon.insert_hole(inner_points)
    cell.shapes(layer).insert(ring_polygon)


def draw_cross(cell, layer, center_x, center_y, size, linewidth_ratio=0.25):
    arm_width = size * linewidth_ratio
    draw_rectangle(cell, layer, center_x, center_y, size, arm_width)
    draw_rectangle(cell, layer, center_x, center_y, arm_width, size)


def draw_mesh(cell, layer, center_x, center_y, size, num_cells=4):
    cell_size = size / (2 * num_cells - 1)
    start_x = center_x - size / 2 + cell_size / 2
    start_y = center_y - size / 2 + cell_size / 2
    for row in range(num_cells):
        for col in range(num_cells):
            x = start_x + col * 2 * cell_size
            y = start_y + row * 2 * cell_size
            draw_rectangle(cell, layer, x, y, cell_size, cell_size)


def draw_shape(cell, layer, shape_type, center_x, center_y, size):
    if shape_type == "circle":
        draw_circle(cell, layer, center_x, center_y, size)
    elif shape_type == "square":
        draw_rectangle(cell, layer, center_x, center_y, size, size)
    elif shape_type == "cross":
        draw_cross(cell, layer, center_x, center_y, size)
    elif shape_type == "ring":
        draw_ring(cell, layer, center_x, center_y, size, size * 0.2)
    elif shape_type == "mesh":
        draw_mesh(cell, layer, center_x, center_y, size)


def draw_shape_matrix(cell, layer, origin_x, origin_y, shape_types, sizes, col_pitch=300, row_pitch=300):
    for row_index, shape_type in enumerate(shape_types):
        for col_index, size in enumerate(sizes):
            cx = origin_x + col_index * col_pitch
            cy = origin_y - row_index * row_pitch
            draw_shape(cell, layer, shape_type, cx, cy, size)


def draw_line_space_array(cell, layer, origin_x, origin_y, line_width, pitch, length, num_lines):
    for i in range(num_lines):
        x = origin_x + i * pitch
        draw_rectangle(cell, layer, x, origin_y, line_width, length)
    return (num_lines - 1) * pitch + line_width


def draw_line_space_matrix(cell, layer, origin_x, origin_y, width_pitch_pairs, length, num_lines=8, block_gap=80):
    x_cursor = origin_x
    for line_width, pitch in width_pitch_pairs:
        block_width = draw_line_space_array(cell, layer, x_cursor, origin_y, line_width, pitch, length, num_lines)
        x_cursor = x_cursor + block_width + block_gap


def draw_trench_ruler(cell, layer, origin_x, origin_y, widths, length, gap=30):
    x_position = origin_x
    previous_half_width = 0
    for i, w in enumerate(widths):
        half_width = w / 2
        if i == 0:
            x_position = origin_x + half_width
        else:
            x_position = x_position + previous_half_width + gap + half_width
        draw_rectangle(cell, layer, x_position, origin_y, w, length)
        previous_half_width = half_width


def draw_microloading_arrays(cell, layer, origin_x, origin_y, line_width, densities, length, num_lines=5, block_gap=120):
    x_cursor = origin_x
    for density in densities:
        pitch = line_width / density
        block_width = draw_line_space_array(cell, layer, x_cursor, origin_y, line_width, pitch, length, num_lines)
        x_cursor = x_cursor + block_width + block_gap


def draw_square_ruler(cell, layer, origin_x, origin_y, sizes, gap=30):
    x_position = origin_x
    previous_half_size = 0
    for i, s in enumerate(sizes):
        half_size = s / 2
        if i == 0:
            x_position = origin_x + half_size
        else:
            x_position = x_position + previous_half_size + gap + half_size
        draw_rectangle(cell, layer, x_position, origin_y, s, s)
        previous_half_size = half_size


def draw_alignment_cross(cell, layer, center_x, center_y, arm_length=200, arm_width=20):
    draw_rectangle(cell, layer, center_x, center_y, arm_length, arm_width)
    draw_rectangle(cell, layer, center_x, center_y, arm_width, arm_length)


# ---------------------------------------------------------------------------
# BUILD ONE COMPLETE DIE (everything from v3, wrapped into a function so it
# can be built once and reused/repeated many times across the wafer)
# ---------------------------------------------------------------------------

def build_full_die(cell, layer):
    margin = 200
    cursor_top = 0

    cross_height = 200
    cross1_y = cursor_top - cross_height / 2
    draw_alignment_cross(cell, layer, 0, cross1_y)
    cursor_top = cross1_y - cross_height / 2 - margin

    shape_types = ["circle", "square", "cross", "ring", "mesh"]
    shape_sizes = [10, 20, 50, 100, 200]
    row_pitch = 300
    matrix_origin_y = cursor_top - max(shape_sizes) / 2
    draw_shape_matrix(cell, layer, 0, matrix_origin_y, shape_types, shape_sizes, row_pitch=row_pitch)
    matrix_bottom = matrix_origin_y - (len(shape_types) - 1) * row_pitch - max(shape_sizes) / 2
    cursor_top = matrix_bottom - margin

    ls_height = 400
    ls_y = cursor_top - ls_height / 2
    width_pitch_pairs = [(1, 2), (2, 4), (3, 6), (5, 10), (10, 20), (20, 40), (50, 100)]
    draw_line_space_matrix(cell, layer, 0, ls_y, width_pitch_pairs, length=ls_height)
    cursor_top = ls_y - ls_height / 2 - margin

    tr_height = 400
    tr_y = cursor_top - tr_height / 2
    trench_widths = [2, 5, 10, 20, 50, 100]
    draw_trench_ruler(cell, layer, 0, tr_y, trench_widths, length=tr_height)
    cursor_top = tr_y - tr_height / 2 - margin

    ml_height = 400
    ml_y = cursor_top - ml_height / 2
    densities = [0.1, 0.3, 0.5, 0.8]
    draw_microloading_arrays(cell, layer, 0, ml_y, 20, densities, length=ml_height)
    cursor_top = ml_y - ml_height / 2 - margin

    square_sizes = [5, 10, 20, 50, 100, 200]
    sq_height = max(square_sizes)
    sq_y = cursor_top - sq_height / 2
    draw_square_ruler(cell, layer, 0, sq_y, square_sizes)
    cursor_top = sq_y - sq_height / 2 - margin

    open_window_sizes = [500, 1500]
    ow_height = max(open_window_sizes)
    ow_y = cursor_top - ow_height / 2
    x_cursor = 0
    for size in open_window_sizes:
        draw_rectangle(cell, layer, x_cursor + size / 2, ow_y, size, size)
        x_cursor = x_cursor + size + 300
    cursor_top = ow_y - ow_height / 2 - margin

    cross2_y = cursor_top - cross_height / 2
    draw_alignment_cross(cell, layer, 0, cross2_y)


# Build it once, into its own cell
die_cell = layout.create_cell("DIE")
build_full_die(die_cell, layer_index)

bbox = die_cell.bbox()
die_left = bbox.left * dbu
die_right = bbox.right * dbu
die_bottom = bbox.bottom * dbu
die_top = bbox.top * dbu
die_width = die_right - die_left
die_height = die_top - die_bottom
print("Single die size: {:.1f} x {:.1f} microns".format(die_width, die_height))


# ---------------------------------------------------------------------------
# STEP AND REPEAT ACROSS THE WAFER
# ---------------------------------------------------------------------------

top = layout.create_cell("TOP")

wafer_radius_um = 50000       # 100mm / 2
edge_margin_um = 3000         # keep dies clear of the physical edge
usable_radius_um = wafer_radius_um - edge_margin_um

scribe_lane_um = 200          # gap between neighboring dies (dicing clearance)
pitch_x = die_width + scribe_lane_um
pitch_y = die_height + scribe_lane_um

max_index_x = int(usable_radius_um / pitch_x) + 2
max_index_y = int(usable_radius_um / pitch_y) + 2

placed_count = 0

for row in range(-max_index_y, max_index_y + 1):
    # brick-lay pattern: shift every other row sideways by half a pitch,
    # so dies in one row nestle into the gaps left by the row above/below.
    # This packs more complete dies into the curved space near the wafer
    # edge than a plain straight grid can.
    if row % 2 == 0:
        row_offset_x = 0
    else:
        row_offset_x = pitch_x / 2

    for col in range(-max_index_x, max_index_x + 1):
        target_left = col * pitch_x + row_offset_x - die_width / 2
        target_bottom = row * pitch_y - die_height / 2

        corners = [
            (target_left, target_bottom),
            (target_left + die_width, target_bottom),
            (target_left, target_bottom + die_height),
            (target_left + die_width, target_bottom + die_height),
        ]

        fits = True
        for cx, cy in corners:
            distance_from_center = math.sqrt(cx * cx + cy * cy)
            if distance_from_center > usable_radius_um:
                fits = False
                break

        if fits:
            shift_x = target_left - die_left
            shift_y = target_bottom - die_bottom
            shift_x_dbu = int(round(shift_x / dbu))
            shift_y_dbu = int(round(shift_y / dbu))
            top.insert(pya.CellInstArray(die_cell.cell_index(), pya.Trans(shift_x_dbu, shift_y_dbu)))
            placed_count += 1

print("Placed", placed_count, "dies across the wafer")


# ---------------------------------------------------------------------------
# WAFER OUTLINE (reference only)
# ---------------------------------------------------------------------------

def make_wafer_outline_points(radius, flats, points_per_degree=2):
    flat_ranges = []
    for center_angle, flat_length in flats:
        half_angle = math.degrees(math.asin((flat_length / 2) / radius))
        start = (center_angle - half_angle) % 360
        end = (center_angle + half_angle) % 360
        flat_ranges.append((start, end))

    def angle_in_flat(angle):
        for start, end in flat_ranges:
            if start < end:
                if start < angle < end:
                    return True
            else:
                if angle > start or angle < end:
                    return True
        return False

    points = []
    total_steps = int(360 * points_per_degree)
    for step in range(total_steps):
        angle_deg = step / points_per_degree
        if angle_in_flat(angle_deg):
            continue
        angle_rad = math.radians(angle_deg)
        x = radius * math.cos(angle_rad)
        y = radius * math.sin(angle_rad)
        points.append(pya.DPoint(x, y))
    return points


flats = [
    (270, 32500),
    (0, 18000),
]
outline_points = make_wafer_outline_points(wafer_radius_um, flats)
outline_points.append(outline_points[0])
wafer_outline_path = pya.DPath(outline_points, 200)
top.shapes(wafer_outline_layer).insert(wafer_outline_path)


# ---------------------------------------------------------------------------
# SAVE
# ---------------------------------------------------------------------------

output_path = os.path.expanduser("~/Desktop/wafer_matrix_design.gds")
layout.write(output_path)
print("Done. File saved to:", output_path)
