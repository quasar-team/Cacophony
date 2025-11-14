#!/usr/bin/env python3
# encoding: utf-8
'''
ConfigInspector.py

@author:     Nikolaos Kanellos <nikolaos.kanellos@cern.ch>
'''

from lxml import etree
import logging
import os
import re

DEBUG = False

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

    def _preprocess_config_with_entities(self, configPath):
        """
        Preprocess configuration file to manually expand external entities.
        This solves the namespace mismatch issue when entity files don't have
        proper namespace declarations.

        Returns a file-like object with the preprocessed content.
        """
        config_dir = os.path.dirname(os.path.abspath(configPath))

        with open(configPath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find DOCTYPE declaration with entity definitions
        # Pattern: <!ENTITY name SYSTEM "path">
        entity_pattern = r'<!ENTITY\s+(\w+)\s+SYSTEM\s+"([^"]+)">'
        entities = {}

        for match in re.finditer(entity_pattern, content):
            entity_name = match.group(1)
            entity_path = match.group(2)

            # Resolve relative paths
            full_entity_path = os.path.join(config_dir, entity_path)

            if os.path.exists(full_entity_path):
                with open(full_entity_path, 'r', encoding='utf-8') as ef:
                    entity_content = ef.read().strip()
                    entities[entity_name] = entity_content
                    if DEBUG:
                        logging.debug(f'Loaded entity {entity_name} from {entity_path}')
            else:
                logging.warning(f'Entity file not found: {full_entity_path}')
                entities[entity_name] = ''  # Empty content for missing files

        # Replace entity references with actual content
        for entity_name, entity_content in entities.items():
            # Pattern: &ENTITY_NAME;
            entity_ref = f'&{entity_name};'
            content = content.replace(entity_ref, entity_content)

        # Remove DOCTYPE declaration (no longer needed after expansion)
        content = re.sub(r'<!DOCTYPE[^>]*\[.*?\]>', '', content, flags=re.DOTALL)

        # Remove XML declaration for StringIO parsing (lxml requirement)
        content = re.sub(r'<\?xml[^>]*\?>\s*', '', content)

        # Create a temporary file-like object with bytes
        from io import BytesIO
        return BytesIO(content.encode('utf-8'))

    def _extract_calculated_variables(self):
        """
        Extract all unique calculated variables from the configuration file.
        Returns a dict with calculated variable names as keys and type info as values.
        Format: {'varName': {'isBoolean': False, 'parentClasses': ['ClassName1', 'ClassName2']}}
        """
        calc_vars = {}
        calc_vars_by_class = {}  # Track variables per class for your approach

        # Find all CalculatedVariable elements (using namespace)
        calc_var_elements = self.tree.xpath('//c:CalculatedVariable', namespaces=QUASAR_CONFIG_NAMESPACES)

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

            if name:
                # Global tracking (all calculated variables)
                if name not in calc_vars:
                    calc_vars[name] = {
                        'isBoolean': is_boolean,
                        'parentClasses': set()
                    }
                else:
                    # If same variable appears with different types, prefer boolean detection
                    if is_boolean:
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
                    # If same variable in same class has different types, prefer boolean
                    if is_boolean:
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
        """
        profiles = {}
        profile_lookup = {}  # Map signature_full to profile_id for fast lookup
        next_profile_number = 1

        # Find all instances of this class that have CalculatedVariables
        xpath = f'//c:{class_name}[c:CalculatedVariable]'
        instances = self.tree.xpath(xpath, namespaces=QUASAR_CONFIG_NAMESPACES)

        for instance in instances:
            instance_name = instance.get('name', 'unknown')

            # Get all CV names for this specific instance
            cv_elements = instance.xpath('./c:CalculatedVariable', namespaces=QUASAR_CONFIG_NAMESPACES)
            cv_names = sorted([cv.get('name') for cv in cv_elements if cv.get('name')])

            if not cv_names:
                continue

            # Create full signature (tuple of sorted names for uniqueness)
            signature_full = tuple(cv_names)

            # Check if we've seen this signature before
            if signature_full in profile_lookup:
                profile_id = profile_lookup[signature_full]
                profiles[profile_id]['instance_count'] += 1
                profiles[profile_id]['instance_names'].append(instance_name)
            else:
                # Assign next profile number as string ID
                profile_id = str(next_profile_number)
                next_profile_number += 1

                # Build cv_info from the elements
                cv_info = {}
                for cv_elem in cv_elements:
                    name = cv_elem.get('name')
                    if name:
                        is_boolean = cv_elem.get('isBoolean', 'false').lower() == 'true'
                        cv_info[name] = {'isBoolean': is_boolean}

                profiles[profile_id] = {
                    'signature_full': signature_full,
                    'cv_names': cv_names,
                    'cv_info': cv_info,
                    'instance_names': [instance_name],
                    'instance_count': 1
                }

                profile_lookup[signature_full] = profile_id

        if DEBUG:
            logging.debug(f'CV profiles for class {class_name}: {profiles}')

        return profiles

    def get_instance_cv_profile(self, class_name, instance_name):
        """
        Get the CV profile ID for a specific instance of a class.

        Returns:
        - profile_id (str) if the instance has calculated variables
        - None if the instance has no calculated variables or doesn't exist
        """
        # Find the specific instance
        xpath = f'//c:{class_name}[@name="{instance_name}"]'
        instances = self.tree.xpath(xpath, namespaces=QUASAR_CONFIG_NAMESPACES)

        if not instances:
            return None

        instance = instances[0]

        # Get all CV names for this instance
        cv_elements = instance.xpath('./c:CalculatedVariable', namespaces=QUASAR_CONFIG_NAMESPACES)
        cv_names = sorted([cv.get('name') for cv in cv_elements if cv.get('name')])

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
