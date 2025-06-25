import os
import subprocess

# Collect all python files in the directory and export the ts file
# output directory
src_dir = "."
output_dir = "i18n"

py_files = [
    os.path.join(root, f)
    for root, _, files in os.walk(src_dir)
    for f in files
    if f.endswith(".py")
]

os.makedirs(output_dir, exist_ok=True)

cmd = (
    ["pyside6-lupdate"]
    + py_files
    + ["-ts", f"{output_dir}/zh_CN.ts", f"{output_dir}/en_US.ts"]
)

print("Running command:")
print(" ".join(cmd))
subprocess.run(cmd)
