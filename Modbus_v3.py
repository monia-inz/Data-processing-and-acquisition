"""
Communication Onduleur en Modbus standard
"""
import os
import sys
import time
from datetime import datetime

import minimalmodbus
import serial

import Com_Lib as com
from Data_send_ftp import send_alarm
from Init_INV import Alarms

TIMEOUT = 0.3
DEFAULT_BAUD = 9600

global measures
measures = []

SLAVE_ERRORS = {
        "Slave reported illegal function" :1,
        "Slave reported illegal data address" :2,
        "Slave reported illegal data value" :3,
        "Slave reported device failure" :4,
        "Slave reported device busy" :6,
        "Slave reported negative acknowledge" :7,
        "Slave reported memory parity error" :8,
        "Slave reported gateway path unavailable" :10,
        "Slave reported gateway target device failed to respond" :11,
        "No communication with the instrument (no answer)" :12
    }

STORED_VALUE = [
    "SN", "Pac", "Status"
]

def init_Serial(inst, my_Config):

    inst.serial.timeout = TIMEOUT
    inst.serial.baudrate = my_Config.daq_Baudrate
    inst.serial.bytesize = 8
    inst.serial.parity   = serial.PARITY_NONE
    inst.serial.stopbits = 1
    inst.serial.timeout=int(my_Config.daq_Timeout_RTU)/1000


def test_bit(n,b):

    n &= (1<<b)

    n = (n  == (1<<b))
    return n


def val_format(value, my_Config, i, file_var, debug):
    """Formattage de la valeur

    avec le champ varScale présent dans le fichier de def on met à la bonne
    échelle la valeur

    Args:
        * my_Config (Objet Config): Objet config créé à partir des fichiers de 
            configuration
        * file_var (Dict): Dict contenant le fichiers de définition de 
            l'onduleur
        * debug (integer): Variable autorisant l'affichage de certains printout.

    Returns:
        value: valeur formattée
    """

    var_type = file_var[i]['varType']

    if var_type != 'STR' and (file_var[i]['varScale'] != 1):

        if debug > 2:
            com._box("Type de donnée: "+str(var_type))
            com._box("Valeur retournée par l'onduleur: "+str(value))

        try:
            value = int(value) // int(file_var[i]['varScale'])

        except TypeError or ValueError:
            raise

    if (file_var[i]['varUnit'] == 's' ):
        try:
            value = int(value)
            if (value > 2600000000):
                pass
            else:
                value = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(value))
        except ValueError:
            raise

    return str(value)


def serial_read(
    inst, 
    var_register, 
    var_type, 
    var_signed, 
    var_nb_register
):
    """Passe par les fonctions de minimalmodbus pour communiquer en Modbus

    Le type de variable est utilisé pour connaitre la bonne fonction de
    la librairie MinimalModbus à utiliser

    U16 demande un registre (16 bits)

    U32 demande 2 registres (32 bits)

    mult demande x registres (champ varNbRegister dans le fichier de definition)

    STR demande x registres (champ varNbRegister dans le fichier de definition)

    Args:
        * inst minimalmodbus.Instrument): Instrument permettant la 
            communication onduleur (parent Serial)
        * var_register (string): registre qu'occupe la mesure
        * var_type (string): type de la mesure
        * var_signed (string): 0 ou 1 si signé ou non
        * var_nb_register (string): nombre de registres qu'occupe la mesure 
            si une mesure est codé sur plus de 16 bits, on renseigne le 
            nombre de registre consécutif dans le fichier de definition

    Returns:
        value (integer): valeur retournée par l'onduleur

    """

    if var_type=='U16' or var_type=='I16' or var_type=='S16':

        value = inst.read_register(
            int(var_register),
            0,
            3, 
            not bool(var_signed)
        ) 

    elif var_type=='U32' or var_type=='I32' or var_type=='S32':

        value = inst.read_long(
            int(var_register),
            3, 
            not bool(var_signed)
        ) 

    elif var_type=='mult':

        value = inst.read_registers(
            int(var_register),
            int(var_nb_register),
            3
        ) 

    elif var_type=='U64' or var_type=='I64' or var_type=='S64':

        value = inst.read_registers(
            int(var_register),
            4,
            3
        ) 

    elif var_type=='STR':

        value=inst.read_string(
            int(var_register), 
            int(var_nb_register),
            3
        )
    else:
        
        value = "";

    return value


def command_serial(
    inst, 
    my_Config, 
    file_var, 
    i,
    count_error,
    debug
):
    """Gestion des erreurs

    Args:
        * inst (minimalmodbus.Instrument): Instrument permettant la 
            communication onduleur (parent Serial)
        * my_Config (Objet Config): Objet config créé à partir des fichiers de 
            configuration
        * file_var (Dict): Dictionnaire contenant le fichiers de définition de 
            l'onduleur
        * i (integer): la valeur i est la position à laquel on se trouve dans 
            le fichier de définition (ième mesure)
        * count_error (integer): nombre d'erreur actuellement
        * debug (integer): [description]

    Returns:
        value: la valeur retournée par l'onduleur
        count_error: le nombre d'erreur (5 si aucune erreur, +1 sinon)


    """
    try:
        try:

            var_register = file_var[i]['varRegister']
            var_type = file_var[i]['varType']
            var_use = file_var[i]["varUse"]
            var_name = file_var[i]["varName"].strip()
            var_signed = file_var[i]['varSigned']
            var_nb_register = file_var[i]['varNbRegister']

            if not '#' in var_register and not 'calc' in var_use and not 'No' in var_use:

                value = serial_read(
                    inst,
                    var_register,
                    var_type,
                    var_signed,
                    var_nb_register
                )

                value = val_format(
                    value, 
                    my_Config, 
                    i, 
                    file_var,  
                    debug
                )

            else:
                if debug > 2:
                    com._box("Le registre est commenté ou non implémenté")

                return "0",7

        except minimalmodbus.NoResponseError:
            raise

        except Exception as e: 

            if debug >= 2: 
                com._box("Registre: "+str(file_var[i]['varRegister']))
                com._box("ERREUR de type: "+str(sys.exc_info()[1]))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                com._box("ERROR : "+str(e)+ " l:" +str(exc_tb.tb_lineno))
                # return "0", 5

            try:

                error = SLAVE_ERRORS[str(e)]
                value = "Err: "+str(error)

                inst.serial.flush()

                count_error = 3

                return value, count_error
                
            except KeyError:

                time.sleep(1)
                value = "Err: Erreur requête"
                count_error += 1

                return value, count_error
            
    except minimalmodbus.NoResponseError:

        if debug >=2:
            com._box("Registre: "+str(file_var[i]['varRegister']))
            com._box("ERREUR de type: "+str(sys.exc_info()[1]))
        
        value = "Err: 12"
        
        inst.serial.flush()
        count_error += 1

        return value, count_error

    if(var_use =="stat"):
        if value != "Err: Erreur requête":
            status_Alarms.update(               
                {
                    var_name:
                    value
                }
            )
    
    count_error = 5
    return value, count_error


def retrieve_value(
    inst, 
    addr, 
    my_Config, 
    file_var, 
    inv_n, 
    debug
):
    """Compte le nombre de fois que la communication retourne une erreur

    Si la communication retourne 3 fois une erreur la valeur est rejetée

    Si l'erreur est une erreur 12, l'onduleur ne communique plus, on sort
    donc de la boucle, aucune valeur n'est retournée

    Boucle for pour chaque mesure dans le fichier de définition

    Args:
        * inst (minimalmodbus.Instrument): Instrument permettant la 
            communication onduleur (parent Serial)
        * addr (integer): Adresse de l'onduleur
        * my_Config (Objet Config): Objet config créé à partir des fichiers de 
            configuration
        * file_var (Dict): Dict contenant le fichiers de définition de 
            l'onduleur
        * inv_n (integer): Numéro de l'onduleur
        * debug (integer): Variable autorisant l'affcihage de certains printout.

    Returns:
        None

    """
    global status_Alarms
    global epice_tmp

    stat = "NOT OK"
    value = ""
    
    if debug >= 2:
        com._box("Envoi de la trame à l'adresse: "+str(addr))

    temporary_values = {}

    for i in range(0,len(file_var)):

        if debug > 2:
            com._box("Registre: "+str(file_var[i]['varRegister']))

        count_error = 0

        while count_error < 3:

            value, count_error = command_serial(
                inst, 
                my_Config, 
                file_var, 
                i,
                count_error,
                debug
            )
        
        
        if "Err" in value and value != "Err: 12":
            value = ""

        temporary_values.update(
            {
                file_var[i]["varIndex"]:value
            }
        )

        if file_var[i]["varEpice"] !="0":
            if file_var[i]["varOption1"] == "moy":

                com.keep_in_memory(inv_n, value, file_var[i]["varEpice"], my_Config.number_of_inv)
                epice_tmp.update({
                    file_var[i]["varEpice"]:"moy"
                }) 
            else:
                epice_tmp.update({
                    file_var[i]["varEpice"]:value
                }) 

        if value == "Err: 12":
            stat = "NOT OK"

            com.create_json(inv_n ,"Status", stat)
            break

        elif count_error != 7:
            stat = "OK"
            com.create_json(inv_n ,"Status", stat)

        # Mise en place d'une valeur calculée par rapport à d'autres
        if file_var[i]["varUse"]=='calc':

            tmp = file_var[i]["varRegister"]
            tmp = tmp.split(',')

            if value == "" or ("Err" in value):
                value = 0

            for index in tmp:

                value = int(value) + int(temporary_values[index])
            
            value = value/int(file_var[i]["varReqIndex"])

            epice_tmp.update({
                file_var[i]["varEpice"]:str(("%.2f" % value))
            }) 

        if file_var[i]["varName"] in STORED_VALUE:

            com.create_json(inv_n ,file_var[i]["varName"], value)


def check_communication(my_Config):
    """Fonction non utilisée de vérification de la bonne communication

    On envoit une requête sur le premier registre connu et on regarde la réponse

    Args:
        * my_Config (Class Config): [description]

    Returns:
        string: Contient une phrase qui décrit l'etat de l'onduleur
    """
    communication = []

    for i in range(0,int(my_Config.number_of_inv)):

        file_var = my_Config.file_var[i]
        inst = minimalmodbus.Instrument(my_Config.port,int(my_Config.addr[i]))
        init_Serial(inst ,my_Config)
        
        value, _ = command_serial(
            inst, 
            my_Config, 
            file_var, 
            0,
            0,
            0
        )
        
        if value == "Err: 12":
            communication.append("Inverter_"+str(i+1)+": Not OK\\n")
            
        else:
            communication.append("Inverter_"+str(i+1)+": OK\\n")

    return communication
            

def routine_acq(
    my_Config, 
    debug, 
    path_to_file_output,
    writing
):
    """Fonction ouvrant la connexion au port pour chaque onduleur.

    Le tableau de mesure est reinitialisé après une communication complète d'un
    onduleur, les Alarmes également.

    Args:
        * my_Config (Class Config): Objet config créé à partir des fichiers de 
            configuration
        * debug (integer): Variable autorisant l'affcihage de certains printout.
        * path_to_file_output (string): Chemin vers l'emplacement du fichier
        * writing (bool): Permet d'ordonner l'ecriture des prochaines données 
            dans le .csv.
    
    Returns:
        None

    """

    inverter_status = {}

    global measures
    global epice_tmp
    global status_Alarms
    global current_Alarms


    for i in range(0,int(my_Config.number_of_inv)):

        status_Alarms = {}
        measures = []
        epice_tmp = {}
        measures.append(com.date_now_utc())
        measures.append("ONDULEUR_NUMERO_"+str(i+1))

        file_var = my_Config.file_var[i]
        inst = minimalmodbus.Instrument(my_Config.port,int(my_Config.addr[i]))

        init_Serial(inst ,my_Config)

        if debug > 2:
            inst.debug = True

        retrieve_value(
            inst, 
            my_Config.addr[i], 
            my_Config, 
            file_var, 
            i+1,
            debug
        )

        current_Alarms.update(
            {
                "ONDULEUR_"+str(i+1): 
                status_Alarms
            }
        )
        
        if writing:

            if not epice_tmp:
                continue

            max_key = com.max_key(epice_tmp)
            for j in range(0, max_key):
                
                measures.append("")

            for key in epice_tmp.keys():
                if epice_tmp[key] == "moy":
                    measures[int(key)+1] = com.calc_from_memory(i+1, key)
                else:
                    measures[int(key)+1]=epice_tmp[key]
            
            try:
                com.write_csv_existing(
                    path_to_file_output, 
                    measures,
                    'a', 
                    i+1, 
                    my_Config.number_of_inv,
                    True
                )

            except FileNotFoundError:

                path_to_file_output = com.create_date_file(my_Config.output_file)

                for k in range(0,int(my_Config.number_of_inv)):
    
                    com.write_csv_epice(
                        path_to_file_output, 
                        ['ONDULEUR_NUMERO_'+str(k+1)],
                        'a'
                    )

                os.chmod(path_to_file_output, 0o777)

                com.write_csv_existing(
                    path_to_file_output, 
                    measures,
                    'a', 
                    i+1, 
                    my_Config.number_of_inv,
                    True
                )


def main(my_Config, debug):
    """Fonction principal dans la mise en palce du csv et lancement des requête.

    On vérifie que cette routine ne tourne pas déjaà puis on place un fichier
    .pid afin de pouvoir prévenir que la routine est déjà en marche. 

    Vérification de la présence d'un fichier csv de donnée actuel. S'il n'y 
    en a pas, on le créé.

    acquisition_time(datetime) est la date actuelle + 10 minutes. Si la date
    actuelle depasse cette variable

    Args:
        * my_Config (Class Config): Objet config créé à partir des fichiers de 
            configuration.
        * debug (integer): Variable autorisant l'affcihage de certains printout.

    Returns:
        None

    """

    global status_Alarms
    global current_Alarms

    my_Alarms = Alarms(my_Config)
    my_Config.check_file_json(STORED_VALUE)

    # now_plus_10 = now + timedelta(minutes = 10)
    acquisition_time = com.time_ten()

    pid = str(os.getpid())
    pidfile = "/tmp/routine.pid"

    open(pidfile, 'w').write(pid)

    try:

        while True:

            current_Alarms= {}   

            # Precise date format  

            path_to_file_output = com.create_date_file(my_Config.output_file)

            path_to_file_output = path_to_file_output.replace("/DATA/","/DATA/tmp/")
            path_to_file_output = path_to_file_output + ".gz"

            Exists = os.path.isfile(path_to_file_output)

            if not Exists:   
                path_to_file_output = path_to_file_output.replace("/DATA/tmp/","/DATA/")
            
                Exists = os.path.isfile(path_to_file_output)

                if not Exists:
                    path_to_file_output = path_to_file_output.replace(".gz","")

                    Exists = os.path.isfile(path_to_file_output)

            if not Exists:
                
                for k in range(0,int(my_Config.number_of_inv)):

                    com.write_csv_epice(
                        path_to_file_output, 
                        ['ONDULEUR_NUMERO_'+str(k+1)],
                        'a'
                    )

                os.chmod(path_to_file_output, 0o777)

            if datetime.now() >= acquisition_time:
                
                routine_acq(
                    my_Config, 
                    debug,
                    path_to_file_output,
                    writing = True
                )
                
                acquisition_time = com.time_ten()

                #now_plus_10 = datetime.now() + timedelta(minutes = 10)
                continue

            routine_acq(
                my_Config,
                debug, 
                path_to_file_output,
                writing = False
            )
            
            alarm, output_file_alarm = my_Alarms.compare_alarms(current_Alarms)

            if alarm:

                send_alarm(my_Config, output_file_alarm, debug)

    finally:
        os.unlink(pidfile)

if __name__=="__main__":
    main()
