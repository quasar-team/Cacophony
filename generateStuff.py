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
	args = parser.parse_args()
	
	transformDesign(
		xsltTransformation=os.path.join(thisModuleName, 'xslt', 'designToDptCreation.xslt'), 
		outputFile=os.path.join(thisModuleName, 'generated', 'createDpts.ctl'), 
		requiresMerge=False, 
		astyleRun=True, 
		additionalParam=['typePrefix={0}'.format(args.dpt_prefix)])
	
	transformDesign(
		xsltTransformation=os.path.join(thisModuleName, 'xslt', 'designToDeviceDefinition.xslt'), 
		outputFile=os.path.join(thisModuleName, 'generated', 'createDeviceDefinitions.ctl'), 
		requiresMerge=False, 
		astyleRun=True, 
		additionalParam=['typePrefix={0}'.format(args.dpt_prefix)])	

    
if __name__=="__main__":
    main()
    
    

