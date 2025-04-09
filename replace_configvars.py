import sys
import re
import os

input_file = sys.argv[1]
print(f"Converting into lowercase for file {input_file}")
#output_file = input_file.lower()
basex=os.path.basename(input_file).lower()
dirx=os.path.dirname(input_file)

output_file = os.path.join(dirx,basex)
# Read the input file
with open(input_file, "r") as file:
    content = file.read()

# Replace occurrences of config.xxxx with config.get('xxxx') (converted to lowercase)
#updated_content = re.sub(r"config\.([a-zA-Z0-9_]+)", lambda m: f"config.get('{m.group(1).lower()}')", content)
#updated_content = re.sub(r"Wave_PostProcessingHpcSubmit\.([a-zA-Z0-9_]+)", lambda m: f"config.get('{m.group(1).lower()}')", content)
updated_content = re.sub(r"([a-zA-Z0-9_]+):", lambda m: f"{m.group(1).lower()}:", content)

# Write the modified content back to a file
with open(output_file, "w") as file:
    file.write(updated_content)

print("Replacement done! Check output.txt")



