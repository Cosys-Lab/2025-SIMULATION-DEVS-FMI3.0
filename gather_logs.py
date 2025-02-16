"""
2025-SIMULATION-DEVS-FMI3.0
Copyright (C) 2025 Cosys-lab, University of Antwerp

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import shutil


# Note: this script was generated using ChatGPT (o1)
def gather_logs(source_dir, destination_dir):
    """
    Walk through all subdirectories under `source_dir`,
    look for 'logs' folders, and copy all .xml files
    to `destination_dir`.
    """
    # Create the destination directory if it doesn't exist
    os.makedirs(destination_dir, exist_ok=True)

    for root, dirs, files in os.walk(source_dir):
        # Check if we're in a 'logs' directory
        if os.path.basename(root) == 'logs':
            for filename in files:
                if filename.lower().endswith('.xml'):
                    src_file = os.path.join(root, filename)
                    print(f"Copying {src_file} to {destination_dir}")
                    shutil.copy2(src_file, destination_dir)


if __name__ == "__main__":
    # Adjust these paths to match your setup
    source_dir = ".\\generated\\acc_system\\FMUs"
    destination_dir = ".\\logs\\FMI_acc_system_logs"

    gather_logs(source_dir, destination_dir)
