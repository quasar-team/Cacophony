# @author Piotr Nikiel <piotr.nikiel@gmail.com>

thisModuleName = "Cacophony"

import sys
import os
sys.path.insert(0, 'FrameworkInternals')

from transformDesign import transformDesign
    
def main():
	transformDesign(
		xsltTransformation=os.path.join(thisModuleName, 'xslt', 'designToDptCreation.xslt'), 
		outputFile=os.path.join(thisModuleName, 'generated', 'createDpts.ctl'), 
		requiresMerge=False, 
		astyleRun=True, 
		additionalParam=None)

    
if __name__=="__main__":
    main()
    
    

