<h1>
    RPI
</h1>

<p> 
    Le projet s'appuie sur le développement d'un outil standard pour la lecture de donnée d'un onduleur. Ce dernier est limité par son protocole de communication. Le              constructeur choisi d'y mettre en place un protocole standard (RS485/Modbus RTU) ou propriétaire (RS485/Protocole Constructeur). Si le protocole est standard alors un          simple fichier csv comprenant les registres correspondants aux données voulues suffit. La lecture du csv est faite, et les trames sont envoyées sur le bus RS485. 
</p>

<p>
    Si le protocole est propriétaire il peut être publique (Solarmax par exemple). Dans ce cas, un fichier csv comprenant les registres et nom des variables est à fournir.           L'appel d'un script sur mesures est nécessaire pour la contruction de trames uniques pour ce modele d'onduleur en particulier.
</p>
 
<h3>
    Config
</h3>

<p>
    Dans le dossier config on retrouve:
</p>

<ul>
    <li>
        INI_Config.ini
    </li>
    <li>
        INI_INV.ini
    </li>
    <li>
        INI_Time.ini
    </li>
    <li>
        Maker.sh
    </li>
    <li>
        Dossiers des configurations de tout les modeles d'onduleurs compatibles:
        <ul>
            <li>
                XXX_Modbus.txt ou XXX est la marque de l'onduleur
            </li>
        </ul>
    </li> 
</ul>

<h5>
    INI_config
</h5>
<p>
    Fichier de configuration des variables concernant les communications serveurs <br>
    <ul>
        <b>[GPRS]</b><br>
        Section non utilisée dans le code<br>
        <b>[FTP]</b><br>
        <code>ftp_serveur:</code> Nom du serveur FTP<br>
        <code>ftp_login:</code> Identifiant du serveur FTP<br>
        <code>ftp_password:</code> Mot de passe du serveur FTP<br>
        <code>ftp_port:</code> Port du serveur FTP<br>
        <code>ftp_dir:</code> Emplacement des fichiers:<br> 
        <ul>
            <li>
                <i>CONFIG</i> pour la configuration sur le serveur FTP.<br>
            </li>
            <li>
                <i>DATA</i> pour les données remontées.<br>
            </li> 
            <li>
                <i>DEF</i> Pour la définitions des registres.<br>
            </li>
            <li>
                <i>ALARM</i> Pour les alarmes remontées
            </li>
        </ul>
    </ul>
</p>
  
<h5>
    INI_INV
</h5>
<p>
    Fichier de configuration des onduleurs, chemin vers les fichiers de registres et de variables. <code>INV_Mode</code> permet d'indiquer à la routine le script à aller   chercher pour le bon protocole de communication: 
    <ul>
        <b>[CONFIG-INV]</b><br>
        <code>inv_model:</code>Marque des onduleurs, (discontinue)<br>
        <code>inv_mode:</code> Mode de communication<br>
        <ul>
            <li>
                ModBus = 'MB'
            </li>
            <li>
                SunSpec = 'SS' <i>(Les onduleurs sunspec utilisent désormais la routine MB)</i>
            </li>
            <li>
                Protocole propriétaire = 'PP'
            </li>
        </ul>
        <code>inv_n:</code> Nombre d'onduleur sur l'installation<br>
        <code>inv_model_n]:</code> Modele de l'onduleur <i>n</i>. Plusieurs modèles différents peuvent être renseignés<br>
        <code>inv_addr_n]:</code> Adresse en <i>int</i> de l'onduleur <i>n</i><br>
        <code>inv_var_n]:</code> Emplacement du fichier de registre de l'onduleur <i>n</i><br>
        <b>[CONFIG-SS]</b><br>
        Un onduleur sunspec utilise désormais la routine <i>MB</i>. Cette section n'est plus utilisée. Elle est cependant lu par <code>Init_Config.py</code> au cas ou.
    </ul>
</p>
  
<h5>
    INI_Time
</h5>
<p>
    Fichier de configuration des temps (delay, timeout, periode d'acquisition...) et configuration de la communication Modbus.
    <ul>
        <b>[CONFIG-ACQ]</b><br>
        <code>daq_period:</code>Periode (en min) de sauvegarde des données. Toutes les <i>daq_periode</i> les données retournées par l'onduleur sont écrites dans un csv, dans le         dossier DATA<br>
        <code>PORT:</code> Périphérique utilisé pour la communication onduleur:<br>
        <ul>  
            <li>
                <i>/dev/ttyS0</i> Dans la plupart des cas, la carte HAT RS485 est initialisée sur ce port.
            </li>
            <li>
                <i>/dev/ttyUSB_DEVICE2</i> L'USB/RS485 est reconnu par la raspberry en tant que "ttyUSB_DEVICE2"<br>
            </li>
        </ul>
        <code>ftp_period:</code> Heure à laquelle, le fichier de donnée est envoyé au serveur ftp (ftp_period = 59 : envoie donc le fichier toutes les heures à 59)<br>
        <code>modbus_mode:</code> Mode modbus<br>
        <code>modbus_baudrate:</code> Baudrate de la communication (9600 par défaut)<br>
        <code>modbus_parity:</code> Bit de parité (aucun par défaut)<br>
        <code>modbus_databit:</code> nombre de bit de donnée (8 par défaut)<br>
        <code>modbus_stopbit:</code> bit de stop (1 par défaut)<br>
        <code>modbus_timeout_tcp:</code> timeout en TCP entre chaque requête<br>
        <code>modbus_timeout_rtu:</code> timeout en RTU entre chaque requête (500 ms est largement suffisant)<br>
    </ul>
</p>
 
<h5>
    Maker.sh
</h5>
<p>
    Script shell de configuration de l'environnement Linux, à lancer à chaque installation. Le maker constitue les tâches et les inscrit dans crontab, grâce aux configurations lues dans le fichier INI_Time. Si la tâche existe, rien ne se passe. Le fichier <code>INI_Time.ini</code> renseigne la periode (en minute) entre chaque lancement du script d'acquisition de donnée de l'onduleur. (voir jobs) Quatre routines tournent périodiquement: <br>
    <ul>
        <li>
            Routine_ACQ.sh: Routine d'acquisition de donnée (toutes les 10 minutes par défaut)
        </li>
        <li>
            Routine_FTP.sh: Routine d'envoi des données sur serveur FTP (toutes les heures à 59 par défaut)
        </li>
        <li>
            Routine_FTP_retrieve.sh: Routine de récuperation de fichiers de config posés sur le serveur FTP (toutes les heures à 30 par défaut)
        </li>
        <li>
            Routine_Wipe.sh: Routine de destruction des fichiers de données mise en mémoire temporairement
        </li>
    </ul> 
Commande: 

    <code>sudo bash $RPI/CONFIG/maker.sh</code>
</p>
<code>maker</code> <br>
Cette commande peut être lancée partout. Elle produit le meme effet que la commande précédente.  

<h5>
    XXX_Modbus.txt
</h5>
<p>
    Les variables sont ecrites dans l'ordre croissant des indexs. Les registres, leurs nom et le format des valeurs à allez récuperer dans l'onduleur. (voir excel compatible_Products pour plus de détails)
</p>
  
<h3>
    Jobs
</h3>
<p>
    Dossier des Scripts Shell regroupant les chemins d'accès aux répertoires des scripts python, et du lancement du bon script de Routine. On y retrouve les outils exécutables (<code>Registre_scanner.py</code>: scan des registres valables ou non sur n'importe quel onduleur).
</p>
  
<h3>
    Library
</h3>
<p>
    Dans le dossier Librairie on retrouve:
</p>
<ul>
    <li>
        Les scripts des protocoles propriétaires
    </li>
    <li>
        Une copie de <code>dashboard.php</code> permettant de modifier le dashboard du point d'accès wifi de la raspberry
    </li>
    <li>
        <code>inverter_status.json</code> qui regroupe quelques informations sur le fonctionnement de l'installation et utilisé par le dashboard 
    </li>
</ul>
  
<h3>
    Crontab
</h3>
<p>
    Crontab est le planificateur de tâche sur linux. Il permet de lancer périodiquement une tâche (script shell dans le dossier jobs). <code>maker.sh</code> edite Crontab et y ajoute les tâches à accomplir ainsi que leur periodicité.
</p>

 <code>killpy</code> <br>
Cette commande peut être lancée partout. Elle arrete la routine d'acquisition en cours. La relance de cette routine n'est pas nécessaire, elle sera fait après un temps donnée.

<h3>
    Routine.py
</h3>
<p>
    Le script Routine est le premier script lancé pour tout type d'onduleur. C'est celui ci qui cherchera, si besoin, le script à lancer pour le modele d'onduleur indiqué dans les fichiers de configuration. Pour les phases de test, ce script peut être lancé directement depuis les commandes suivantes: <br>
    <code>sudo -E python3 $RPI/Routine.py -d</code> <br>
    -E: correspond à l'argument indiquant a "sudo" de garder les variables d'environnement de l'utilisateur actuel<br>
    -d: permet d'afficher plus d'information dans l'invite de commande. <br>
    <code>sudo $RPI/Jobs/Routine_ACQ.sh -fd</code> <br>
    -fd: Applique un debug max (permet d'avoir toutes les infos de la communication en cours<br>
</p>

<h3>
    Modbus_v2.py (discontinue, utiliser Modbus_v3.py)
</h3>
<p>
    Script basique de lancement et de construction de requêtes ModBus, ce script est appellé par <code>Routine.py</code> si le mode de l'onduleur est fixé a "MB"
</p>

<h3>
    Modbus_v3.py 
</h3>
<p>
    Script basique de lancement et de construction de requêtes ModBus, ce script est appellé par <code>Routine.py</code> si le mode de l'onduleur est fixé a "MB". Le format du csv des données sauvegardées sont compatible avec Epices.
</p>
 
<h3>
    Modbus_Sunspec.py (discontinue, utiliser Modbus_v3.py)
</h3>
<p>
    Script utilisant le protocole SunSpec, il est appellé par Routine si le mode de l'onduleur est fixé a "SS"
</p>
 
<h3>
    Init_INV.py
</h3>
<p>
    Script de Lecture des fichiers de configurations (<code>init_var_XXX.ini</code>, <code>INI_config.ini</code>,<code>INI_INV.ini</code>, <code>INI_models.txt</code>, INI_Time.ini</code>). L'objet <code>Config</code> est crée par tout les protocoles.<br> Les variables d'adresses des onduleurs, leurs types et leurs numéro de séries (comme ils sont nombreux) sont sous forme de listes. L'index de celles-ci est le numéro de l'onduleur (comme indiqué dans le fichier de config <code>INI_INV.ini</code>). <br>
    La variable file_var regroupe également tout les registres valables pour un onduleur donnée. Cette variable est également sous forme de liste et l'index est le numéro de l'onduleur concerné.
</p>

<h1>
    Tests
</h1>

<p>
    Afin de tester la routine d'acquisition, il est possible de lancer un simulateur d'esclave sur l'ordinateur et de connecter la Raspberry en USB/RS485. <code>Test_Modbus_RPI.py</code>, initialise des blocs possedant des valeurs affectées à certains registres. Un fichier <code>register.csv</code> permet de lister des registres ou l'on voudrait ajouter des mesures à lire. 
</p>

<h1>
    SMS
</h1>

<p>
    Gammu-smsd est le service qui reçoit et renvoi les sms. Ce service lance le scipt shell, <code>sms_handling.sh</code> à l'arriver de n'importe quel sms (Run on receive). <code>sms_handling.sh</code> appelle le script python <code>sms_handling.py</code> qui s'occupera de décoder quelles actions faire par rapport au message recu. Finalement, la réponse est contenu dans un fichier tmp détruit après l'envoi d'un sms.
</p>

<h3>
    RTC
</h3>
<p>
    lorsque la carte est hors ligne, elle ne possède pas d'horloge interne, il n'est donc pas possible pour elle de récupérer l'heure actuelle. Cependant, le module GPRS possède une commande AT (<code>AT+CCLK</code>) permettant de récuperer une date et une heure. A chaque lancement de la carte une tâche est lancé: <code>RTC.py</code>: celle-ci envoi une demande CCLK et remplace la date actuelle de la carte par la réponse de cette commande. Cela permet de ne pas avoir à installer une horloge temps-réel externe à la carte.
</p>

<h3>
    Fonctions à développer
</h3>
<p>
    <ul>
    <li>
        Le modbus TCP n'est pas mis en place, il faut reprendre le schéma du programme Modbus_v3.py (Modbus RTU) et implémenter la fonction de la communication en TCP. La librairie minimalmodbus possède des fonctions pour le TCP.
    </li>
    <li>
        Pour le script solarmax, il faut mettre en place la gestion d'alarme. Le code SYS est celui dédié au code alarme, il faut donc faire en sorte que les valeurs de ce code soit envoyé dans le fichier d'alarme seulement si il est différent de 20001 ('statut normal')
    </li>
    <li>
        Mettre en place plus de possibilité de code SMS. Dans le dossier <code>/home/pi/bin</code>
    </li>
    <li>
        Si besoin, transformer le code en C. un code "libmodbus" est disponible, déjà installé sur la Raspberry pour le traitement des communications Modbus dossier <code>/home/pi/src/C_RPI/</code>
    </li>
    <li>
        Modifier le code Routine.py afin de permettre de lancer des scripts propriétaires et le script Modbus de base en même temps. 
    </li>
</ul>
</p>
