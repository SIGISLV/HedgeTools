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

    # lance la fonctionne
    AxeMed1 = __Thin__(raster, pdTAILLEARCPENDANT, os.path.join(geodata,"AxeMed1"))

    # on lance un buffer de 1m pour éliminer les malformations chose biscornues
    Axe1Buff = os.path.join(geodata, "BufferAxemed1")
    arcpy.Buffer_analysis(AxeMed1, Axe1Buff, 1,"","","ALL")

    # On relance les dernières opérations
    raster=os.path.join(geodata,"raster2")
    listFld = arcpy.ListFields(Axe1Buff)
    arcpy.FeatureToRaster_conversion(Axe1Buff,listFld[0].name,raster,pdTAILLEPIXEL)
    __Thin__(raster,pdTAILLEARCPENDANT, output)

    # simplification de la classe en sortie
    # arcpy.Generalize_edit(output,pdTAILLEPIXEL)
    arcpy.ExtendLine_edit(output,0.5)

    # retourner l'entité
    return output

def __Thin__(raster,pdTAILLEARCPENDANT, thinFC):
    # on utilise l'outils fines. il faut checkout l'extension sinon ca ne marche pas.
    from arcpy.sa import Thin
    arcpy.CheckOutExtension("Spatial")
    Fine=Thin(raster,"","","",pdTAILLEARCPENDANT)

    # on transforme en ligne.
    arcpy.RasterToPolyline_conversion(Fine,thinFC,"",pdTAILLEARCPENDANT,"SIMPLIFY")
    arcpy.Delete_management(Fine)

    # on retourne le résultat :
    return thinFC

if __name__ == "__main__":

    # on récupère les variables :
    polyhaie=arcpy.GetParameterAsText(0)
    sortie=arcpy.GetParameterAsText(1)
    TAILLEPIXEL=arcpy.GetParameter(2) # taille du pixel pour la rasterisation de la carte.
    TAILLEARCPENDANT=arcpy.GetParameter(3) # taille des arcs pendants.

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