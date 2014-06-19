# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Villierme
#
# Created:     17/07/2013
# Copyright:   (c) Villierme 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy
from arcpy import env


# Paramètres utilisateur :
"""
inFeat = r'H:\5_STAGE\indicateurs\BCaract_Cont\Proche_Foret\DataProche.gdb\axehaie'
nearFeat = r'H:\5_STAGE\indicateurs\BCaract_Cont\Proche_Foret\DataProche.gdb\Foret_Selectd'
outFeat = r'H:\5_STAGE\indicateurs\BCaract_Cont\Proche_Foret\DataProche.gdb\Foret_Selectd'
"""

inFeat = arcpy.GetParameterAsText(0)
nearFeat = arcpy.GetParameterAsText(1)
outFeat = arcpy.GetParameterAsText(2)


# On fait une copie de la couche en entrée :
arcpy.CopyFeatures_management(inFeat,outFeat)

# process : appliquer une opération de proximité :
# Near_analysis (in_features, near_features, {search_radius}, {location}, {angle})
arcpy.Near_analysis(outFeat, nearFeat, "", "LOCATION", "ANGLE")
