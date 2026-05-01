import configparser #Lecture et écriture de fichiers de configuration
import os# execute un interpreteur de commande
import sys#Paramètres et fonctions propres à des systèmes
import time#acces auc temps et conversion
import json#Le module JSON est principalement utilisé pour convertir le dictionnaire python ci-dessus en une chaîne JSON qui peut être écrite dans un fichier
from datetime import datetime#Lorsque vous utilisez datetime import datetime, vous importez uniquement la classe datetime à partir du module datetime. 

import Com_Lib as com # je pense intégaration de la librairie


class Config:#objet qui regroupe plusieurs “fonctions”
       
    def __init__(self):#aucune valeur à retour attendue

        self.file_stat = []#renseigne le fichier de définition car certaines marques d'onduleur possèdent plusieurs types de modèles
        self.file_var = []
        self.number_of_inv = 1
        self.addr = []
        self.inv_Type = []
        self.SN = []
        self.file_var_name = []
        self.model_name = []

        config_path = "/home/pi/src/git/RPI/CONFIG/"

        com._box()
        com._box("INITIALISATION DES VARIABLES ONDULEURS", True)# condition de if else
        com._box()#utilise cette fonction pour afficher des infos importantes
        com.check_existsing_ini(
           config_path+'INI_Time.ini', 
           config_path
        )
        com.check_existsing_ini(
           config_path+'INI_INV.ini', 
           config_path
        )
        com.check_existsing_ini(
            config_path+'INI_config.ini', 
           config_path
        )
        configParser = configparser.RawConfigParser()# On créé un nouvel objet "config" 
        configFilePath = config_path+r'INI_INV.ini' #  savoir ou se trouve ton fichier de configuration 
        #relier à la ligne config_path = "/home/pi/src/git/RPI/CONFIG/"
        configParser.read(configFilePath)#le configparser doit lire le configfilepath

        self.number_of_inv = configParser.get('CONFIG-INV','INV_N') #Nombre d'onduleur
        self.file_stat = str(configParser.get('CONFIG-INV','INV_Ini_stat')) 
        self.output_file = "/home/pi/src/git/RPI/DATA/Output_INV"# appel le fichier self qui contient la config qui 
        #permette d'aller chercher le fichier

        for i in range(0,int(self.number_of_inv)):
        
            self.model_name.append(str(configParser.get('CONFIG-INV', 'inv_model_'+str(i))))#permet d'intégerer un élément à  la liste précédente

        self.mode = str(configParser.get('CONFIG-INV', 'INV_mode'))

        for i in range(0,int(self.number_of_inv)):

           self.file_var.append(configParser.get('CONFIG-INV', 'inv_var_'+str(i)))
           com.check_existsing_ini(
                config_path+str(self.model_name[i])+'/'+str(self.file_var[i]),# opération division enetre deux variables 
                config_path
           )
           self.file_var[i] = config_path+str(self.model_name[i])+'/'+str(self.file_var[i])# va chercher les fichiers et les affiches dans model nameet self var 
           self.file_var_name.append(self.file_var[i].replace(config_path+str(self.model_name)+'/', ""))# remplacer une fonction puis intègre un élément 

        com.check_existsing_ini(# affiche les éléments des fichiers 
           config_path+str(self.model_name)+'/'+str(self.file_stat),
           config_path
        )

        self.file_stat = config_path+str(self.model_name)+'/'+str(self.file_stat)

        for i in range(0,int(self.number_of_inv)):

            try:
              self.file_var[i] = com.open_csv(self.file_var[i])# permet d'ouvrir le fichier excel

            except OSError:
              continue #if else du python 

        for i in range(0,int(self.number_of_inv)):

            self.addr.append(int(configParser.get('CONFIG-INV', 'inv_addr_'+str(i)),0))
            #self.inv_Type.append(str(configParser.get('CONFIG-INV', 'INV_Type['+str(i))))
            #self.SN.append(str(configParser.get('CONFIG-INV', 'inv_sn_'+str(i))))

        configParser = configparser.RawConfigParser()   
        configFilePath = config_path+r'INI_config.ini' 
        configParser.read(configFilePath)# lire le fichier configpath

        self.GPRS_Apn = configParser.get('FTP','GPRS_APN') 
        self.GPRS_Login = str(configParser.get('FTP','GPRS_Login'))#permet d'affiche ce qui ets voulu voir figure 19 du rapport
        self.GPRS_Password = str(configParser.get('FTP','GPRS_Password'))
        self.GPRS_Phonenumber = str(configParser.get('FTP','GPRS_PhoneNumber'))
        self.FTP_Server = str(configParser.get('FTP', 'FTP_Server'))
        self.FTP_Login = str(configParser.get('FTP', 'FTP_Login'))
        self.FTP_Password = str(configParser.get('FTP', 'FTP_Password'))
        self.FTP_Port = str(configParser.get('FTP', 'FTP_Port'))
        self.FTP_dir_data = str(configParser.get('FTP', 'ftp_dirdata'))
        self.FTP_dir_alarm = str(configParser.get('FTP', 'ftp_diralarm'))
        self.FTP_dir_config = str(configParser.get('FTP', 'ftp_dirconfig'))
        self.nosim = str(configParser.get('FTP','nosim'))
        self.local_edit = str(configParser.get('FTP','local_edit'))

        configParser = configparser.RawConfigParser()# permet de configurer le temps    
        configFilePath = config_path+'INI_Time.ini' 
        configParser.read(configFilePath)

        self.daq_Period = str(configParser.get('CONFIG-ACQ','DAQ_Period'))# permet d'afficher ce qui ets voulu voir figure 20 du rapport 
        self.daq_Timeout_RTU = str(configParser.get('CONFIG-ACQ','modbus_timeout_rtu'))
        self.daq_Baudrate = str(configParser.get('CONFIG-ACQ','modbus_baudrate'))
        self.port = str(configParser.get('CONFIG-ACQ','PORT'))
        configParser = configparser.RawConfigParser()   
        configFilePath = self.file_stat 
        configParser.read(configFilePath)

        self.stat_code = configParser.items#La méthode items() renvoie un objet view. 
        #L’objet view contient les paires clé-valeur du dictionnaire, sous forme de tuples dans une liste.
    
        com._box()
        com._box("INITIALISATION TERMINEE", True)
        com._box()
    

    def inv_models(self):#permet de savoir ouù son mis les fichiers de registres

        com._box()
        com._box("Recherche de la liste des modeles", True)
        com._box()  
        path = "/home/pi/src/git/RPI/CONFIG/INV_models.txt" 
        try:    
           inv_models = com.open_csv(path,'',';',False)

        except IOError:
           print("Fichier: INV_models.txt introuvable")
        finally:
           return inv_models
   
    def check_file_json(self, stored_value):

        json_path = "/home/pi/src/git/RPI/Library/Portal/inverter_status.json"

        if not os.path.isfile(json_path):
            
            json_object = {}
            tmp = {}
            
            for i in range(0,int(self.number_of_inv)):
                
                for value_name in stored_value:
                    tmp.update({
                    value_name:"0"
                })

                json_object.update({
                    "Inverter_"+str(i+1):
                    tmp
                })

            with open(json_path, 'w') as outfile:

                json.dump(json_object, outfile)
                outfile.close

            os.chmod(json_path, 0o777)
        


class Alarms:

    def __init__(self, my_Config):

        self.alarm_states = {}
        self.alarm_file = "/home/pi/src/git/RPI/DATA/ALARM/LATEST_ALARM.txt"
        self.output_alarm = "/home/pi/src/git/RPI/DATA/ALARM/Output_ALARM"

        if not os.path.isfile(self.alarm_file):#L’instruction if not peut également être utilisée 
            #pour vérifier si une collection de données comme une liste, un dictionnaire est vide ou non
            cfg_alarm_file = open(self.alarm_file, "w")# w est write pour écrire dans le fichier 
            Config = configparser.SafeConfigParser()

            for i in range(0,int(my_Config.number_of_inv)):
            
                Config.optionxform = str
                Config.add_section("ONDULEUR_"+str(i+1))#répertirier les fichiers des onduleurs 
                       
                for j in range(0,len(my_Config.file_var[i])):
                
                    var_name = str(my_Config.file_var[i][j]["varName"]).strip()
                    var_use = my_Config.file_var[i][j]["varUse"]

                    if var_use == "stat":
                        Config.set("ONDULEUR_"+str(i+1), var_name, "0")
            
            os.chmod(self.alarm_file, 0o777)
            Config.write(cfg_alarm_file)
            cfg_alarm_file.close()

         
        try:#fichier de configuration d'alarme

            Config = configparser.RawConfigParser()
            Config.optionxform = str
            Config.read(self.alarm_file)
        
            for i in range(0,int(my_Config.number_of_inv)):

                status = {}
            
                for j in range(0, len(my_Config.file_var[i])):
                    
                    var_use = my_Config.file_var[i][j]["varUse"]
                    var_name = my_Config.file_var[i][j]["varName"].strip()

                    if var_use == "stat":
    
                        status.update(
                        {
                            var_name:
                            str(Config.get("ONDULEUR_"+str(i+1), var_name))
                        })
                        self.alarm_states.update(
                        { 
                            "ONDULEUR_"+str(i+1): 
                            status
                        })

        except configparser.Error:
            
            com._box("Erreur : Fichier d'alarme mal configuré")
            com._box("ERREUR de type: "+str(sys.exc_info()[1]))
            os.remove(self.alarm_file)
            self.__init__(my_Config)
                  

    def compare_alarms(self, current_Alarms):
        """[summary]

        Args:
            current_Alarms (Dict): [description]

        Returns:
            [type]: [description]
        """
        alarm = False
        
        alarm_date = datetime.now().strftime('%x-%X')  

        for key in current_Alarms.keys():

            for cle in current_Alarms[key].keys():

                value = current_Alarms[key][cle]

                try:
                    if str(value) != str(self.alarm_states[key][cle]):
                        alarm = True

                        self.alarm_states[key][cle] = value

                        Config = configparser.SafeConfigParser()
                        Config.optionxform = str
                        Config.read(self.alarm_file)
                        Config.set(key, cle, value)

                        with open(self.alarm_file, 'w') as configfile:
                            Config.write(configfile)

                except KeyError:

                    print("Erreur de clé?")

        if alarm:

            output_file = com.create_date_file(
                self.output_alarm, 
                True,
                precise = True
            )
            
            com.write_alarm(self.alarm_states, output_file, alarm_date, 'a')
        else:
            output_file = ""

        return alarm, output_file

class Config_Sunspec(Config):
       
    def __init__(self):

        super(Config_Sunspec, self).__init__()

        self.file_sun = []
            
        config_path = "/home/pi/src/git/RPI/CONFIG/"
        
        configParser = configparser.RawConfigParser()   
        configFilePath = config_path+r'INI_INV.ini' 
        configParser.read(configFilePath)

        for i in range(0,int(self.number_of_inv)):
                
            try:

                self.file_sun.append(configParser.get('CONFIG-SS', 'INV_sun['+str(i)+']'))
                

                com.check_existsing_ini(
                    config_path+str(self.model_name)+'/'+str(self.file_sun[i]),
                    config_path     
                )
                self.file_sun[i] = config_path+str(self.model_name)+'/'+str(self.file_sun[i])
                self.file_sun[i] = com.open_csv(self.file_sun[i])

            except OSError:
                continue
            
         



    