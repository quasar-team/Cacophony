#!/usr/bin/env python3
# encoding: utf-8
'''
ConfigInspector.py

@author:     Nikolaos Kanellos <nikolaos.kanellos@cern.ch>
'''

from lxml import etree
import logging
import os

# Configure logging with default WARNING level
# To enable debug messages, set level=logging.DEBUG before importing this module
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

DEBUG = False
DEBUG_XPATH = False

# Quasar Configuration namespace
QUASAR_CONFIG_NAMESPACES = {'c': 'http://cern.ch/quasar/Configuration'}

class ConfigInspector():
    """This class inspects configuration XML files to extract calculated variable information"""

    def __init__(self, configPath):
        """Initialize ConfigInspector with a configuration XML file path"""
        # Preprocess the config file to resolve entities manually
        # This is needed because lxml has issues with entity expansion when
        # entity files don't have proper namespace declarations
        processed_config = self._preprocess_config_with_entities(configPath)

        # Parse the preprocessed configuration
        parser = etree.XMLParser()
        self.tree = etree.parse(processed_config, parser)
        self.calculated_variables = self._extract_calculated_variables()

    def xpath(self, expr, *args):
        """Just a wrapper on top of etree.xpath that does quasar config namespaces mapping"""
        xpath_expr = expr.format(*args)
        result = self.tree.xpath(xpath_expr, namespaces=QUASAR_CONFIG_NAMESPACES)
        if DEBUG_XPATH:
            logging.debug(f"xpath({xpath_expr}) gives {result}")
        return result

    def _validate_class_exists(self, class_name):
        """
        Validate that a class exists in the configuration file.
        Raises an exception if the class is not found.

        Returns: True if class exists
        Raises: Exception if class not found
        """
        xpath = f'//c:{class_name}'
        instances = self.xpath(xpath)

        if not instances:
            raise Exception(
                f"ERROR: Class '{class_name}' NOT FOUND in configuration file. "
                f"No instances of this class exist in the configuration."
            )
        return True

    def _validate_instance_exists(self, class_name, instance_name):
        """
        Validate that a specific instance exists in the configuration file.

        Returns: The instance element if found
        Raises: Exception if class or instance not found
        """
        # First validate class exists
        self._validate_class_exists(class_name)

        # Then check for specific instance
        xpath = f'//c:{class_name}[@name="{instance_name}"]'
        instances = self.xpath(xpath)

        if not instances:
            raise Exception(
                f"ERROR: Instance '{instance_name}' of class '{class_name}' NOT FOUND in configuration file."
            )
        return instances[0]

    def _validate_cv_name(self, name, parent_class, instance_name=None):
        """
        Validate calculated variable name is non-empty and non-whitespace.

        Args:
            name: The calculated variable name to validate
            parent_class: The class containing this calculated variable
            instance_name: Optional instance name for more specific error messages

        Returns: True if valid
        Raises: Exception if name is None, empty, or only whitespace
        """
        location = f"class '{parent_class}'"
        if instance_name:
            location = f"instance '{instance_name}' of class '{parent_class}'"

        if not name:
            raise Exception(
                f"ERROR: CalculatedVariable in {location} has missing or empty 'name' attribute. "
                f"All calculated variables must have a non-empty name."
            )

        if not name.strip():
            raise Exception(
                f"ERROR: CalculatedVariable in {location} has whitespace-only 'name' attribute: '{name}'. "
                f"Calculated variable names must contain non-whitespace characters."
            )

        return True

    def _preprocess_config_with_entities(self, configPath):
        """
        Preprocess configuration file to expand external entities using xmllint.
        This uses the same entity expansion method as the CTL runtime (xmllint --noent)
        to ensure consistent handling of entities between build time and runtime.

        Returns a file-like object with the preprocessed content.

        Raises:
            FileNotFoundError: if xmllint is not available
            Exception: if xmllint fails to process the file
        """
        import subprocess
        import tempfile
        import shutil

        # Check if xmllint is available
        if shutil.which('xmllint') is None:
            raise FileNotFoundError(
                "ERROR: 'xmllint' command not found. "
                "Please install libxml2-utils (Debian/Ubuntu) or libxml2 (RHEL/CentOS). "
                "xmllint is required for entity expansion in configuration files."
            )

        # Create temporary file for expanded content
        temp_fd, temp_path = tempfile.mkstemp(suffix='.xml', prefix='config_expanded_')

        try:
            # Close the file descriptor as we'll write via subprocess
            os.close(temp_fd)

            # Use xmllint --noent to expand entities (same as CTL runtime)
            # This ensures consistent entity resolution between build time and runtime
            result = subprocess.run(
                ['xmllint', '--noent', configPath],
                capture_output=True,
                text=True,
                check=False  # We'll check return code manually
            )

            if result.returncode != 0:
                raise Exception(
                    f"ERROR: xmllint failed to process configuration file '{configPath}'. "
                    f"Return code: {result.returncode}\n"
                    f"Error output: {result.stderr}"
                )

            # Write expanded content to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(result.stdout)

            if DEBUG:
                logging.debug(f'Entity expansion completed using xmllint for: {configPath}')
                logging.debug(f'Expanded content written to temporary file: {temp_path}')

            # Return file-like object (BytesIO) for lxml to parse
            from io import BytesIO
            return BytesIO(result.stdout.encode('utf-8'))

        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

        finally:
            # Clean up temp file after parsing (best effort)
            # Note: The BytesIO object contains the content, so we can delete the file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass  # Ignore cleanup errors

    def _extract_calculated_variables(self):
        """
        Extract all unique calculated variables from the configuration file.
        Returns a dict with calculated variable names as keys and type info as values.
        Format: {'varName': {'isBoolean': False, 'parentClasses': ['ClassName1', 'ClassName2']}}
        """
        calc_vars = {}
        calc_vars_by_class = {}  # Track variables per class for your approach

        # Find all CalculatedVariable elements (using namespace)
        calc_var_elements = self.xpath('//c:CalculatedVariable')

        for cv_elem in calc_var_elements:
            name = cv_elem.get('name')
            is_boolean_str = cv_elem.get('isBoolean', 'false')
            is_boolean = is_boolean_str.lower() == 'true'

            # Find parent class tag name (strip namespace if present)
            parent = cv_elem.getparent()
            if parent is not None:
                # Remove namespace prefix from tag name
                parent_class = parent.tag.split('}')[-1] if '}' in parent.tag else parent.tag
            else:
                parent_class = 'Unknown'

            # Validate CV name is non-empty and non-whitespace
            if name and name.strip():
                self._validate_cv_name(name, parent_class)
                # Global tracking (all calculated variables)
                if name not in calc_vars:
                    calc_vars[name] = {
                        'isBoolean': is_boolean,
                        'parentClasses': set()
                    }
                else:
                    # Check for type conflicts
                    existing_type = calc_vars[name]['isBoolean']
                    if existing_type != is_boolean:
                        logging.warning(
                            f"Type conflict for calculated variable '{name}' in class '{parent_class}': "
                            f"previously isBoolean={existing_type}, now found isBoolean={is_boolean}. "
                            f"Using isBoolean=True (boolean type takes precedence)."
                        )
                        calc_vars[name]['isBoolean'] = True
                    elif is_boolean:
                        calc_vars[name]['isBoolean'] = True

                calc_vars[name]['parentClasses'].add(parent_class)

                # Per-class tracking
                if parent_class not in calc_vars_by_class:
                    calc_vars_by_class[parent_class] = {}

                if name not in calc_vars_by_class[parent_class]:
                    calc_vars_by_class[parent_class][name] = {
                        'isBoolean': is_boolean,
                        'occurrences': 0
                    }
                else:
                    # Check for type conflicts within the same class
                    existing_type = calc_vars_by_class[parent_class][name]['isBoolean']
                    if existing_type != is_boolean:
                        logging.warning(
                            f"Type conflict for calculated variable '{name}' within class '{parent_class}': "
                            f"previously isBoolean={existing_type}, now found isBoolean={is_boolean}. "
                            f"Using isBoolean=True (boolean type takes precedence)."
                        )
                        calc_vars_by_class[parent_class][name]['isBoolean'] = True
                    elif is_boolean:
                        calc_vars_by_class[parent_class][name]['isBoolean'] = True

                calc_vars_by_class[parent_class][name]['occurrences'] += 1

        # Convert sets to lists for easier Jinja2 handling
        for var_name in calc_vars:
            calc_vars[var_name]['parentClasses'] = list(calc_vars[var_name]['parentClasses'])

        # Store by-class information
        self.calc_vars_by_class = calc_vars_by_class

        if DEBUG:
            logging.debug(f'Calculated variables found: {calc_vars}')
            logging.debug(f'Calculated variables by class: {calc_vars_by_class}')

        return calc_vars

    def get_calculated_variable_names(self):
        """Returns a list of all unique calculated variable names"""
        return list(self.calculated_variables.keys())

    def get_calculated_variables_info(self):
        """Returns the complete dictionary of calculated variable information"""
        return self.calculated_variables

    def has_calculated_variables(self):
        """Returns True if any calculated variables are present in the config"""
        return len(self.calculated_variables) > 0

    def is_calculated_variable_boolean(self, var_name):
        """Returns True if the specified calculated variable is boolean type"""
        if var_name in self.calculated_variables:
            return self.calculated_variables[var_name]['isBoolean']
        return False

    def get_calculated_variable_parent_classes(self, var_name):
        """Returns list of parent classes that contain this calculated variable"""
        if var_name in self.calculated_variables:
            return self.calculated_variables[var_name]['parentClasses']
        return []

    def get_calculated_variables_by_parent_class(self):
        """
        Returns a dict mapping parent class names to lists of calculated variable names.
        Format: {'SCA': ['constant_1V5', 'constant_2V5'], 'AnalogInput': ['computedValue']}
        """
        result = {}
        for class_name, calc_vars in self.calc_vars_by_class.items():
            result[class_name] = list(calc_vars.keys())
        return result

    def get_calculated_variables_for_class(self, class_name):
        """
        Returns detailed info about calculated variables for a specific class.
        Format: {'varName': {'isBoolean': False, 'occurrences': 3}, ...}
        """
        return self.calc_vars_by_class.get(class_name, {})

    def get_cv_profiles_for_class(self, class_name):
        """
        Detect unique calculated variable profiles (signatures) for a class.
        A profile is a unique combination of calculated variable names that appear together
        on instances of the class.

        Returns:
        {
            '1': {
                'signature_full': ('cv1', 'cv2', 'cv3'),  # Full sorted tuple of CV names
                'cv_names': ['cv1', 'cv2', 'cv3'],  # List of CV names
                'cv_info': {
                    'cv1': {'isBoolean': False},
                    'cv2': {'isBoolean': False},
                    ...
                },
                'instance_names': ['instance1', 'instance2', ...],  # Names of instances with this profile
                'instance_count': 5
            },
            ...
        }
        Note: The profile number is the dict key (e.g., '1', '2', '3')

        Returns empty dict {} if:
        - Class doesn't exist in configuration (normal - not all design classes are instantiated)
        - Class exists but has no calculated variables (normal - CVs are optional)
        """
        profiles = {}
        profile_lookup = {}  # Map signature_full to profile_id for fast lookup
        next_profile_number = 1

        # Find all instances of this class that have CalculatedVariables
        # NOTE: Don't validate class exists - templates call this for ALL design classes,
        # but not all design classes are instantiated in configuration
        xpath = f'//c:{class_name}[c:CalculatedVariable]'
        instances = self.xpath(xpath)

        # Return empty dict if class not in config OR class has no CVs (both are normal)
        if not instances:
            if DEBUG:
                logging.debug(f'Class {class_name} has no CV profiles (not in config or no CVs)')
            return {}

        for instance in instances:
            instance_name = instance.get('name', 'unknown')

            # Get all CV names for this specific instance
            cv_elements = instance.xpath('./c:CalculatedVariable', namespaces=QUASAR_CONFIG_NAMESPACES)

            # Validate and collect CV names with type information (filter out empty/whitespace-only names)
            signature_components = []
            cv_info_temp = {}
            for cv_elem in cv_elements:
                name = cv_elem.get('name')
                if name and name.strip():
                    self._validate_cv_name(name, class_name, instance_name)
                    is_boolean = cv_elem.get('isBoolean', 'false').lower() == 'true'
                    cv_info_temp[name] = {'isBoolean': is_boolean}
                    # Include type in signature: (name, isBoolean)
                    signature_components.append((name, is_boolean))

            # Sort by name for consistency
            signature_components.sort(key=lambda x: x[0])

            if not signature_components:
                continue

            # Create full signature with type information: (('current', False), ('voltage', False))
            # This ensures instances with same CV names but different types get separate profiles
            signature_full = tuple(signature_components)

            # Extract just the names for cv_names list
            cv_names = sorted([comp[0] for comp in signature_components])

            # Check if we've seen this signature before
            if signature_full in profile_lookup:
                profile_id = profile_lookup[signature_full]
                profiles[profile_id]['instance_count'] += 1
                profiles[profile_id]['instance_names'].append(instance_name)
            else:
                # Assign next profile number as string ID
                profile_id = str(next_profile_number)
                next_profile_number += 1

                profiles[profile_id] = {
                    'signature_full': signature_full,
                    'cv_names': cv_names,
                    'cv_info': cv_info_temp,
                    'instance_names': [instance_name],
                    'instance_count': 1
                }

                profile_lookup[signature_full] = profile_id

        # Sort signatures alphabetically to ensure profile numbering independent of XML element order
        sorted_signatures = sorted(profile_lookup.keys())

        # Reassign profile IDs based on sorted signature order
        final_profiles = {}
        for idx, signature in enumerate(sorted_signatures, start=1):
            old_profile_id = profile_lookup[signature]
            new_profile_id = str(idx)

            # Copy profile data with new deterministic ID
            final_profiles[new_profile_id] = profiles[old_profile_id]

        if DEBUG:
            logging.debug(f'CV profiles for class {class_name}: {final_profiles}')

        return final_profiles

    def get_instance_cv_profile(self, class_name, instance_name):
        """
        Get the CV profile ID for a specific instance of a class.

        Returns:
        - profile_id (str) if the instance has calculated variables
        - None if the instance has no calculated variables

        Raises:
        - Exception if class or instance not found in configuration
        """
        # Validate instance exists (raises exception if class or instance not found)
        instance = self._validate_instance_exists(class_name, instance_name)

        # Get all CV names for this instance
        cv_elements = instance.xpath('./c:CalculatedVariable', namespaces=QUASAR_CONFIG_NAMESPACES)
        cv_names = sorted([cv.get('name') for cv in cv_elements if cv.get('name')])

        # Valid instance with no CVs - return None (normal operation)
        if not cv_names:
            return None

        # Create signature and find matching profile
        signature_full = tuple(cv_names)

        # Get all profiles for this class
        profiles = self.get_cv_profiles_for_class(class_name)

        # Find the profile with matching signature
        for profile_id, profile_data in profiles.items():
            if profile_data['signature_full'] == signature_full:
                return profile_id

        return None

    def get_all_cv_profiles(self):
        """
        Get CV profiles for all classes that have calculated variables.

        Returns:
        {
            'ClassName1': {profiles_dict},
            'ClassName2': {profiles_dict},
            ...
        }
        """
        all_profiles = {}

        # Get all unique parent classes that have calculated variables
        for class_name in self.calc_vars_by_class.keys():
            profiles = self.get_cv_profiles_for_class(class_name)
            if profiles:
                all_profiles[class_name] = profiles

        return all_profiles

if __name__ == "__main__":
    """Test fixture for manual testing and validation"""
    import sys
    from colorama import Fore, Style

    # Default config path (can be overridden via command line)
    config_path = 'bin/config.xml'
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    print(f"{Fore.CYAN}ConfigInspector Test Fixture{Style.RESET_ALL}")
    print(f"Config file: {config_path}\n")

    try:
        # Create inspector instance
        inspector = ConfigInspector(config_path)

        # Test 1: Get calculated variable names
        print(f"{Fore.GREEN}1. Calculated Variables:{Style.RESET_ALL}")
        cv_names = inspector.get_calculated_variable_names()
        print(f"   Found {len(cv_names)} unique calculated variable(s): {', '.join(cv_names)}\n")

        # Test 2: Get calculated variables by parent class
        print(f"{Fore.GREEN}2. Calculated Variables by Parent Class:{Style.RESET_ALL}")
        cv_by_class = inspector.get_calculated_variables_by_parent_class()
        for class_name, vars_list in cv_by_class.items():
            print(f"   {class_name}: {len(vars_list)} variable(s) - {', '.join(vars_list)}")
        print()

        # Test 3: Get CV profiles for all classes
        print(f"{Fore.GREEN}3. CV Profiles:{Style.RESET_ALL}")
        all_profiles = inspector.get_all_cv_profiles()
        for class_name, profiles in all_profiles.items():
            print(f"   {class_name}: {len(profiles)} profile(s)")
            for profile_id, profile_data in profiles.items():
                print(f"      Profile {profile_id}:")
                print(f"         Signature: {profile_data['signature_full']}")
                print(f"         CV Names: {', '.join(profile_data['cv_names'])}")
                print(f"         Instance count: {profile_data['instance_count']}")
                # Show first 3 instances
                instances_str = ', '.join(profile_data['instance_names'][:3])
                if profile_data['instance_count'] > 3:
                    instances_str += f" ... (+{profile_data['instance_count'] - 3} more)"
                print(f"         Instances: {instances_str}")

        print(f"\n{Fore.GREEN}All tests completed successfully{Style.RESET_ALL}")

    except FileNotFoundError as e:
        print(f"{Fore.RED}ERROR: {e}{Style.RESET_ALL}")
        print(f"\nUsage: python3 ConfigInspector.py [path/to/config.xml]")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}ERROR: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
