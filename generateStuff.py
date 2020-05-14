# @author Piotr Nikiel <piotr.nikiel@gmail.com>

import sys
import os
import argparse
from colorama import Fore, Style

thisModuleName = "Cacophony"

sys.path.insert(0, 'FrameworkInternals')

from transformDesign import transformDesign

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

def quasar_data_type_to_dpt_type_constant(quasar_data_type):
    if quasar_data_type in ObviousMapping:
        return ObviousMapping[quasar_data_type]
    # for the remaining types, we have to do less obvious choices.
    elif quasar_data_type == 'OpcUa_Byte':
        template_debug("WARNING: mapped OpcUa_Byte to DPEL_UINT, because of no corresponding type in WinCC OA.")
        return "DPEL_UINT";
    elif quasar_data_type == 'OpcUa_SByte':
        template_debug("WARNING: mapped OpcUa_SByte to DPEL_INT, because of no corresponding type in WinCC OA.")
        return "DPEL_INT";
    elif quasar_data_type == 'OpcUa_UInt16':
        template_debug("WARNING: mapped OpcUa_UInt16 to DPEL_UINT, because of no corresponding type in WinCC OA.")
        return "DPEL_UINT";
    elif quasar_data_type == 'OpcUa_Int16':
        template_debug("WARNING: mapped OpcUa_Int16 to DPEL_INT, because of no corresponding type in WinCC OA.")
        return "DPEL_INT";
    else:
        raise Exception("The following quasar datatype: '{0}' is not yet supported in Cacophony.".format(quasar_data_type))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpt_prefix", dest="dpt_prefix", default="Quasar")
    parser.add_argument("--server_name", dest="server_name", default="QUASAR_SERVER")
    parser.add_argument("--driver_number", dest="driver_number", default="69")
    parser.add_argument("--subscription", dest="subscription", default="MyQuasarSubscription")
    parser.add_argument("--function_prefix", dest="function_prefix", default="")
    args = parser.parse_args()

    additional_params = {
        'typePrefix'       : args.dpt_prefix,
        'serverName'       : args.server_name,
        'driverNumber'     : args.driver_number,
        'subscriptionName' : args.subscription,
        'functionPrefix'   : args.function_prefix}
    
    print(Fore.GREEN + "For your information, current settings are: \n" + Fore.BLUE
        + '\n'.join([('  {0:20} : {1}'.format(k, additional_params[k])) for k in additional_params.keys()])
        + Style.RESET_ALL)
    
    additional_params.update({'mapper' : quasar_data_type_to_dpt_type_constant})

    cacophony_root = os.path.dirname(os.path.sep.join([os.getcwd(), sys.argv[0]]))
    print('Cacophony root is at: ' + cacophony_root)
    transformDesign(
        xsltTransformation=os.path.join(cacophony_root, 'templates', 'designToDptCreation.jinja'),
        outputFile=os.path.join(thisModuleName, 'generated', 'createDpts.ctl'),
        requiresMerge=False,
        astyleRun=True,
        additionalParam=additional_params)

    # transformDesign(
    #     xsltTransformation=os.path.join(thisModuleName, 'xslt', 'designToConfigParser.xslt'),
    #     outputFile=os.path.join(thisModuleName, 'generated', 'configParser.ctl'),
    #     requiresMerge=False,
    #     astyleRun=True,
    #     additionalParam=additional_params)

if __name__ == "__main__":
    main()
