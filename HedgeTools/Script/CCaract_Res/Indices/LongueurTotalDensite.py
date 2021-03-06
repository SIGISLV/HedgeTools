﻿# ---------------------------------------------------------------------------
# LongueurTotalDensite.py
# Created on: 2013-07-25 12:30:06.00000
#   (generated by ArcGIS/ModelBuilder)
# Description:
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy, os

from arcpy import env
env.overwriteOutput = True

# Local variables:
axemedian = arcpy.GetParameterAsText(0)
sitetude = arcpy.GetParameterAsText(1)
output = arcpy.GetParameterAsText(2)
gdb, nameOutput = os.path.split(output)

# Process: Découper
ClipArc = os.path.join(gdb,"cliparc")
arcpy.Clip_analysis(axemedian, sitetude, ClipArc, "")

# Process: Jointure spatiale
# il faut instancier un objet fieldmapping :
fieldmapping = arcpy.FieldMappings()
fieldmapping.addTable(ClipArc)
fieldmapping.addTable(sitetude)

# A partir de cet objet il faut créer un fieldmap
indexShapelength = fieldmapping.findFieldMapIndex("Shape_length")
fieldmap = fieldmapping.getFieldMap(indexShapelength)
field = fieldmap.outputField

# on prépare le field
field.name = "TotalLongueur"
field.aliasName = "TotalLongueur"
fieldmap.outputField = field

# on applique le merge rule :
fieldmap.mergeRule = "Sum"
fieldmapping.addFieldMap(fieldmap)

arcpy.SpatialJoin_analysis(sitetude, ClipArc , output, "JOIN_ONE_TO_ONE", "KEEP_ALL", fieldmapping, "CONTAINS", "", "")

# Process: Ajouter un champ
arcpy.AddField_management(output, "Denshaie_mha", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

# Process: Calculer un champ
arcpy.CalculateField_management(output, "Denshaie_mha", "[TotalLongueur] / [Shape_Area]", "VB", "")

# on efface l'entité intermédaire :
arcpy.Delete_management(ClipArc)