# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        OrientPente
# Purpose:      Cherche l'orientation générale d'une pente par échantillonnage
#               (buffer). Le rayon de recherche sera préciser par l'uitlisateur.
#               Une fois l'orientation générale obtenue on la compare avec l'azimut
#               soit de de l'arc d'une haie, soit du vecteur de la haie.
#
# Author:      Villierme
#
# Created:     18/07/2013
# Copyright:   (c) Villierme 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# import des bibliothèque :
import arcpy, os
from arcpy import env

# paramètre utilisateur :
axemedian = arcpy.GetParameterAsText(0)
champID = arcpy.GetParameterAsText(1)
mnt = arcpy.GetParameterAsText(2)
searchradius = arcpy.GetParameterAsText(3)
NbClasses = arcpy.GetParameterAsText(4)
outputaxemedian = arcpy.GetParameterAsText(5)
workspace = arcpy.GetParameterAsText(6)

# définition de l'environnement de travail :
env.workspace = workspace
env.overwriteOutput = True
# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

# les fonctions utiles :
def orientation(firstpoint, lastpoint):
    import math
    angle = math.atan2(lastpoint.X - firstpoint.X, lastpoint.Y - firstpoint.Y) * (180/math.pi)
    if angle<0:
        angle += 360
    return angle

def AxeToDict(pdaxe, pdIdfield,pdNbClasse):
    # fonction qui transforme l'axe en un dictionnaire
    scur , d = arcpy.SearchCursor(pdaxe) , {}
    for row in scur:
        idf = row.getValue(pdIdfield)
        g = arcpy.Geometry()
        g = row.Shape
        azimut = orientation(g.firstPoint, g.lastPoint)
        if pdNbClasse==4:
            d[idf] = {"Azimut": azimut, "PenteGenerale":0., "Plat": 0., "Orientation" : {
                                                            "45" : 0.,
                                                            "135" : 0.,
                                                            "225" : 0.,
                                                            "315" : 0.
                                                                        }}
        if pdNbClasse==8:
            d[idf] = {"Azimut": azimut, "PenteGenerale":0., "Plat": 0., "Orientation" : {
                                                            "22" : 0.,
                                                            "67" : 0.,
                                                            "112" : 0.,
                                                            "157" : 0.,
                                                            "202" : 0.,
                                                            "247" : 0.,
                                                            "292" : 0.,
                                                            "337" : 0.
                                                                        }}

    # il faut en le ver les véroux.
    del row, scur

    return d

# Calculer l'expostion à partir du mnt :
from arcpy.sa import Aspect
mnt = mnt.encode('utf8')
outAspect = Aspect(mnt)
exposition = os.path.join(workspace,"exposition")
outAspect.save(exposition)

# Reclasser l'exposition : en fonction du nombre de classes en entrée.
if NbClasses=="4":
    b1, b2, b3, b4 = 90,180,270,360
    classes = "%s %s 45;%s %s 135;%s %s 225; %s %s 315" %(0,b1,b1,b2,b2,b3,b3,b4)

if NbClasses=="8":
    b1, b2, b3, b4, b5, b6, b7, b8 = 45,90,135,180,225,270,315,360
    classes = "%s %s 22;%s %s 67;%s %s 112; %s %s 157;%s %s 202;%s %s 247;%s %s 292; %s %s 337" %(0,b1,b1,b2,b2,b3,b3,b4,b4,b5,b5,b6,b6,b7,b7,b8)

arcpy.gp.Reclassify_sa(exposition, "Value", classes, "OrientReclass", "DATA")

# Vectoriser le raster reclasser :
arcpy.RasterToPolygon_conversion("OrientReclass", "PolyExpo", "NO_SIMPLIFY", "VALUE")

# Travail sur le réseau de haie


# on fait les buffeurs :
# les buffeurs prennent l'identifiant de l'axe. On va se basé dessus.
# version simple (sans split)
buffaxe = "buffaxe"
arcpy.Buffer_analysis(axemedian, buffaxe, eval(searchradius),"","FLAT")

""" version avec split :

# fractionner l'axe médian aux sommets
arcpy.SplitLine_management(axemedian,"AxeSplit")
buffaxesplit = "buffaxesplit"
arcpy.Buffer_analysis("AxeSplit", buffaxesplit , searchradius, "","FLAT")
# on execute un découpage puis une identification
arcpy.Clip_analysis("PolyExpo", buffaxesplit, "PolyExpoClip")
arcpy.Identity_analysis("PolyExpoClip", buffaxesplit, "ExpoIdentity")
"""
# on execute un découpage puis une identification
arcpy.Clip_analysis("PolyExpo", buffaxe, "PolyExpoClip")
arcpy.Identity_analysis("PolyExpoClip", buffaxe, "ExpoIdentity")

# on construit le dictionnaire de l'axe médian :
dAxeMedian=AxeToDict(axemedian,champID,int(NbClasses))

# on parcours la couche ExpoIdentity :
scur = arcpy.SearchCursor("ExpoIdentity")

# on se préviens le l'encodage d'arcgis qui rajoute un u'
axemedian=axemedian.encode('utf8')

# on définit les identifiants pour le groupement les résultats par buffer
# et par orientation
namelayer = os.path.basename(axemedian)
OrientAngle, IdField = "grid_code", champID

for row in scur :
    # on récupère les données de chaque ligne
    surface = row.Shape_Area
    IdAxe= row.getValue(IdField)
    anglePente = str(row.getValue(OrientAngle))

    # on fait appel au dictionnaire de l'axe médian et on addition les surface entre elles
    if anglePente=="32767" or  anglePente=="-32768" or anglePente=="-1" or anglePente=="1": dAxeMedian[IdAxe]["Plat"]+=surface
    else : dAxeMedian[IdAxe]["Orientation"][anglePente]+=surface
del row, scur

# on reparours les dictionnaire pour connaitre la surface la plus importante des angles
# on récupère l'angle générale de cette surface que l'on donne à la valeur Pente Générale

for axe in dAxeMedian:
    Orient, lSurface = dAxeMedian[axe]["Orientation"], []
    SurfTop = 0
    # on récpère dans une liste les valeurs de surface :
    for angle in Orient.keys():
        SAngle = Orient[angle]
        # on cherche l'angle avec la surface la plus importante :
        if SurfTop < SAngle :
            SurfTop = SAngle
            TopAngle = eval(angle)
    # on met en place la condition et on remplit l'attribut Pente Générale
    dAxeMedian[axe]["PenteGenerale"] = TopAngle

# on fait une copie de la table axemedian et on la met à jour :
arcpy.CopyFeatures_management(axemedian,outputaxemedian)

# on ajoute un champ angle_compare :
arcpy.AddField_management(outputaxemedian,"PenteOrient", "DOUBLE")

# on met à jour la table copié de l'axe médian
ucur = arcpy.UpdateCursor(outputaxemedian)

for row in ucur:
    # on récupère le champ identifiant
    idField = row.getValue(champID)
    # on récupère l'angle de la pente la plus importante en surface
    AnglePenteGenerale = dAxeMedian[idField]["PenteGenerale"]
    # on récupère l'azimut de l'axe
    AngleAxe = dAxeMedian[idField]["Azimut"]
    # on effectue l'opération de soustraction
    if NbClasses == "4": AngleCompare = AngleAxe-AnglePenteGenerale
    if NbClasses == "8": AngleCompare = AngleAxe-AnglePenteGenerale+0.5
    if AngleCompare<0 : AngleCompare+=360
    # on met à jour le champ PenteOrient crée plus haut
    row.setValue("PenteOrient", AngleCompare)
    # commande importante pour une mise à jour.
    ucur.updateRow(row)

del row, ucur