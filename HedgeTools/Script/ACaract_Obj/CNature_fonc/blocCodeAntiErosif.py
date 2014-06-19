#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Villierme
#
# Created:     17/07/2013
# Copyright:   (c) Villierme 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# bloc code pour Calculer l'azimut d'une ligne
def Azimut(azi):
    if azi<0:azi+=360
    return azi

# bloc code pour evaluer si une haie en travers de la pente ou pas

def Evaluate (pdPente, pdExpo, pdAzi):

    # ************** fonction *********************
    def perpendiculaire(angle):
        Intervales=[]
        # on cherche la perpendiculaire à la pente :
        perpent=angle+90

        # on vérifie que la perpendiculaire n'est pas supérieur à 360
        # qi oui on ajoute 360°
        if perpent>180 : perpent=perpent-180

        # Les bornes sont définis avec +/- 30°
        B1, B2 = perpent-30 , perpent+30

        # Cas normale
        Intervales=[B1,B2,0,0]

        #Cas 1 : si la borne inférieure est négative.
        if B1<0:
            Intervales=[0,B2,B1+180,180]

        #Cas2
        if B2>180:
                Intervales=[0,B2-180,B1,180]
        return Intervales

    # cette fonction evaluera si une haie se positionne avec un angle +/- 30° à la perpendiculaire de la pente.
    # on déclare les fonctions qui seront utilisées.
    # 1 ) il faut évaluer si la haie est sur une pente de plus de 7 ° si non on n'est pas sur une pente
    #     de plus de 7°
    # 2) on évalue la l'angle de la haie sur 180°

    # on ramène l'angle à 180°
    if pdAzi>180 : pdAzi-=180

    if pdPente==0 : AntiErosif = "non"
    if pdExpo==-1 : AntiErosif = "non"
    if pdPente==1 :

        # b1, b2 , b3, b4 récupère respectivement les enregistrement de la liste.
        Intervales = perpendiculaire(pdExpo)
        b1, b2, b3, b4 = Intervales
        # on teste si l'azimut de la haie se trouve dans l'intervales de la perpendiculaire à +/-30
        if b1<pdAzi<b2 or b3<pdAzi<b4 :
            AntiErosif = "oui"
        else : AntiErosif = "non"

    return AntiErosif


