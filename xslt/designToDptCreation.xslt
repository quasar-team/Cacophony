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
	
    <xsl:function name="fnc:quasarDataTypeToDptTypeConstant">
    <xsl:param name="dataType"/>
    <xsl:choose>
        <xsl:when test="$dataType='OpcUa_Boolean'">DPEL_BOOL</xsl:when>
        <xsl:when test="$dataType='OpcUa_UInt16'">DPEL_UINT</xsl:when>
        <xsl:when test="$dataType='OpcUa_UInt32'">DPEL_UINT</xsl:when>
        <xsl:when test="$dataType='OpcUa_UInt64'">DPEL_ULONG</xsl:when>
        <xsl:when test="$dataType='OpcUa_Float'">DPEL_FLOAT</xsl:when>
        <xsl:when test="$dataType='OpcUa_Double'">DPEL_FLOAT</xsl:when>
        <xsl:when test="$dataType='UaString'">DPEL_STRING</xsl:when>
        <xsl:otherwise>
            <xsl:message terminate="yes">The following quasar datatype is not yet supported: 
                <xsl:value-of select="$dataType"/>
            </xsl:message>
        </xsl:otherwise>
    </xsl:choose>
    </xsl:function>

    <xsl:template name="classToDpt">
    <xsl:param name="className"/>
    //<xsl:value-of select="$className"/>
    bool createDpt<xsl:value-of select="@name"/>()
    {
    // the names of vars and the way of generating DPT come directly from examples of dpTypeCreate
    dyn_dyn_string xxdepes;
    dyn_dyn_int xxdepei;
    <xsl:for-each select="d:cachevariable">
    dynAppend(xxdepes, makeDynString("<xsl:value-of select='@name'/>"));
    dynAppend(xxdepei, makeDynInt(
    <xsl:value-of select='fnc:quasarDataTypeToDptTypeConstant(@dataType)'/>));
    </xsl:for-each>
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
