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

		const string CONNECTIONSETTING_KEY_DRIVER_NUMBER = "DRIVER_NUMBER";
		const string CONNECTIONSETTING_KEY_SERVER_NAME = "SERVER_NAME";
		const string CONNECTIONSETTING_KEY_SUBSCRIPTION_NAME = "SUBSCRIPTION_NAME";

    bool <xsl:value-of select="$functionPrefix"/>addressConfigWrapper (
    string  dpe,
    string  address,
    int     mode,
		mapping connectionSettings,
    bool active=true
    )
    {
    string subscription = "";
    if (mode != DPATTR_ADDR_MODE_IO_SQUERY &amp;&amp; mode != DPATTR_ADDR_MODE_INPUT_SQUERY)
    {
      subscription = connectionSettings[CONNECTIONSETTING_KEY_SUBSCRIPTION_NAME];
    }
            dyn_string dsExceptionInfo;
            fwPeriphAddress_setOPCUA (
                dpe /*dpe*/,
                connectionSettings[CONNECTIONSETTING_KEY_SERVER_NAME],
                connectionSettings[CONNECTIONSETTING_KEY_DRIVER_NUMBER],
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

        DebugTN("Setting active on dpe: "+dpe+" to "+active);
	    dpSetWait(dpe + ":_address.._active", active);

        return true;


    }

    bool <xsl:value-of select="$functionPrefix"/>evaluateActive(
        mapping addressActiveControl,
        string className,
        string varName,
        string dpe)
    {
        bool active = false;
        if (mappingHasKey(addressActiveControl, className)) <!-- we're query for the class name in the mapping -->
        {
          string regex = addressActiveControl[className];
          int regexMatchResult = regexpIndex(regex, varName, makeMapping("caseSensitive", true));
          DebugTN("The result of evaluating regex: '"+regex+"' with string: '"+varName+" was: "+regexMatchResult);
          if (regexMatchResult>=0)
            active = true;
          else
          {
            active = false;
            DebugN("Note: the address on dpe: "+dpe+" will be non-active because such instructions were passed in the addressActive mapping.");
          }
        }
        else
          active = true; // by default
        return active;
    }

    <xsl:for-each select="/d:design/d:class">
    <xsl:variable name="className"><xsl:value-of select="@name"/></xsl:variable>
    bool <xsl:value-of select="$functionPrefix"/>configure<xsl:value-of select="@name"/> (
        int     docNum,
        int     childNode,
        string  prefix,
        bool    createDps,
        bool    assignAddresses,
        bool    continueOnError,
        mapping addressActiveControl,
				mapping connectionSettings)
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
        bool active = false;


        <xsl:for-each select="d:cachevariable">
            dpe = fullName+".<xsl:value-of select='@name'/>";
            address = dpe; // address can be generated from dpe after some mods ...
            strreplace(address, "/", ".");

        active = <xsl:value-of select="$functionPrefix"/>evaluateActive(
          addressActiveControl,
          "<xsl:value-of select="$className"/>",
          "<xsl:value-of select='@name'/>",
          dpe);

	    success = <xsl:value-of select="$functionPrefix"/>addressConfigWrapper(
	    dpe,
	    address,
	    <xsl:value-of select="fnc:cacheVariableToMode(@addressSpaceWrite)"/> /* mode */,
			connectionSettings,
        active);

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

        active = <xsl:value-of select="$functionPrefix"/>evaluateActive(
          addressActiveControl,
          "<xsl:value-of select="$className"/>",
          "<xsl:value-of select='@name'/>",
          dpe);

	    success = <xsl:value-of select="$functionPrefix"/>addressConfigWrapper(
	    dpe,
	    address,
	    <xsl:value-of select="fnc:sourceVariableToMode(@addressSpaceRead, @addressSpaceWrite)"/> /* mode */,
			connectionSettings,
        active);

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
        <xsl:value-of select="$functionPrefix"/>configure<xsl:value-of select="@class"/> (docNum, children[i], fullName+"/", createDps, assignAddresses, continueOnError, addressActiveControl, connectionSettings);
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

    int <xsl:value-of select="$functionPrefix"/>parseConfig (
        string  configFileName,
        bool    createDps,
        bool    assignAddresses,
        bool    continueOnError,
        mapping addressActiveControl = makeMapping(),
				mapping connectionSettings = makeMapping())
    /* Create instances */
    {

		/* Apply defaults in connectionSettings, when not concretized by the user */
		if (!mappingHasKey(connectionSettings, CONNECTIONSETTING_KEY_DRIVER_NUMBER))
		{
			connectionSettings[CONNECTIONSETTING_KEY_DRIVER_NUMBER] = <xsl:value-of select="$driverNumber"/>;
		}
		if (!mappingHasKey(connectionSettings, CONNECTIONSETTING_KEY_SERVER_NAME))
		{
			connectionSettings[CONNECTIONSETTING_KEY_SERVER_NAME] = "<xsl:value-of select='$serverName'/>";
		}
		if (!mappingHasKey(connectionSettings, CONNECTIONSETTING_KEY_SUBSCRIPTION_NAME))
		{
			connectionSettings[CONNECTIONSETTING_KEY_SUBSCRIPTION_NAME] = "<xsl:value-of select='$subscriptionName'/>";
		}

    /* Pre/Suffix the expression with ^$ to enable exact matches and also check if given patterns make sense */
    for (int i=1; i&lt;=mappinglen(addressActiveControl); i++)
    {
    string regexp = mappingGetValue(addressActiveControl, i);
    regexp = "^"+regexp+"$";
    addressActiveControl[mappingGetKey(addressActiveControl, i)] = regexp;
        int regexpResult = regexpIndex(regexp, "thisdoesntmatter");
        if (regexpResult &lt;= -2)
        {
            DebugTN("It seems that the given regular expression is wrong: "+regexp+"    the process will be aborted");
            return -1;
        }
    }

        string errMsg;
        int errLine;
        int errColumn;


	string configFileToLoad = configFileName;

	if (! _UNIX)
	{
	DebugTN("This code was validated only on Linux systems. For Windows, BE-ICS should perform the validation and release the component. See at https://its.cern.ch/jira/browse/OPCUA-1519 for more information.");
	return -1;
	}

      // try to perform entity substitution
      string tempFile = configFileToLoad + ".temp";
      int result = system("xmllint --noent " + configFileToLoad + " > " + tempFile);
      DebugTN("The call to 'xmllint --noent' resulted in: "+result);
      if (result != 0)
      {
	  DebugTN("It was impossible to run xmllint to inflate entities. WinCC OA might load this file incorrectly if entity references are used. So we decided it wont be possible. See at https://its.cern.ch/jira/browse/OPCUA-1519 for more information.");
	  return -1;
	}
	configFileToLoad = tempFile;

	int docNum = xmlDocumentFromFile(configFileToLoad , errMsg, errLine, errColumn);
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
                <xsl:value-of select="$functionPrefix"/>configure<xsl:value-of select="@class"/> (docNum, children[i], "", createDps, assignAddresses, continueOnError, addressActiveControl, connectionSettings);
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
