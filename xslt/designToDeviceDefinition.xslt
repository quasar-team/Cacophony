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
     
    <xsl:template name="classToDeviceDefinition">
    <xsl:param name="className"/>
    //<xsl:value-of select="$className"/>
    <xsl:variable name="dpt"><xsl:value-of select="$typePrefix"/><xsl:value-of select="$className"/></xsl:variable>
    bool createDeviceDefinition<xsl:value-of select="@name"/>()
    {
        int rv;
        rv = dpCreate("<xsl:value-of select="$dpt"/>Info", "_FwDeviceDefinition");
        if (rv != 0)
        {
          throwError(getLastError());
          return false;
        }
        dpSet("<xsl:value-of select="$dpt"/>Info.dpType", "<xsl:value-of select="$dpt"/>");
        dpSet("<xsl:value-of select="$dpt"/>Info.version", 1);
        dpSet("<xsl:value-of select="$dpt"/>Info.configuration.address.canHave", true);
        dpSet("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.general.canHave", true);
        dpSet("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.general.serverName", "<xsl:value-of select="$serverName"/>");
        dpSet("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.general.driverNumber", <xsl:value-of select="$driverNumber"/>);
        <xsl:for-each select="d:cachevariable">
        // for cachevar <xsl:value-of select="@name"/>
        appendToDpe("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.items", "ns=2;s=xxx.<xsl:value-of select="@name"/>");
        appendToDpe("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.subscriptions", "OPCUA_SUBSCRIPTION");
        appendToDpe("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.kinds", 1);
        appendToDpe("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.variants", 1);
        appendToDpe("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.types", 750);
        appendToDpe("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.direction", 2);
        appendToDpe("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.variants", 1);
        appendToDpe("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.variants", "EMPTY");
        
        </xsl:for-each>    

        return true;    
    }
    </xsl:template>
	
    
	<xsl:template match="/">	
    // generated using Cacophony, an optional module of quasar
    // generated at: TODO
    
    void appendToDpe(string dpe, string value)
    {
        dyn_string dsSomething;
        dpGet(dpe, dsSomething);
        dynAppend(dsSomething, value);
        dpSet(dpe, dsSomething);
    }
    
    <xsl:for-each select="/d:design/d:class">
    <xsl:call-template name="classToDeviceDefinition">
        <xsl:with-param name="className"><xsl:value-of select="@name"/></xsl:with-param>
    </xsl:call-template>   
    </xsl:for-each>
    
    
    int main ()
    {
        <xsl:for-each select="/d:design/d:class">
            if (!createDeviceDefinition<xsl:value-of select="@name"/>())
            return 1;
        </xsl:for-each>
        return 0;
    }
    
    </xsl:template>



</xsl:transform>
