# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        RoleHydro
# Purpose:      A travers une bibliothèque de foctions cherche les candidats de l'entite de proximité
#               qui suivent l'entité de référence.
#               Attention il se base sur le FID ou OBJECTID.
#
# Author:      Villierme
#
# Created:     15/07/2013
# Copyright:   (c) Villierme 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy, math, os
from arcpy import env

# bibliothèque de fonctions  :
# *********************************************************************
def ChercheChampID(InFeature):
    """ Focntion qui cherche un champ qui contient d'abord un champ nommé FID ou OBJECTID
        sinon il cherche un champ avec ID à l'intérieur. """
    listField=arcpy.ListFields(InFeature)

    # on parcours la liste des champs
    for field in listField:
        if field.name=="FID": champId=field.name
        elif field.name=="OBJECTID":champId=field.name

    # si on ne trouve toujours pas le champId
    if not champId:
        for field in listField:
            if "ID" in field.name : champId=field.name

    return champId

def FeatureToDictionaire(InFeature, InIdField):
    """ premet de convertir une classe d'entité vers un dictionnaire """
    scur, dFeature = arcpy.SearchCursor(InFeature), {}
    for row in scur:
        g=arcpy.Geometry()
        g=row.Shape
        dFeature[row.getValue(InIdField)]={"geometrie": g,"angle":CalculerAngle(g.firstPoint,g.lastPoint)}
    del row, scur

    # on retourne le dictionnaire
    return dFeature

def Proximite(InFeature,ProxiFeature, inametable):
    """ Focntion qui génère la table de proximité """
    # GenerateNearTable_analysis (in_features, near_features, out_table, {search_radius}, {location}, {angle}, {closest}, {closest_count})
    arcpy.GenerateNearTable_analysis(InFeature, ProxiFeature, inametable, 15,"","","ALL",3 )

    # on parcours la table :
    scur, dProxi = arcpy.SearchCursor(inametable), {}
    # on intègre les données de table dans un ditionnaire :
    for row in scur:
        InFid=row.getValue("IN_FID")
        NearFid=row.getValue("NEAR_FID")
        NearDist=row.getValue("NEAR_DIST")
        IdNearTable=row.getValue("OBJECTID")
        dProxi[IdNearTable]={"IN_FID":InFid, "NEAR_FID":NearFid, "NEAR_DIST":NearDist}
    del row, scur
    # on retourne la valeur :
    return dProxi

def ChercherSuiveur(InFeatureRef, InFeatureFollow, InDictTableProxi, inAngle):
    """ on cherche l'entité qui suivent les austres entités.  """
    # on récupère le champ id de l'entité d'entrée et on créer un dictionnaire.
    inRefId=ChercheChampID(InFeatureRef)
    dFeatRef=FeatureToDictionaire(InFeatureRef, inRefId)

    # on récupère le id de l'entité qu'il faut suivre et on créer un dictionnaire
    inFollowId=ChercheChampID(InFeatureFollow)
    dFeatFollow=FeatureToDictionaire(InFeatureFollow,inFollowId)

    # on récupère le dictionnaire de la table de proximité :
    dProche=InDictTableProxi

    # on parcours la table de proximité
    lfeatRefFollow=[]
    for proche in dProche:
        # on récupère les identifiants à comparer :
        IdRef=dProche[proche]["IN_FID"]
        IdProche=dProche[proche]["NEAR_FID"]
        RefAngle=dFeatRef[IdRef]["angle"]
        FollowAngle=dFeatFollow[IdProche]["angle"]

        # on compare les entités entre elles :
        if RefAngle-inAngle<FollowAngle<RefAngle+inAngle:
           lfeatRefFollow.append(IdRef)

    # On retourne la liste des entités qui sont suiveur.
    return lfeatRefFollow

def UpdateCopyRef(inFeature,inliste,inFeatureOut):
    """ Une fonction qui permet de mettre à jour la table spécifiée """
    # on fait une copie de la table d'entrée de Référence :
    arcpy.Copy_management(inFeature,inFeatureOut)
    # on ajoute un champ :
    arcpy.AddField_management(inFeatureOut,"RHydro", "TEXT")
    idChamp=ChercheChampID(inFeatureOut)
    # met à jour la table entrée avec la liste en entrée :
    ucur=arcpy.UpdateCursor(inFeatureOut)
    for row in ucur:
        if row.getValue(idChamp) in inliste:
           row.setValue("RHydro","oui")
           ucur.updateRow(row)
        else:
            row.setValue("RHydro","non")
            ucur.updateRow(row)

    return inFeatureOut

def CalculerAngle(InfirstPoint, InlastPoint):
    import math

    angle = math.atan2(InlastPoint.X-InfirstPoint.X, InlastPoint.Y-InfirstPoint.Y)*(180/math.pi)

    # le calcule de l'arctangante fournit un angle compris entre 180 et -180 °
    # donc il faut ajouter 360 ou 180 pour que l'angle soit dans les valeur positive pour comparer
    # ici on ajoute 180 pour avoir l'angle entre 0 et 180.
    if angle<0:
       angle=angle+180

    # on retourne la valeur
    return angle

def HydroRole(polyhaid,Hydro,axehaie,output, geodata):
    # Paramètre d'environnement :
    arcpy.env.workspace = geodata
    arcpy.env.overwriteOutput = True

    # on construit des couches :
    arcpy.MakeFeatureLayer_management(polyhaid,"LayPoly")
    arcpy.MakeFeatureLayer_management(Hydro, "LayHydro")
    arcpy.MakeFeatureLayer_management(axehaie, "LayAxehaie")

    # on cherche l'intersection entre l'emprise de la haie et le réseau hydrologique.
    arcpy.SelectLayerByLocation_management("LayPoly","INTERSECT","LayHydro")

    # on sélectionne les haies (axe médian) et l'emprise (pour travail avec des lignes.
    arcpy.SelectLayerByLocation_management("LayAxehaie", "INTERSECT", "LayPoly")

    # On fractionne le réseau hydrologique pour obtenir l'orientation.
    arcpy.SplitLine_management(Hydro, "splitHydro")

    # on fait appel à la fonction qui transforme en dictionnaire une table de proximité.
    # on récupère un dictionnaire.
    dProxi=Proximite("LayAxehaie", "splitHydro", "dProxi")

    # la fonction ChercherSuiveur retourne une liste des identifiants qui suivent un troçon hydrologique.
    lFollow=ChercherSuiveur("LayAxehaie","splitHydro",dProxi,45)

    # La fonction fait une copie de l'axe médian ajoute une colonne "Rhydro" et à partir de la liste des ID
    # donne une valeur oui ou non selon que l'identifiant fait partie de la liste ou pas.
    UpdateCopyRef(axehaie,lFollow,output)

    # retourner le résultat:
    return output

if __name__ == "__main__":

# ***************************************************************************************************

    # les entrées sont récupérées ici :
    polyhaid = arcpy.GetParameterAsText(0)

    Hydro = arcpy.GetParameterAsText(1)

    axehaie = arcpy.GetParameterAsText(2)

    output = arcpy.GetParameterAsText(3)

    # on définit l'environnement de travail :
    workspace, nom = os.path.split(output)

    # on lance la fonction :
    HydroRole(polyhaid,Hydro, axehaie, output, workspace)

