# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        ConnectForet
# Purpose:
#
# Author:      lvillier
#
# Created:     22/10/2013
# Copyright:   (c) lvillier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy,os
from arcpy import env
env.overwriteOutput = True


# ----------- User parameters ----------

# Entrée : Axemdian
Network = arcpy.GetParameterAsText(0)
InAxemedian = os.path.join(Network,"arc")
InNode = os.path.join(Network,"node")

# Entrée : Foret
foret = arcpy.GetParameterAsText(1)

# Entrée Facultative : rayon de recherche (double)
# Valeur par défaut
Search_Radius = 0
Search_Radius= eval(arcpy.GetParameterAsText(2))

# Entrée facultive : nombre de candidats
# Valeur par défaut
NbFeature = 0
NbFeature = eval(arcpy.GetParameterAsText(3))

# Sortie : les arcs de connexions avec les haies
OutNetWork = arcpy.GetParameterAsText(4)
OutLine = os.path.join(OutNetWork,"arc")

# Sortie : Les points de connexions avec les haies ou les forêts.
OutPoint = arcpy.GetParameterAsText(5)

def CreatLine(inlpoints, inCenter):
    """
    Créer des arcs entre la liste de points de le point center
    entrée :
           inlpoints : une liste d'objet points.
           incenter : un objet point
    sortie :
           une liste d'objet polyline.
    """
    lPolyline = []
    # on parcours la liste de point
    for points in inlpoints:
        array = arcpy.Array()
        array.add(points.centroid)
        array.add(inCenter.centroid)
        lPolyline.append(arcpy.Polyline(array))
        array.removeAll()
    # retourner le résultat
    return lPolyline

def XYCentroids(inLstPoint):
    """
    Calcul le centroid d'une liste de géométrie de point.
    entrée :
           inLstPoint : liste de point géométrie
    sortie :
           pntC : un objet point
    """
    #initialiser les liste X et Y :
    lgeomX, lgeomY = [], []
    # Contruire l'objet point :
    pntC = arcpy.Point()
    # on parcours la liste de point puis on stocke séparément X et Y:
    for geom in inLstPoint:
        lgeomX.append(geom.centroid.X)
        lgeomY.append(geom.centroid.Y)
    # la somme des éléments de la liste
    xC = sum(lgeomX)/len(lgeomX)
    yC = sum(lgeomY)/len(lgeomY)
    # intancier l'objet point
    pntC.X, pntC.Y = xC, yC
    # retourner la valeur:
    return arcpy.PointGeometry(pntC)

def main():
    """ main program """
    # workspace :
    wrksp, name = os.path.split(InAxemedian)
    env.workspace = wrksp
    # creer le dictionnaire forêt :
    scur = arcpy.SearchCursor(foret)
    dForet = {}
    # on parcours la couche de forêt pour remplir le dictionnaire de donnée:
    arcpy.AddMessage("Construction du dictionnaire de forêt")
    for row in scur:
        geom, pnt = arcpy.Geometry(), arcpy.Point()
        ForetID = row.OBJECTID
        geom = row.Shape
        pnt.X, pnt.Y = geom.trueCentroid.X, geom.trueCentroid.Y
        dForet[ForetID]={"LPoints" : [], "CentroidPnt": arcpy.PointGeometry(pnt)}
    del scur, row, pnt
    arcpy.AddMessage('il y a %s foret.' % len(dForet))

    # Créer la table de proximité :
    arcpy.AddMessage("Génération de la table de proximité")
    arcpy.GenerateNearTable_analysis(InAxemedian,foret,"tableProxi",Search_Radius,"LOCATION", "NO_ANGLE","ALL",NbFeature)
    scur = arcpy.SearchCursor("tableProxi")
    dforet={}
    # parcourir le tableau de proximité
    arcpy.AddMessage("Construction du dictionnaire de la table de proximité")
    for row in scur:
        pnt= arcpy.Point()
        IDArc = row.IN_FID
        IDForet = row.NEAR_FID
        pnt.X,pnt.Y = row.NEAR_X, row.NEAR_Y

        # construction du dictionnaire
        dForet[IDForet]["LPoints"].append(arcpy.PointGeometry(pnt))
    del scur, row

    # On parcours le dictionnaire :
    arcpy.AddMessage("Construction des noeuds et arcs de connexion")
    lpnt, lPolyline = [] , []

    for IdForet in dForet:
        # cas 1 il y a plusieurs haies qui sont connectées à une forêt alors on trace des arcs entre les haies
        # et les points de connexions.
        if len(dForet[IdForet]["LPoints"])>2 :
           # On calcul le point moyen de tous les points
           pnt = XYCentroids(dForet[IdForet]["LPoints"])
           # On créer la liste des arcs de connexion entre le point moyen et les autres points.
           lstline = CreatLine(dForet[IdForet]["LPoints"], pnt)
           # On ajoute à la liste des points et des lignes pour construire ces géométries plus tard.
           lpnt.append(pnt)
           lpnt.extend(dForet[IdForet]["LPoints"])
           lPolyline.extend(lstline)

        # Cas 2 il y a 2 ou 1 connexion avec la forêt. On trace alors l'arcs entre le centroide et les deux autres
        # lignes.
        if len(dForet[IdForet]["LPoints"]) in [1,2]:
           # prendre le centroide de la forêt :
           centroid = dForet[IdForet]["CentroidPnt"]
           # Créer les lignes :
           lstline = CreatLine(dForet[IdForet]["LPoints"], centroid)
           # On ajoute à la liste des points et des lignes pour construire ces géométries plus tard.
           lpnt.append(centroid)
           lpnt.extend(dForet[IdForet]["LPoints"])
           lPolyline.extend(lstline)

    # soustraction avec les points du réseau en entrée et les nouveaux points du réseau.
    arcpy.Erase_analysis(InNode,lpnt,"NodeErase")
    arcpy.AddField_management("NodeErase", "TypeNode","TEXT", "20")
    arcpy.CalculateField_management("NodeErase","TypeNode","'OTHER'","PYTHON")

    # créer l'entité pour insérer le champ forêt.
    arcpy.CopyFeatures_management(lpnt,"Foret")
    # créer le champ correspondant :
    arcpy.AddField_management("Foret","TypeNode", "TEXT", "20")
    arcpy.CalculateField_management("Foret", "TypeNode", "'Foret'", "PYTHON")

    # combiner lpnt et NodeErase:
    arcpy.Merge_management(["Foret","NodeErase"],"pnts")


    # Récupérer le point d'intersection :
    arcpy.FeatureclassToCoverage_conversion([lPolyline,"pnts"],OutNetWork)

if __name__ == '__main__':
    main()
