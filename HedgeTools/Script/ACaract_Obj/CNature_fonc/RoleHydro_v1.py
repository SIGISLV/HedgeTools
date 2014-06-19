# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      lvillier
#
# Created:     28/06/2013
# Copyright:   (c) lvillier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy,os
from arcpy import env

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

def MakeSql(inlist,inChamp):
    sql=""
    for e in inlist:
        if sql: sql = "OR" + sql
        sql = inChamp + " = " + str(e) + sql
    return sql

def ChercheChampID(InFeature):
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
    # premet de convertir une classe d'entité vers un dictionnaire
    scur, dFeature = arcpy.SearchCursor(InFeature), {}
    for row in scur:
        g=arcpy.Geometry()
        g=row.Shape
        dFeature[row.getValue(InIdField)]={"geometrie": g,"angle":CalculerAngle(g.firstPoint,g.lastPoint)}
    # on retourne le dictionnaire
    return dFeature

def Proximite(InFeature,ProxiFeature,distance, NbClose):
    # il faut générer la table de procimité
    #  GenerateNearTable_analysis (in_features, near_features, out_table, {search_radius}, {location}, {angle}, {closest}, {closest_count})
    arcpy.GenerateNearTable_analysis(InFeature, ProxiFeature, "TableProche",distance,"","","ALL",NbClose)

    # on parcours la table :
    scur, dProxi = arcpy.SearchCursor("TableProche"), {}
    # on intègre les données de table dans un ditionnaire :
    for row in scur:
        InFid=row.getValue("IN_FID")
        NearFid=row.getValue("NEAR_FID")
        NearDist=row.getValue("NEAR_DIST")
        IdNearTable=row.getValue("OBJECTID")
        dProxi[IdNearTable]={"IN_FID":InFid, "NEAR_FID":NearFid, "NEAR_DIST":NearDist}
    # on retourne la valeur :
    return dProxi

def ChercherSuiveur(InFeatureRef, InFeatureFollow, InDictTableProxi):
    # on cherche l'entité qui suivent les austres entités.
    # on récupère le champ id de l'entité d'entrée et on créer un dictionnaire.
    inRefId=ChercheChampID(InFeatureRef)
    dFeatRef=FeatureToDictionaire(InFeatureRef, infeatId)

    # on récupère le id de l'entité qu'il faut suivre et on créer un dictionnaire
    inFollowId=ChercheChampID(InFeatureFollow)
    dfeatRef=FeatureToDictionaire(InFeatureFollow,inFollowId)

    # on récupère le dictionnaire de la table de proximité :
    dProche=Proximite(InfeatureRef,InfeatureFollow,2,3)

    # on parcours la table de proximité
    dfeatRefFollow=[]
    for proche in dProche:
        # on récupère les identifiants à comparer :
        IdRef=dProche[proche]["IN_FID"]
        IdProche=dProche[proche]["NEAR_FID"]
        RefAngle=dFeatRef[IdRef]["angle"]
        ProcheAngle=dProche[IdProche]["angle"]

        # on compare les entités entre elles :
        if RefAngle-20<ProcheAngle<RefAngle+20:
           lfeatRefFollow.append(IdRef)

    return lfeatRefFollow

def UpdateCopyRef(inFeature,inliste,inFeatureOut):
    # on fait une copie de la table d'entrée de Référence :
    arcpy.Copy_management(inFeature,inFeatureOut)
    # on ajoute un champ :
    arcpy.AddField_management(inFeatureOut,"RHydro", "TEXT")
    idChamp=ChercheChampID(inFeature)
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

if __name__ == '__main__':
   # on récupère les variables :
   EntiteDeReference=arcpy.GetParameterAsText(0)
   ChampID=arcpy.GetParameterAsText(1)
   EntiteDeProximite=arcpy.GetParameterAsText(2)
   CopieEntiteSortie=arcpy.GetParameterAsText(3)

   # on créer un environnement de travail
   chemin,nom=os.path.split(CopieEntiteSortie)
   env.workspace=chemin

   # on définit les paramètres d'environnement : réécriture, espace de travail.
   env.overwriteOutput=True

   # on lance la fonction qui génère un dictionnaire de table de proximité
   dTableProxi1=Proximite(EntiteDeReference,EntiteDeProximite,5,"")

   # on récupère dans une liste les entités qui se croisent et celles qui ne se croisent pas
   lcross,lproche = [],[]
   for entite in dTableProxi1:
    if dTableProxi1[entite]["NEAR_DIST"]>0 : lproche.append(entite)
    if dTableProxi1[entite]["NEAR_DIST"]==0 : lcross.append(entite)

   # il faut créer une requête SQL
   IdChampEntRef=ChercheChampID(EntiteDeReference)
   sqlcross=MakeSql(lcross,IdChampEntRef)
   sqlproche=MakeSql(lproche,IdChampEntRef)

   # on créer les layers cross et proche :
   CROSSENTITE = arcpy.MakeFeatureLayer_management(EntiteDeReference,"CROSSENTITE", sqlcross)
   PROCHENTITE = arcpy.MakeFeatureLayer_management(EntiteDeReference, "PROCHENTITE", sqlproche)

   # on regarde maintenant pour le layer proche si il suit à +- 20°
   lEntitesuiveurProche=ChercherSuiveur(PROCHENTITE,EntiteDeProximite,dTableProxi1)

   # il faut chercher pour les lignes qui se croisent d'autre candidats
   dTableProxiCross=Proximite(CROSSENTITE,EntiteDeProximite,5,4)
   lEntiteSuiveurCross=ChercherSuiveur(CROSSENTITE,EntiteDeProximite,dTableProxiCross)

   # on combine les deux listes
   lEntiteSuiveur=[]
   lEntiteSuiveur.append(lEntiteSuiveurCross)
   lEntiteSuiveur.append(lEntitesuiveurProche)
   # on met à jour la table de référence.
   UpdateCopyRef(EntiteDeReference,lEntiteSuiveur,CopieEntiteSortie)




