import subprocess
import sys

def run_geom_command(command: str):     
   subprocess.run(f"python3 -m geom {command}".split()) 

