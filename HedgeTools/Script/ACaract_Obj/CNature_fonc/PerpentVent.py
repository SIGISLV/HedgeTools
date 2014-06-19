# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        BriseVent
# Purpose:
#
# Author:      Villierme
#
# Created:     19/04/2013
# Copyright:   (c) Villierme 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# Les entrées
import arcpy, os
from arcpy import env

# Ligne pour le calcul de l'orientation.
haie = arcpy.GetParameterAsText(0)
# Emprise des polygones
polygone = arcpy.GetParameterAsText(1)
# Direction du vent en sortie.
Vent = arcpy.GetParameterAsText(2)
#Taille du pixel.
Cell_size = arcpy.GetParameterAsText(3)
# raster booleen en sortie.
Output = arcpy.GetParameterAsText(4)

# transformer en entier la direction du vent.
Vent = int(Vent)

# Environnement de stockage.
workspace, name = os.path.split(Output)
arcpy.env.workspace= workspace

# fonction qui calcul l'orientation
def orientation(firstpoint, lastpoint):
    import math
    orient = math.atan2(lastpoint.X-firstpoint.X, lastpoint.Y-firstpoint.Y)*(180/math.pi)
    if orient<0:
        orient+=180
    return orient

# Fonction qui cherche les bornes pour qu'une haie soie brise vent.
def Perpenvent(pdvent):

    perpent=pdvent+90

    if perpent>180:perpent=perpent-180

    B1=perpent-45
    B2=perpent+45

# Cas normale
    Intervales=[B1,B2,0,0]

#Cas 1
    if B1<0:
        Intervales=[0,B2,B1+180,180]

#Cas2
    if B2>180:
        Intervales=[0,B2-180,B1,180]

    return Intervales

# On vérifie les noms des champs avant d'ajouter le champs briseVent
#on récupère les noms des champs dans une liste
fields=arcpy.ListFields(haie)
# on initialise les booléens qui détecteront la présence d'un champ
BriseVentExists=False
# Affecte la valeur booléen si le champ est présent
for field in fields:
    if field.name == "PVent":
        BriseVentExists=True
#Creation du champs BriseVent s'il n'existe pas
if BriseVentExists==False:arcpy.AddField_management(haie,"PVent","SHORT")

arcpy.CopyFeatures_management(haie, Output)

# Création du curseur de mise à jour
rows=arcpy.UpdateCursor(Output)

# On récupère le résultat de la fonction qui est une liste des bornes B1, B2, B3, B4.
Intervales=Perpenvent(Vent)

# On affecte les variables B1 B2 B3 B4.
B1,B2,B3,B4=Intervales[0], Intervales[1], Intervales[2], Intervales[3]

# il faut récupérer les identifiants des haies perpendiculaire +/- 45° au vent.
lperpenVent=[]

#Parcours de la table Haie :

for row in rows:

    # définition d'une variable qui prend la valeur de chaque entité
    g=arcpy.Geometry()
    g=row.Shape
    AziHaie=orientation(g.firstPoint,g.lastPoint)

    # En détecte si l'angle de la haie correspond aux bornes
    # Deux bornes sont nécessaire si l'utilisateur rentre une valeur basée 180°

    if B1<AziHaie<B2 or B3<AziHaie<B4:
        row.PVent = 1
        lperpenVent.append(row.IDHedge)
    else:
        row.PVent = 0
    # commande nécessaire pour la mise à jour du champ
    rows.updateRow(row)

# on efface les curseurs
del row, rows

# Construction de la requête SQL
sql="PVent = " + str(lperpenVent[0])

# Il faut retirer le premier élément
lperpenVent.pop(0)

# on boucle sur tout les objet qui sont dans la liste et on construit la requête SQL.
for ident in lperpenVent:
    sql+= " OR " + " PVent = " + str(ident)

# On transforme en couche les polygônes.
arcpy.MakeFeatureLayer_management(polygone, "PerpendVent",sql)

# On transforme en shape la couche
arcpy.CopyFeatures_management("PerpendVent", "HaiePerpentVent")

# on transforme la couche en raster.
arcpy.PolylineToRaster_conversion("HaiePerpentVent", "PVent",Output,"","",Cell_size)
