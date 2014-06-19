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

def MakeSql(inlist,inChamp,inInverse):
    sql=""
    for e in inlist:
        if sql: sql = " OR " + sql
        if not inInverse: sql = inChamp + " = " + str(e) + " " + sql
        if inInverse: sql = inChamp + " = " + str(e) + " " + sql
    return sql

def FeatureToDictionaire(InFeature, InIdField):
    # premet de convertir une classe d'entité vers un dictionnaire
    scur, dFeature = arcpy.SearchCursor(InFeature), {}
    for row in scur:
        g=arcpy.Geometry()
        g=row.Shape
        dFeature[row.getValue(InIdField)]={"geometrie": g,"angle":CalculerAngle(g.firstPoint,g.lastPoint)}
    # on retourne le dictionnaire
    return dFeature

def Proximite(InFeature,ProxiFeature,distance, NbClose, intabletype, inametable):
    # il faut générer la table de procimité
    #  GenerateNearTable_analysis (in_features, near_features, out_table, {search_radius}, {location}, {angle}, {closest}, {closest_count})
    if intabletype==0 : arcpy.GenerateNearTable_analysis(InFeature, ProxiFeature, inametable, distance)
    if intabletype==1 : arcpy.GenerateNearTable_analysis(InFeature, ProxiFeature, inametable,distance,"","","ALL",NbClose)

    # on parcours la table :
    scur, dProxi = arcpy.SearchCursor(inametable), {}
    # on intègre les données de table dans un ditionnaire :
    for row in scur:
        InFid=row.getValue("IN_FID")
        NearFid=row.getValue("NEAR_FID")
        NearDist=row.getValue("NEAR_DIST")
        IdNearTable=row.getValue("OBJECTID")
        dProxi[IdNearTable]={"IN_FID":InFid, "NEAR_FID":NearFid, "NEAR_DIST":NearDist}
    # on retourne la valeur :
    return dProxi

def ChercherSuiveur(InFeatureRef, InFeatureFollow, InDictTableProxi, inTableProxi, inAngle):
    # on cherche l'entité qui suivent les austres entités.
    # on récupère le champ id de l'entité d'entrée et on créer un dictionnaire.
    inRefId=ChercheChampID(InFeatureRef)
    dFeatRef=FeatureToDictionaire(InFeatureRef, inRefId)
    # on récupère l'entité à suivre :

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

    return lfeatRefFollow

def UpdateCopyRef(inFeature,inliste,inFeatureOut):
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

if __name__ == '__main__':
   # on récupère les variables :
   """
   EntiteDeReference=arcpy.GetParameterAsText(0)
   ChampID=arcpy.GetParameterAsText(1)
   EntiteDeProximite=arcpy.GetParameterAsText(2)
   CopieEntiteSortie=arcpy.GetParameterAsText(3)
   """
   EntiteDeReference=r'H:\5_STAGE\HedgeTools\DataTest\Data.gdb\axehaie'
   EntiteDeProximite=r'H:\5_STAGE\HedgeTools\DataTest\Data.gdb\TRONCON_COURS_EAU_Peyriss'
   CopieEntiteSortie=r'H:\5_STAGE\HedgeTools\DataTest\Results.mdb\output'

   # on créer un environnement de travail
   chemin,nom=os.path.split(CopieEntiteSortie)
   env.workspace=chemin

   # on définit les paramètres d'environnement : réécriture, espace de travail.
   env.overwriteOutput=True

   # il faut briser la ligne en tout point
   arcpy.SplitLine_management(EntiteDeReference,"splitEntiteRef")
   arcpy.SplitLine_management(EntiteDeProximite,"splitEntiteProche")
   EntiteDeProximite, EntiteDeReference = "splitEntiteProche","splitEntiteRef"

   # on lance la fonction qui génère un dictionnaire de table de proximité
   dTableProxi1=Proximite(EntiteDeReference,EntiteDeProximite,20,"",0,"dTableProxi1")

   # on récupère dans une liste les entités qui se croisent et celles qui ne se croisent pas
   lcross,lproche = [],[]
   for entite in dTableProxi1:
    InFid=dTableProxi1[entite]["IN_FID"]
    if dTableProxi1[entite]["NEAR_DIST"]>0 : lproche.append(InFid)
    if dTableProxi1[entite]["NEAR_DIST"]==0 : lcross.append(InFid)

   # il faut créer une requête SQL
   sqlcross=MakeSql(lcross,"OBJECTID",False)

   # on créer les layers cross et proche :
   arcpy.MakeFeatureLayer_management(EntiteDeReference,"CROSSENTITE", sqlcross)
   arcpy.MakeFeatureLayer_management(EntiteDeReference, "PROCHENTITE")
   arcpy.SelectLayerByAttribute_management("PROCHENTITE","SWITCH_SELECTION",sqlcross)

   # on regarde maintenant pour le layer proche si il suit à +- 20°
   lEntitesuiveurProche=ChercherSuiveur("PROCHENTITE",EntiteDeProximite,dTableProxi1,"TableSuiveur1", 35)

   # il faut chercher pour les lignes qui se croisent d'autre candidats
   dTableProxiCross=Proximite("CROSSENTITE",EntiteDeProximite,15,4,1,"dTableProxiCross")
   lEntiteSuiveurCross=ChercherSuiveur("CROSSENTITE",EntiteDeProximite,dTableProxiCross,"TabeSuiveur2",35)

   # on combine les deux listes
   lEntiteSuiveur=[]
   lEntiteSuiveur.extend(lEntiteSuiveurCross)
   lEntiteSuiveur.extend(lEntitesuiveurProche)

   # on met à jour la table de référence.
   UpdateCopyRef(EntiteDeReference,lEntiteSuiveur,CopieEntiteSortie)