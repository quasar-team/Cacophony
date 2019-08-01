# @author Piotr Nikiel <piotr.nikiel@gmail.com>

thisModuleName = "Cacophony"

import sys
import os
import argparse
sys.path.insert(0, 'FrameworkInternals')

from transformDesign import transformDesign
    
def main():
	parser=argparse.ArgumentParser()
	parser.add_argument("--dpt_prefix", dest="dpt_prefix", default="Quasar")
	parser.add_argument("--server_name", dest="server_name", default="QUASAR_SERVER")
	parser.add_argument("--driver_number", dest="driver_number", default="69")
	parser.add_argument("--subscription", dest="subscription", default="MyQuasarSubscription")
        parser.add_argument("--function_prefix", dest="function_prefix", default="")
	args = parser.parse_args()
	
	additionalParams=[
		'typePrefix={0}'.format(args.dpt_prefix), 
		'serverName={0}'.format(args.server_name),
		'driverNumber={0}'.format(args.driver_number),
		'subscriptionName={0}'.format(args.subscription),
                'functionPrefix={0}'.format(args.function_prefix)]
	
	transformDesign(
		xsltTransformation=os.path.join(thisModuleName, 'xslt', 'designToDptCreation.xslt'), 
		outputFile=os.path.join(thisModuleName, 'generated', 'createDpts.ctl'), 
		requiresMerge=False, 
		astyleRun=True, 
		additionalParam=additionalParams)
	
	transformDesign(
		xsltTransformation=os.path.join(thisModuleName, 'xslt', 'designToConfigParser.xslt'), 
		outputFile=os.path.join(thisModuleName, 'generated', 'configParser.ctl'), 
		requiresMerge=False, 
		astyleRun=True, 
		additionalParam=additionalParams)	
    
if __name__=="__main__":
    main()
    
    

