#-------------------------------------------------------------------------------
# Name:        CreateIdentifiedPolygon
# Purpose:
#
# Author:      Villierme
#
# Created:     12/06/2014
# Copyright:   (c) Villierme 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy,os
from arcpy import env
from PointOTX import MakeNodes

env.overwriteOutput = True
lnodeExist = False

def ToGraph(InEdge,InNode):
    """Fonction qui creera le graph"""
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
        # on fabrique le dictionnaire de dNode avec les thèmes vides
        dNode[idNode]={"edge":[], "NeigboresNode":[]}
    # on efface les curseurs pour retirer les verroux
    del row, scur

    # on travail maintenant sur les edges :
    # dénition du curseur pour les arretes
    scur = arcpy.SearchCursor(InEdge)
    # on met dans une liste les noms des champs pour chercher le FNODE et TNODE
    lfields = arcpy.ListFields(InEdge)

    # On parcours la liste des nom de champ pour trouver le FNODE et TNODE
    for fields in lfields:
        if "FNODE" in fields.name : FNODE=fields.name
        if "TNODE" in fields.name : TNODE = fields.name

    # on initialise un dictionnaire
    dEdge = dict()
    # dans le curseur de edge on cherche les noeuds qui composent ce le edge.
    for row in scur:
        # on cherche à connaitre la distance d'un arc :
        g = arcpy.Geometry()
        g = row.Shape
        # on remplit le dictionnaire de edge
        dEdge[row.getValue("FID")] = {"lnodeEdge" : [row.getValue(TNODE), row.getValue(FNODE)], "length" : g.length}
    del scur
    # dans la liste de neouds que l'on parcours on va chercher les edges qui sont
    # reliés au noeud qui est analysé.
    for node in lNode:
        # on a pris un noeud dans la liste de noeud.
        for edge in dEdge:
            # on parcours le dictionnaire des edges pour chercher les edges qui sont reliés aux point que l'on analyse.
            if node in dEdge[edge]["lnodeEdge"]:
                # si le node se trouve dans la liste des noeuds de l'edge on l'ajoute dans son thème "edges"
                dNode[node]["edge"].append(edge)
                # ici on cherche les neouds qui sont sont voisin du noeud que l'on analyse.
                lnodeEdge = dEdge[edge]["lnodeEdge"]
                # dans cette boucle on cherche les noeuds voisins.
                for nodeEdge in lnodeEdge:
                    # on ajoute le neoud si ce dernier n'est égale au noeud que l'on analyse et n'est pas dans la liste
                    if nodeEdge != node and nodeEdge not in dNode[node]["NeigboresNode"] : dNode[node]["NeigboresNode"].append(nodeEdge)

    # il faut maintenant indiquer les noeuds voisins de chaque neouds pour obtenir le GRAPH

    # on initialise le GRAPH :
    graph = dict()

    for node in dNode:
        lNodeNeigbores = dNode[node]["NeigboresNode"]
        graph[node]=lNodeNeigbores

    return graph, lNode, dEdge, dNode

def DefineNodeType(WrkDir, InLine, ext):
    """
    Retourne la classe d'entité de neouds avec l'identification du type de connexion.
    InLine : classe d'entité de ligne
    """
    # on créer les points à partir des lignes:
    InPoints = os.path.join(WrkDir, "Points")
    if arcpy.Exists(InPoints):arcpy.Delete_management(InPoints)

    arcpy.FeatureVerticesToPoints_management(InLine, InPoints)

    # on créer un coverage :
    path, gdb = os.path.split(WrkDir)
    coverage = os.path.join(path,"TmpCover")
    if arcpy.Exists(coverage):arcpy.Delete_management(coverage)

    arcpy.FeatureclassToCoverage_conversion([InLine,InPoints], coverage)

    # on définit les entité arc et node
    node = os.path.join(coverage, "node")
    arc = os.path.join(coverage,"arc")

    # on lance la fonction qui transforme en graph :
    g, lnode, dEdge, dNode =ToGraph(arc, node)
    # on copie la couche de noeud :
    OutputNoeud=os.path.join(WrkDir,ext)
    arcpy.CopyFeatures_management(sommet,OutputNoeud)

    arcpy.AddField_management(OutputNoeud, "TypeNode", "TEXT")
    arcpy.AddField_management(OutputNoeud, "NbEdge", "SHORT")
    # on met à jour la table de sortie :
    ucur = arcpy.UpdateCursor(OutputNoeud)
    for row in ucur:
        idNode = row.OBJECTID
        NbEdge = len(dNode[idNode]["edge"])
        if NbEdge == 1 : row.setValue("TypeNode", "Onode")
        elif NbEdge == 2 : row.setValue("TypeNode" ,"Lnode")
        elif NbEdge == 3 : row.setValue("TypeNode", "Tnode")
        elif NbEdge == 4 : row.setValue("TypeNode" ,"Xnode")
        else : row.setValue("TypeNode", "Other ; "+str(NbEdge))
        row.setValue("NbEdge", NbEdge)
        ucur.updateRow(row)

    del row, ucur

    # il faut effacer la couverture :
    arcpy.Delete_management(coverage)

    return OutputNoeud

def MakelistNode(InNode, InIdfield, InNodeFieldType):
    """
    Retourne une liste de noeuds avec leur type
    """
    # on définit un curseur de recherche sur la couche de neoud
    scur = arcpy.SearchCursor(InNode)
    # on définit la liste qui contiendra toute les valeurs
    lNode = {}
    for row in scur:
        idNode = row.getValue(InIdfield)
        nodeType = row.getValue(InNodeFieldType)
        lNode[idNode]={"Type":nodeType}
    # On supprime le curseur
    del scur
    lnodeExist=True
    # on retourne le résultat
    return lNode


def getListNodeType(InNode, InIdField, InFieldType, InType):
    """
    Cherche les noeuds de même type. retourne une liste de neouds du même type.
    InNode : la classe d'entité de neouds
    InField : le champs de l'identification des type de noeuds
    InType : Le type de neouds que l'on cherche
    """
    # On cherche si la variable lnode exist
    if not lnodeExist: lnode = MakelistNode(InNode, InIdField, InType)
    # on parcours la liste pour retourner la liste des neouds du type demandé
    lType = {}
    for node in lnode:
        if lnode[node]["Type"] == InType: lType.append(node)
    # on retourne la liste
    return lType


def main(EmpClass,WrkDir, fieldId, FieldNodeType, MaximunAngle, Output):
    # fusionner les emprises:
    DissolveEmpClass = os.path.join(WrkDir,'EmpDissolve')
    arcpy.Dissolve_management(EmpClass, DissolveEmpClass)
    # Transformer les lignes en polygone
    EmpLine = os.path.join(WrkDir,'EmpLine')
    arcpy.FeatureToLine_management(DissolveEmpClass, EmpLine)
    # on créer les noeuds L de l'emprise.
    LnodeEmp = os.path.join(WrkDir,"LnodeEmp")
    MakeNodes(EmpLine, LnodeEmp, True, 135, WrkDir)
    # Traiter les neouds de type L:

if __name__ == '__main__':
    emprise = arcpy.GetParameterAsText(0)
    axehaieNodeIdentifiy = arcpy.GetParameterAsText(1)
    fieldId = arcpy.GetParameterAsText(2)
    FieldNodeType = arcpy.GetParameterAsText(3)
    MaximunAngle = int(arcpy.GetParameterAsText(4))
    Output = arcpy.GetParameterAsText(4) # stocker dans une géodatabase !!

    dirWrk, nameOutput = os.path.split(Output)

    main(emprise, dirWrk, fieldId, FieldNodeType, MaximunAngle, Output)
