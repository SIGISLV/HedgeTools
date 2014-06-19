# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        PointL
# Purpose:     A tool to create L node from median line with an specify angle.
#
#
# Author:      Villierme Lewis
#
# Created:     21/05/2013
# Copyright:   (c) lvillierme 2013
# Licence:     BSD
#-------------------------------------------------------------------------------

# ----------  import des bibliothèques --------
import arcpy
from arcpy import env
env.overwriteOutput=True
import os
import sys


def Azimut(InPoint1,InPoint2):
    """ Calculate azimut of a couple of points"""
    import math
    # on test les entrées de la fonctions si c'est un objet point ou si c'est une liste.
    if type(InPoint1)==arcpy.Point() and type(Inpoint2)==arcpy.Point():
       orient = math.atan2(InPoint2.X-InPoint1.X, InPoint2.Y-InPoint1.Y)*(180/math.pi)
    if type(InPoint1)==list and type(InPoint2)==list :
       orient = math.atan2(InPoint2[0]-InPoint1[0], InPoint2[1]-InPoint1[1])*(180/math.pi)
    if orient<0:
        orient+=360
    return orient

def AngleEdges(InNodePoint, InEdges1, InEdges2):
    """Calculate angle of edges from node and edges points. It returns the angle form by the
    non common points of the edges 1 and 2.
    InNodePoint : [X,Y]
    InEdges1 and 2 : [[X,Y],[X,Y]]
    Results : [X,Y],[X,Y]"""

    # On Cherche la position du couple de coordonnée de points communs.
    Index1, Index2=InEdges1.index(InNodePoint), InEdges2.index(InNodePoint)

    # On cherche l'indice des coordonnées qui ne sont pas communs. Ne pas utiliser un pop car il enlèverait aussi dans le dictionnaire.
    if Index1==0 : index10=1
    else : index10=0
    if Index2==0 : index20=1
    else : index20=0

    # On calcule l'orientation de chacune d'entre elle.
    AziEdge1, AziEdge2 = Azimut(InNodePoint,InEdges1[index10]), Azimut(InNodePoint, InEdges2[index20])

    # On choisit l'angle le plus faible
    if AziEdge2 > AziEdge1 :
       b2, b1 = AziEdge1, AziEdge2
    elif AziEdge1 > AziEdge2 :
       b2, b1 = AziEdge2, AziEdge1

    # on calcul l'angle formé par les 2 arrêtes
    angle = b1 - b2
    if angle>180 : angle=abs(angle-360)

    # on retourne l'angle :
    return angle


def FindEdges(InEdge,InNode):
    """ Finds FROM and TO edges of a L node. It returns a dictionnary of a node angle."""

    # on travail maintenant sur les edges :
    # dénition du curseur pour les arretes
    scur = arcpy.SearchCursor(InEdge)
    # on met dans une liste les noms des champs pour chercher le FNODE et TNODE
    lfields = arcpy.ListFields(InEdge)

    # On parcours la liste des nom de champ pour trouver le FNODE et TNODE
    FNODE=lfields[3].name
    TNODE = lfields[4].name

    # on initialise un dictionnaire
    dEdge, FTnodeList = dict(), list()

    # dans le curseur de edge on cherche les noeuds qui composent ce le edge.
    for row in scur:
        # Création d'une liste de tous les occurences des noeuds
        FTnodeList.append(row.getValue(TNODE))
        FTnodeList.append(row.getValue(FNODE))
        # on charge les  :
        g = arcpy.Geometry()
        g = row.Shape
        # on remplit le dictionnaire de edge
        dEdge[row.getValue("FID")] = {"lNodeTF" : [row.getValue(TNODE), row.getValue(FNODE)], "Points": [[round(g.firstPoint.X,0),round(g.firstPoint.Y,0)],[round(g.lastPoint.X,0),round(g.lastPoint.Y,0)]], "length" : g.length}
    # On efface les curseurs pour enlever les verroux
    del row, scur

    # On initialise la liste des node qui sera remplit dans le curseur de recherche
    lNode , dNode = [], dict()
    # définition du curseur de recherche pour les noeuds
    scur = arcpy.SearchCursor(InNode)
    # Boucle sur le curseur :
    for row in scur:
        # idNode est l'identifiant du noeud
        idNode = row.FID
        # on remplit la liste des noeuds
        lNode.append(idNode)
        # On teste le noeud pour avoir uniquement les noeuds qui apparaissent 2 fois.
        if FTnodeList.count(idNode)==2:
           # on initailise la liste des edges :
           ledge, lPoints= [],[]
           # on cherche les 2 arcs associés:
           for edge in dEdge:
               if idNode in dEdge[edge]["lNodeTF"]:
                  coord = dEdge[edge]["Points"]
                  ledge.append(edge)
                  lPoints.append(coord)
               if len(ledge)==2 : break
           # on récupère la géométrie
           g=arcpy.Geometry()
           g=row.Shape
           # on calcul le
           X,Y = round(g.firstPoint.X,0),round(g.firstPoint.Y,0)
           # On calcule l'angle
           Angle = AngleEdges([X,Y], lPoints[0], lPoints[1])
           # on fabrique le dictionnaire de dNode avec les thèmes vides
           dNode[idNode]={"edges":ledge, "XY":[X,Y] ,"angle":Angle}

    # on retourne le dictionnaire :
    return dNode



#------ Geotraitements -------
def MakeLnode(medianaxe,output, UserAngle):
    # on récupère le nom de l'entité en sortie.
    directory, name = os.path.split(output)

    dirpath = os.path.dirname(directory)
    geodata=os.path.join(dirpath,"tmp.gdb")
    if not arcpy.Exists(geodata):arcpy.CreateFileGDB_management(dirpath,"tmp.gdb")
    arcpy.env.workspace=geodata
    arcpy.env.overwriteOutput = True

    # Diviser les lignes
    arcpy.SplitLine_management(medianaxe,"lineSplit")

    # Create Both-ENDS points.
    arcpy.FeatureVerticesToPoints_management("lineSplit","PotenL","BOTH_ENDS")

    # construct the InFeature variables.
    Infeature = ["lineSplit","PotenL"]

    # ------ Make the dictionary for potential L node with associate arcs.
    coverage= os.path.join(dirpath,"coverage2")
    arcpy.FeatureclassToCoverage_conversion(Infeature,coverage)

    # create path of arcs and node.
    arcs, nodes = os.path.join(coverage,"arc"), os.path.join(coverage,"node")

    # Launch the FindEges function.
    dNode = FindEdges(arcs,nodes)

    # create a list of geometry
    lPointL = []

    # Filtering the angle with the user parameter.
    for node in dNode:
        if dNode[node]["angle"]<UserAngle:
           X, Y = dNode[node]["XY"][0], dNode[node]["XY"][1]
           point = arcpy.Point()
           point.X, point.Y = X, Y
           pointGeom = arcpy.PointGeometry(point)
           lPointL.append(pointGeom)

    # Create the shape.
    SpatialRef = arcpy.Describe(lpointL).spatialReference.exporttostring()
    arcpy.CopyFeatures_management(lPointL,output,"",SpatialRef)

    # retourne le résultat :
    return output


if __name__=="__main__":
   # ----- Environnement -------

    # Variable medianaxe
    medianaxe=arcpy.GetParameterAsText(0)

    # Variable output
    output=arcpy.GetParameterAsText(1)

    # angle in degree for creating L node
    UserAngle=arcpy.GetParameter(2)

    # si on lance l'outil en principale
    MakeLnode(medianaxe,output,UserAngle)
