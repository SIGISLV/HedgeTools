# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        CreateMedianAxe

# Purpose:     Permet de calculer un axe median à partir d'un polygone bois/non bois
#
# Author:      Villierme Lewis
#
# Created:     30/05/2013
# Copyright:   (c) lvillier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, os
from arcpy import env
env.overwriteOutput=True

# la fonction medianaxe
def MakeMedianAxe(pdPolyhaie, geodata, pdTAILLEPIXEL, pdTAILLEARCPENDANT,output):
    """
    Cette fonction calcule un axe médian en utilisant la fonction fines.
    entrées :
        pdPolyhaie :
    """

    # il faut transformer en raster.
    raster=os.path.join(geodata,"raster")
    if arcpy.Exists(raster):arcpy.Delete_management(raster)
    listFld = arcpy.ListFields(pdPolyhaie)
    arcpy.FeatureToRaster_conversion(pdPolyhaie,listFld[0].name,raster,pdTAILLEPIXEL)

    # on utilise l'outils fines. il faut checkout l'extension sinon ca ne marche pas.
    from arcpy.sa import Thin
    arcpy.CheckOutExtension("Spatial")
    Fine=Thin(raster,"","","",pdTAILLEARCPENDANT)
    del Thin

    # on transforme en ligne.
    arcpy.RasterToPolyline_conversion(Fine,output,"",pdTAILLEARCPENDANT,"SIMPLIFY")
    arcpy.Delete_management(Fine)

    # retourner l'entité
    return output


if __name__ == "__main__":

    # on récupère les variables :
    polyhaie=arcpy.GetParameterAsText(0)
    sortie=arcpy.GetParameterAsText(1)
    TAILLEPIXEL=arcpy.GetParameter(2) # taille du pixel pour la rasterisation de la carte.
    TAILLEARCPENDANT=arcpy.GetParameter(3) # taille des arcs pendants.

    """
    polyhaie=r'C:\Users\Villierme\Documents\ArcGIS\Default.gdb\RasterT_haieRas1'
    sortie=r'C:\Users\Villierme\Documents\ArcGIS\Default.gdb\RasterT_MedianAxis'
    TAILLEPIXEL=1
    TAILLEARCPENDANT=30
    """
    # import les outils d'aide
    import HelperTool as ht
    geodata = ht.getScratchWorkspace(sortie)

    """
    # on définit les chemins et le système de projection :
    chemin , nom =os.path.split(sortie)
    spatialref=arcpy.Describe(polyhaie).spatialReference
    """
    # Appel de la fonction :
    MakeMedianAxe(polyhaie, geodata, TAILLEPIXEL, TAILLEARCPENDANT, sortie)

    del os, arcpy, env