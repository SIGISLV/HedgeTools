# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Axemedian

# Purpose:     Permet de calculer un axe median à partir d'un polygone bois/non bois
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
join=os.path.join

env.overwriteOutput=True

"""
polyhaie=r'H:\5_STAGE\indicateurs\ACaract_Obj\CNature_fonc\AData_source\Fonction.gdb\Bois_Test'
sortie=r'H:\5_STAGE\indicateurs\ACaract_Obj\AMorpho2D\Data_source\Source_data.gdb'
"""
# on récupère les variables :
polyhaie=arcpy.GetParameterAsText(0)
sortie=arcpy.GetParameterAsText(1)
TAILLEPOLY=int(arcpy.GetParameterAsText(2)) # surface des polgones qui seront enlevées
DISTBUFFER=int(arcpy.GetParameterAsText(3)) # distance du buffer qui sera mis en place
TAILLEPIXEL=int(arcpy.GetParameterAsText(4)) # taille du pixel pour la rasterisation de la carte.
TAILLEARCPENDANT=int(arcpy.GetParameterAsText(5)) # taille des arcs pendants.
TOLERANCEGENE=int(arcpy.GetParameterAsText(6)) # Tolérance pour la simplification des lignes.

# on définit les chemins et le système de projection :
chemin , nom =os.path.split(sortie)
spatialref=arcpy.Describe(polyhaie).spatialReference

# la fonction medianaxe
def medianaxe(pdPolyhaie, pdchemin, pdTAILLEPOLY, pdDISTBUFFER, pdTAILLEPIXEL, pdTAILLEARCPENDANT, pdTOLERANCEGENE, pdnom):

    import os
    join=os.path.join

    dirpath=os.path.dirname(pdchemin)
    geodata=os.path.join(dirpath,"axemedian.gdb")
    if arcpy.Exists(geodata):arcpy.Delete_management(geodata)
    arcpy.CreateFileGDB_management(dirpath,"axemedian.gdb")

    # on rempli les trous du polygone:
    polyplein=join(geodata,"polyplein")
    if arcpy.Exists(polyplein):arcpy.Delete_management(polyplein)
    arcpy.EliminatePolygonPart_management(pdPolyhaie, polyplein, "AREA", pdTAILLEPOLY , "", "CONTAINED_ONLY")

    # on fait une copie de la couches.
    copypolyhaie=join(geodata,"copypolyhaie")
    if arcpy.Exists(copypolyhaie):arcpy.Delete_management(copypolyhaie)
    arcpy.CopyFeatures_management(polyplein,copypolyhaie)

    # il faut simplifier la couche de polygone.
    Dilat=join(geodata,"Dilat")
    Erodil=join(geodata,"Erodil")
    arcpy.Buffer_analysis(copypolyhaie,Dilat,pdDISTBUFFER,"","","ALL")
    arcpy.Generalize_edit(Dilat, 6)
    arcpy.Buffer_analysis(Dilat,Erodil,-pdDISTBUFFER,"","","ALL")


    # remplir les trous du polygones dilaté.
    dilateplein=join(geodata,"dilateplein")
    arcpy.EliminatePolygonPart_management(Erodil, dilateplein, "AREA", pdTAILLEPOLY , "", "CONTAINED_ONLY")

    # il faut transformer en raster.
    raster=join(geodata,"raster")
    if arcpy.Exists(raster):arcpy.Delete_management(raster)
    arcpy.FeatureToRaster_conversion(dilateplein,"OBJECTID",raster,pdTAILLEPIXEL)

    # on utilise l'outils fines. il faut checkout l'extension sinon ca ne marche pas.
    from arcpy.sa import Thin
    arcpy.CheckOutExtension("Spatial")
    Fine=Thin(raster,"","","",pdTAILLEARCPENDANT)
    del Thin

    # on transforme en ligne.
    templine=join(pdchemin,pdnom)
    arcpy.RasterToPolyline_conversion(Fine,templine,"",pdTAILLEARCPENDANT,"SIMPLIFY")
    arcpy.Delete_management(Fine)
    arcpy.TrimLine_edit(templine,pdTAILLEARCPENDANT)
    arcpy.Delete_management(geodata)

                                            #***********************
                                            #  fin de la fonction  *
                                            #***********************

# Appel de la fonction :
medianaxe(polyhaie, chemin, TAILLEPOLY, DISTBUFFER, TAILLEPIXEL, TAILLEARCPENDANT, TOLERANCEGENE, nom)

del os, arcpy, env