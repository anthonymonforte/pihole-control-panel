"""
services/nebula.py

This module provides the service logic for triggering Nebula synchronization commands.
"""

import subprocess

def trigger_nebula_sync(command):
    """
    Run the Nebula synchronization command as a subprocess.

    Args:
        command (list): The command to run as a list of arguments.

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        subprocess.run(command, check=True)
        return True, "NebulaSync triggered."
    except subprocess.CalledProcessError as e:
        return False, f"NebulaSync failed: {e}"
