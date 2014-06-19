#
#-------------------------------------------------------------------------------
# Name:         Delta Métrique
# Purpose:      Calculer les delta métrique.
#
# Author:      Villierme
#
# Created:     21/07/2013
# Copyright:   (c) Villierme 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy, os
from arcpy import env



axemedian = arcpy.GetParameterAsText(0)
noeud = arcpy.GetParameterAsText(1)
EmpriseSite = arcpy.GetParameterAsText(2)
OutputEmpriseSite = arcpy.GetParameterAsText(3)
env.overwriteOutput = True

# ici seul le chemin de la geodatabase nous est utile.
chemin, namout = os.path.split(axemedian)

# on découpe l'axe médian et les noeuds avec le site d'étude
axeClip = os.path.join(chemin,"axeclip")
noeudClip = os.path.join( chemin, "noeudClip")

arcpy.Clip_analysis(axemedian, EmpriseSite, axeClip)
arcpy.Clip_analysis(noeud, EmpriseSite, noeudClip)

# il faut chercher les noeuds cul-de-sac :
noeudClip2 = os.path.join(chemin, "noeudClip2")
arcpy.FeatureVerticesToPoints_management(axeClip, noeudClip2,"BOTH_ENDS")


# on transforme en couverture :
dossier = os.path.dirname(chemin)
Coverage = os.path.join(dossier,"couverture")
arcpy.FeatureclassToCoverage_conversion([axeClip, noeudClip2],Coverage)

arret = os.path.join(Coverage, "arc")
sommet = os.path.join(Coverage,"node")

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

def dfs_rec(graph,start,path = []):
    """ Parcours en profondeur avec récursivité
    Cette fonction retourne tous les sommets qui sont interconnectées """
    path = path + [start]
    for edge in graph[start]:
        if edge not in path:
            path = dfs_rec(graph, edge,path)
    return path

def PopList(inListpop, inListTopop):
    """ une fonction qui permet de retirer un ensemble d'une liste et de
    renvoyer la liste avec ces éléments retirés """
    for popElement in inListpop:
        # on cherche l'index de l'élément dans la liste à retirer
        indexEle=inListTopop.index(popElement)
        # on retire l'élement
        inListTopop.pop(indexEle)

    return inListTopop

def LengthPath(inPath, indEdge, indNode):
    """ Cette fonction permet de Calculer la longeur total d'un chemin"""
    # on initialise les variables qui seront utiles pour le parcours du chemin
    lEdgeChecked, lengthPath = [], 0
    # on parcours le sous-réseau :
    for node in inPath:
        # on récupère la liste des edges qui touche le sommet analysé
        lEdge=indNode[node]["edge"]
        # on parcours la liste des edges
        for edge in lEdge :
            # on vérifie que l'on ne compte pas deux fois la longueur.
            if edge not in lEdgeChecked :
                lengthPath+=dEdge[edge]["length"]
                lEdgeChecked.append(edge)

    return lengthPath

# on récupère le graph, la liste des neouds, le dictionnaire des arret, et le dictionnaire de noeuds.
g, lnode, dEdge, dNode =ToGraph(arret, sommet)

n = len(lnode)
m = len(dEdge)
# on définit les sous-ensemble :
dSousEnsemble, k, lLongueur = dict(), 0,[]
# la boucle qui permettra de parcourir le réseau de haie:
while len(lnode)>0 :
    node = min(lnode)
    indexNode = lnode.index(node)
    path=dfs_rec(g,node)
    lnode = PopList(path,lnode)
    LongPath = LengthPath(path, dEdge, dNode)
    dSousEnsemble[k+1]={"path" : path, "longueur" : LongPath}
    lLongueur.append(LongPath)
    k+=1

# calcul de la longueur moyenne des sous-réseaux.
moyLongSousReseau = sum(lLongueur)/len(lLongueur)

# Calcul de l'indice de connexité simple :
IndConnexite = ((n-k)/(n-1.))*100
alpha =(m-n+k)/(2*n-5.)
beta = m*1.0/n*1.0
gamma = m/(3*(n-2.))
mu = m-n+1.


# on travail sur le site d'étude :
arcpy.CopyFeatures_management(EmpriseSite, OutputEmpriseSite)
for field in ["IndConnexite", "alpha", "beta", "gamma", "mu"]:
    arcpy.AddField_management(OutputEmpriseSite, field, "DOUBLE")

ucur = arcpy.UpdateCursor(OutputEmpriseSite)

for row in ucur:
    row.setValue("IndConnexite", IndConnexite)
    row.setValue("alpha", alpha)
    row.setValue("beta", beta)
    row.setValue("gamma", gamma)
    row.setValue("mu", mu)
    ucur.updateRow(row)

del row, ucur
"""
# on efface les éléments intermédiaires
for delElement in [Coverage, axeClip, noeudClip, noeudClip2]:
    arcpy.Delete_management(delElement)
"""
