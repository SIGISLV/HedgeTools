#
#-------------------------------------------------------------------------------
# Name:        SousReseauIdentity
# Purpose:
#
# Author:      Villierme
#
# Created:     21/07/2013
# Copyright:   (c) Villierme 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy, os
from arcpy import env
env.overwriteOutput=True


# Les fonctions qui seront utilisées

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

def UpdatedEdge(inPath, indEdge, indNode,i):
    """ Cette fonction permet de mettre à jour le dictionnaire de edge
    pour avoir l'identifiant du sous-réseau"""
    # on initialise les variables qui seront utiles pour le parcours du chemin
    lEdgeChecked, lengthPath = [], 0
    # on parcours le sous-réseau :
    for node in inPath:
        # on récupère la liste des edges qui touche le sommet analysé
        lEdge=indNode[node]["edge"]
        # on parcours la liste des edges
        for edge in lEdge :
            indEdge[edge].update({"IdSres":i+1})

    # On retourne le dictionnaire de côté mit à jour.
    return indEdge

def identifySubNetwork(Incoverage, OutNode, OutEdge, geodata):
    """
    La fonction principale de l'identification des sous-réseaux.
    Entries:
        Incoverage : the coverage to work with
        OutNode : path where to store the node result
        OutEdge : path where to store the edge result
        geodata : where to store the intermediate features
    Output :
        [OutEdge, OutNode]
    """
    # Paramètres et environnement de travail
    env.workspace = geodata

    # Préparer les variables
    arret, idfieldArret = os.path.join(Incoverage, "arc"), os.path.basename(Incoverage)+"_ID"
    sommet, idfieldSommet = os.path.join(Incoverage, "node"), os.path.basename(Incoverage)+"_ID"

    # on transforme en classe d'entité les couches sélectionnées
    arcpy.CopyFeatures_management(arret, OutEdge)
    arcpy.CopyFeatures_management(sommet, OutNode)

    # on ajoute les champs IdSres
    arcpy.AddField_management(OutEdge,"IdSres", "SHORT")
    arcpy.AddField_management(OutNode, "IdSres", "SHORT")

    # on récupère le graph, la liste des neouds, le dictionnaire des arret, et le dictionnaire de noeuds.
    g, lnode, dEdge, dNode =ToGraph(arret,sommet)

    # on définit les sous-ensemble :
    dSousEnsemble, i, dIdNodeIdPath = dict(), 0,[]

    # la boucle qui permettra de parcourir le réseau de haie:
    while len(lnode)>0 :
        node = min(lnode)
        path=dfs_rec(g,node)
        lnode = PopList(path,lnode)
        # on met à jour le dictionnaire de node pôur avoir l'identifiant du sous réseau node
        for nodepath in path:
            dNode[nodepath].update({'IdSres':i+1})
        # on met à jour le dictionnaire de edge pour obtenir l'identifiant du sous- réseau
        dEdge = UpdatedEdge(path, dEdge,dNode, i)
        i+=1

    # parcourir la liste de noeuds pour mettre à jour le champs IdSres.
    ucur = arcpy.UpdateCursor(OutNode)
    for row in ucur:
        idSommet = row.getValue(idfieldSommet)
        try:
            idSres = dNode[idSommet]["IdSres"]
            row.setValue('IdSres', idSres)
            ucur.updateRow(row)
        except:
            pass

    del ucur, row
    # on efface les champs dont on ne se sert pas
    lFields = arcpy.ListFields(OutNode)
    for field in lFields:
        if field.name not in ["IdSres"]:
            try:
                arcpy.DeleteField_management(OutNode,field.name)
            except:
                pass

    # parcourir la les lignes pour mettre à jour le champ IdSres
    ucur = arcpy.UpdateCursor(OutEdge)

    for row in ucur:
        idArret = row.getValue(idfieldArret)
        try:
            idSres = dEdge[idArret]["IdSres"]
            row.setValue("IdSRes", idSres)
            ucur.updateRow(row)
        except:
            pass

    del row, ucur

    # on efface les champs dont on ne se sert pas
    lFields = arcpy.ListFields(OutEdge)
    for field in lFields:
        if field.name not in ["IdSres"]:
            try:
                arcpy.DeleteField_management(OutEdge,field.name)
            except:
                pass

    # on retourne la sortie
    return OutEdge, OutNode

if __name__=='__main__':
    # on récupère les entrées de l'utilisateur
    coverage = arcpy.GetParameterAsText(0)
    Outnode = arcpy.GetParameterAsText(1)
    Outedge = arcpy.GetParameterAsText(2)

    # on définit le lieu de travail
    geodata = os.path.dirname(Outnode)

    # on execute la fonction principale
    identifySubNetwork(coverage, Outnode, Outedge, geodata)
