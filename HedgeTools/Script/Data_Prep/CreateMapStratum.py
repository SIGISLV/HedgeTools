#-------------------------------------------------------------------------------
# Name:        CreateMapStratum
# Purpose:     Create a map of different stratum.
#
#
# Author:      Villierme Lewis
#
# Created:     21/05/2013
# Copyright:   (c) lvillierme 2013
# Licence:     BSD
#-------------------------------------------------------------------------------

# ----------  import des bibliothèques --------
import arcpy, os, sys
from arcpy import env
from arcpy.sa import ExtractByMask, Reclassify, RemapRange
arcpy.CheckOutExtension('Spatial')

def TextToRemap(txt):
    file=open(txt,"r")
    l=[]
    for line in file:
        line = line.rstrip("\n")
        cl , val = line.split(":")
        b1, b2 = cl.split("-")
        if len(val)>0: val
        l.append([int(b1), int(b2), int(val)])
    # Create the remap object
    rmap = RemapRange(l)
    return rmap

def CreateMapStratum(mnh, emprise, TextRemap, idfield, outputFC, geodata):

    # Définir l'environnement de travail
    arcpy.env.workspace = geodata
    arcpy.env.overwriteOutput = True
    disp = arcpy.AddMessage

    # Extraire par le masque
    disp("Ectracting MNH ...")
    pathOutExtract = os.path.join(geodata,"OutExtract")
    OutExtract = ExtractByMask(mnh, emprise)
    OutExtract.save(pathOutExtract)

    # Reclassement
    disp("Reclassing ...")
    remap = TextToRemap(TextRemap)
    pathOutReclass = os.path.join(geodata,"Reclass")
    OutReclass = Reclassify(pathOutExtract,"Value", remap)
    OutReclass.save(pathOutReclass)

    # Convertir en polygon
    disp("Vectorisating ...")
    arcpy.RasterToPolygon_conversion(pathOutReclass, "PolyRaster")

    # clip
    arcpy.Clip_analysis("PolyRaster", emprise, "PolyRaster_Clip")

    # identity
    arcpy.Identity_analysis("PolyRaster_Clip", emprise, "PolyRaster_Ident")

    # Dissolve
    disp("Dissolving ...")
    dissolveFileds =[idfield, "grid_code"]
    arcpy.Dissolve_management("PolyRaster_Ident", outputFC, dissolveFileds)

    # supprimer le champ grid_code
    arcpy.AddField_management(outputFC,"Strate", "SHORT")
    arcpy.CalculateField_management(outputFC, "Strate", "!grid_code!","PYTHON")
    lfields = arcpy.ListFields(outputFC)
    arcpy.DeleteField_management(outputFC,"grid_code")


    # retourner le résultat :
    return outputFC

if __name__=="__main__":
    mnh = arcpy.GetParameterAsText(0) # MNH (Raster)
    emprise = arcpy.GetParameterAsText(1) # Emprise du réseau
    idfield = arcpy.GetParameterAsText(2)
    txtrmap = arcpy.GetParameterAsText(3) # Reclassement
    outputFC = arcpy.GetParameterAsText(4) # Sortie de l'outil

    # Rechercher un endroit pour stocker les entités transitoires
    geodata, name = os.path.split(outputFC)

    # lancer la fonction CreateMapStratum
    CreateMapStratum(mnh, emprise, txtrmap, idfield, outputFC, geodata)