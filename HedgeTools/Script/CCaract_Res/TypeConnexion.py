#
#-------------------------------------------------------------------------------
# Name:         Type de connexion
# Purpose:      Trouver le type de connexion d'un noeud.
#
# Author:      Villierme
#
# Created:     21/07/2013
# Copyright:   (c) Villierme 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy, os
from arcpy import env
env.overwriteOutput =True

axemedian = arcpy.GetParameterAsText(0)
noeud = arcpy.GetParameterAsText(1)
OutputNoeud = arcpy.GetParameterAsText(2)

# on récupère la direction du dossier :
geodatabase, nameout = os.path.split(OutputNoeud)
dossier = os.path.dirname(geodatabase)

# on construit la couverture pour obtenir la topologie
coverage = os.path.join(dossier, "coverage")
arcpy.FeatureclassToCoverage_conversion([axemedian,noeud],coverage)

# on récupère les entités dans la couverture topologique
arret = os.path.join(coverage,"arc")
sommet = os.path.join(coverage, "node")

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


# on récupère le graph, la liste des neouds, le dictionnaire des arret, et le dictionnaire de noeuds.
g, lnode, dEdge, dNode =ToGraph(arret, sommet)

# on copie la couche de noeud :
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
