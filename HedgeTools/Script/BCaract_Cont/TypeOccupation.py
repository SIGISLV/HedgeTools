# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        TypeOccupation
# Purpose:     Count
#
# Author:      Villierme Lewis
#
# Created:     22/10/2013
# Copyright:   (c) lvillier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# Import arcpy module
import arcpy, os
from arcpy import env
env.overwriteOutput = True

# variables :
# ici les variables de l'utilisateur sont récupérées par la méthodes GetParameterAsText.
# la variable est récupérer en format string donc appliqué un eval sur les variables de type réel
OccupeSol = arcpy.GetParameterAsText(0)

fieldOccsol = arcpy.GetParameterAsText(1)

haie = arcpy.GetParameterAsText(2)

outHaie = arcpy.GetParameterAsText(3)

# Local variables:
# Les variables en dur pour débugger

"""
OccupeSol = r'E:\5_STAGE\HedgeTools\DataTest\Contexte.gdb\Occ_Sol_WithoutHaie_2009'
fieldOccsol = 'OS2009_Rec'

haie = r'E:\5_STAGE\HedgeTools\DataTest\Contexte.gdb\Peyriss_haie'

outCoverage = r'E:\5_STAGE\HedgeTools\DataTest\coverageODS'

outHaie = r'E:\5_STAGE\HedgeTools\DataTest\Contexte.gdb\haie_TypeOccupe'
"""

# ici on définit les paramètres de l'environnement:
# wrk : est le chemin d'une géodatabase dans laquelle on sera stocher toutes les entité générées par le script.
wrk = os.path.dirname(haie)
# ici on définit l'espace de travail.
env.workspace = wrk
# ici on cherche le chemin de la géodatabase pour stocker la couverture, car elle ne peut être stocker dans une géodatabase.
path = os.path.dirname(wrk)
# ici on définit le chemin de la couverture que l'on nommera "coverageLU"
outCoverage = os.path.join(path,"coverageLU")


def findIdField(inFeatClasse):
    """
    Une fonction qui prend le premier champ de la table attibutaire. Elle correspond à l'objectID ou le OID ou FID
    entrée :
           inFeatClasse : (string) chemin de la classe d'entité.
    sortie :
           lisField[0].name : (string) nom du champ.
    """
    listField=arcpy.ListFields(inFeatClasse)
    return listField[0].name

def main() :
    """
    Programme principale. On a accès à toutes les variables globales. C'est une structure qui permet de simplfier par la suite le
    bloc de try except.

    Ce programme cherche à caractériser l'occupation du sol autour d'une haie. Pour ce faire on se base sur le principe de contiguité
    de la topologie. L'outil coverage de l'arctoolbox nous permet d'obtenir cette règle topologique. Il faut alors se basé sur
    les arcs. Ces arcs identifient ($LEFTPOLYGON et $RIGHTPOLYGON) ce qui est à gauche et à droite de l'arc. Toutefois, ces identifiants
    correspondent au identifiants de la couche Polygon créer en même temps que les arcs c-a-d pendant l'opération de conversion en
    couverture (coverage). On découpe alors en plusieurs phase les opérations de ce script.

    phase 1 : création de la couverture à partir de l'occupation du sol et de la haie. Attention il est important que l'occupation du sol
    et la carte de haie soient topologiquement correctes (elles se suivent).

    phase 2 : intersection et identification entre haie et polygon (créer par l'outil coverage). Cela permet de faire la relation entre
    les identifiant utiliser par le coverage et l'identifiant de la haie et l'occupation du sol.

    phase 3 : Pour que la relation soit rapide on créé des dictionnaires (dOccsol et dHaie) indicé par les identifiants
    de coverage et contenant l'information de l'occupation du sol ou de l'identifiant de la haie.

    phase 4 : On fait une sélection spatiale de tous les arcs qui touchent la haie pour éviter de parcourir des arcs qui ne nous
    intéressent pas.

    phase 5 : On parcours la couche d'entité et on analyse les champs droite et gauche. On cherche les arcs qui ont l'identifiant
    (coverage) d'une haie puis on regarde ce qui de l'autre côté. Dans cette phase on va mettre à jour le dictionnaire de haie.
    Enfin on créer une liste de tous les type d'occupation du sol.

    phase 6 : On prépare la couche d'entité en sortie. On copie la couche de haie après intersection et identification ("Polygon_haie") en
    il prend le nom que l'utilisateur a fixé, et on ajoute les champs correspondant à chaque type d'occupation du sol.

    phase 7 : on met à jour la couche avec le dictionnaire de haie.
    """
    #---------------------------------------------------------------------------
    """                             phase 1                                  """
    #---------------------------------------------------------------------------
    fieldIDHaie = findIdField(haie) # on cherche le champ d'identifiant.
    # Process: Classe d’entités vers couverture
    # ici on créer la couverture entre l'occupation du sol (polygon) et la haie (polygon).
    arcpy.FeatureclassToCoverage_conversion([OccupeSol,haie], outCoverage, "", "DOUBLE")

    #---------------------------------------------------------------------------
    """                             Phase 2                                  """
    #---------------------------------------------------------------------------

    # Process : Intersect avec haie et Occupsol.
    # on récupère l'intersection entre le polygon (couverture) et le l'occupation du sol. On nomme "Polygon_OccSolInter" l'entité en sortie.
    #
    arcpy.Intersect_analysis([outCoverage+"\polygon",OccupeSol],"Polygon_OccSolInter")
    arcpy.Intersect_analysis([outCoverage+"\polygon",haie],"Polygon_HaieInter")

    # Process: Identité
    arcpy.Identity_analysis("Polygon_OccSolInter", OccupeSol,"Polygon_OccSol" , "ALL", "", "NO_RELATIONSHIPS")
    arcpy.Identity_analysis("Polygon_HaieInter", haie,"Polygon_Haie" , "ALL", "", "NO_RELATIONSHIPS")

    # ******Attention**** Le champ d'identifiant du polygon sera "FID_polygon"

    #---------------------------------------------------------------------------
    """  Phase 3 : Transformer en dictionnaire la couche d'occupation du sol """
    #---------------------------------------------------------------------------

    scur = arcpy.SearchCursor("Polygon_OccSol")
    dOccsol = {}
    for row in scur:
        FIDPoly = row.getValue('FID_polygon') # FID_Polygon est l'identifiant utilisé par la couverture pour chaque arc.
        occsol = row.getValue(fieldOccsol) # on cherche à connaitre la l'occupation du sol indicé par leur identifiant.
        dOccsol[FIDPoly]={"occupationSol":occsol}
    del row, scur

    #---------------------------------------------------------------------------
    """     Phase 3 : Transformer en dictionnaire la couche Haie :           """
    #---------------------------------------------------------------------------

    scur = arcpy.SearchCursor("Polygon_Haie")
    dHaie = {}
    for row in scur:
        idex = row.getValue("FID_polygon")
        HedgeID = row.getValue (fieldIDHaie)
        dHaie[idex]={"HedgeID":HedgeID, "llibelle":[] }
    del row, scur

    # Transformation en couche des classe d'entité arc et haie :
    arc = os.path.join(outCoverage,"arc")
    arcpy.MakeFeatureLayer_management(arc,"layerArc")
    #---------------------------------------------------------------------------
    """                             Phase 4                                  """
    #---------------------------------------------------------------------------
    # Sélection spatiale des arcs et de la haie
    # mais il il existe encore des arcs qui ne bordent pas les haies donc il faut filtré :
    arcpy.SelectLayerByLocation_management("layerarc","BOUNDARY_TOUCHES", haie)

    # --------------------------------------------------------------------------
    """             Phase 5 : Parcourir la couche layerarc :                 """
    #---------------------------------------------------------------------------

    scur = arcpy.SearchCursor("layerarc")
    # Créer la liste des champs à créer :
    lfields = []
    for row in scur :
        idleft = row.getValue("$LEFTPOLYGON")
        idright = row.getValue("$RIGHTPOLYGON")
        length = row.Shape.length

        #-----------------------------------------------------------------------------------
        # Cas 1 : l'identifiant du polygon gauche est dans la liste des haies :
        # on prend alors les informations du polygon à droite (le type d'occupation du sol).
        # l'identifiant 1 n'existe pas dans une table de coverage. il correspond à un vide donc il faut veillez à
        # ne pas le prendre
        # il faut aussi gérer le voisinage entre deux haies d'où le "idright not in dHaie".
        #-----------------------------------------------------------------------------------
        if idleft in dHaie and idright!=1 and idright not in dHaie:
           typeOccSol = dOccsol[idright]["occupationSol"]
           # on ajoute le nom du type de d'occupation du sol à une liste pour créer le champ
           if typeOccSol not in lfields: lfields.append(typeOccSol)
           # cas ou le type d'occupation du sol n'est pas dans la liste des type d'occupation
           # Il faut gérer l'occupation du sol vide.
           elif typeOccSol not in dHaie[idleft]["llibelle"]:
              # on ajoute une rubrique dans le dictionnaire de haie avec la longueur de l'occupation :
              dHaie[idleft].update({typeOccSol:length})
              # on ajoute le type d'occupation du sol à liste d'occupation du sol de la haie.
              dHaie[idleft]["llibelle"].append(typeOccSol)
           # cas ou le type d'occupation du sol est dans la liste
           elif typeOccSol in dHaie[idleft]["llibelle"]:
              # on additionne la longueur à la valeur de la rubrique existante
              dHaie[idleft][typeOccSol]+=length

        #-------------------------------------------------------------------------------------
        # Cas 2 : l'identifiant du polygon droite est dans la liste des haies :
        # on prend alors les informations du polygon à droite (le type d'occupation sol)
        # l'identifiant 1 n'existe pas une table de coverage. il correspond à un vide donc il faut veillez à
        # ne pas le prendre
        # il faut aussi gérer le voisinage entre deux haies.
        # il faut aussi gérer le voisinage entre deux haies d'où le "idleft not in dHaie".
        #-------------------------------------------------------------------------------------
        if idright in dHaie and idleft!=1 and idleft not in dHaie:
           typeOccSol = dOccsol[idleft]["occupationSol"]
           # on ajoute le nom du type de d'occupation du sol à une liste pour créer le champ
           if typeOccSol not in lfields: lfields.append(typeOccSol)
           # cas ou le type d'occupation du sol n'est pas dans la liste des types d'occupation
           # Il faut gérer l'occupation du sol vide.
           elif typeOccSol not in dHaie[idright]["llibelle"]:
              # on ajoute la rubrique dans le dictionnaire de haie avec la longueur de l'occupation :
              dHaie[idright].update({typeOccSol: length})
              # on ajoute à la liste des type d'occupation du sol de cette haie :
              dHaie[idright]["llibelle"].append(typeOccSol)
           # cas ou le type d'occupation du sol est dans la liste
           elif typeOccSol in dHaie[idright]["llibelle"]:
              # on additionne la longueur à la valeur de la rubrique existante :
              dHaie[idright][typeOccSol]+=length

    del row, scur

    #---------------------------------------------------------------------------
    """                  phase 6 : préparation de la table                   """
    #---------------------------------------------------------------------------

    # champs identifiants :
    idPolyCoverage = "FID_polygon"
    idPoly = "FID_Polygon_HaieInter"

    # copier la table :
    arcpy.CopyFeatures_management("Polygon_Haie",outHaie)

    # ajouter les champs à partir de la liste de champs
    for field in lfields:
        arcpy.AddField_management(outHaie,field,"FLOAT",10)

    # --------------------------------------------------------------------------
    """         phase 7 : on met à jour la table des haies                   """
    #---------------------------------------------------------------------------

    # mettre à jour le champ
    ucur = arcpy.UpdateCursor(outHaie)

    for row in ucur:
        idexHaie = row.getValue(fieldIDHaie)
        # attention il faut écarter l'indice 1 car il ne correspond à aucun polygon.
        if idexHaie in dHaie :
            # on cherche dans le dictionnaire de haie
            hedge = dHaie[idexHaie]
            # on met à jour les différent champs des type d'occupation du sol.
            for field in hedge["llibelle"]:
                   longueur = hedge[field]
                   row.setValue(field,longueur)
            ucur.updateRow(row)
    del row, ucur

if __name__=='__main__':       #  __name__ == "__main__" quant le script est executé mais n'exécutera pas si le script est importé.

   # execution de la fonction principale
   main()