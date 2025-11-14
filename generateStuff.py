#!/usr/bin/env python3

# @author Piotr Nikiel <piotr.nikiel@gmail.com>

import sys
import os
import argparse
from colorama import Fore, Style

thisModuleName = "Cacophony"

sys.path.insert(0, 'FrameworkInternals')

from transformDesign import transformDesign
from DesignInspector import DesignInspector
from ConfigInspector import ConfigInspector
from quasarExceptions import DesignFlaw
import quasar_basic_utils
from merge_design_and_meta import merge_user_and_meta_design

# we use template_debug to print out to keep uniform debug style with what comes out as debug
# from the transform itself
from transform_filters import template_debug

ObviousMapping = {  # these are unanimously good choices
    'OpcUa_Boolean' : "DPEL_BOOL",
    'OpcUa_UInt32'  : "DPEL_UINT",
    'OpcUa_Int32'   : "DPEL_INT",
    'OpcUa_UInt64'  : "DPEL_ULONG",
    'OpcUa_Int64'   : "DPEL_LONG",
    'OpcUa_Float'   : "DPEL_FLOAT",
    'OpcUa_Double'  : "DPEL_FLOAT",
    'UaString'      : "DPEL_STRING",
    'UaByteString'  : "DPEL_BLOB"
    }

LessObviousMapping = {
    'OpcUa_Byte'    : 'DPEL_UINT',
    'OpcUa_SByte'   : 'DPEL_INT',
    'OpcUa_UInt16'  : 'DPEL_UINT',
    'OpcUa_Int16'   : 'DPEL_INT'
}

ObviousMappingArray = {  # these are unanimously good choices
    'OpcUa_Boolean' : "DPEL_DYN_BOOL",
    'OpcUa_UInt32'  : "DPEL_DYN_UINT",
    'OpcUa_Int32'   : "DPEL_DYN_INT",
    'OpcUa_UInt64'  : "DPEL_DYN_ULONG",
    'OpcUa_Int64'   : "DPEL_DYN_LONG",
    'OpcUa_Float'   : "DPEL_DYN_FLOAT",
    'OpcUa_Double'  : "DPEL_DYN_FLOAT",
    'UaString'      : "DPEL_DYN_STRING",
    'UaByteString'  : "DPEL_DYN_BLOB"
    }

LessObviousMappingArray = {
    'OpcUa_Byte'    : 'DPEL_DYN_UINT',
    'OpcUa_SByte'   : 'DPEL_DYN_INT',
    'OpcUa_UInt16'  : 'DPEL_DYN_UINT',
    'OpcUa_Int16'   : 'DPEL_DYN_INT'
}

def handle_float_variables():
    design_inspector = DesignInspector(os.path.sep.join(['Design', 'Design.xml']))
    float_variables = []
    for class_name in design_inspector.get_names_of_all_classes():
        cvs = design_inspector.objectify_cache_variables(class_name,
            "[@dataType='OpcUa_Float' and @addressSpaceWrite != 'forbidden' and not(d:array)]")
        float_variables += ['{0}/{1}(cache-var)'.format(class_name, cv.get('name')) for cv in cvs]
        svs = design_inspector.objectify_source_variables(class_name,
            "[@dataType='OpcUa_Float' and @addressSpaceWrite != 'forbidden' and not(d:array)]")
        float_variables += ['{0}/{1}(source-var)'.format(class_name, sv.get('name')) for sv in svs]
    if len(float_variables) > 0:
        raise Exception(("In your design, there is/are scalar variables of "
                         "type OpcUa_Float. This data-type has no direct correspondence in "
                         "WinCC OA and will cause problems especially when writing from WinCC "
                         "OA. Please convert these variables to OpcUa_Double data-type. "
                         "List of variables (incl class names): \n{0}").format(
                         '\n'.join(float_variables)))

def quasar_data_type_to_dpt_type_constant(quasar_data_type, cls, cv, noarray = True):
    if(noarray) :
        if quasar_data_type in ObviousMapping:
            return ObviousMapping[quasar_data_type]
        # for the remaining types, we have to do less obvious choices.
        elif quasar_data_type in LessObviousMapping:
            to = LessObviousMapping[quasar_data_type]
            template_debug(("WARNING: mapped {0} to {1}, because of no corresponding type in WinCC OA. "
                            "(at: class={2} cv={3})").format(quasar_data_type, to, cls, cv))
            return to
        else:
            raise Exception("The following quasar datatype: '{0}' is not yet supported in Cacophony.".format(quasar_data_type))
    else :
        if quasar_data_type in ObviousMapping:
            return ObviousMappingArray[quasar_data_type]
        # for the remaining types, we have to do less obvious choices.
        elif quasar_data_type in LessObviousMapping:
            to = LessObviousMappingArray[quasar_data_type]
            template_debug(("WARNING: mapped {0} to {1}, because of no corresponding type in WinCC OA. "
                            "(at: class={2} cv={3})").format(quasar_data_type, to, cls, cv))
            return to
        else:
            raise Exception("The following quasar datatype: '{0}' is not yet supported in Cacophony.".format(quasar_data_type))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpt_prefix", dest="dpt_prefix", default="Quasar")
    parser.add_argument("--server_name", dest="server_name", default="QUASAR_SERVER")
    parser.add_argument("--driver_number", dest="driver_number", default="69")
    parser.add_argument("--subscription", dest="subscription", default="MyQuasarSubscription")
    parser.add_argument("--function_prefix", dest="function_prefix", default="")
    parser.add_argument("--use_design_with_meta", dest="use_design_with_meta", action="store_true",
                        help="Merge Design.xml with Meta design and use DesignWithMeta.xml for generation")
    parser.add_argument("--config_file", dest="config_file", default=None,
                        help="Configuration XML file to enable calculated variable support")
    args = parser.parse_args()

    additional_params = {
        'typePrefix'       : args.dpt_prefix,
        'serverName'       : args.server_name,
        'driverNumber'     : args.driver_number,
        'subscriptionName' : args.subscription,
        'functionPrefix'   : args.function_prefix}

    # Handle optional calculated variable support
    config_inspector = None
    if args.config_file:
        config_file_path = os.path.join(os.getcwd(), 'bin', args.config_file)
        if not os.path.isfile(config_file_path):
            raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
        print(Fore.CYAN + f"Enabling calculated variable support from: {config_file_path}" + Style.RESET_ALL)
        config_inspector = ConfigInspector(config_file_path)
        additional_params['configInspector'] = config_inspector

        # Print summary
        cv_by_class = config_inspector.get_calculated_variables_by_parent_class()
        print(Fore.GREEN + f"  Found {len(config_inspector.get_calculated_variable_names())} unique calculated variable(s):" + Style.RESET_ALL)
        for class_name, calc_vars in cv_by_class.items():
            print(Fore.BLUE + f"    {class_name}: {len(calc_vars)} variable(s) - {', '.join(sorted(calc_vars))}" + Style.RESET_ALL)
    else:
        additional_params['configInspector'] = None

    print(Fore.GREEN + "For your information, current settings are: \n" + Fore.BLUE
        + '\n'.join([('  {0:20} : {1}'.format(k, additional_params[k])) for k in additional_params.keys() if k != 'configInspector'])
        + Style.RESET_ALL)

    additional_params.update({'mapper' : quasar_data_type_to_dpt_type_constant})

    cacophony_root = os.path.dirname(os.path.sep.join([os.getcwd(), sys.argv[0]]))
    print('Cacophony root is at: ' + cacophony_root)

    # Determine which design file to use
    if args.use_design_with_meta:
        print(Fore.YELLOW + "Using DesignWithMeta (merging Design.xml with meta-design.xml)..." + Style.RESET_ALL)
        design_xml_filename = 'DesignWithMeta.xml'
        design_xml_path: str = os.path.join(os.getcwd(), 'Design', design_xml_filename)

        # Create the merged design file
        user_design_path = os.path.join(os.getcwd(), 'Design', 'Design.xml')
        meta_design_path = os.path.join(os.getcwd(), 'Meta', 'design', 'meta-design.xml')

        # Check that required files exist
        if not os.path.isfile(user_design_path):
            raise FileNotFoundError(f"User design file not found: {user_design_path}")
        if not os.path.isfile(meta_design_path):
            raise FileNotFoundError(f"Meta design file not found: {meta_design_path}")

        print(f"  Merging: {user_design_path}")
        print(f"      with: {meta_design_path}")
        print(f"      into: {design_xml_path}")

        with open(user_design_path, mode='r', encoding='utf-8') as user_file, \
             open(meta_design_path, mode='r', encoding='utf-8') as meta_file, \
             open(design_xml_path, mode='w', encoding='utf-8') as merged_file:
            merge_user_and_meta_design(user_file, meta_file, merged_file)

        print(Fore.GREEN + "  DesignWithMeta.xml created successfully!" + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + "Using Design.xml (default behavior)" + Style.RESET_ALL)
        design_xml_path: str = os.path.join(os.getcwd(), 'Design', 'Design.xml')

    try:
        handle_float_variables()
        transformDesign(
            os.path.join(cacophony_root, 'templates', 'designToDptCreation.jinja'),
            designXmlPath=design_xml_path,
            outputFile=os.path.join(cacophony_root, 'generated', 'createDpts.ctl'),
            requiresMerge=False,
            astyleRun=True,
            additionalParam=additional_params)

        transformDesign(
            os.path.join(cacophony_root, 'templates', 'designToConfigParser.jinja'),
            designXmlPath=design_xml_path,
            outputFile=os.path.join(cacophony_root, 'generated', 'configParser.ctl'),
            requiresMerge=False,
            astyleRun=True,
            additionalParam=additional_params)

        transformDesign(
            os.path.join(cacophony_root, 'templates', 'designToInstantiationFromDesign.jinja'),
            designXmlPath=design_xml_path,
            outputFile=os.path.join(cacophony_root, 'generated', 'instantiateFromDesign.ctl'),
            requiresMerge=False,
            astyleRun=True,
            additionalParam=additional_params)

        # Clean up: delete DesignWithMeta.xml if it was created
        if args.use_design_with_meta and os.path.isfile(design_xml_path):
            os.remove(design_xml_path)
            print(Fore.YELLOW + f"  Cleaned up: {design_xml_path} deleted" + Style.RESET_ALL)

    except:
        quasar_basic_utils.quasaric_exception_handler()
if __name__ == "__main__":
    main()
