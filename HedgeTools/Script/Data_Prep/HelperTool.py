# -*- coding: utf-8 -*
#-------------------------------------------------------------------------------
# Name:        GetAWorkSpace
# Purpose:     Find a work space
#              1 : the scratchWorkspace is define in environnement setting it return this one
#              2 : It return a
#
# Author:      lvillier
#
# Created:     22/11/2013
# Copyright:   (c) lvillier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy
from arcpy import env
import sys
import os

def getScratchWorkspace(outDataset):
  # outDataSet is assumed to be the full pathname to a dataset. Typically,
  #  this would be a tool's output parameter value.
  #
  # Get the scratch workspace environment. If it's set, just return it.
  #
  scratchWS = env.scratchWorkspace
  if scratchWS:
    return scratchWS

  # Let's go fishing...
  #
  # If you're using the ToolShare folder structure, look for scratch.gdb in
  #  the Scratch folder.
  #
  scriptPath      = sys.path[0]
  print scriptPath
  toolSharePath   = os.path.dirname(scriptPath)
  print toolSharePath
  scratchWS       = os.path.join(toolSharePath, "Scratch\scratch.gdb")
  print scratchWS
  if not arcpy.Exists(scratchWS):
     try :
         arcpy.CreateFileGDB_management(scratchWS)
         return scratchWS
     except:
            scratchWS = ""

  # No scratch workspace environment and no scratch.gdb in the ToolShare folder
  #
  if not scratchWS:
    # Get the workspace of the output dataset (if any passed in)
    #  by going up one level
    #
    if outDataset:
      scratchWS = os.path.dirname(str(outDataset))

      # If this isn't a workspace, go up another level and
      #  test again.
      #
      desc = arcpy.Describe(scratchWS)
      if desc.dataType.upper() <> "WORKSPACE":
        scratchWS = os.path.dirname(scratchWS)
        desc = arcpy.Describe(scratchWS)
        if desc.dataType.upper() <> "WORKSPACE":
          scratchWS = ""

  # If we have a workspace, make sure it's not a remote (SDE) database.
  #  If it is remote, set workspace to the system temp directory.
  #
  # If we don't have a workspace, just set it to the system temp directory.
  #
  usingTemp = False
  if scratchWS:
      desc = arcpy.Describe(scratchWS)
      if desc.workspaceType.upper() == "REMOTEDATABASE":
          scratchWS = arcpy.GetSystemEnvironment("TEMP")
          usingTemp = True
  else:
      scratchWS = arcpy.GetSystemEnvironment("TEMP")
      usingTemp = True

  # If we're using the system temp directory (a shapefile workspace), look
  #  for a scratch file geodatabase.  If it exists, use it.  If it doesn't,
  #  create it.
  #
  if usingTemp:
    scratchWS = os.path.join(scratchWS, "scratch.gdb")
    if arcpy.Exists(scratchWS):
      return scratchWS
    else:
      arcpy.CreateFileGDB_management(arcpy.GetSystemEnvironment("TEMP"),
                                     "scratch.gdb")

  return scratchWS

def main():
    print getScratchWorkspace(r'E:\7_CDD\HedgeTools\DataTest\Data.gdb\Bois_Test_Skelet')


if __name__ == '__main__':
    main()
