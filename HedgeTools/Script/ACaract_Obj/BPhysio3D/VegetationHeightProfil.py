#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Villierme
#
# Created:     11/01/2014
# Copyright:   (c) Villierme 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy, os

def VegetationHeightProfil(emprise, mnh, bornes, OutputFc, idfield, geodata):
    from arcpy import env
    from arcpy.sa import ExtractByMask, Slope
    arcpy.CheckOutExtension("spatial")
    env.workspace= geodata
    env.overwriteOutput = True

    # Extraire le mnh
    pathExtract = os.path.join(geodata, "ExtractMNH")
    Extract_MNH = ExtractByMask(mnh, emprise)
    Extract_MNH.save(pathExtract)

    # Calculer la pente
    pathSlope = os.path.join(geodata,"SlopeMNH")
    slope_mnh = Slope(pathExtract,"DEGREE")
    slope_mnh.save(pathSlope)

    # Transformer le raster en point
    arcpy.RasterToPoint_conversion(slope_mnh, "Slope", "Value")

    # Jointure spatiale Cauler Moyenne et Ecart type
    fmap = arcpy.FieldMappings()
    fmap.addTable(emprise)
    fmap.addTable("Slope")

    # Create fieldmap for Mean
    fldMean = arcpy.FieldMap()
    fldMean.addInputField("Slope", "grid_code")
    fMean = fldMean.outputField
    fMean.name = "Mean"
    fMean.aliasName = "Mean"
    fldMean.outputField = fMean
    fldMean.mergeRule= "Mean"
    fmap.addFieldMap(fldMean)

    # Create fieldmap for StdDev
    fldEcartype = arcpy.FieldMap()
    fldEcartype.addInputField("Slope","grid_code")
    fEcartype = fldEcartype.outputField
    fEcartype.name = "Stdv"
    fEcartype.aliasName = "Stdv"
    fldEcartype.outputField = fEcartype
    fldEcartype.mergeRule = "StdDev"
    fmap.addFieldMap(fldEcartype)

    # Perform de spatial join
    arcpy.SpatialJoin_analysis(emprise, "Slope", OutputFc, "", "", fmap)

    # Create a field
    arcpy.AddField_management(OutputFc, "Prof_Typ", "TEXT")

    # Delete Field:
    for fld in arcpy.ListFields(OutputFc):
        if fld.name not in [idfield,"Stdv","Mean","Prof_Typ"]:
            try:
                arcpy.DeleteField_management(OutputFc,fld.name)
            except:
                pass

    # Evaluer la pente avec les bornes
    b1 = bornes[0]
    b2 = bornes[1]
    Code_bloc="""def Eval(Moyenne, EcarType):
        if Moyenne > """+str(b2)+ """ and EcarType < """+str(b1)+ """ : ProfilType = "Asc/Desc_Continue"
        if Moyenne < """+str(b2)+ """ and EcarType < """+str(b1)+ """ : ProfilType = "Plat"
        else : ProfilType = "Hétérogène"
        return ProfilType
    """
    expression = "Eval(!Mean!,!Stdv!)"

    # Calcul du champ Prof Typ
    arcpy.CalculateField_management(OutputFc, "Prof_Typ", expression, "PYTHON_9.3", Code_bloc)

    # Return the result
    return OutputFc

if __name__ == '__main__':
    emprise = arcpy.GetParameterAsText(0)
    idfield = arcpy.GetParameterAsText(1)
    mnh=arcpy.GetParameterAsText(2)
    BorneSup=arcpy.GetParameter(3)
    BorneInf=arcpy.GetParameter(4)
    OutPutFc = arcpy.GetParameterAsText(5)
    geodata = os.path.dirname(OutPutFc)
    VegetationHeightProfil(emprise, mnh, [BorneInf,BorneSup], OutPutFc, idfield, geodata)
