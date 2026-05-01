import sys, getopt
from datetime import datetime
import time
import os
import serial
import configparser

from CONFIG import *

from Init_INV import Config
import Com_Lib as com

import filecmp

from ftplib import FTP

def _format(string, convert=False):
    
    try:

        string = str(string, 'utf-8')#string.decode('UTF-8')
        string.replace("b'","")
        string.replace("\r","")
        string.replace("\n","")

    except UnicodeDecodeError:
        string = "Mauvais encodage"

    return string


def _format_get(string):

    try:
        #string.decode('UTF-8')
        index_start = string.find("[", 0,1500)
        print(string)
        if index_start != -1:
            index_end = string.find("OK",index_start,1500)

            if index_end != -1:
                string = string[index_start:index_end]
                Erreur = False
            else:
                com._box("Message not ok")
                Erreur = True

        else:
            com._box("Not a config file")
            Erreur = True

    except UnicodeDecodeError:
        string = "Mauvais encodage"
        Erreur = True

    return string, Erreur


def put_ftp(myConfig, list_of_config):
    
    ftp = FTP(
        myConfig.FTP_Server, 
        myConfig.FTP_Login, 
        myConfig.FTP_Password
    )

    # ftp.login()
    ftp.cwd(myConfig.FTP_dir_config)

    files=[]

    for file in list_of_config:

        with open('CONFIG/'+file,'rb') as fp:
            try:
                ftp.storbinary('STOR %s' % file, fp)

            except Exception as e:
                return True

    ftp.quit()
    com._box()

    return False

def put_ftp_gprs(myConfig, list_of_config):

    while os.path.exists('/tmp/alarm.pid'):
        time.sleep(5)
        
    errcount = 0

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
            return Error

    for file_data in list_of_config:
        
        file_tmp = open(file_data, 'rb')
        lines = file_tmp.readlines()
        file_tmp.close()

        file_data = file_data.replace("/home/pi/src/git/RPI/CONFIG/", "")
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
    
    return True


def get_ftp_files(myConfig, list_of_config):

    ftp = FTP(
        myConfig.FTP_Server, 
        myConfig.FTP_Login, 
        myConfig.FTP_Password
    )

    # ftp.login()
    ftp.cwd(myConfig.FTP_dir_config)

    files=[]

    for file in list_of_config:

        os.system("mv CONFIG/"+file +" CONFIG/"+file+"_tmp")

        with open('CONFIG/'+file,'wb') as fp:

            ftp.retrbinary('RETR %s' % file, fp.write)

        try:
            myConfig = Config()
            
            comp = filecmp.cmp("CONFIG/"+file, "CONFIG/"+file+"_tmp", shallow = False)
            
            if comp:
                os.system("sudo kill -9 `cat /tmp/routine.pid`")
            
            os.remove("CONFIG/"+file+"_tmp")
            com._box("Files are good, replacing...")

            os.system("chown pi CONFIG/"+file)

        except Exception as e:

            com._box("Files are wrong")
            print(e)

            if os.path.exists("CONFIG/"+file+"_tmp"):

                os.remove("CONFIG/"+file)
                os.system("mv CONFIG/"+file+"_tmp" +" CONFIG/"+file)

    ftp.quit()
    com._box()


def _wait_end_get(gsm):

    timeout = time.time() + 20
    Error = False
    state = _format(gsm.read(gsm.inWaiting()))

    while (state.find('+FTPGET: 1,0') == -1):

        time.sleep(0.3)
        state = _format(gsm.read(gsm.inWaiting()))

        if time.time() < timeout:
            continue

        elif state.find('+CME ERROR: 3') != -1:
            com._box("still in get session")
            time.sleep(3)

        elif state.find('OK') != -1:
            com._box("Can continue")
            break

        else:
            Error = True
            break


def main(argv, debug=3, alarm = False):

    """Fonction de telechargement d'un fichier depuis le serveur FTP

    Si nosim est à True dans INI_config.ini, on n'utilisera pas le 
    port série. On passe directement avec la librairie "ftplib" 
    pour communiquer avec le serveur FTP.
    
    Sinon une communication sur le port série ou se trouve le module
    SIM est lancé. Un objet "gsm" est créé.

    Les commandes "AT" sont utilisées par le module SIM

    Args:
        argv (): [description]
        debug (int, optional): [description]. Defaults to 3.
        alarm (bool, optional): [description]. Defaults to False.
    """

    list_of_config= ["INI_INV.ini", "INI_config.ini", "INI_Time.ini"]

    # * means all if need specific format then *.csv
    try:
        opts, args = getopt.getopt(argv, "-s")

    except getopt.GetoptError:
        print("invalid arguments: \n -s <config file to retrieve>")
        sys.exit(2)

    myConfig=Config()

    if myConfig.local_edit == "True":

        configParser = configparser.RawConfigParser()   
        # Writing our configuration file to 'example.ini'
        configFilePath = '/home/pi/src/git/RPI/CONFIG/INI_config.ini' 
        
        configParser.read(configFilePath)
        configParser.optionxform = str
        
        configParser.set('FTP','local_edit','False')

        with open(configFilePath, 'w') as configfile:
            configParser.write(configfile)

        if myConfig.nosim == "True":
            error_code = put_ftp(myConfig, list_of_config)
        else:
            error_code = put_ftp_gprs(myConfig, list_of_config)

        if error_code:

            configParser.set('FTP','local_edit','True')

            with open(configFilePath, 'w') as configfile:
                configParser.write(configfile)

        sys.exit(2)
        

    if myConfig.nosim == "True":

        get_ftp_files(myConfig, list_of_config)
        sys.exit(2)
    

    while os.path.exists('/tmp/alarm.pid'):

        time.sleep(5)

    gsm = serial.Serial("/dev/ttyUSB_DEVICE1", baudrate=115200, timeout=1)

    com._box("opened port : "+gsm.portstr)

    if gsm.isOpen():

        gsm.write(b'AT\r\n')
        time.sleep(0.3)

        gsm.write(b'AT+SAPBR=1,1\r\n')
        time.sleep(0.3)

        if debug > 2:
            gsm.write(b'ATE1\r\n')
            time.sleep(0.3)

        else:
            gsm.write(b'ATE0\r\n')
            time.sleep(0.3)

        # Test de la force du signal
        gsm.write(b'AT+CSQ\r\n')
        time.sleep(0.3)

        gsm.write(b'AT+SAPBR=3,1,"CONTYPE","GPRS"\r\n')
        time.sleep(0.3)
        
        # initialisation des variable du serveur FTP
        apn = bytes(myConfig.GPRS_Apn, 'utf-8')
        gsm.write(b'AT+SAPBR=3,1,"APN","'+apn+b'"\r\n')
        time.sleep(0.3)
        
        gsm.write(b'AT+FTPGETPATH="'+bytes(myConfig.FTP_dir_config, 'utf-8')+b'"\r\n')
        time.sleep(0.3)
        
        gsm.write(b'AT+FTPSERV="'+bytes(myConfig.FTP_Server, 'utf-8')+b'"\r\n')
        time.sleep(0.3)
        
        gsm.write(b'AT+FTPUN="'+bytes(myConfig.FTP_Login, 'utf-8')+b'"\r\n')
        time.sleep(0.3)
        
        gsm.write(b'AT+FTPPW="'+bytes(myConfig.FTP_Password, 'utf-8')+b'"\r\n')
        time.sleep(0.3) 
        
        gsm.write(b'AT+FTPPORT="'+bytes(myConfig.FTP_Port, 'utf-8')+b'"\r\n')
        time.sleep(0.3)

        if debug>1:com._box("O89: Ports configured")
        if debug>2:com._box("D89: Ports configured: "+_format(gsm.read(gsm.inWaiting())))


        for file in list_of_config:

            try:

                if args[0] == "get_ini_inv":
                    time.sleep(2)
                    gsm.write(b'AT+FTPGETNAME="'+bytes("/Bonjour.ini", 'utf-8')+b'"\r\n')
                    #_wait_end_get(gsm)

                elif args[0] == "full":
                    gsm.write(b'AT+FTPGETNAME="'+bytes("/"+file, 'utf-8')+b'"\r\n')
                    #_wait_end_get(gsm)

                else:
                    sys.exit(2)

            except IndexError:
                sys.exit(2)

            if debug>1:com._box("O90: GETNAME done")
            # if debug>2:com._box("D90: "+_format(gsm.read(gsm.inWaiting())))
                
            timeout = time.time() + 10
            Error = False
            tmp=""

            gsm.write(b'AT+FTPEXTGET=1\r\n')

            while (tmp.find('OK')==-1):
                time.sleep(0.3)

                tmp = _format(gsm.read(gsm.inWaiting()))

                if time.time() < timeout:
                    continue

                else:
                    Error == True
                    break

            if Error:
                com._box("ERROR: No answer from FTP server")

            connected = False
            data_str=""
            err = True
            timeout = time.time() + 30

            gsm.write(b'at+ftpextget?\r\n')
            time.sleep(1)

            while _format(gsm.read(gsm.inWaiting())).find('+FTPEXTGET= 1,0') == -1:

                time.sleep(0.5)

                if time.time() < timeout:
                    continue

                else:
                    break

            gsm.write(b'AT+FTPEXTGET=3,0,1024\r\n')

            timeout = time.time() + 15

            while not connected:

            #serin = ser.read()
                connected = True

                while err is True and time.time() < timeout:
                    
                    if (gsm.inWaiting()>0): 

                        data_str = data_str + _format(gsm.read(gsm.inWaiting())) 
                        message, err = _format_get(data_str)

                    # if err is True and data_str.find('+FTPGET: 1,1'):

                    #     gsm.write(b'AT+FTPGET=2,1024\r\n')
                    
                    time.sleep(0.01) #
    
            time.sleep(2)

            if not err:
                com._box("Fichier recu")
                os.system("mv CONFIG/"+file +" CONFIG/"+file+"_tmp")

                tmp = open('CONFIG/'+file,'w')
                tmp.write(message)
                tmp.close()

                time.sleep(5)
                os.system("chown pi CONFIG/"+file)
            
            else:
                com._box("Error in config file, will not replace")
                _wait_end_get(gsm)
                continue

            Error = False

            if debug>1:print("O89: ALL DONE"+_format(gsm.read(gsm.inWaiting())))

            try:
                myConfig = Config()
                comp = filecmp.cmp("CONFIG/"+file, "CONFIG/"+file+"_tmp", shallow = False)
            
                if comp:
                    os.system("sudo kill -9 `cat /tmp/routine.pid`")
                    
                os.remove("CONFIG/"+file+"_tmp")

            except Exception as e:

                com._box("Files are wrong")
                print(e)

                if os.path.exists("CONFIG/"+file+"_tmp"):

                    os.remove("CONFIG/"+file)
                    os.system("mv CONFIG/"+file+"_tmp" +" CONFIG/"+file)
                    
            gsm.write(b'AT+FTPEXTGET=0\r\n')
            # _wait_end_get(gsm)

if __name__=="__main__":
    main(sys.argv[1:])