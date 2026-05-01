import csv
import filecmp
import json
import os
import pickle
import re
import sys
import time
from datetime import datetime, timedelta
from shutil import copyfile

import pytz

def create_json(inverter, name, value):
    """Creation du json d'information

    json utilisé pour renvoyer les informations par sms *

    utilisé pour l'affichage du dashboard sur la page web

    Args:
        * inverter (string): numero de l'onduleur
        * name (string): nom de la variable à stocker
        * value (string): valeur de la variable

    """

    json_path = "/home/pi/src/git/RPI/Library/Portal/inverter_status.json"
    tmp = {}
    tmp.update({
        name:
        value
    })

    data = {}

    with open(json_path) as f:

        try:

            data = json.load(f)

        except Exception as e:

            os.remove(json_path)

            data.update({
                'Inverter_'+str(inverter):
                tmp
            })

        try: 

            data['Inverter_'+str(inverter)].update(tmp)

        except KeyError:

            data.update({
                'Inverter_'+str(inverter):
                tmp
            })

            data['Inverter_'+str(inverter)].update(tmp)
 
    with open(json_path,'w') as json_file:
        json.dump(data, json_file)

    # json_object['Inverter_N_'+str(inverter)][]


def time_ten():

    """Calcul d'une date/heure 10 minutes plus tard

    Returns:
        [datetime]: date/heure actuelle + 10 minutes
    """

    tm = datetime.now()

    discard = timedelta(minutes=tm.minute % 10,
                                 seconds=tm.second,
                                 microseconds=tm.microsecond)
    tm -= discard

    tm += timedelta(minutes=10)
    
    return tm


def _box(description=None, center=False, value=None):

    """Fonction print formattée et datée

    utiliser cette fonction pour afficher des infos importantes

    Args:
        * description (string, optional): texte à afficher. Defaults to None.
        * center (bool, optional): centre le texte. Defaults to False.
        * value (string, optional): [description]. Defaults to None.
    """

    now = datetime.now()
    dt = now.strftime("%d/%m/%y %H:%M:%S ")
    WIDTH = 67
    MAX_WIDTH = 85
    DESCR_WIDTH = 30
    space = " "

    if description is None:
        _print_out(dt+"#"*WIDTH)

    else:
        if value is None and center == False:
            line = dt+"## {}".format(description)

        elif value is None and center == True:
            center_point = int((WIDTH-len(description)-4)/2)
            space = space*center_point
            line = dt+"## "+space+"{}".format(description) 

        else:
            
            line = dt+"## {}:".format(description).ljust(DESCR_WIDTH) + str(value)

        line = line.ljust(MAX_WIDTH - 2) + "##"
        _print_out(line)


def max_key(measures):

    """Calcul de la clé la plus haute du csv epice

    Le fichier csv d'epice a un format standard dans un ordre particulier.

    timestamp || id_inv || pac || uac1 || ...

    Les valeurs demandées aux onduleurs ne sont pas forcément dans cette ordre 
    du csv. 
    
    Args:
        * measures (Dict): Dictionnaire de toutes les clés enregistrées

    Returns:
        [int]: clé la plus haute
    """

    count = 0

    for key in measures.keys():
        
        if count==0:
            max_number = int(key)
            count=1
        
        if max_number < int(key):
            max_number = int(key)

    return max_number


def calc_from_memory(inv_n, epice_index):

    """[summary]

    Args:
        inv_n ([type]): [description]
        epice_index ([type]): [description]

    Returns:
        [type]: [description]
    """

    json_path = "/home/pi/src/git/RPI/DATA/tmp_values/inverter_values.json"

    if not os.path.isfile(json_path):
        return ""

    with open(json_path) as json_file:
        json_object = json.load(json_file)

    tab_values = json_object["Onduleur_"+str(inv_n)][str(epice_index)]
    final_value = sum(tab_values)/len(tab_values)

    json_object["Onduleur_"+str(inv_n)][str(epice_index)] = []

    with open(json_path, 'w') as outfile:

        json.dump(json_object, outfile)
        outfile.close

    return str(final_value)


def keep_in_memory(inv_n, value, epice_index, number_of_inv):
   
    """[summary]

    Args:
        inv_n ([type]): [description]
        value ([type]): [description]
        epice_index ([type]): [description]
        number_of_inv ([type]): [description]
    """

    if value == "Err: 12" and value == "":
        value = 0

    json_path = "/home/pi/src/git/RPI/DATA/tmp_values/inverter_values.json"

    if not os.path.isfile(json_path):
            
        json_object = {}
        dict_values = {}
        for i in range(0,int(number_of_inv)):
            
            json_object.update({
                "Onduleur_"+str(i+1):{}
            })

        tab_values = []

        dict_values.update({
            str(epice_index):tab_values
        })
            
        tab_values.append(int(value))

        json_object.update({
            "Onduleur_"+str(inv_n):dict_values
        })

        with open(json_path, 'w') as outfile:

            json.dump(json_object, outfile)
            outfile.close

        os.chmod(json_path, 0o777)

    else:
        dict_values = {}
        with open(json_path) as json_file:
            json_object = json.load(json_file)

        dict_values = json_object["Onduleur_"+str(inv_n)]

        try:

            tab_values= dict_values[str(epice_index)]

        except KeyError:

            tab_values = []

        tab_values.append(int(value))

        dict_values.update({
            str(epice_index):tab_values
        })

        # tab_values=json_object["Onduleur_"+str(inv_n)][]
        json_object.update({
            "Onduleur_"+str(inv_n):dict_values})
        
        with open(json_path, 'w') as outfile:

            json.dump(json_object, outfile)
            outfile.close

        os.chmod(json_path, 0o777)


def date_now_utc():

    """Transformation de la date en format UTC

    Returns:
        [datetime]: date/heure en format UTC
    """

    dt = datetime.now()
    dt = dt.astimezone(pytz.utc)
    dt = dt.strftime('%x-%X')

    return dt


def create_date_file(output_name, alarm = False, precise = False):

    """Creation d'un fichier de donnée daté

    Args:
        * output_name ([type]): [description]
        * precise (bool, optional): True: fichier daté a la minute, 
            False: fichier daté à l'heure. Defaults to False.

    Returns:
        [string]: chemin vers le fichier créé
    """

    dt = datetime.now()
    dt = dt.astimezone(pytz.utc)

    if precise:
        output_file = output_name+'_'+dt.strftime("%y%m%d")+'_'+dt.strftime("%H%M%S")+".csv"

    else:
        output_file = output_name+'_'+dt.strftime("%Y_%m_%d_%H_00")+".csv"

    if alarm:
        copyfile(
        "/home/pi/src/git/RPI/Library/ALARM_Epices.csv",
        output_file
        )

    return output_file


def write_alarm(alarms, output, date, state):

    """Ecriture des alarmes dans un fichier csv

    Args:
        * alarms (Dict): Double dictionnaire ayant pour clé l'onduleur
        * output (string): Emplacement du fichier d'alarme
        * date (string): Date/heure actuelle
        * state (string): état d'écriture (append ou write)
    """

    with open(output, state, newline='', encoding='utf-8') as csvfile:

        csv_values = csv.writer(csvfile,delimiter=';')

        for key in alarms.keys():

            for cle in alarms[key].keys():

                header = []
                values = []

                values.append(date)
                values.append(key)

                values.append(str(alarms[key][cle]))
                values.append(str(cle))# +" : "+str(alarms[key][cle]))
                
                csv_values.writerow(values)
        

def check_alarm(output, my_Config, my_Alarms):

    """Fonction de verification des alarmes

    Args:
        * output (string): chemin vers le fichier d'alarme
        * my_Config (Objet Config): Objet config créé à partir des 
            fichiers de configuration
        * my_Alarms (Objet Alarms): Objet regroupant les états des alarmes

    Returns:
        [bool]: True: Changement d'état d'une alarme
        [string]: Chemin vers le fichier "pid" ftp
        [string]: Chemin vers le fichier d'alarme
    """

    latest = "/home/pi/src/git/RPI/DATA/ALARM/LATEST_ALARM.txt"
    
    if not os.path.isfile(latest):
        open(latest, 'a').close()
        
    filecmp._cache.clear()
    comp = filecmp.cmp(output, latest, shallow = False)

    if comp == False:
        os.remove(latest)

        pid = str(os.getpid())
        pidfile = "/tmp/ftp_routine.pid"

        if os.path.isfile(pidfile):
            print("%s already exists, exiting" %pidfile)

            while os.path.isfile(pidfile):

                time.sleep(10)

        pidfile="/tmp/ftp.pid"
        open(pidfile, 'w').write(pid)
        return True, pidfile, output

    else:

        os.remove(output)
        return False, "", ""


def write_csv(output, value, state):

    """Fonction d'écriture d'un fichier csv

    Args:
        output (string): Chemin du fichier csv
        value (array): Tableau de valeur à écrire
        state (string): état d'ecriture (append ou write)
    """

    with open(output, state, newline='', encoding='utf-8') as csvfile:

        csv_values = csv.writer(csvfile,delimiter=';')
        csv_values.writerow(value)


def write_csv_epice(output, value, state):
    
    """Fonction de copie du csv standard d'epices

    Args:
        output (string): [description]
        value (array): [description]
        state (string): [description]
    """

    copyfile(
        "/home/pi/src/git/RPI/Library/INI_Epices.csv",
        output
    )
    


def write_csv_existing(output, value, state, no = 1, maxno = 1, epice = False):

    """Ecriture des valeurs dans un csv deja existant

    Args:
        output ([type]): [description]
        value ([type]): [description]
        state ([type]): [description]
        no (int, optional): [description]. Defaults to 1.
        maxno (int, optional): [description]. Defaults to 1.
        epice (bool, optional): [description]. Defaults to False.
    """

    lookup_next = 'ONDULEUR_NUMERO_'+str(no+1)
    cond1 = (lookup_next == 'ONDULEUR_NUMERO_'+str(int(maxno)+1))

    with open(output) as myFile:

        for num, line_next in enumerate(myFile, 1):

            if lookup_next in line_next:
                index = num-1
                break

            elif cond1 :
                index = num

            else:
                index = num
            # elif bool(line_next.strip()) and not cond1 :
            #     print("heya")
            #     index = num
            #     if epice:
            #         index = num+1
            #         break

    with open(output, "r") as f:

        contents = f.readlines()
        value=';'.join(value)
        f.close()
        contents.insert(index, str(value)+'\n')

    with open(output, "w") as f:

        contents = "".join(contents)
        f.write(contents)
         


def check_new_inverter(output, value, state, no, file_var):
    
    """[summary]

    Args:
        output ([type]): [description]
        value ([type]): [description]
        state ([type]): [description]
        no ([type]): [description]
        file_var ([type]): [description]
    """

    lookup = 'ONDULEUR_NUMERO_'+str(no)
    exists = False

    with open(output) as myFile:

        for num, line_next in enumerate(myFile, 1):

            if lookup in line_next:
                exists = True
                break

            elif bool(line_next.strip()):
                index = num
                exists = False
                value = 'ONDULEUR_NUMERO_'+str(no)

    if exists == False:
        varIndex = []

        for j in range(0, len(file_var)):

            varIndex.append(file_var[j]['varIndex'])

        with open(output, "r") as f:
            contents = f.readlines()
        
        contents.insert(index, str(value)+'\n')
        value=';'.join(varIndex)
        contents.insert(index+1, str(value)+'\n')

        with open(output, "w") as f:
            contents = "".join(contents)
            f.write(contents)
      


def _print_out(text):
    
    """[summary]

    Args:
        text ([type]): [description]
    """

    # Python2 and 3 compatible
    sys.stdout.write("{}\n".format(text))
    sys.stdout.flush()


def open_csv(ini_file, newline= '', delimiter=';', dic=True):

    """[summary]

    Returns:
        [type]: [description]
    """

    data = []

    if dic:
        with open(ini_file, newline='') as config:

            reader = csv.DictReader(config, delimiter =';')
            for row in reader:
                
                data.append(row)

        return data

    else:
        with open(ini_file) as config:
            
            reader = csv.reader(config, delimiter=':')
            data = dict(reader)
            
        return data


def check_csv(ini_file):
    
    """[summary]

    Args:
        ini_file ([type]): [description]

    Returns:
        [type]: [description]
    """

    try:

        open(ini_file)
        return True

    except IOError:

        _box("Output file doesn't exist")
        return False


def check_existsing_ini(ini_file, path_strip = ""):
    
    """[summary]

    Args:
        ini_file ([type]): [description]
        path_strip (str, optional): [description]. Defaults to "".
    """

    try:

        with open(ini_file) as f:
            ini_file = ini_file.replace(path_strip, "")
            _box('File: '+ini_file+' found! ** OK' )

    except IOError:
        ini_file = ini_file.replace(path_strip, "")
        _box("File: "+ini_file + " not accessible! ** ERROR")
    
        
