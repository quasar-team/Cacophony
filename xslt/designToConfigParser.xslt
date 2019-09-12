<?xml version="1.0" encoding="UTF-8"?>
<!-- author pnikiel -->
<xsl:transform version="2.0" xmlns:xml="http://www.w3.org/XML/1998/namespace" 
xmlns:xs="http://www.w3.org/2001/XMLSchema" 
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
xmlns:d="http://cern.ch/quasar/Design"
xmlns:fnc="http://cern.ch/quasar/MyFunctions"
xsi:schemaLocation="http://www.w3.org/1999/XSL/Transform ../../Design/schema-for-xslt20.xsd ">
	<xsl:include href="../../Design/CommonFunctions.xslt" />
	<xsl:output method="text"></xsl:output>
    <xsl:param name="typePrefix"/>
    <xsl:param name="serverName"/>
    <xsl:param name="driverNumber"/>
    <xsl:param name="subscriptionName"/>
    <xsl:param name="functionPrefix"/>	

    <xsl:function name="fnc:cacheVariableToMode">
    <xsl:param name="addressSpaceWrite"/>
    <xsl:choose>
    <xsl:when test="$addressSpaceWrite='forbidden'">DPATTR_ADDR_MODE_INPUT_SPONT</xsl:when>
    <xsl:otherwise>DPATTR_ADDR_MODE_IO_SPONT</xsl:otherwise>
    </xsl:choose>
    </xsl:function>
   
    <xsl:function name="fnc:sourceVariableToMode">
    <xsl:param name="addressSpaceRead"/>
    <xsl:param name="addressSpaceWrite"/>
    <xsl:choose>
    <xsl:when test="$addressSpaceRead!='forbidden' and $addressSpaceWrite!='forbidden'">DPATTR_ADDR_MODE_IO_SQUERY</xsl:when>
    <xsl:when test="$addressSpaceRead!='forbidden' and $addressSpaceWrite='forbidden'">DPATTR_ADDR_MODE_INPUT_SQUERY</xsl:when>
    <xsl:when test="$addressSpaceRead='forbidden' and $addressSpaceWrite!='forbidden'">DPATTR_ADDR_MODE_OUTPUT_SINGLE</xsl:when>
    <xsl:otherwise><xsl:message terminate="yes">Don't know how to map this address because it support neither read nor write...</xsl:message></xsl:otherwise>
    </xsl:choose>
    </xsl:function>
   
	<xsl:template match="/">	
    <xsl:message terminate="no">
        Note: typePrefix=<xsl:value-of select="$typePrefix"/>
    </xsl:message>
    // generated using Cacophony, an optional module of quasar, see: https://github.com/quasar-team/Cacophony
    // generated on <xsl:value-of  select="current-date()"/>

    bool <xsl:value-of select="$functionPrefix"/>addressConfigWrapper (
    string dpe,
    string address,
    int mode,
    bool active=false
    )
    {
    string subscription = "";
    if (mode != DPATTR_ADDR_MODE_IO_SQUERY &amp;&amp; mode != DPATTR_ADDR_MODE_INPUT_SQUERY)
    {
      subscription = "<xsl:value-of select='$subscriptionName'/>";
    }
            dyn_string dsExceptionInfo;
            fwPeriphAddress_setOPCUA (
                dpe /*dpe*/,
                "<xsl:value-of select='$serverName'/>" /* server name*/,
                <xsl:value-of select="$driverNumber"/>,
                "ns=2;s="+address,
                subscription /* subscription*/,
                1 /* kind */,
                1 /* variant */,
                750 /* datatype */,
                mode,
                "" /*poll group */,
                dsExceptionInfo
                );
	    if (dynlen(dsExceptionInfo)>0)
		return false;
	    else
		return true;
	    dpSet(dpe + ":_address.._active", active);
		
    
    }
    
    
    <xsl:for-each select="/d:design/d:class">
    bool <xsl:value-of select="$functionPrefix"/>configure<xsl:value-of select="@name"/> (
        int docNum, 
        int childNode, 
        string prefix,
        bool createDps, 
        bool assignAddresses, 
        bool continueOnError)
    {
        DebugTN("Configure.<xsl:value-of select="@name"/> called");
        string name;
        xmlGetElementAttribute(docNum, childNode, "name", name);
        string fullName = prefix+name;
        string dpt = "<xsl:value-of select="$typePrefix"/>"+"<xsl:value-of select="@name"/>";
        
        if (createDps)
        {
            DebugTN("Will create DP "+fullName);
            int result = dpCreate(fullName, dpt);
            if (result != 0)
            {
                DebugTN("dpCreate name='"+fullName+"' dpt='"+dpt+"' not successful or already existing");
                if (!continueOnError)
                    throw(makeError("Cacophony", PRIO_SEVERE, ERR_IMPL, 1, "XXX YYY ZZZ"));
            }
        }
        
        if (assignAddresses)
        {
        string dpe, address;
        dyn_string dsExceptionInfo;
	bool success;
        <xsl:for-each select="d:cachevariable">
            dpe = fullName+".<xsl:value-of select='@name'/>";
            address = dpe; // address can be generated from dpe after some mods ...
            strreplace(address, "/", ".");

	    success = <xsl:value-of select="$functionPrefix"/>addressConfigWrapper(
	    dpe,
	    address,
	    <xsl:value-of select="fnc:cacheVariableToMode(@addressSpaceWrite)"/> /* mode */);

	    if (!success)
	    {
	       DebugTN("Failed setting address "+address+"; will terminate now.");
	       return false;
	    }
	    
        </xsl:for-each>
        
         <xsl:for-each select="d:sourcevariable">
            dpe = fullName+".<xsl:value-of select='@name'/>";
            address = dpe; // address can be generated from dpe after some mods ...
            strreplace(address, "/", ".");

	    success = <xsl:value-of select="$functionPrefix"/>addressConfigWrapper(
	    dpe,
	    address,
	    <xsl:value-of select="fnc:sourceVariableToMode(@addressSpaceRead, @addressSpaceWrite)"/> /* mode */);
	    
	    if (!success)
	    {
	       DebugTN("Failed setting address "+address+"; will terminate now.");
	       return false;
	    }
	    
            
        </xsl:for-each>       
        }
        
        dyn_int children;
        <xsl:for-each select="d:hasobjects[@instantiateUsing='configuration']">
        children = <xsl:value-of select="$functionPrefix"/>getChildNodesWithName(docNum, childNode, "<xsl:value-of select='@class'/>");
        for (int i=1; i&lt;=dynlen(children); i++)
        <xsl:value-of select="$functionPrefix"/>configure<xsl:value-of select="@class"/> (docNum, children[i], fullName+"/", createDps, assignAddresses, continueOnError);
        </xsl:for-each>
        
    }

    </xsl:for-each>
    
    dyn_int <xsl:value-of select="$functionPrefix"/>getChildNodesWithName (int docNum, int parentNode, string name)
    {
        dyn_int result;
        int node = xmlFirstChild(docNum, parentNode);
        while (node >= 0)
        {
            if (xmlNodeName(docNum, node)==name)
                dynAppend(result, node);
            node = xmlNextSibling (docNum, node);
        }
        return result;
    }
    
    int <xsl:value-of select="$functionPrefix"/>parseConfig (string configFileName, bool createDps, bool assignAddresses, bool continueOnError )
    /* Create instances */
    {
        string errMsg;
        int errLine;
        int errColumn;
        int docNum = xmlDocumentFromFile(configFileName, errMsg, errLine, errColumn);
        if (docNum &lt; 0)
        {
            DebugN("Didn't open the file: at Line="+errLine+" Column="+errColumn+" Message=" + errMsg);
            return -1;
        }
               
        int firstNode = xmlFirstChild(docNum);
        if (firstNode &lt; 0)
        {
            DebugN("Cant get the first child of the config file.");
            return -1;
        }
        while (xmlNodeName(docNum, firstNode) != "configuration")
        {
            firstNode = xmlNextSibling(docNum, firstNode);
            if (firstNode &lt; 0)
            {
                DebugTN("configuration node not found, sorry.");
                return -1;
            }
        }
        // now firstNode holds configuration node   
        dyn_int children;
        <xsl:for-each select="/d:design/d:root/d:hasobjects[@instantiateUsing='configuration']">      
            dyn_int children = <xsl:value-of select="$functionPrefix"/>getChildNodesWithName(docNum, firstNode, "<xsl:value-of select='@class'/>");
            for (int i = 1; i&lt;=dynlen(children); i++)
            {
                <xsl:value-of select="$functionPrefix"/>configure<xsl:value-of select="@class"/> (docNum, children[i], "", createDps, assignAddresses, continueOnError);
            }
        </xsl:for-each>
        
        <!-- add support for design-based instantiation  
        <xsl:for-each select="/d:design/d:root/d:hasobjects[@instantiateUsing='design']">      
            
        </xsl:for-each>   
        -->     
        return 0;
    }
    
    </xsl:template>



</xsl:transform>
