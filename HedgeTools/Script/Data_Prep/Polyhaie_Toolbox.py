#-------------------------------------------------------------------------------
# Name:        Polyhaid
# Purpose:      Permet de découpé l'emprise des haie pour obtenir une emprise découpé
#               et identifiée. l'emprise est identifiée à partir de l'axe médian qui
#               doit être au préalable identifié.
#
# Author:      Villierme
#
# Created:     19/06/2013
# Copyright:   (c) Villierme 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy
import os
from arcpy import env

env.overwriteOutput=True

axehaie=arcpy.GetParameterAsText(0)
champID =arcpy.GetParameterAsText(1)
poly=arcpy.GetParameterAsText(2)
output=arcpy.GetParameterAsText(3)

chemin, nom = os.path.split(output)

InGdb = True
# on test si on est dans une géodatabase:
filename, fileExtension = os.path.splitext(chemin)
if len(fileExtension)<1: InGdb = False

spatialreference=arcpy.Describe(axehaie).SpatialReference

# on instancie un objet Geometry
geom=arcpy.Geometry()
lbuff=arcpy.Buffer_analysis(axehaie,geom,15,"","FLAT")

dbuff  = {}
scur = arcpy.SearchCursor(axehaie)
for row in scur:
    for buff in lbuff :
            if row.Shape.within(buff):
                dbuff[row.getValue(champID)]={"geometrie":buff }
                break
del row, scur

lgeom=[]

for buff in dbuff:
    g, gclip  = arcpy.Geometry(), arcpy.Geometry()
    gclip=dbuff[buff]["geometrie"]
    clipg = arcpy.Clip_analysis(poly,gclip,g)
    for l in clipg :
        lgeom.append(l)

NPolyT = "polytemp"
NPolyToLine = "polytoline"
NLineTopoly = "lineToPoly"

# copie
if not InGdb:
    NPolyT = "polytemp.shp"
    NPolyToLine = "polytoline.shp"
    NLineTopoly = "lineToPoly.shp"


polytemp=os.path.join(chemin,NPolyT)
arcpy.CopyFeatures_management(lgeom,polytemp)

polytoline=os.path.join(chemin,NPolyToLine)
arcpy.FeatureToLine_management(polytemp,polytoline)

lineToPoly=os.path.join(chemin,NLineTopoly)
arcpy.FeatureToPolygon_management(polytoline,lineToPoly)

# effacer les entités intermédiaire :
for entite in [polytemp,polytoline]:
    arcpy.Delete_management(entite)

arcpy.DefineProjection_management(lineToPoly,spatialreference)

# on identifie les géométrie :
arcpy.AddField_management(lineToPoly, "HEDGEID", "LONG")
ucur=arcpy.UpdateCursor(lineToPoly)

for row in ucur:
    for buff in dbuff:
        if dbuff[buff]["geometrie"].contains(row.shape):
            row.setValue("HEDGEID", buff)
            ucur.updateRow(row)
            break
del row, ucur

polyhaid=os.path.join(chemin,nom)
arcpy.Dissolve_management(lineToPoly,polyhaid,"HEDGEID")
