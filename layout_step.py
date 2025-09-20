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

def create_3d_model(positions, cell_size, spacing, height=10.0, terminal_diameter=7.0, terminal_depth=1.0, cover_thickness=0.4, rounded_corners=False, bms_holes=True, ledge_width=1.0, fillet_bms=False, layout_type=0):
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
    
    if layout_type == 2:
        bms_fillet_radius = 1.5
    else:
        bms_fillet_radius = 0.5
    
    hole_offset = r + spacing - 2.3 - spacing
    
    if layout_type == 2:
        hole_offset -= 2.25

    rows = defaultdict(list)
    for x, y in adjusted:
        rows[int(y * 1000)].append((x, y))

    width = max_x - min_x
    length = max_y - min_y
    corner_radius = 5.0

    valid_bms_holes = []
    if bms_holes:
        if rounded_corners:
            test_body = cq.Workplane("XY").rect(width, length).extrude(height).edges("|Z").fillet(corner_radius)
        else:
            test_body = cq.Workplane("XY").box(width, length, height, centered=(True, True, False))

        potential_holes = []
        x_step = cell_size + spacing
        
        top_y_key = max(rows)
        bottom_y_key = min(rows)
        
        if len(rows[top_y_key]) > 0:
            top_row = rows[top_y_key]
            y_pos = top_row[0][1] + hole_offset
            potential_holes.append((top_row[0][0] - x_step / 2, y_pos))
            for i in range(len(top_row) - 1):
                potential_holes.append(((top_row[i][0] + top_row[i + 1][0]) / 2, y_pos))
            potential_holes.append((top_row[-1][0] + x_step / 2, y_pos))

        if len(rows[bottom_y_key]) > 0:
            bottom_row = rows[bottom_y_key]
            y_pos = bottom_row[0][1] - hole_offset
            potential_holes.append((bottom_row[0][0] - x_step / 2, y_pos))
            for i in range(len(bottom_row) - 1):
                potential_holes.append(((bottom_row[i][0] + bottom_row[i + 1][0]) / 2, y_pos))
            potential_holes.append((bottom_row[-1][0] + x_step / 2, y_pos))

        if layout_type == 2:
            adjusted_potential_holes = []
            
            holes_by_row = defaultdict(list)
            for hole_x, hole_y in potential_holes:
                holes_by_row[hole_y].append(hole_x)
            
            for y_pos in holes_by_row:
                holes_by_row[y_pos].sort()
            
            for hole_x, hole_y in potential_holes:
                new_hole_x = hole_x
                
                row_holes = holes_by_row[hole_y]
                
                is_leftmost = hole_x == min(row_holes)
                is_rightmost = hole_x == max(row_holes)
                
                if is_leftmost:
                    has_cell_to_left = any(cx < hole_x - x_step/4 
                                         for cx, cy in adjusted 
                                         if abs(cy - hole_y) < (cell_size + spacing)/2)
                    if not has_cell_to_left:
                        adjustment = x_step / 2 * 0.5
                        new_hole_x = hole_x - adjustment
                
                elif is_rightmost:
                    has_cell_to_right = any(cx > hole_x + x_step/4 
                                          for cx, cy in adjusted 
                                          if abs(cy - hole_y) < (cell_size + spacing)/2)
                    if not has_cell_to_right:
                        adjustment = x_step / 2 * 0.5
                        new_hole_x = hole_x + adjustment
                
                adjusted_potential_holes.append((new_hole_x, hole_y))
            
            potential_holes = adjusted_potential_holes

        test_pin_volume = (np.pi * (hole_diameter / 2)**2) * height
        for x, y in potential_holes:
            test_pin = cq.Workplane("XY").pushPoints([(x, y)]).circle(hole_diameter / 2).extrude(height)
            intersection = test_body.intersect(test_pin)
            
            if intersection.val() and intersection.val().Volume() >= (test_pin_volume * 0.49):
                valid_bms_holes.append((x, y))

    if rounded_corners:
        base = cq.Workplane("XY").rect(width, length).extrude(height).edges("|Z").fillet(corner_radius)
    else:
        base = cq.Workplane("XY").box(width, length, height, centered=(True, True, False))

    base = base.cut(cq.Workplane("XY").pushPoints(adjusted).circle(r).extrude(height))

    if valid_bms_holes:
        unique_valid_holes = sorted(list(set(valid_bms_holes)))
        bms_holes_cut = cq.Workplane("XY").pushPoints(unique_valid_holes).circle(hole_diameter / 2).extrude(height)
        base = base.cut(bms_holes_cut)

        if fillet_bms:
            all_edges_sel = None
            for x_pos, y_pos in unique_valid_holes:
                s_top = cq.selectors.NearestToPointSelector((x_pos, y_pos, height)) & cq.selectors.RadiusNthSelector(0)
                s_bot = cq.selectors.NearestToPointSelector((x_pos, y_pos, 0)) & cq.selectors.RadiusNthSelector(0)
                hole_sel = s_top + s_bot
                if all_edges_sel is None: all_edges_sel = hole_sel
                else: all_edges_sel = all_edges_sel + hole_sel
            
            if all_edges_sel is not None and base.edges(all_edges_sel).vals():
                base = base.edges(all_edges_sel).fillet(bms_fillet_radius)

    base = base.cut(cq.Workplane("XY", origin=(0, 0, height)).pushPoints(adjusted).circle(terminal_diameter / 2).extrude(terminal_depth))
    rings = cq.Workplane("XY", origin=(0, 0, cover_thickness)).pushPoints(adjusted).circle(r).circle(r - ledge_width).extrude(-cover_thickness)
    
    return base.union(rings, glue=True)

def save_models(x_dim, y_dim, grid_positions, honeycomb_positions, vertical_honeycomb_positions, cell_size, spacing, cover_thickness, rounded_corners, bms_holes, ledge_width, fillet_bms=False):
    height = 10.0
    terminal_diameter = 7.0
    terminal_depth = 1.0

    layouts = [
        (grid_positions, "grid_layout.step", "Grid Layout", 0),
        (honeycomb_positions, "honeycomb_layout.step", "Honeycomb Layout", 1),
        (vertical_honeycomb_positions, "vertical_honeycomb_layout.step", "Vertical Honeycomb Layout", 2)
    ]

    for positions, filename, layout_name, layout_type in layouts:
        model = create_3d_model(positions, cell_size, spacing, height, terminal_diameter, terminal_depth, cover_thickness, rounded_corners, bms_holes, ledge_width, fillet_bms, layout_type)
        if model:
            cq.exporters.export(model.val(), filename, exportType='STEP', opt={"schema": "AP214"})
            if fillet_bms:
                print(f"Saved {layout_name} with filleted BMS holes to {filename} with {len(positions)} cells")
            else:
                print(f"Saved {layout_name} to {filename} with {len(positions)} cells")
        else:
            print(f"No cells in {layout_name}, skipping export")

def main():
    if len(sys.argv) < 9 or len(sys.argv) > 10:
        print("Usage: python3 layout_step.py <x_dim> <y_dim> <spacing> <cell_size> <cover_thickness> <rounded_corners[true/false]> <bms_holes[true/false]> <ledge_width> [fillet_bms[true/false]]")
        sys.exit(1)

    x_dim = float(sys.argv[1])
    y_dim = float(sys.argv[2])
    spacing = float(sys.argv[3])
    cell_size = float(sys.argv[4])
    cover_thickness = float(sys.argv[5])
    rounded_corners = sys.argv[6].lower() == "true"
    bms_holes = sys.argv[7].lower() == "true"
    ledge_width = float(sys.argv[8])
    
    fillet_bms = False
    if len(sys.argv) == 10:
        fillet_bms = sys.argv[9].lower() == "true"

    if cell_size <= 0:
        print("Cell size must be positive")
        sys.exit(1)

    grid_positions = generate_grid_layout(x_dim, y_dim, spacing, cell_size)
    honeycomb_positions = generate_honeycomb_layout(x_dim, y_dim, spacing, cell_size)
    vertical_honeycomb_positions = generate_vertical_honeycomb_layout(x_dim, y_dim, spacing, cell_size)

    save_models(x_dim, y_dim, grid_positions, honeycomb_positions, vertical_honeycomb_positions, cell_size, spacing, cover_thickness, rounded_corners, bms_holes, ledge_width, fillet_bms)

if __name__ == "__main__":
    main()