"""
Communication Modbus SunSpec
"""
import os
import sys
import time

from datetime import datetime

sys.path.append('/home/pi/src/pysunspec2')
import sunspec2.modbus.modbus as mb
import sunspec2.modbus.client as client

import Com_Lib as com

from Data_send_ftp import send_alarm
from Init_INV import Alarms

global measures
measures = []

STORED_VALUE = [
    "SN", "Pac", "Status"
]

ss_Errors = [mb.ModbusClientTimeout, mb.ModbusClientException, mb.ModbusClientError]

def sunspec_scan(
    inst, 
    addr, 
    my_config, 
    file_var, 
    sun_models, 
    inv_n, 
    debug
):

    global measure_tmp

    models = {}

    for j in range(0, len(sun_models)):

        models.update(
        {
            sun_models[j]['varIndex']:
            sun_models[j]['varName']
        })

    try:
        inst.scan()

    except mb.ModbusClientTimeout as e:

        measures.append("Erreur de Communication")


    try:
        for k in range(0, len(file_var)):

            if file_var[k]['varUse'] == "No":
                continue
        
            model = models[str(file_var[k]['varReqIndex'])]

            variable = file_var[k]['varName']

            value = getattr(inst,model)
            variable = getattr(value[0], variable)
            value = variable.value

            if file_var[i]["varEpice"] !="0":
    
                measure_tmp.update({
                    file_var[i]["varEpice"]:value
                }) 


            if file_var[k]["varName"] in STORED_VALUE:
        
                com.create_json(inv_n ,file_var[k]["varName"], value)

    except Exception as e:

        if debug > 2: 
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("Error: "+str(exc_type)+ " in "+ str(fname)+ " at line: " +str(exc_tb.tb_lineno))
            print("ERROR : "+str(e))


def routine_Acq_Sun(
    my_Config, 
    debug, 
    path_to_file_output,
    writing
):

    global measures
    global measure_tmp
    global status_Alarms
    global current_Alarms

    for i in range(0,int(my_Config.number_of_inv)):

        status_Alarms = {}
        measure_tmp = {}
        measures = []
        measures.append(com.date_now_utc())
        measures.append("ONDULEUR_NUMERO_"+str(i+1))

        file_var = my_Config.file_var[i]

        sun_models = my_Config.file_sun[i]
    
    inst = client.SunSpecModbusClientDeviceRTU(
        slave_id=my_Config.addr[i-1], 
        name=my_Config.port, 
        baudrate=my_Config.daq_Baudrate,
        timeout=int(my_Config.daq_Timeout_RTU)/1000
    )

    sunspec_scan(
        inst, 
        my_Config.addr[i], 
        my_Config, 
        file_var, 
        sun_models,
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

        for j in range(2, len(measure_tmp)+2):
            
            measures.append("")

            for key in measure_tmp.keys():

                measures[int(key)+1]=measure_tmp[key]

        # com.check_new_inverter(
        #     path_to_file_output, 
        #     ['ONDULEUR_NUMERO_'+str(i+1)],
        #     'a', 
        #     i+1, 
        #     file_var
        # )

        com.write_csv_existing(
            path_to_file_output, 
            measures,
            'a', 
            i+1, 
            my_Config.number_of_inv
        )


def main(my_Config, debug):
    
    global status_Alarms
    global current_Alarms

    my_Alarms = Alarms(my_Config)
    my_Config.check_file_json(STORED_VALUE)

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
                
                for j in range(0,int(my_Config.number_of_inv)):
                    
                    com.write_csv_epice(
                        path_to_file_output, 
                        ['ONDULEUR_NUMERO_'+str(j+1)],
                        'a'
                    )

                os.chmod(path_to_file_output, 0o777)

            if datetime.now() >= acquisition_time:
                
                routine_Acq_Sun(
                    my_Config, 
                    debug,
                    path_to_file_output,
                    writing = True
                )
                
                acquisition_time = com.time_ten()

                #now_plus_10 = datetime.now() + timedelta(minutes = 10)
                continue
                

            routine_Acq_Sun(
                my_Config,
                debug, 
                path_to_file_output,
                writing = False
            )

            alarm, output_file_alarm = my_Alarms.compare_alarms(current_Alarms)

            if alarm:

                send_alarm(
                    my_Config, 
                    output_file_alarm, 
                    debug
                )


    finally:
        os.unlink(pidfile)

if __name__=="__main__":
    main()

