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
import math
import ast
import xml.etree.ElementTree as ET

# Note: this script was generated using ChatGPT (o1)
def is_float(s: str) -> bool:
    """Return True if string s can be converted to float, else False."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def parse_floats_in_string(s: str):
    """
    Attempt to parse a string that may contain numeric values.
    Examples:
      - "0.1"
      - "[12.0, 20.0, 0.0]"
      - "1.0"
    Returns:
      - A float if possible,
      - A list of floats if the string is bracketed,
      - or the original string if it can't parse numeric content.
    """
    s = s.strip()

    # If it's bracketed like "[12.0, 20.0, 0.0]"
    if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
        # Safely evaluate to Python object
        try:
            val = ast.literal_eval(s)
            if isinstance(val, (list, tuple)):
                # Convert each element to float if possible
                float_list = []
                for item in val:
                    if isinstance(item, (int, float)):
                        float_list.append(float(item))
                    else:
                        # If it's not numeric, store as is
                        float_list.append(item)
                return float_list
            else:
                return val
        except (SyntaxError, ValueError):
            # If it fails, just return string
            return s

    # If it's a single numeric value
    if is_float(s):
        return float(s)

    # Otherwise, return as string
    return s


def floats_close(val1, val2, abs_tol=1e-6):
    """Return True if val1 and val2 are close within abs_tol."""
    return math.isclose(val1, val2, abs_tol=abs_tol)


def lists_close(list1, list2, abs_tol=1e-6):
    """
    Return True if two lists of floats (or float-convertible items)
    have the same length and each corresponding element is close.
    """
    if len(list1) != len(list2):
        return False
    for a, b in zip(list1, list2):
        if not floats_close(a, b, abs_tol=abs_tol):
            return False
    return True


def compare_values(val1, val2, abs_tol=1e-6):
    """
    Compare val1 and val2, which could be:
      - floats
      - lists of floats
      - strings
    Return True if they match (within tolerance if numeric).
    """
    # If both are floats, compare with tolerance
    if isinstance(val1, float) and isinstance(val2, float):
        return floats_close(val1, val2, abs_tol=abs_tol)
    # If both are lists, compare length and float closeness
    if isinstance(val1, list) and isinstance(val2, list):
        # Assume numeric (or float-convertible) lists
        return lists_close(val1, val2, abs_tol=abs_tol)
    # Otherwise, compare as strings
    return val1 == val2


def compare_xml_events(events1, events2, abs_tol=1e-6):
    """
    Compare two lists of <event> elements from run1 and run2.
    Returns True if all events match (within tolerance), otherwise False.
    Also returns a list of mismatch messages.
    """
    mismatches = []

    if len(events1) != len(events2):
        mismatches.append(f"Number of events differ: {len(events1)} vs {len(events2)}")
        return False, mismatches

    for i, (e1, e2) in enumerate(zip(events1, events2)):
        # Compare <model>
        model1 = e1.find("model").text.strip() if e1.find("model") is not None else ""
        model2 = e2.find("model").text.strip() if e2.find("model") is not None else ""
        if model1 != model2:
            mismatches.append(f"Event {i}: model mismatch ({model1} vs {model2})")
            continue

        # Compare <time> with floating-point tolerance
        time1_str = e1.find("time").text.strip() if e1.find("time") is not None else "0.0"
        time2_str = e2.find("time").text.strip() if e2.find("time") is not None else "0.0"

        time1 = float(time1_str) if is_float(time1_str) else 0.0
        time2 = float(time2_str) if is_float(time2_str) else 0.0

        if not floats_close(time1, time2, abs_tol=abs_tol):
            mismatches.append(f"Event {i}: time mismatch ({time1} vs {time2})")
            continue

        # Compare <kind>
        kind1 = e1.find("kind").text.strip() if e1.find("kind") is not None else ""
        kind2 = e2.find("kind").text.strip() if e2.find("kind") is not None else ""
        if kind1 != kind2:
            mismatches.append(f"Event {i}: kind mismatch ({kind1} vs {kind2})")
            continue

        # Compare <mode> within <state>
        state1_elem = e1.find("state")
        state2_elem = e2.find("state")

        mode1 = ""
        mode2 = ""

        if state1_elem is not None:
            mode1_elem = state1_elem.find("mode")
            if mode1_elem is not None and mode1_elem.text:
                mode1 = mode1_elem.text.strip()

        if state2_elem is not None:
            mode2_elem = state2_elem.find("mode")
            if mode2_elem is not None and mode2_elem.text:
                mode2 = mode2_elem.text.strip()

        if mode1 != mode2:
            mismatches.append(f"Event {i}: mode mismatch ({mode1} vs {mode2})")
            continue

        # Compare <port> elements (order is assumed to be consistent)
        ports1 = e1.findall("port")
        ports2 = e2.findall("port")
        if len(ports1) != len(ports2):
            mismatches.append(f"Event {i}: number of ports differ ({len(ports1)} vs {len(ports2)})")
            continue

        for p_idx, (p1, p2) in enumerate(zip(ports1, ports2)):
            name1 = p1.get("name", "").strip()
            name2 = p2.get("name", "").strip()
            if name1 != name2:
                mismatches.append(f"Event {i}, Port {p_idx}: name mismatch ({name1} vs {name2})")
                continue

            cat1 = p1.get("category", "").strip()
            cat2 = p2.get("category", "").strip()
            if cat1 != cat2:
                mismatches.append(f"Event {i}, Port {p_idx}: category mismatch ({cat1} vs {cat2})")
                continue

            msg1_elem = p1.find("message")
            msg2_elem = p2.find("message")
            msg1_str = msg1_elem.text.strip() if (msg1_elem is not None and msg1_elem.text) else ""
            msg2_str = msg2_elem.text.strip() if (msg2_elem is not None and msg2_elem.text) else ""

            # Parse messages as numeric or list-of-numerics if possible
            val1 = parse_floats_in_string(msg1_str)
            val2 = parse_floats_in_string(msg2_str)

            # Compare values with tolerance if numeric
            if not compare_values(val1, val2, abs_tol=abs_tol):
                mismatches.append(f"Event {i}, Port {p_idx}: message mismatch ({val1} vs {val2})")
                continue

    # If we have no mismatches, everything matched (within tolerance)
    return (len(mismatches) == 0), mismatches


def compare_two_logs(file1, file2, abs_tol=1e-6):
    """
    Compare the events in file1 vs file2.
    Return True if match (within tolerance), else False.
    Also return a list of mismatch details.
    """
    # Parse XML logs
    tree1 = ET.parse(file1)
    tree2 = ET.parse(file2)

    root1 = tree1.getroot()
    root2 = tree2.getroot()

    # We assume the <event> nodes are direct children of <trace>, but adapt if needed
    events1 = root1.findall("event")
    events2 = root2.findall("event")

    # Compare
    matched, mismatches = compare_xml_events(events1, events2, abs_tol=abs_tol)
    return matched, mismatches


def compare_log_dirs(run1_dir, run2_dir, abs_tol=1e-6):
    """
    Compare all .xml log files in run1_dir with those in run2_dir.
    Print comparison results.
    """
    match = True

    # Gather all .xml files in run1_dir
    run1_files = [f for f in os.listdir(run1_dir) if f.endswith(".xml")]

    # Compare
    for xml_file in run1_files:
        file1 = os.path.join(run1_dir, xml_file)
        file2 = os.path.join(run2_dir, xml_file)

        # Ensure file2 exists
        if not os.path.isfile(file2):
            print(f"WARNING: {xml_file} not found in {run2_dir}. Skipping.")
            continue

        matched, mismatches = compare_two_logs(file1, file2, abs_tol=abs_tol)

        if matched:
            print(f"[MATCH] {xml_file}")
        else:
            match = False
            print(f"[DIFF]  {xml_file}")
            for mm in mismatches:
                print(f"    - {mm}")

    return match

if __name__ == "__main__":
    # Example usage:
    # Provide two directories containing matching .xml log files.
    PythonPDEVS_logs = "../Logs"
    DEVS_FMI_logs = "./FMI_acc_system_logs"

    # You can adjust the absolute tolerance if needed
    TOLERANCE = 1e-10

    compare_log_dirs(PythonPDEVS_logs, DEVS_FMI_logs, abs_tol=TOLERANCE)
