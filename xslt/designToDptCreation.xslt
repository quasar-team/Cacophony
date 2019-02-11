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
	

    <xsl:template name="classToDpt">
    <xsl:param name="className"/>
    //<xsl:value-of select="$className"/>
    bool createDpt<xsl:value-of select="@name"/>()
    {
    
    }
    </xsl:template>
	
	<xsl:template match="/">	
    // generated using Cacophony, an optional module of quasar
    // generated at: TODO
    
    <xsl:for-each select="/d:design/d:class">
    <xsl:call-template name="classToDpt">
        <xsl:with-param name="className"><xsl:value-of select="@name"/></xsl:with-param>
    </xsl:call-template>   
    </xsl:for-each>
    
    </xsl:template>



</xsl:transform>
