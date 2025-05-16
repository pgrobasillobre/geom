import subprocess

def run_geom_command(command: str):     
   """
   Run the given GEOM CLI command using subprocess.

   Args:
       command (str): The GEOM command string to execute.
   """

   subprocess.run(f"python3 -m geom {command}".split()) 

