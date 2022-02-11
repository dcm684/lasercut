import os
import sys


def exit_with_error(error_str: str):
    print(error_str)
    exit(1)

# Verify that the given file exists
source_abs_path = None
source_basename = None
source_folder = None
if len(sys.argv) == 1:
    exit_with_error("Need input file")
else:
    source_abs_path = f"{os.path.abspath(sys.argv[1])}"
    if not os.path.isfile(source_abs_path):
        exit_with_error(f"Invalid source file: {sys.argv[1]}")
    else:
        source_basename = os.path.basename(source_abs_path)
        source_folder = os.path.dirname(source_abs_path)

# Get the path to openSCAD
openscad_path = None
enviro_val = os.environ.get("OPENSCAD_BIN")
if enviro_val is not None:
    openscad_path = enviro_val
else:
    import platform

    python_platform = platform.platform()

    if "Darwin" in python_platform:
        # OSX
        openscad_path = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"

    elif "Windows" in python_platform:
        # Windows. Determine if openSCAD is 32-bit or 64-bit
        prog_files_32_path = os.environ["PROGRAMFILES"]
        prog_files_64_path = os.environ["ProgramW6432"]
        prog_files_openscad = "OpenSCAD/openscad.exe"

        openscad_32_path = os.path.join(prog_files_32_path, prog_files_openscad)
        if os.path.isfile(openscad_32_path):
            openscad_path = os.path.normpath(openscad_32_path)

        elif prog_files_64_path is not None:
            openscad_64_path = os.path.join(prog_files_64_path, prog_files_openscad)

            if os.path.isfile(openscad_64_path):
                openscad_path = os.path.normpath(openscad_64_path)
                print(openscad_64_path)
                print(openscad_path)

    else:
        # Assume Linux. See if the openscad exists on the path
        from shutil import which

        if which("openscad") is not None:
            openscad_path = "openscad"

if openscad_path is None:
    exit_with_error("Could not find the openscad executable")

# openscad has been found
# Get the output file name
source_base_no_ext = os.path.splitext(source_basename)[0]
out_file_base = f"{source_base_no_ext}_2d"
out_scad_path = os.path.join(source_folder, f"{out_file_base}.scad")

# Process the input openscad file
temp_folder = source_folder
temp_csg = os.path.join(temp_folder, f"temp_{out_file_base}.csg")

import subprocess

output = subprocess.run(
    f'"{openscad_path}" "{source_abs_path}" -D generate=1 -o "{temp_csg}"',
    capture_output=True,
)

# The CSG file was only used to get the output, delete it immediately
os.remove(temp_csg)

if output.returncode != 0:
    exit_with_error(f"Failed to convert to csg file.\nError: {output.stderr}")

# Process the outputted text (rendered text via stderr)
output_file_contents = output.stderr.decode()
output_file_contents = output_file_contents.replace("\r\n", "\n")

# Strip the string 'ECHO: "[LC] ' and its closing '"' and remove warnings
import re

output_file_contents = re.sub('ECHO: "\[LC\] ', "", output_file_contents)
output_file_contents = re.sub('"\n', "\n", output_file_contents)
output_file_contents = re.sub("WARNING.*", "", output_file_contents)
output_file_contents += ";"

# Add the library and some other basic commands to make a working scad file
scad_header = """// May need to adjust location of <lasercut.scad>
use <lasercut/lasercut.scad>;
$fn=60;
projection(cut = false)\n\n"""

output_file_contents = scad_header + output_file_contents

# Write the output file
with open(out_scad_path, "w") as outfile:
    outfile.write(output_file_contents)

# Render the file as an SVG
print("Rendering and exporting as SVG")
out_svg_path = os.path.join(source_folder, f"{out_file_base}.svg")

output = subprocess.run(
    f'"{openscad_path}" "{out_scad_path}" -o "{out_svg_path}"',
    capture_output=True,
)

if (output.returncode != 0):
    exit_with_error(f"Failed to convert to SVG:\n{output.stderr}")