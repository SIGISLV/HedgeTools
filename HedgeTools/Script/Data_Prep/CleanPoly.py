# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        CleanPoly

# Purpose:     Nettoie les polygones pour calculer l'axe médian.
#
# Author:      Villierme Lewis
#
# Created:     30/05/2013
# Copyright:   (c) lvillier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, sys
from arcpy import env
import os
join=os.path.join

env.overwriteOutput=True


# la fonction CleanPoly
def CleanPoly(InPolyhaie,TAILLEPOLY,DISTBUFFER,InSortie,InGeodata):
    """
    Simplifie les polygones : généralisation par une érosion dilatation de la même
    distance avant et après une suppression des polygones intérieures (donuts).
    entrées :
            polyhaie : emprise de la haie originelle
            TAILLEPOLY : Superficie du polygon en unité de carte selon la projection.
            DISTBUFFER :  distance utilisé pour la dialatation et l'érosion.
            sortie : la classe d'entité en sortie.
            InGeodata : geodatbase de travail temporaire pour les fichier de transition.
    """

    arcpy.env.workspace=InGeodata

    # on rempli les trous du polygone:
    polyplein=join(InGeodata,"polyplein")
    arcpy.AddMessage("Eliminate contained polygon ...")
    arcpy.EliminatePolygonPart_management(InPolyhaie, polyplein, "AREA", TAILLEPOLY , "", "CONTAINED_ONLY")

    # il faut simplifier la couche de polygone.
    Dilat=join(InGeodata,"Dilat")
    Erodil=join(InGeodata,"Erodil")

    # Dilatation
    arcpy.AddMessage("Performing dilatation ...")
    arcpy.Buffer_analysis(polyplein,Dilat,DISTBUFFER,"","","ALL")

    # Erosion
    arcpy.AddMessage("Performing erosion ...")
    arcpy.Buffer_analysis(Dilat,Erodil,-DISTBUFFER,"","","ALL")

    # remplir les trous du polygones dilaté.
    dilateplein=join(InGeodata,"dilateplein")
    arcpy.AddMessage("Eliminate contained polygon ...")
    arcpy.EliminatePolygonPart_management(Erodil, InSortie, "AREA", TAILLEPOLY , "", "CONTAINED_ONLY")

    # retourner le fichier en sortie:
    return sortie

                                            #***********************
                                            #  fin de la fonction  *
                                            #***********************

# Appel de la fonction :
if __name__ == "__main__":
    """
    # local variables :
    polyhaie=r'H:\5_STAGE\indicateurs\ACaract_Obj\CNature_fonc\AData_source\Fonction.gdb\Bois_Test'
    sortie=r'H:\5_STAGE\indicateurs\ACaract_Obj\AMorpho2D\Data_source\Source_data.gdb'
    """
    # on récupère les variables :
    polyhaie=arcpy.GetParameterAsText(0)
    TAILLEPOLY=arcpy.GetParameter(1)# surface des polgones qui seront enlevées
    DISTBUFFER=arcpy.GetParameter(2) # distance du buffer qui sera mis en place
    sortie=arcpy.GetParameterAsText(3) # le de sortie de l'entité.

    # on définit les chemins et le système de projection :
    chemin , nom =os.path.split(sortie)
    spatialref=arcpy.Describe(polyhaie).spatialReference

    # Paramètres environnement
    import os
    # créer la géodatabase :
    join=os.path.join
    dirpath=os.path.dirname(chemin)
    geodata=os.path.join(dirpath,"tmp.gdb")
    if not arcpy.Exists(geodata): arcpy.CreateFileGDB_management(dirpath,"tmp.gdb")

    # Set the function :
    outClean = CleanPoly(polyhaie,TAILLEPOLY,DISTBUFFER,sortie,geodata)

    # Delete unwanted fields.
    flist = arcpy.ListFields(outClean)
    for field in flist[2:]:
        arcpy.DeleteField_management(outClean, field.name)

