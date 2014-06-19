# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        CreateHedgeNetwork
# Purpose:     Create topology with points and line. It add also the "HedgeID"
#              on each feature class created. The inputs are point (OLTX), line
#              can be created by.
#              Each Feature classes came from a geodatabase.
#
#
# Author:      lvillier
#
# Created:     21/10/2013
# Copyright:   (c) lvillier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------


# --------------------------- import des bibliothèques --------
import arcpy
from arcpy import env
env.overwriteOutput=True
import os
import sys


# Fonction principale

def CreateNetWork(Lines, PointsL, PointsOTX, output, geodata):
    arcpy.env.workspace=geodata
    # on fusionne les lignes
    arcpy.AddMessage("Merging lines ...")
    g=arcpy.Geometry()
    lgeom = arcpy.UnsplitLine_management(Lines,g)
    arcpy.CopyFeatures_management(lgeom,Lines)
    # combiner les deux couches de points :
    if PointsL!="":
       arcpy.Merge_management([PointsL,PointsOTX], "Points")
    else:
         arcpy.CopyFeatures_management(PointsOTX,"Points")

    # Make the list of feature class :
    lFeatC=["Points", Lines]

    # Create the coverage
    arcpy.AddMessage("Converting into a coverage ...")
    arcpy.FeatureclassToCoverage_conversion(lFeatC,output)

    # Create the HedgeID field for arcs and point class
    # set the worksapce for a listFeatclasse
    arcpy.env.workspace=output

    # set le listFeatclassse
    lCoverFeat = arcpy.ListFeatureClasses()

    # set the arc and point path then addfield "HedgeID" and fill them.

    for feat in lCoverFeat:
        if 'node' in feat :
           arcpy.AddMessage("Adding the HEDGEID field on the node class ...")
           node = os.path.join(output, feat)
           arcpy.AddField_management(node, "HedgeID", "LONG")
           arcpy.CalculateField_management(node, "HedgeID", "!ARC#!+1","PYTHON")
        if 'arc' in feat :
           arcpy.AddMessage("Adding the HEDGEID field on the arc class ...")
           arc =os.path.join(output,feat)
           arcpy.AddField_management(arc, "HedgeID", "LONG")
           arcpy.CalculateField_management(arc,"HedgeID", "!FID!+1","PYTHON")

    # on retire les champs inutile :
    try :
        lfldarc, lfldnode = arcpy.ListFields(arc), arcpy.ListFields(node)
        KeepField =  ["FID", "Shape","FNODE#", "TNODE#", "LPOLY#", "RPOLY#","HEDGID"]

        # on cherche à supprimer tous les champs dont le nom n'est pas dans la liste suivante : ["FID", "Shape","FNODE#", "TNODE", "HEDGID"]
        # ici c'est pour la couche arc.
        for fldarc in lfldarc:
            if fldarc.name not in KeepField :
               arcpy.DeleteField_management(arc,fldarc)

        # on cherche à supprimer tous les champs dont le nom n'est pas dans la liste suivante : ["FID", "Shape","FNODE#", "TNODE", "HEDGID"]
        # ici c'est pour la couche node.
        for fldnode in lfldnode:
            if fldnode.name not in KeepField :
               arcpy.DeleteField_management(node,fldnode)

        return output

    except:

        return output

if __name__ == '__main__':

    # -------------------------- User parameters ------------------
    # Variable des points OTX et L
    PointsOTX=arcpy.GetParameterAsText(0)
    PointsL=arcpy.GetParameterAsText(1)

    # Variable Lines
    Lines=arcpy.GetParameterAsText(2)

    # Chemin de sortie de la couverture topologique
    output=arcpy.GetParameterAsText(3)

    # créer la géodatabase :
    join=os.path.join
    dirpath=os.path.dirname(output)
    geodata=os.path.join(dirpath,"tmp.gdb")
    if not arcpy.Exists(geodata): arcpy.CreateFileGDB_management(dirpath,"tmp.gdb")

    # Lancement de la fonction.
    CreateNetWork(Lines, PointsL, PointsOTX, output, geodata)
