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
	<xsl:param name="functionPrefix"/>
	
    <xsl:function name="fnc:quasarDataTypeToDptTypeConstant">
    <xsl:param name="dataType"/>
    <xsl:choose>
        <xsl:when test="$dataType='OpcUa_Boolean'">DPEL_BOOL</xsl:when>
        <xsl:when test="$dataType='OpcUa_Byte'"><xsl:message>Warning: mapped Byte to DPEL_UINT.</xsl:message>DPEL_UINT</xsl:when>
        <xsl:when test="$dataType='OpcUa_SByte'"><xsl:message>Warning: mapped SByte to DPEL_INT.</xsl:message>DPEL_INT</xsl:when>
	    <xsl:when test="$dataType='OpcUa_UInt16'"><xsl:message>Warning: mapped UInt16 to DPEL_UINT.</xsl:message>DPEL_UINT</xsl:when>
	    <xsl:when test="$dataType='OpcUa_Int16'"><xsl:message>Warning: mapped Int16 to DPEL_INT.</xsl:message>DPEL_INT</xsl:when>
        <xsl:when test="$dataType='OpcUa_UInt32'">DPEL_UINT</xsl:when>
	    <xsl:when test="$dataType='OpcUa_Int32'">DPEL_INT</xsl:when>
        <xsl:when test="$dataType='OpcUa_UInt64'">DPEL_ULONG</xsl:when>
	    <xsl:when test="$dataType='OpcUa_Int64'">DPEL_LONG</xsl:when>
        <xsl:when test="$dataType='OpcUa_Float'">DPEL_FLOAT</xsl:when>
        <xsl:when test="$dataType='OpcUa_Double'">DPEL_FLOAT</xsl:when>
        <xsl:when test="$dataType='UaString'">DPEL_STRING</xsl:when>
        <xsl:when test="$dataType='UaByteString'">DPEL_BLOB</xsl:when>
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
    bool <xsl:value-of select="$functionPrefix"/>createDpt<xsl:value-of select="@name"/>()
    {
    // the names of vars and the way of generating DPT come directly from examples of dpTypeCreate
    dyn_dyn_string xxdepes;
    dyn_dyn_int xxdepei;
    dynAppend(xxdepes, makeDynString("<xsl:value-of select="$typePrefix"/><xsl:value-of select='$className'/>", ""));
    dynAppend(xxdepei, makeDynInt(DPEL_STRUCT));
    <xsl:for-each select="d:cachevariable">
        <xsl:choose>
            <xsl:when test="d:array">
                <xsl:message>WARNING Class <xsl:value-of select="$className"/> cachevariable <xsl:value-of select="@name"/> is an array.
                Arrays are not yet supported by Cacophony. Please request from Piotr.
                </xsl:message>
            </xsl:when>
            <xsl:otherwise>
                dynAppend(xxdepes, makeDynString("", "<xsl:value-of select='@name'/>"));
                dynAppend(xxdepei, makeDynInt(0, 
                <xsl:value-of select='fnc:quasarDataTypeToDptTypeConstant(@dataType)'/>));
            </xsl:otherwise>
        </xsl:choose>
    </xsl:for-each>
    
     <xsl:for-each select="d:sourcevariable">
        <xsl:choose>
            <xsl:when test="d:array">
                <xsl:message>WARNING Class <xsl:value-of select="$className"/> sourcevariable <xsl:value-of select="@name"/> is an array.
                Arrays are not yet supported by Cacophony. Please request from Piotr.
                </xsl:message>
            </xsl:when>
            <xsl:otherwise>
                dynAppend(xxdepes, makeDynString("", "<xsl:value-of select='@name'/>"));
                dynAppend(xxdepei, makeDynInt(0, 
                <xsl:value-of select='fnc:quasarDataTypeToDptTypeConstant(@dataType)'/>));
            </xsl:otherwise>
        </xsl:choose>
    </xsl:for-each>   
   

    <xsl:if test="d:method">
        <xsl:message>WARNING Class <xsl:value-of select="$className"/> has method(s) but there is no method support in WinCC OA, skipping!</xsl:message>
    </xsl:if>
    
    int status = dpTypeCreate(xxdepes, xxdepei);
    return status == 0;
    }
    </xsl:template>
	
	<xsl:template match="/">	
    // generated using Cacophony, an optional module of quasar, see: https://github.com/quasar-team/Cacophony
    // generated on <xsl:value-of  select="current-date()"/>
    
    <xsl:for-each select="/d:design/d:class">
    <xsl:call-template name="classToDpt">
        <xsl:with-param name="className"><xsl:value-of select="@name"/></xsl:with-param>
    </xsl:call-template>   
    </xsl:for-each>
    
    int <xsl:value-of select="$functionPrefix"/>createDpts (string dptFilter=".*")
    {
    <xsl:for-each select="/d:design/d:class">
      {
      int result = regexpIndex(dptFilter, "<xsl:value-of select="@name"/>");
      if (result >= 0)
      {
            if (!<xsl:value-of select="$functionPrefix"/>createDpt<xsl:value-of select="@name"/>())
            return 1;
	    }
	    else
	    {
	       DebugN("DPT <xsl:value-of select="@name"/> not covered by provided dptFilter, skipping");
	    }
      }
        </xsl:for-each>
        return 0;
    }
    
    </xsl:template>



</xsl:transform>
