import sys
from datetime import datetime
import time
import os
import serial

import gzip, io
from CONFIG import *
import Library

from ftplib import FTP

from Init_INV import Config
import Com_Lib as com
import glob

from shutil import copyfile


def _format(string, convert=False):
    
    try:

        string = str(string, 'utf-8')#string.decode('UTF-8')
        string.replace("b'","")
        string.replace("\r","")
        string.replace("\n","")

    except UnicodeDecodeError:
        string = "Mauvais encodage"

    return string


def put_ftp_files(myConfig, list_of_files, type):

    ftp = FTP(
        myConfig.FTP_Server, 
        myConfig.FTP_Login, 
        myConfig.FTP_Password
    )

    if type =="DATA":
        ftp.cwd('htdocs/DATA/INV')
        path = '/home/pi/src/git/RPI/DATA/'

    elif type =="ALARM":
        ftp.cwd('htdocs/ALARM')
        path = '/home/pi/src/git/RPI/DATA/ALARM/'

    for file in list_of_files:

        with open(file,'rb') as fp:

            file = file.replace(path, "")

            ftp.storbinary('STOR %s' % str(file), fp)

            copyfile(
                path+file, 
                path+"tmp/"+file
            )

            os.remove(path+file)

    ftp.quit()


def send_alarm(myConfig, file_data_o, debug):
    list_of_files = glob.glob('/home/pi/src/git/RPI/DATA/ALARM/Output_ALARM*.csv')

    if myConfig.nosim == "True":
    
        put_ftp_files(myConfig, list_of_files, "ALARM")
        return

    pid = str(os.getpid())
    pidfile = "/tmp/alarm.pid"

    open(pidfile, 'w').write(pid)

    try:
        
        for file_data in list_of_files:
            
            file_tmp = open(file_data, 'rb')
            lines = file_tmp.readlines()
            file_tmp.close()
            
            file_data = file_data.replace("/home/pi/src/git/RPI/DATA/ALARM/", "")

            try:

                gsm = serial.Serial(
                    "/dev/ttyUSB_DEVICE1",
                    baudrate=9600, 
                    timeout=1
                )

            except serial.serialutil.SerialException:
                com._box("GSM_not connected")
                sys.exit()

            com._box("opened port : "+gsm.portstr)

            if gsm.isOpen():

                gsm.write(b'AT\r\n')
                time.sleep(0.5)
                gsm.write(b'AT+FTPPUT=2,0\r\n')
                time.sleep(3)
                timeout = time.time() + 20
                Error = False

                while (_format(gsm.read(gsm.inWaiting())).find('+FTPPUT: 1,0')==-1):
                    time.sleep(0.5)

                    if time.time() < timeout:
                        continue

                    else:
                        Error == True
                        break

                # Mets fin à une communication en cours, si aucune communication est en cours, une erreur sera affichée
                gsm.write(b'AT+FTPPUTOPT="STOR"\r\n')
                time.sleep(0.5)
                gsm.write(b'AT+SAPBR=1,1\r\n')
                time.sleep(0.5)

                gsm.write(b'ATE1\r\n')
                time.sleep(0.5)
                
                # Test de la force du signal
                gsm.write(b'AT+CSQ\r\n')
                time.sleep(0.5)

                gsm.write(b'AT+SAPBR=3,1,"CONTYPE","GPRS"\r\n')
                time.sleep(0.5)
                
                # initialisation des variable du serveur FTP
                apn = bytes(myConfig.GPRS_Apn, 'utf-8')
                gsm.write(b'AT+SAPBR=3,1,"APN","'+apn+b'"\r\n')
                time.sleep(1)
                #5
                gsm.write(b'AT+FTPPUTNAME="'+bytes(file_data, 'utf-8')+b'"\r\n')
                time.sleep(0.5)
                #5
                gsm.write(b'AT+FTPPUTPATH="'+bytes(myConfig.FTP_dir_alarm, 'utf-8')+b'"\r\n')
                time.sleep(0.5)
                #5
                gsm.write(b'AT+FTPSERV="'+bytes(myConfig.FTP_Server, 'utf-8')+b'"\r\n')
                time.sleep(0.5)
                #5
                gsm.write(b'AT+FTPUN="'+bytes(myConfig.FTP_Login, 'utf-8')+b'"\r\n')
                time.sleep(0.5)
                #5
                gsm.write(b'AT+FTPPW="'+bytes(myConfig.FTP_Password, 'utf-8')+b'"\r\n')
                time.sleep(0.5) 
                #5
                gsm.write(b'AT+FTPPORT="'+bytes(myConfig.FTP_Port, 'utf-8')+b'"\r\n')
                time.sleep(0.5)
                if debug>1:com._box("O89: "+_format(gsm.read(gsm.inWaiting())))
                #5
                gsm.write(b'AT+FTPPUT=1\r\n')
                time.sleep(0.5)
                if debug>1:com._box("O90: "+_format(gsm.read(gsm.inWaiting())))
                
                # Attente d'une reponse du serveur afin de pouvoir écrire 
                timeout = time.time() + 20
                Error = False

                while (_format(gsm.read(gsm.inWaiting())).find('+FTPPUT:')==-1):
                    time.sleep(0.5)

                    if time.time() < timeout:
                        continue

                    else:
                        Error == True
                        break

                count= 0

                if Error:
                    com._box("ERROR: No answer from FTP server")
                    sys.exit()

                #Chaque ligne doit être écrite, sans dépasser la limite d'octets fixée par le serveur
                for line in lines:

                    time.sleep(1)
                    
                    if count+int(len(line)) <= 1360:
                        
                        count+=int(len(line))

                        gsm.write(b'AT+FTPPUT=2,'+bytes(str(len(line)),'utf-8')+b'\r\n')
                        time.sleep(0.5)

                        gsm.write(line)

                        if debug>1:print("O93: "+_format(gsm.read(gsm.inWaiting())))

                    else:

                        gsm.write(b'AT+FTPPUTOPT="APPE"\r\n')

                        count = 0+int(len(line))

                        gsm.write(b'AT+FTPPUT=2,'+bytes(str(len(line)),'utf-8')+b'\r\n')
                        time.sleep(0.5)
                        gsm.write(line)

                        if debug>1:print("O94: "+_format(gsm.read(gsm.inWaiting())))

                copyfile(
                    "/home/pi/src/git/RPI/DATA/ALARM/"+file_data, 
                    "/home/pi/src/git/RPI/DATA/ALARM/tmp/"+file_data
                )

                os.remove("/home/pi/src/git/RPI/DATA/ALARM/"+file_data)

                gsm.write(b'AT+FTPPUT=2,0\r\n')
                time.sleep(1)
                timeout = time.time() + 5
                Error = False

                while (_format(gsm.read(gsm.inWaiting())).find('+FTPPUT: 1,0')==-1):

                    time.sleep(0.5)

                    if time.time() < timeout:
                        continue

                    else:
                        Error == True
                        break

                if debug>1:print("O89: "+_format(gsm.read(gsm.inWaiting())))
        
    finally:
        os.unlink(pidfile)

        
def main(debug=2, alarm = False):
    
    # * means all if need specific format then *.csv

    list_of_files = glob.glob('/home/pi/src/git/RPI/DATA/*.gz')

    myConfig=Config()

    if myConfig.nosim == "True":

        put_ftp_files(myConfig, list_of_files, "DATA")
        sys.exit(2)

    while os.path.exists('/tmp/alarm.pid'):
        time.sleep(5)
        
    errcount = 0

    for file_data in list_of_files:
        
        file_tmp = open(file_data, 'rb')
        lines = file_tmp.readlines()
        file_tmp.close()
    
        file_data = file_data.replace("/home/pi/src/git/RPI/DATA/", "")

        gsm = serial.Serial("/dev/ttyUSB_DEVICE1", baudrate=9600, timeout=1)

        com._box("opened port : "+gsm.portstr)

        if gsm.isOpen():

            #1
            gsm.write(b'AT\r\n')
            time.sleep(0.5)
            gsm.write(b'AT+FTPPUT=2,0\r\n')
            time.sleep(3)
            timeout = time.time() + 20
            Error = False

            while (_format(gsm.read(gsm.inWaiting())).find('+FTPPUT: 1,0')==-1):
                time.sleep(0.5)
                if time.time() < timeout:
                    continue
                else:
                    break

            # Mets fin à une communication en cours, si aucune communication est en cours, une erreur sera affichée
            gsm.write(b'AT+FTPPUTOPT="STOR"\r\n')
            time.sleep(0.5)
            gsm.write(b'AT+SAPBR=1,1\r\n')
            time.sleep(0.5)

            gsm.write(b'ATE1\r\n')
            time.sleep(0.5)
            
            # Test de la force du signal
            gsm.write(b'AT+CSQ\r\n')
            time.sleep(0.5)

            gsm.write(b'AT+SAPBR=3,1,"CONTYPE","GPRS"\r\n')
            time.sleep(0.5)
            
            # initialisation des variable du serveur FTP
            apn = bytes(myConfig.GPRS_Apn, 'utf-8')
            gsm.write(b'AT+SAPBR=3,1,"APN","'+apn+b'"\r\n')
            time.sleep(1)
            #5
            gsm.write(b'AT+FTPPUTNAME="'+bytes(file_data, 'utf-8')+b'"\r\n')
            time.sleep(0.5)
            #5
            gsm.write(b'AT+FTPPUTPATH="'+bytes(myConfig.FTP_dir_data, 'utf-8')+b'"\r\n')
            time.sleep(0.5)
            #5
            gsm.write(b'AT+FTPSERV="'+bytes(myConfig.FTP_Server, 'utf-8')+b'"\r\n')
            time.sleep(0.5)
            #5
            gsm.write(b'AT+FTPUN="'+bytes(myConfig.FTP_Login, 'utf-8')+b'"\r\n')
            time.sleep(0.5)
            #5
            gsm.write(b'AT+FTPPW="'+bytes(myConfig.FTP_Password, 'utf-8')+b'"\r\n')
            time.sleep(0.5) 
            #5
            gsm.write(b'AT+FTPPORT="'+bytes(myConfig.FTP_Port, 'utf-8')+b'"\r\n')
            time.sleep(0.5)
            if debug>1:com._box("O89: "+_format(gsm.read(gsm.inWaiting())))
            #5
            gsm.write(b'AT+FTPPUT=1\r\n')
            time.sleep(0.5)
            if debug>1:com._box("O90: "+_format(gsm.read(gsm.inWaiting())))
            
            # Attente d'une reponse du serveur afin de pouvoir écrire 
            timeout = time.time() + 20
            Error = False

            while (_format(gsm.read(gsm.inWaiting())).find('+FTPPUT:')==-1):
                time.sleep(0.5)

                if time.time() < timeout:
                    continue

                else:
                    Error == True
                    break

            count= 0


            if Error:
                com._box("ERROR: No answer from FTP server")
                errcount= errcount + 1
                break

            # Chaque ligne doit être écrite, sans dépasser la limite d'octets fixée par le serveur
            for line in lines:
                time.sleep(1)
                
                if count+int(len(line)) <= 1360:
                    
                    count+=int(len(line))

                    gsm.write(b'AT+FTPPUT=2,'+bytes(str(len(line)),'utf-8')+b'\r\n')
                    time.sleep(0.5)

                    gsm.write(line)

                    if debug>1:print("O93: "+_format(gsm.read(gsm.inWaiting())))

                else:

                    gsm.write(b'AT+FTPPUTOPT="APPE"\r\n')

                    count = 0+int(len(line))

                    gsm.write(b'AT+FTPPUT=2,'+bytes(str(len(line)),'utf-8')+b'\r\n')
                    time.sleep(0.5)
                    gsm.write(line)
                    if debug>1:print("O94: "+_format(gsm.read(gsm.inWaiting())))

            copyfile(
                "/home/pi/src/git/RPI/DATA/"+file_data, 
                "/home/pi/src/git/RPI/DATA/tmp/"+file_data
            )

            os.remove("/home/pi/src/git/RPI/DATA/"+file_data)

            gsm.write(b'AT+FTPPUT=2,0\r\n')
            time.sleep(3)
            timeout = time.time() + 20
            Error = False

            while (_format(gsm.read(gsm.inWaiting())).find('+FTPPUT: 1,0')==-1):

                time.sleep(0.5)
                if time.time() < timeout:
                    continue

                else:
                    Error == True
                    break
            
            if debug>1:print("O89: "+_format(gsm.read(gsm.inWaiting())))



if __name__=="__main__":
    main()