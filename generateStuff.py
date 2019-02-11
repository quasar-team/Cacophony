# @author Piotr Nikiel <piotr.nikiel@gmail.com>

import sys
import os
sys.path.insert(0, 'FrameworkInternals')

from transformDesign import transformDesign

def runGenerator(className,uaoDirectory='UaoForQuasar', namespace='UaoClient'):
    output_header = os.path.join(uaoDirectory,'generated','{0}.h'.format(className))
    output_body = os.path.join(uaoDirectory,'generated','{0}.cpp'.format(className))
    additionalParam=['className={0}'.format(className), 'namespace={0}'.format(namespace)]
    transformDesign(
        xsltTransformation=os.path.join(uaoDirectory, 'xslt', 'designToClassHeader.xslt'), 
        outputFile=output_header, 
        requiresMerge=False, 
        astyleRun=True, 
        additionalParam=additionalParam)

    transformDesign(
        xsltTransformation=os.path.join(uaoDirectory, 'xslt', 'designToClassBody.xslt'), 
        outputFile=output_body, 
        requiresMerge=False, 
        astyleRun=True, 
        additionalParam=additionalParam)
    
def main():
    className = sys.argv[1]
    runGenerator(className)
    
if __name__=="__main__":
    main()
    
    

