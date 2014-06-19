# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        CleanMedianAxis

# Purpose:     Nettoie l'axe médian. Il supprime les doublons puis les arc pendants.
#
# Author:      Villierme Lewis
#
# Created:     30/05/2013
# Copyright:   (c) lvillier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy
from arcpy import env
import os

env.overwriteOutput=True


# la fonction medianaxe
def CleanMedianAxis(inMedianAxis, inoutput, InLengthExtendLine, InDangleLength, geodata):
    """
    Nettoie l'axe médian.
    entrées :
        inMedianAxis : path of the line to clean.
        inoutput : path of the output feature.
        geodata : the workspace
    """
    # Set the workspace
    arcpy.env.workspace = geodata

    # copier l'entité en entrée
    arcpy.AddMessage("Copie de l'axe médian ...")
    arcpy.CopyFeatures_management(inMedianAxis, "MedianAxis")

    # Netoyer les doublons
    num=None
    arcpy.AddMessage("Suppression des doublons ...")
    while num !=0:
        arcpy.DeleteIdentical_management("MedianAxis", "Shape")
        mess = arcpy.GetMessages(0)
        messSplit = mess.split('\n')
        stnum = str(messSplit[2][0:messSplit[2].find('doublons')-1])
        num = int(stnum)
        arcpy.AddMessage( stnum + " doublons supprimés ...")

    # Prolonger les lignes
    arcpy.AddMessage("Prologation des lignes ...")
    arcpy.ExtendLine_edit("MedianAxis", InLengthExtendLine, "FEATURE")

    # fusioner les lignes
    arcpy.AddMessage("Fusion des lignes ...")
    arcpy.UnsplitLine_management("MedianAxis", "MedianAxisUnsplit")

    # tronquer la ligne:
    arcpy.AddMessage("Suppression des arcs pendants ...")
    arcpy.TrimLine_edit("MedianAxisUnsplit", InDangleLength, "DELETE_SHORT")

    # fusionner les lignes
    arcpy.UnsplitLine_management("MedianAxisUnsplit", output)

    # retourner le résultat
    return inoutput


if __name__ == "__main__":

    # Paramters
    MedianAxis = arcpy.GetParameter(0)
    output =arcpy.GetParameterAsText(1)
    extendLine = arcpy.GetParameter(2)
    dangle = arcpy.GetParameter(3)

    """
    # local variables:
    MedianAxis = r'H:\7_CDD\HedgeTools\DataTest\data.gdb\MedianAxe4Communescopy'
    output = r'H:\7_CDD\HedgeTools\DataTest\data.gdb\MedianAxe4CommunesClean'
    extendLine = 2
    dangle = 20
    """
    geodata = r'H:\7_CDD\HedgeTools\DataTest\tmp.gdb'

    CleanMedianAxis(MedianAxis, output, extendLine, dangle, geodata)