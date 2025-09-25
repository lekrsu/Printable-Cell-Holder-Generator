-----

# Printable Cell Holder Generator

Provides a Python script to generate custom `.step` files for 3D-printable battery cell holders. You can easily define the dimensions, cell size, spacing, and other features.

-----

## Usage

To generate a cell holder, run the script from your terminal using the following command structure.

```bash
python3 layout_step.py <x_dim> <y_dim> <spacing> <cell_size> <cover_thickness> <rounded_corners> <bms_holes> <ledge_width> [fillet_bms]
```

-----

## Setup venv

Before running the script, it is recommended to create a Python virtual environment and install the required dependencies.

1. Create a venv:

python3 -m venv venv

2. Activate the venv:

Linux/macOS:
```bash
source venv/bin/activate
```

Windows (PowerShell):
```bash
.\venv\Scripts\Activate.ps1
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

Note: If your Python version is above 3.12 and the installed cadquery version is below 2.5.2, the standard requirements.txt installation may fail. In that case, run:

pip install git+https://github.com/CadQuery/cadquery.git

-----

## Parameters

The script accepts the following arguments in order:

| Parameter | Description | Data Type |
| :--- | :--- | :--- |
| `x_dim` | Total width in mm. | `float` |
| `y_dim` | Total height of the holder in mm. | `float` |
| `spacing` | The minimum wall thickness between cell holes. (e.g., `0.43` for a 0.4mm nozzle). | `float` |
| `cell_size` | The diameter of your battery cell, including any desired tolerance (e.g., `21.5-21.7` for a 21700 cell). | `float` |
| `cover_thickness`| The thickness of the base plate of the holder. (`0.2-0.4` is normal) | `float` |
| `rounded_corners`| Enables or disables rounded external corners on the holder. | `true` / `false` |
| `bms_holes` | Adds mounting holes for balancing. | `true` / `false` |
| `ledge_width` | Ledge of cover in mm, `3.75` to mimic fishpaper. | `float` |
| `fillet_bms` | **(Optional, causes segmentation fault <18.5 cells)** Adds a fillet to the balancing holes. | `true` / `false` |

-----

## Example

Here is an example command for generating a holder for **21700 cells**, optimized for printing with a **0.4mm nozzle**.

```bash
python3 layout_step.py 100 100 0.43 21.5 0.4 true true 3.75 true
```
