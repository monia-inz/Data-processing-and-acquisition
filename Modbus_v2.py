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
    inst.serial.baudrate = DEFAULT_BAUD
    inst.serial.bytesize = 8
    inst.serial.parity   = serial.PARITY_NONE
    inst.serial.stopbits = 1
    inst.serial.timeout=int(my_Config.daq_Timeout_RTU)/1000


def test_bit(n,b):

    n &= (1<<b)

    n = (n  == (1<<b))
    return n


def val_format(value, my_Config, i, file_var, debug):

    var_type = file_var[i]['varType']

    if var_type != 'STR' and (file_var[i]['varScale'] != 1):

        if debug > 2:
            com._box("Type de donnée: "+str(var_type))
            com._box("Valeur retournée par l'onduleur: "+str(value))
        try:
            value = value / int(file_var[i]['varScale'])
        except TypeError:
            pass

    if (file_var[i]['varUnit'] == 's' ):
        try:
            value = int(value)
            if (value > 2600000000):
                pass
            else:
                value = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(value))
        except ValueError:
            pass


        #statuses = my_Config.stat_code(str(file_var[i]['varName']))

        # if var_type == 'Bit16' or var_type == 'Bit32':
        #     for l in range (0, len(statuses)):
        #         present=test_bit(int(value), int(statuses[l][0]))
        #         if present:
        #            status_message+= str(statuses[l][1].split(',')[0])+' | '
        #         else:
        #             status_message+=str(statuses[l][1].split(',')[1])+' | '

            # ok = test_bit(my_Config.stat_code(file_var[i]['varName']),)

        # if var_type == "U16":

            # for l in range (0, len(statuses)):

            #     if int(value) == int(statuses[l][0],0):
            #         status_message += str(statuses[l][1]) + ' | '
            #     else:
            #         pass

            #status_message += statuses[str(int(value))]

            #value = inverter.status(register, value)
    return str(value)


def measure_roundtrip_time(instr):

    ADDR_SETPOINT = 0x1001
    SECONDS_TO_MILLISECONDS = 1000
    NUMBER_OF_VALUES = 100
    START_VALUE = 200
    STOP_VALUE = 500
    STEPSIZE = 5

    com._box("Measure request-response round trip time")
    com._box("Setting the setpoint value {} times. Baudrate {} bits/s.".format(
        NUMBER_OF_VALUES, instr.serial.baudrate
    ))

    value = START_VALUE
    step = STEPSIZE
    start_time = time.time()

    for i in range(NUMBER_OF_VALUES):
        if value > STOP_VALUE or value < START_VALUE:
            step = -step
        value += step
        instr.write_register(ADDR_SETPOINT, value, functioncode=6)

    time_per_value = (
        (time.time() - start_time)
        * float(SECONDS_TO_MILLISECONDS)
        / NUMBER_OF_VALUES
    )
    
    com._box("Time per value: {:0.1f} ms.\n".format(time_per_value))


def Serial_read(
    inst, 
    var_register, 
    var_type, 
    var_signed, 
    var_nb_register
):

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

    return value


def command_serial(
    inst, 
    my_Config, 
    file_var, 
    i,
    count_error,
    debug
):

    try:
        try:

            var_register = file_var[i]['varRegister']
            var_type = file_var[i]['varType']
            var_use = file_var[i]["varUse"]
            var_name = file_var[i]["varName"].strip()
            var_signed = file_var[i]['varSigned']
            var_nb_register = file_var[i]['varNbRegister']
            
            if not '#' in var_register:

                value = Serial_read(
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

                return "0",5

        except minimalmodbus.NoResponseError:
            raise

        except Exception as e: 

            if debug >= 2: 
                com._box("Registre: "+str(file_var[i]['varRegister']))
                com._box("ERREUR de type: "+str(sys.exc_info()[1]))

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
            })
    
    count_error = 5
    return value, count_error
    


##########################################################################################
# retrieve_value
##########################################################################################
# Fonction d'envoi de requête sur le port RS485 en Modbus
# * file_var regroupe toutes les variables récupérables. Pour
#   chaque ligne dans file_var, on récupère le registre et le type de la variable
#   La taille de cette variable indiquera quel type de lecture on fait
# * Si la variable est de type string, la taille est dynamique 
#   On récupère la taille de la variable (varNbRegister) et on appelle la fonction
#   de lecture avec un nombre de registre à indiquer
##########################################################################################

#   inst: Instrument correspondant à l'onduleur avec qui on communique
#   addr: Indication de l'adresse de l'onduleur
#   my_Config: Objet Config contenant toutes les informations de/des onduleurs
#   file_var: Fichier listant tout les registres, types, tailles et noms des variables
#   debug: Variable qui active l'affchage d'information

def retrieve_value(
    inst, 
    addr, 
    my_Config, 
    file_var, 
    inv_n, 
    debug
):

    global measures
    global status_Alarms
    stat = "NOT OK"
    value = ""
    
    if debug >= 2:
        com._box("Envoi de la trame à l'adresse: "+str(addr))
    
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

        measures.append(value) 

        if value == "Err: 12":
            stat = "NOT OK"
            break

        if file_var[i]["varName"] in STORED_VALUE:

            com.create_json(inv_n ,file_var[i]["varName"], value)



def check_communication(my_Config):

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
            

def routine_Acq(
    my_Config, 
    debug, 
    path_to_file_output,
    writing
):

    inverter_status = {}

    global measures
    global status_Alarms
    global current_Alarms

    for i in range(0,int(my_Config.number_of_inv)):

        status_Alarms = {}
        measures = []
        measures.append(com.date_now_utc())

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

            com.check_new_inverter(
                path_to_file_output, 
                ['ONDULEUR_NUMERO_'+str(i+1) ],
                'a', 
                i+1, 
                file_var
            )
            com.write_csv_existing(
                path_to_file_output, 
                measures,
                'a', 
                i+1, 
                my_Config.number_of_inv
            )


##########################################################################################
# main
##########################################################################################
# Fonction principal mettant en place la communication
# * La variable global measures peut être modifier par toutes les fonctions
#   elle permet le stockage temporaire des valeurs retournées par l'onduleur
# * Verification de l'existence du fichier csv des valeurs. Si il n'existe
#   pas, on le crée en y introduisant une ligne pour chaque onduleur.
#   Si le fichier existe on introduit chaque ligne de mesure sous le titre de son onduleur
##########################################################################################

def main(my_Config, debug):

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

            if not os.path.isfile(path_to_file_output):
                Exists = False

            else:
                Exists = True

            if Exists == False:
                
                for k in range(0,int(my_Config.number_of_inv)):

                    file_var = my_Config.file_var[k]
                    varIndex = []
                    varIndex.append(0)

                    for j in range(0,len(file_var)):

                        varIndex.append(file_var[j]['varIndex'])

                    com.write_csv(
                        path_to_file_output, 
                        ['ONDULEUR_NUMERO_'+str(k+1)],
                        'a'
                    )

                    com.write_csv(
                        path_to_file_output, 
                        varIndex,
                        'a'
                    )

                os.chmod(path_to_file_output, 0o777)

            if datetime.now() >= acquisition_time:
                
                routine_Acq(
                    my_Config, 
                    debug,
                    path_to_file_output,
                    writing = True
                )
                
                acquisition_time = com.time_ten()

                #now_plus_10 = datetime.now() + timedelta(minutes = 10)
                continue


            routine_Acq(
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
