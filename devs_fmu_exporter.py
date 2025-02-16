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

from jinja2 import Environment, FileSystemLoader, Template
from lxml import etree
from acc_models import *
import getpass
from datetime import datetime, timezone
import uuid
import shutil
import os
from xml.etree import ElementTree as ET
import inspect
from pypdevs.DEVS import Port
import json
from io import BytesIO


def beautify_xml(xml_string):
    """Beautify XML using lxml."""
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(BytesIO(xml_string.encode('utf-8')), parser)
    return etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True).decode('utf-8')



def increment_version(version):
    """Increment the version string."""
    try:
        major, minor, patch = map(int, version.split('.'))
        patch += 1
        return f"{major}.{minor}.{patch}"
    except ValueError:
        return "0.0.1"


def parse_and_update_version(destination_dir, model_description_path):
    """Parse the version from modelDescription.xml and increment it."""
    if os.path.exists(destination_dir):
        print(f"Existing folder found: {destination_dir}. Checking for modelDescription.xml...")
        if os.path.isfile(model_description_path):
            print(f"Found {model_description_path}. Reading version...")
            try:
                tree = ET.parse(model_description_path)
                root = tree.getroot()
                current_version = root.get("version", "0.0.1")
                print(f"Current version: {current_version}")
                new_version = increment_version(current_version)
                print(f"New version: {new_version}")
                return new_version
            except ET.ParseError:
                print("Failed to parse XML. Defaulting to version 0.0.1")
                return "0.0.1"
        else:
            print(f"{model_description_path} not found. Defaulting to version 0.0.1")
            return "0.0.1"
    else:
        print(f"Folder {destination_dir} does not exist. Defaulting to version 0.0.1")
        return "0.0.1"


def initialize_template_environment(template_dir):
    """Initialize Jinja2 environment."""
    return Environment(loader=FileSystemLoader(template_dir))


def setup_model_directory(source_dir, destination_dir):
    """Create the model directory by copying the source template."""
    if os.path.exists(destination_dir):
        shutil.rmtree(destination_dir)  # Remove existing directory if it exists
    shutil.copytree(source_dir, destination_dir)  # Copy the source directory to the destination


def parse_model_description(path):
    """Parse and return version from model description XML."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        return root.get("version", "0.0.1")
    except (ET.ParseError, FileNotFoundError):
        return "0.0.1"


def categorize_ports(obj):
    """Categorize ports into in_ports and out_ports based on is_input."""
    in_ports = {}
    out_ports = {}

    for attr_name in dir(obj):
        # Skip special and private attributes
        if attr_name.startswith("__"):
            continue

        try:
            attr_value = getattr(obj, attr_name)
            # Check if the attribute is a Port
            if isinstance(attr_value, Port):
                if attr_value.is_input:
                    in_ports[attr_name] = attr_value
                else:
                    out_ports[attr_name] = attr_value
        except Exception as e:
            # Handle inaccessible attributes
            print(f"Could not access attribute {attr_name}: {e}")

    return in_ports, out_ports


def prepare_model_variables(model, template_vars):
    """Prepare model variables for the template using categorized ports."""
    in_ports, out_ports = categorize_ports(model)  # Get categorized ports
    i = 2
    for _, port in in_ports.items():
        template_vars["model_variables"].extend([
            {"type": "Clock", "name": port.name, "value_reference": str(1000 + i), "causality": "input",
             "interval_variability": "triggered"},
            {"type": "String", "name": f"{port.name}_data", "value_reference": str(i), "causality": "input",
             "variability": "discrete", "clocks": str(1000 + i), "dimensions": [{"start": "1"}],
             "starts": [{"value": ""}]}])
        i += 1
    for _, port in out_ports.items():
        template_vars["model_variables"].extend([
            {"type": "Clock", "name": port.name, "value_reference": str(1000 + i), "causality": "output",
             "interval_variability": "triggered", "clocks": "1001"},
            {"type": "String", "name": f"{port.name}_data", "value_reference": str(i), "causality": "output",
             "variability": "discrete", "clocks": str(1000 + i)}])
        template_vars["model_structure"]["outputs"].append({"value_reference": str(1000 + i), "dependencies": "1001"})
        i += 1


def copy_model_source_file(model, destination_dir):
    """Copy the source file of the model object to the resources directory."""
    # Get the source file of the model
    try:
        model_source_file = inspect.getfile(type(model))
        resources_dir = os.path.join(destination_dir, "resources")

        # Ensure resources directory exists
        os.makedirs(resources_dir, exist_ok=True)

        # Copy the source file
        shutil.copy(model_source_file, resources_dir)
        print(f"Copied model source file to: {resources_dir}")
    except TypeError:
        print("The source file for the model could not be determined.")
    except FileNotFoundError:
        print(f"The source file {model_source_file} does not exist.")
    except Exception as e:
        print(f"An error occurred while copying the model source file: {e}")


def create_and_capture(cls, *args, **kwargs):
    """
    Instantiate `cls` using the given positional (args) and keyword (kwargs) arguments.
    Return a tuple of:
      - the new instance
      - a dictionary describing the instantiation
    """
    instance = cls(*args, **kwargs)

    # You can store whatever metadata you like here
    captured_info = {
        "class_name": cls.__name__,
        "args": args,
        "kwargs": kwargs
    }

    return instance, captured_info


def extract_model_init_args(model):
    """Extract the arguments explicitly used to initialize the model."""
    init_signature = inspect.signature(type(model).__init__)
    init_params = init_signature.parameters

    # Extract only explicitly set arguments
    init_args = {}
    for param_name, param in init_params.items():
        if param_name == "self":
            continue
        value = getattr(model, param_name, None)
        if value is not None and value != param.default:
            init_args[param_name] = value

    return init_args


def generate_python_file(model, init_info, destination_dir, env):
    """Generate a Python file dynamically based on the model using categorized ports."""
    in_ports, out_ports = categorize_ports(model)  # Get categorized ports
    resources_dir = os.path.join(destination_dir, "resources")
    python_file_path = os.path.join(resources_dir, "model.py")

    # Get the model module and name
    model_source_file = inspect.getfile(type(model))
    model_module = os.path.splitext(os.path.basename(model_source_file))[0]
    model_name = type(model).__name__

    # Handle initialization arguments
    if init_info and "kwargs" in init_info:
        # Use provided initialization arguments
        init_kwargs = init_info["kwargs"].copy()
    else:
        # Try to infer initialization arguments using extract_model_init_args
        init_kwargs = extract_model_init_args(model)

    # Ensure `name` is always included
    init_kwargs["name"] = "self.instance_name"  # Replace `name` with `self.instance_name`

    # Format initialization arguments
    init_args_string = ", ".join(
        f"{key}={value!r}" if key != "name" else f"{key}={value}"  # Avoid quoting `self.instance_name`
        for key, value in init_kwargs.items()
    )

    # Generate attributes and mappings for ports
    attributes = []
    # Default mapping
    reference_to_attribute = {
        999: "time",
        1001: "ta",
        1: "state",
    }
    in_port_to_attributes = {}
    out_port_to_attributes = {}

    i = 2
    for attribute_name, port in in_ports.items():
        attributes.append(f"self.{port.name} = False")
        attributes.append(f"self.{port.name}_data = ''")
        reference_to_attribute[1000 + i] = port.name
        reference_to_attribute[i] = f"{port.name}_data"
        in_port_to_attributes[f"self.DEVS_wrapper.model.{attribute_name}"] = (
            f"{port.name}", f"{port.name}_data")
        i += 1

    for attribute_name, port in out_ports.items():
        attributes.append(f"self.{port.name} = False")
        attributes.append(f"self.{port.name}_data = ''")
        reference_to_attribute[1000 + i] = port.name
        reference_to_attribute[i] = f"{port.name}_data"
        out_port_to_attributes[f"self.DEVS_wrapper.model.{attribute_name}"] = (
            f"{port.name}", f"{port.name}_data")
        i += 1

    # Render the template using Jinja2
    template_vars = {
        "model_module": model_module,
        "model_name": model_name,
        "init_args": init_args_string,
        "attributes": "\n        ".join(attributes),
        "reference_to_attribute": reference_to_attribute,
        "in_port_to_attributes": in_port_to_attributes,
        "out_port_to_attributes": out_port_to_attributes,
    }
    template = env.get_template("model_template.py.j2")
    rendered_content = template.render(template_vars)

    # Ensure the resources directory exists
    os.makedirs(resources_dir, exist_ok=True)

    # Write the rendered content to a Python file
    with open(python_file_path, "w") as python_file:
        python_file.write(rendered_content)

    print(f"Python file generated at: {python_file_path}")


def generate_fmu(model_name, template_vars, env, destination_dir, output_fmu_path):
    """Generate FMU with updated version."""
    model_description_path = os.path.join(destination_dir, "modelDescription.xml")

    # Render the template and write XML
    template = env.get_template('fmi_template.xml')
    raw_xml = template.render(template_vars)
    beautiful_xml = beautify_xml(raw_xml)

    with open(model_description_path, "w", encoding="utf-8") as file:
        file.write(beautiful_xml)

    # Create and rename archive
    shutil.make_archive(destination_dir, 'zip', destination_dir)

    if os.path.exists(output_fmu_path):
        os.remove(output_fmu_path)  # Remove existing FMU if needed

    os.rename(f"{destination_dir}.zip", output_fmu_path)
    print(f"FMU generated at: {output_fmu_path}")


def export_fmu(model, init_info=None, output_dir='./generated'):
    source_dir = './templates/fmu_common'
    destination_dir = f"{output_dir}/{model.name}"
    output_fmu_path = f"{output_dir}/{model.name}.fmu"
    model_description_path = os.path.join(destination_dir, "modelDescription.xml")

    # Initialize template variables and environment
    env = initialize_template_environment('templates')

    # Parse version before deleting the directory
    version = parse_and_update_version(destination_dir, model_description_path)

    # Prepare template variables with the updated version
    template_vars = {
        "model_name": model.name,
        "instantiation_token": str(uuid.uuid4()),
        "author": getpass.getuser(),
        "version": version,
        "license": "MIT",
        "generation_date_time": datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z'),
        "variable_naming_convention": "flat",
        "generation_tool": "PythonPDEVS_FMI",
        "co_simulation": {
            "model_identifier": "unifmu",
            "needs_execution_tool": "true",
            "can_be_instantiated_only_once": "false",
            "can_get_and_set_fmu_state": "false",
            "can_serialize_fmu_state": "false",
            "can_handle_variable_communication_step_size": "true",
            "has_event_mode": "true"
        },
        "log_categories": [
            {"name": "logStatusWarning"},
            {"name": "logStatusDiscard"},
            {"name": "logStatusError"},
            {"name": "logStatusFatal"},
            {"name": "logStatusPending"},
            {"name": "logAll"}
        ],
        "model_variables": [
            {"type": "Float64", "name": "time", "value_reference": "999", "causality": "independent",
             "variability": "continuous", "description": "Simulation time"},
            {"type": "Clock", "name": "ta", "value_reference": "1001", "causality": "input",
             "interval_variability": "countdown"},
            {"type": "String", "name": "state", "value_reference": "1", "causality": "output",
             "variability": "discrete"}
        ],
        "model_structure": {"outputs": []}
    }

    # Remove existing directory and generate FMU
    setup_model_directory(source_dir, destination_dir)
    prepare_model_variables(model, template_vars)
    copy_model_source_file(model, destination_dir)
    generate_python_file(model, init_info, destination_dir, env)
    generate_fmu(model.name, template_vars, env, destination_dir, output_fmu_path)


def export_coupled_model(coupled_model, output_dir=None):
    """
    Exports FMUs for each sub-model in 'coupled_model' (using export_fmu)
    and writes a coupling.json file describing components and their connections.

    :param coupled_model: The coupled model object (e.g., AdaptiveCruiseControlSystem).
                         Must have 'name' and 'component_set' attributes.
    :param output_dir: Base output directory for this coupled model.
                       If None, defaults to './<coupled_model.name>'.
    """

    # Use a default output directory if none is provided
    if output_dir is None:
        output_dir = f"./{coupled_model.name}"

    # Define the FMUs subdirectory
    fmus_dir = os.path.join(output_dir, "FMUs")
    os.makedirs(fmus_dir, exist_ok=True)

    # Export an FMU for each component model in the coupled_model
    for model in coupled_model.component_set:
        export_fmu(model, output_dir=fmus_dir)

    # Build the connections list
    connections = []
    for model in coupled_model.component_set:
        # We traverse each model's OPorts (output ports)
        for out_port in model.OPorts:
            # 'outline' is the list of input ports this output port is connected to
            for in_port in out_port.outline:
                connections.append({
                    "source_model": model.name,
                    "source_port": out_port.name,
                    "dest_model": in_port.host_DEVS.name,
                    "dest_port": in_port.name
                })

    # Build the JSON data structure
    data = {
        "root_model": coupled_model.name,
        "components": [
            {
                "name": model.name,
                "fmu": os.path.join('FMUs', f"{model.name}.fmu"),
                "source": os.path.join('FMUs', model.name),
            }
            for model in coupled_model.component_set
        ],
        "connections": connections,
    }

    # Write to coupling.json
    coupling_json_path = os.path.join(output_dir, "coupling.json")
    try:
        with open(coupling_json_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"coupling.json created successfully at {coupling_json_path}")
    except OSError as e:
        print(f"Failed to write coupling.json: {e}")


# Main Logic
if __name__ == "__main__":
    # model, init_info = create_and_capture(Vehicle, name="ego_vehicle", x0=10.0)
    model, init_info = create_and_capture(Sine, name="sine_generator", interval=0.1, amplitude=0.6, omega=0.2)
    export_fmu(model)
