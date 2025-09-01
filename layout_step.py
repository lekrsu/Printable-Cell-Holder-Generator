import sys
import cadquery as cq
import numpy as np
from collections import defaultdict

def generate_grid_layout(x_dim, y_dim, spacing, cell_size):
    radius = cell_size / 2
    x_start = radius + spacing
    y_start = radius + spacing
    y_coords = np.arange(y_start, y_dim - radius - spacing + 0.01, cell_size + spacing)
    x_coords = np.arange(x_start, x_dim - radius - spacing + 0.01, cell_size + spacing)
    return [(x, y) for y in y_coords for x in x_coords]

def generate_honeycomb_layout(x_dim, y_dim, spacing, cell_size):
    radius = cell_size / 2
    y = radius + spacing
    row = 0
    positions = []
    while y + radius + spacing <= y_dim:
        x_offset = (cell_size + spacing) / 2 if row % 2 else 0
        x = radius + spacing + x_offset
        while x + radius + spacing <= x_dim:
            positions.append((x, y))
            x += cell_size + spacing
        y += np.sqrt(3) * (radius + spacing / 2)
        row += 1
    return positions

def generate_vertical_honeycomb_layout(x_dim, y_dim, spacing, cell_size):
    radius = cell_size / 2
    x = radius + spacing
    col = 0
    positions = []
    while x + radius + spacing <= x_dim:
        y_offset = (cell_size + spacing) / 2 if col % 2 else 0
        y = radius + spacing + y_offset
        while y + radius + spacing <= y_dim:
            positions.append((x, y))
            y += cell_size + spacing
        x += np.sqrt(3) * (radius + spacing / 2)
        col += 1
    return positions

def create_3d_model(positions, cell_size, spacing, height=10.0, terminal_diameter=7.0, terminal_depth=1.0, cover_thickness=0.4, rounded_corners=False, bms_holes=True, ledge_width=1.0):
    if not positions:
        return None

    r = cell_size / 2
    min_x = min(x for x, y in positions) - r - spacing
    min_y = min(y for x, y in positions) - r - spacing
    max_x = max(x for x, y in positions) + r + spacing
    max_y = max(y for x, y in positions) + r + spacing

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    adjusted = [(x - center_x, y - center_y) for x, y in positions]

    hole_diameter = 4.0
    hole_offset = r - spacing * 5

    rows = defaultdict(list)
    for x, y in adjusted:
        rows[int(y * 1000)].append((x, y))

    top_y = max(rows)
    bottom_y = min(rows)

    top_holes = [((rows[top_y][i][0] + rows[top_y][i + 1][0]) / 2, rows[top_y][0][1] + hole_offset) for i in range(len(rows[top_y]) - 1)]
    bottom_holes = [((rows[bottom_y][i][0] + rows[bottom_y][i + 1][0]) / 2, rows[bottom_y][0][1] - hole_offset) for i in range(len(rows[bottom_y]) - 1)]

    width = max_x - min_x
    length = max_y - min_y
    corner_radius = 5.0

    if rounded_corners:
        base = cq.Workplane("XY").rect(width, length).extrude(height).edges("|Z").fillet(corner_radius)
    else:
        base = cq.Workplane("XY").box(width, length, height, centered=(True, True, False))

    base = base.cut(cq.Workplane("XY").pushPoints(adjusted).circle(r).extrude(height))

    if bms_holes:
        all_bms = top_holes + bottom_holes
        base = base.cut(cq.Workplane("XY").pushPoints(all_bms).circle(hole_diameter / 2).extrude(height))

    base = base.cut(cq.Workplane("XY", origin=(0, 0, height)).pushPoints(adjusted).circle(terminal_diameter / 2).extrude(terminal_depth))

    rings = cq.Workplane("XY", origin=(0, 0, cover_thickness)).pushPoints(adjusted).circle(r).circle(r - ledge_width).extrude(-cover_thickness)
    return base.union(rings, glue=True)

def save_models(x_dim, y_dim, grid_positions, honeycomb_positions, vertical_honeycomb_positions, cell_size, spacing, cover_thickness, rounded_corners, bms_holes, ledge_width):
    height = 10.0
    terminal_diameter = 7.0
    terminal_depth = 1.0

    layouts = [
        (grid_positions, "grid_layout.step", "Grid Layout"),
        (honeycomb_positions, "honeycomb_layout.step", "Honeycomb Layout"),
        (vertical_honeycomb_positions, "vertical_honeycomb_layout.step", "Vertical Honeycomb Layout")
    ]

    for positions, filename, layout_name in layouts:
        model = create_3d_model(positions, cell_size, spacing, height, terminal_diameter, terminal_depth, cover_thickness, rounded_corners, bms_holes, ledge_width)
        if model:
            cq.exporters.export(model.val(), filename, exportType='STEP', opt={"schema": "AP214"})
            print(f"Saved {layout_name} to {filename} with {len(positions)} cells")
        else:
            print(f"No cells in {layout_name}, skipping export")

def main():
    if len(sys.argv) != 9:
        print("Usage: python3 layout_step.py <x_dim> <y_dim> <spacing> <cell_size> <cover_thickness> <rounded_corners[true/false]> <bms_holes[true/false]> <ledge_width>")
        sys.exit(1)

    x_dim = float(sys.argv[1])
    y_dim = float(sys.argv[2])
    spacing = float(sys.argv[3])
    cell_size = float(sys.argv[4])
    cover_thickness = float(sys.argv[5])
    rounded_corners = sys.argv[6].lower() == "true"
    bms_holes = sys.argv[7].lower() == "true"
    ledge_width = float(sys.argv[8])

    if cell_size <= 0:
        print("Cell size must be positive")
        sys.exit(1)

    grid_positions = generate_grid_layout(x_dim, y_dim, spacing, cell_size)
    honeycomb_positions = generate_honeycomb_layout(x_dim, y_dim, spacing, cell_size)
    vertical_honeycomb_positions = generate_vertical_honeycomb_layout(x_dim, y_dim, spacing, cell_size)

    save_models(x_dim, y_dim, grid_positions, honeycomb_positions, vertical_honeycomb_positions, cell_size, spacing, cover_thickness, rounded_corners, bms_holes, ledge_width)

if __name__ == "__main__":
    main()
