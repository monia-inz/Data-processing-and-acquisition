import sys
from datetime import datetime

import numpy as np

import Com_Lib as com
import Modbus_Sunspec
import Modbus_v3
from Init_INV import Config, Config_Sunspec
from Library import *


def main(argv = ''):
    
    verbosity = 0
    turn = False
    for arg in sys.argv:
        if arg == '-d' or arg == '-debug':
            verbosity = 2
            turn = False
        elif arg == '-fd':
            verbosity = 3
            turn = False

    my_Config = Config()
    
    if my_Config.mode == 'PP':

        models = my_Config.model_name
        unique = np.unique(my_Config.model_name)

        if len(unique) == 1:
            com._box("MODELE: "+str(models[0]), True)
            com._box()
            com._box("Communication en protocole propriétaire")
            script=str(models[0])
            eval(script+'.main(my_Config, verbosity)')

        else:

            acquisition_time = com.time_ten()

            while True:

                com._box("Communication en protocole propriétaire")

                if datetime.now() >= acquisition_time:
                    for i in range(0,len(models)):

                        com._box("MODELE: "+str(models[i]), True)
                        com._box()
                        com._box("Communication en protocole propriétaire")
                        script=str(models[i])
                        eval(script+'.main(my_Config, verbosity, True, True)')

                    acquisition_time = com.time_ten()

                    continue

                for i in range(0,len(models)):
    
                    com._box("MODELE: "+str(models[i]), True)
                    com._box()
                    com._box("Communication en protocole propriétaire")
                    com._box(models[i])
                    script=str(models[i])
                    eval(script+'.main(my_Config, verbosity, True, True)')

        
    elif my_Config.mode == 'MB':
        com._box("MODBUS", True)
        com._box()
        com._box("Communication en protocole ModBus")
        Modbus_v3.main(my_Config, verbosity)
        
    elif my_Config.mode=='SS':
        com._box("SUNSPEC", True)
        com._box()
        com._box("Communication en protocole SunSpec")
        my_Config = Config_Sunspec()
        Modbus_Sunspec.main(my_Config, verbosity)

    com._box()
    com._box("FIN DE LA COMMUNICATION", True)
    com._box()

if __name__ == "__main__":
    main()
