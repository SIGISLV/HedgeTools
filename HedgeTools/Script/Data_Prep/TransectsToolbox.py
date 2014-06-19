#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      lvillier
#
# Created:     29/05/2013
# Copyright:   (c) lvillier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

#-------------------------------------- Fonctions qui calcule les orientations des transects ----------------------------------------


#------------------------------------------------------- import de la bibliothèque -------------------------------------------------
# import des bibliothèques
import arcpy
from arcpy import env
import os


def orientTransect(arc,point,transDist):
    # on récupère l'orientation de la ligne dans la liste arc
    startx,starty,endx,endy=arc.firstPoint.X, arc.firstPoint.Y, arc.lastPoint.X, arc.lastPoint.Y
    ix, iy = point.X, point.Y
    # on modifie le type de de transdist qui doit être en integer :
    transDist=int(transDist)
    # If the line is horizontal or vertical, the slope and
    # negative reciprocal calculations will fail, so do this instead
    if starty==endy or startx==endx:
        if starty == endy:
            y1 = iy + transDist
            y2 = iy - transDist
            x1 = ix
            x2 = ix

        if startx == endx:
            y1 = iy
            y2 = iy
            x1 = ix + transDist
            x2 = ix - transDist


    else:

        # Get slope of line
        m = ((starty - endy)/(startx - endx))

        # Get negative reciprocal
        negativereciprocal = -1*((startx - endx)/(starty - endy))

        # For all values of slope, calculate perpendicular line
        # with length = transDist
        if m > 0:
            if m >= 1:
                y1 = negativereciprocal*(transDist)+ iy
                y2 = negativereciprocal*(-transDist) + iy
                x1 = ix + transDist
                x2 = ix - transDist
            if m < 1:
                y1 = iy + transDist
                y2 = iy - transDist
                x1 = (transDist/negativereciprocal) + ix
                x2 = (-transDist/negativereciprocal)+ ix

        if m < 0:
            if m >= -1:
                y1 = iy + transDist
                y2 = iy - transDist
                x1 = (transDist/negativereciprocal) + ix
                x2 = (-transDist/negativereciprocal)+ ix

            if m < -1:
                y1 = negativereciprocal*(transDist)+ iy
                y2 = negativereciprocal*(-transDist) + iy
                x1 = ix + transDist
                x2 = ix - transDist

    # on prépare l'objet ligne pour le retour de la fonction
    fpoint, spoint=arcpy.Point(), arcpy.Point()
    larray=arcpy.Array()
    fpoint.X, fpoint.Y, spoint.X, spoint.Y=x1,y1,x2,y2
    larray.add(fpoint)
    larray.add(spoint)
    trans=arcpy.Polyline(larray)
    larray.removeAll()
    return trans


def Transects(axemedian, rayon, ecart, sortie, nom):

    chemin=os.path.dirname(sortie)
    spatialref=arcpy.Describe(axemedian).spatialReference
    #--------------------------------------- définition de l'environnement de travail --------------------------------------------------

    # on définit l'environnement de travail.
    env.workspace=os.path.dirname(axemedian)

    # on créer une geodatabase pour stocker toutes les entités crées CreateFileGDB_management (out_folder_path, out_name, {out_version})
    gdbmorpho=os.path.join(chemin,"data.gdb")
    if arcpy.Exists(gdbmorpho): arcpy.Delete_management(gdbmorpho)
    arcpy.CreateFileGDB_management(chemin,"data.gdb")
    stockage=gdbmorpho

    #------------------------------------------------------- On définit les variables de départ ---------------------------------------

    # on divise la ligne en arc:
    arcs=os.path.join(stockage,"arcs")
    if arcpy.Exists(arcs):arcpy.Delete_management(arcs)
    arcpy.SplitLine_management (axemedian, arcs)

    # On copie l'axe médian et on travail sur la copie.
    copyaxe=os.path.join(stockage,"copyaxe")
    if arcpy.Exists(copyaxe):arcpy.Delete_management(copyaxe)
    arcpy.CopyFeatures_management(arcs,copyaxe)

    # on divise copyaxe en fonction de la distance en entrée
    ecart=int(ecart)
    arcpy.Densify_edit(copyaxe, "DISTANCE", ecart)

    #on récupère tous les points
    points=os.path.join(stockage,"points")
    if arcpy.Exists(points):arcpy.Delete_management(points)
    arcpy.FeatureVerticesToPoints_management(copyaxe,points,"ALL")

    # identifié les points qui touchent la ligne
    Scur=arcpy.SearchCursor(arcs)
    shapearcs=arcpy.Describe(arcs).shapeFieldName
    ligneArray=arcpy.Array()
    pnt1 = arcpy.Point()
    pnt2 = arcpy.Point()
    listarcs=[]
    for row in Scur:
        # on récupère la géométrie dans featarcs
        featarcs=row.getValue(shapearcs)
        # on initialise le point1 et le point2
        pnt1.X, pnt1.Y = featarcs.firstPoint.X, featarcs.firstPoint.Y
        pnt2.X, pnt2.Y = featarcs.lastPoint.X, featarcs.lastPoint.Y
        # on l'enregistre dans un tableau
        ligneArray.add(pnt1)
        ligneArray.add(pnt2)
        # on le transforme en un objet polyligne
        ligne=arcpy.Polyline(ligneArray)
        # on stocke les lignes dans une liste qui pourra être intégrer dans un copyfeature_management pour sa création
        listarcs.append(ligne)
        # on oublie pas de réinitialiser la tableau sinon il y aura une liaison avec les autres ligne.
        ligneArray.removeAll()
    del Scur, row

    # on récupère les indentifiants des points et leur coordonnées xy
    Scur=arcpy.SearchCursor(points)
    shapename=arcpy.Describe(points).ShapeFieldName
    pnt=arcpy.Point()
    lpointxy=[]
    for row in Scur:
        feat=row.getValue(shapename)
        pnt=feat.firstPoint
        lpointxy.append(pnt)
    del Scur, row

    # on identifie les points pour obtenir l'orientation par rapport à leur arc :
    # exemple : listlinepoint = [[arc,points],[arc,point]...]
    listlinepoint=[]
    for point in lpointxy:
        for line in listarcs:
            if point.within(line):
               listlinepoint.append([line,point])
               break

    # on fabrique les transects
    listtransects=[]
    for linepoint in listlinepoint:
        trst=orientTransect(linepoint[0],linepoint[1],rayon)
        listtransects.append(trst)

    # on créer la couche de transects
    transects=os.path.join(sortie,nom)
    if arcpy.Exists(transects):arcpy.Delete_management(transects)
    arcpy.CopyFeatures_management(listtransects,transects)
    arcpy.DefineProjection_management(transects,spatialref)

    # on efface la géodatabase:
    arcpy.Delete_management(gdbmorpho)



                                #************************
                                #  fin de la fonction   *
                                #************************

if __name__ == "__main__":

   # classe d'entité ligne l'axe médian
   axemedian=arcpy.GetParameterAsText(0)

   # les paramètres de distance et écart entre les transects.
   ecart=arcpy.GetParameterAsText(1)
   rayon=arcpy.GetParameterAsText(2)

   # Classe d'entité ligne
   sortie=arcpy.GetParameterAsText(3)

   sortie, nom = os.path.split(sortie)

   Transects(axemedian, rayon, ecart, sortie, nom)
   # ligne , longueur transects, distance entre les transects, sortie