# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Indicateur de morphologie
# Purpose:     Met à jour l'axe médian de l'entité en entrée. Il créera les champs suivants :
#              longueur, largeur, forme, orientation.
#              Le calcul de ces différents indices se fera en fonction du choix de l'utilisateur.
#              --> entrée : emprise, axemedian, transects, indexlist
#                  indexlist :
#                            longueur,
#                            largeur (ne sera pas calculé si il n'y a pas de transects),
#                            forme ((ne sera pas calculé si il n'y a pas de transects),
#                            orientation.
#
#              <-- sortie : copie de axemedian avec attributs.
#
# Author:      Villierme Lewis
#
# Created:     14/06/2013
# Copyright:   (c) lvillier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# import de la biliothèque arcpy et création et difinition de l'environnement de travail
import arcpy, os, math
arcpy.env.overwriteOutput=True


def FindField(InFc, WordField):
    """
    return the exact name of a field
    """
    fname= ""
    fields = arcpy.ListFields(InFc)
    for fld in fields:
        if WordField.capitalize() in fld.name.capitalize() : fname = fld.name

    return fname

def InAgeodatabase (Workspace):
    """
    tell if we are in a gedatabase
    """
    path, ext = os.path.splitext(Workspace)
    InGdb = True
    if ext not in [".gdb",".mdb"]: InGdb = False
    return InGdb

# la fonction qui calcul l'orientation :
def orientation(firstpoint, lastpoint):
    orient = math.atan2(lastpoint.X-firstpoint.X, lastpoint.Y-firstpoint.Y)*(180/math.pi)
    if orient<0:
        orient+=180
    return orient

def GetMorphoIndex(axemedian, IdField, transects, emprise, OutputClass, geodata):

    # définition de l'environnement de travail :
    arcpy.env.workspace = geodata


    arcpy.Copy_management(axemedian,OutputClass)

    # on initialise du dictionnaire axe médian
    Daxemedian = {}

    """
    # il faut créer les champs
    for indices in indexlist:
        if indices not in lfield:
            arcpy.AddField_management(OutputClass,indices,"DOUBLE")
    """
    # on initialise les curseurs de recherche.
    Scuraxe = arcpy.SearchCursor(axemedian)

    # ***************************************** ici on calcul la longueur dans le dictionnaire *******************
    # on définit le dictionnaire de l'axe médian et la longueur :
    for row in Scuraxe:
        fPoint, lPoint, Array = arcpy.Point(), arcpy.Point(), arcpy.Array()
        fPoint, lPoint = row.Shape.firstPoint, row.Shape.lastPoint
        Array.add(fPoint)
        Array.add(lPoint)
        line = arcpy.Polyline(Array)
        Array.removeAll()
        ID = row.getValue(IdField)
        Daxemedian[ID]={"geometrie": line, "longueur": line.length, "largeurs":{"listlarge": [],"nblarge": 0,"largeurtotal": 0.,"largeurmoyenne": 0.}, "forme": 0., "orientation": 0.}
    del row, Scuraxe

    # *******************************  ici on calcule la largeur **************************************************
    # on fait la somme des transects qui sont déocoupé par la couche emprise :
    InGdb = True
    filename, filextension = os.path.splitext(gdb)
    if len(filextension) <1 : InGdb=False
    NClipTrans = "cliptrans"
    NClipTransId = "ClipTransId"
    if not filextension:
        NClipTrans= "Cliptrans.shp"
        NClipTransId = "ClipTransId.shp"

    # ltrans est une liste des objets de découpé:
    Cliptrans = os.path.join(gdb, NClipTrans)
    arcpy.Clip_analysis(transects,emprise, Cliptrans)

    # on indentifie les transects :
    cliptransId = os.path.join(gdb, NClipTransId)
    if not arcpy.Exists(cliptransId):arcpy.Identity_analysis(Cliptrans, emprise, cliptransId, "ONLY_FID")
    empName = os.path.basename(emprise)
    fempName, extEmpName = os.path.splitext(empName)
    IdFieldTrans = FindField(cliptransId, "FID_" + fempName[:6])

    # on parcours la couche Transects :
    scur = arcpy.SearchCursor(cliptransId)

    # on ajoute dans le dictionnaire des arcs les transects qui ont le même identifiant :
    for row in scur :
        idaxe = row.getValue(IdFieldTrans)
        length = row.Shape.length
        # pour éviter les indices qui ne sont pas dans la liste
        if idaxe in Daxemedian:
            Daxemedian[idaxe]["largeurs"]["listlarge"].append(length)
            Daxemedian[idaxe]["largeurs"]["nblarge"]+=1
            Daxemedian[idaxe]["largeurs"]["largeurtotal"]+=length
    del scur,row
    # calcul de la moyenne :
    for axe in Daxemedian:
        largeur=Daxemedian[axe]["largeurs"]
        # il faut éviter les division par zéro ;)
        if largeur["nblarge"] > 0 : largeur["largeurmoyenne"]= largeur["largeurtotal"]/largeur["nblarge"]

    # **************************  ici on calcule la forme ****************************************************

    for axe in Daxemedian:
        # il faut éviter les division par zéro ;)
        if Daxemedian[axe]["largeurs"]["largeurmoyenne"]>0 :
            Daxemedian[axe]["forme"]=Daxemedian[axe]["longueur"]/Daxemedian[axe]["largeurs"]["largeurmoyenne"]

    # ************************* ici on calcule l'orientation des lignes **************************************

    for axe in Daxemedian:
        Point1, Point2 = arcpy.Point(), arcpy.Point()
        Point1, Point2 = Daxemedian[axe]["geometrie"].firstPoint, Daxemedian[axe]["geometrie"].lastPoint
        Daxemedian[axe]["orientation"]=orientation(Point1, Point2)

    # ****************************** ici on met à jour la table axemedian ************************************

    for index in indexlist :
        arcpy.AddField_management(OutputClass, index, "FLOAT")

    Ucur=arcpy.UpdateCursor(OutputClass)

    for row in Ucur:
        indice=row.getValue(IdField)
        if "longueur" in indexlist:
            row.setValue("longueur", Daxemedian[indice]["longueur"])
        if "largeur" in indexlist:
            row.setValue("largeur", Daxemedian[indice]["largeurs"]["largeurmoyenne"])
        if "forme" in indexlist:
            row.setValue("forme", Daxemedian[indice]["forme"])
        if "orientation" in indexlist:
            row.setValue("orientation", Daxemedian[indice]["orientation"])
        Ucur.updateRow(row)
    del Ucur

    # retourner la classe d'entité en sortie.
    return OutputClass


if __name__ == "__main__":
    # on récupère les paramètres :

    emprise=arcpy.GetParameterAsText(0)

    axemedian=arcpy.GetParameterAsText(1)

    IdField = "HEDGEID"

    transects=arcpy.GetParameterAsText(2)

    indexlist=arcpy.GetParameterAsText(3)

    OutputClass=arcpy.GetParameterAsText(4)

    """
    emprise=r'H:\5_STAGE\HedgeTools\DataTest\Data.gdb\polyhaid'

    axemedian=r'H:\5_STAGE\HedgeTools\DataTest\Data.gdb\axehaie'

    IdField = "OBJECTID"

    transects=r'H:\5_STAGE\indicateurs\ACaract_Obj\AMorpho2D\Data_source\sortie.gdb\transects'

    indexlist="longueur;largeur;forme;orientation"

    OutputClass=r'H:\5_STAGE\HedgeTools\DataTest\Data.gdb\morphoAxe'
    """

    gdb,namout = os.path.split(OutputClass)

    indexlist=indexlist.split(";")

    GetMorphoIndex(axemedian, IdField, transects, emprise, OutputClass,gdb )