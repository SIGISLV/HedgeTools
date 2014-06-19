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

haie = arcpy.GetParameterAsText(0)
Vent = arcpy.GetParameterAsText(1)
tolerance = arcpy.GetParameter(2)
Output = arcpy.GetParameterAsText(3)

Vent = int(Vent)
tolerance = int(tolerance)

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
def Perpenvent(pdvent,tolerance):

    perpent=pdvent+90

    if perpent>180:perpent=perpent-180

    B1=perpent-tolerance
    B2=perpent+tolerance

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
    if field.name == "BrisVent":
        BriseVentExists=True
#Creation du champs BriseVent s'il n'existe pas
if BriseVentExists==False:arcpy.AddField_management(haie,"BriseVent","TEXT")

arcpy.CopyFeatures_management(haie, Output)

# Création du curseur de mise à jour
rows=arcpy.UpdateCursor(Output)

# On récupère le résultat de la fonction qui est une liste des bornes B1, B2, B3, B4.
Intervales=Perpenvent(Vent,tolerance)

# On affecte les variables B1 B2 B3 B4.
B1,B2,B3,B4=Intervales[0], Intervales[1], Intervales[2], Intervales[3]

#Parcours de la table Haie :

for row in rows:

    # définition d'une variable qui prend la valeur de chaque entité
    g=arcpy.Geometry()
    g=row.Shape
    AziHaie=orientation(g.firstPoint,g.lastPoint)

    # En détecte si l'angle de la haie correspond aux bornes
    # Deux bornes sont nécessaire si l'utilisateur rentre une valeur basée 180°

    if B1<AziHaie<B2 or B3<AziHaie<B4:
        row.BriseVent = 'Oui'
    else:
        row.BriseVent = 'Non'
    # commande nécessaire pour la mise à jour du champ
    rows.updateRow(row)

# on efface les curseurs
del row, rows