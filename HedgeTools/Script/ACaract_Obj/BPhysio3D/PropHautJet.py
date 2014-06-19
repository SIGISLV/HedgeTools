#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Strate de haut jet
# Purpose:     Permet de renseigné la haie sur la strate qui en superficie est la
#              plus importante. on découpe le polygones vectoriser par strate.
#              il faudra aussi diviser en plusieurs entités.
#              une jointure spatiale 1-n pour identifié toute les strate par leur identifiant.
#              On fait une somme des superficie de strate puis on regarde quelle
#              est la superficie la plus importante. On se basera sur un dictionnaire
#              des polygones identifié.
#              il s'agira de mettre à jour la couche de d'emprise identifiée en sortie avec un champ
#              Stratedom en Short.
#
# Author:      Villierme Lewis
#
# Created:     21/06/2013
# Copyright:   (c) lvillier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# import des bibliothèques
import arcpy, os
from arcpy import env
from operator import add

env.overwriteOutput=True

# définition des variables d'entrée :
polyhaid=arcpy.GetParameterAsText(0)

polystrate=arcpy.GetParameterAsText(1)

champID=arcpy.GetParameterAsText(2)

champstrate=arcpy.GetParameterAsText(3)

outfeature=arcpy.GetParameterAsText(4)

chemin, nom = os.path.split(polystrate)

# on fait une copie de la couche :
arcpy.Copy_management(polyhaid,outfeature)

# il faut récupérer les identifiants des emprises :
scur, lid = arcpy.SearchCursor(outfeature), []

for row in scur:
    lid.append(row.getValue(champID))
# on retire le vérouillage de la couche
del row, scur

# on ajoute un champ à la table :
arcpy.AddField_management(outfeature,"PropHautJet","FLOAT")

# parcequ'il n'est pas possible de mettre à jour un couche il faut enregistrer les infos
# dans un dictionnaire.
dentite={}

scur=arcpy.SearchCursor(polystrate)
# on parcours la liste des indentifiants
for ident in lid:
        dentite[ident]={"stratetype":[],
    "stratesurface":{"buissonante":0, "arbustive":0, "arboree":0, "hautjet":0}}

for row in scur:

    #on récupère l'identifiant
    HAID=row.getValue(champID)

    # on récupère les valeurs qui nous intéresse
    typecode=row.getValue(champstrate)
    surface=row.Shape.area

    # on crée la ligne du dictionnaire qui contiendra les valeurs
    stratetype, stratesurface = dentite[HAID]["stratetype"],dentite[HAID]["stratesurface"]

    # cas d'une strate buissonante
    if typecode==1:
       strate="buissonante"
       stratetype.append(typecode)
       stratesurface[strate]+=surface

    # cas d'une strate arbustive
    if typecode==2:
       strate="arbustive"
       stratetype.append(typecode)
       stratesurface[strate]+=surface

    # cas d'une strate arboree
    if typecode==3:
       strate="arboree"
       stratetype.append(typecode)
       stratesurface[strate]+=surface

    # cas d'une strate de hautjet
    if typecode==4:
       strate="hautjet"
       stratetype.append(typecode)
       stratesurface[strate]+=surface

# il faut mettre à jour la table outfeature:
ucur=arcpy.UpdateCursor(outfeature)


# on parcours la table pour mettre à jour cette dernière.
for row in ucur:
    # on récupère les valeurs dans le dictionnaire :
    entsurf=dentite[row.getValue(champID)]["stratesurface"]
    # on créer une liste des valeur de surface.
    lsurface=[entsurf["buissonante"],entsurf["arbustive"],entsurf["arboree"],entsurf["hautjet"]]
    # Calcul de la proportion d'arbre de haujet.
    PropHautJet=entsurf["hautjet"]/reduce(add,lsurface)*1.
    row.setValue("PropHautJet",PropHautJet)
    ucur.updateRow(row)