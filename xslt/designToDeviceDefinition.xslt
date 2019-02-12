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
	
     
    <xsl:template name="classToDeviceDefinition">
    <xsl:param name="className"/>
    //<xsl:value-of select="$className"/>
    <xsl:variable name="dpt"><xsl:value-of select="$typePrefix"/><xsl:value-of select="$className"/></xsl:variable>
    bool createDeviceDefinition<xsl:value-of select="@name"/>()
    {
        int rv;
        rv = dpCreate("<xsl:value-of select="$dpt"/>Info", "_FwDeviceDefinition");
        if (rv != 0)
          return false;
        dpSet("<xsl:value-of select="$dpt"/>Info.dpType", "<xsl:value-of select="$dpt"/>");
        dpSet("<xsl:value-of select="$dpt"/>Info.version", 1);
        dpSet("<xsl:value-of select="$dpt"/>Info.configuration.address.canHave", true);
        dpSet("<xsl:value-of select="$dpt"/>Info.configuration.address.OPCUA.general.canHave", true);
            
    
    }
    </xsl:template>
	
    
	<xsl:template match="/">	
    // generated using Cacophony, an optional module of quasar
    // generated at: TODO
    
    
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
