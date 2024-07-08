import configparser
import os, json, shutil, random, tracker, database, controller
from pathlib import Path
import chardet

def write_chr_file(file_path, config):
    with open(file_path, 'w+') as file:
        write_chart_section(file, config['chart'])
        
def write_chart_section(file, chart):
    file.write("<chart>\n")
    
    for key, value in chart.items():
        if key == 'expert':
            write_expert_section(file, value)
        elif key == 'window':
            write_window_section(file, value)
        else:
            file.write(f"{key}={value}\n")
    
    file.write("</chart>\n")

def write_expert_section(file, expert):
    file.write("\n<expert>\n")
    
    for key, value in expert.items():
        if key == 'inputs':
            write_inputs_section(file, value)
        else:
            file.write(f"{key}={value}\n")
    
    file.write("</expert>\n")

def write_inputs_section(file, inputs):
    file.write("\n<inputs>\n=\n")
    
    for key, value in inputs.items():
        file.write(f"{key}={value}\n")
    
    file.write("</inputs>\n")

def write_window_section(file, window):
    file.write("\n<window>\n")
    
    for key, value in window.items():
        if key == 'indicator':
            write_indicator_section(file, value)
        elif key == 'object':
            write_object_section(file, value)
        else:
            file.write(f"{key}={value}\n")
    
    file.write("</window>\n")

def write_indicator_section(file, indicator):
    file.write("\n<indicator>\n")
    
    for key, value in indicator.items():
        file.write(f"{key}={value}\n")
    
    file.write("</indicator>\n")

def write_object_section(file, obj):
    file.write("\n<object>\n")
    
    for key, value in obj.items():
        file.write(f"{key}={value}\n")
    
    file.write("</object>\n")

def parseSetFile(file_path):
     with open(file_path, 'r') as file:
         all = file.read()
         all = all.split("\n")
     config = {}
     for line in all:
          if ";" not in line:
               try:
                    key, value = line.split("=")
                    value = value.split("|")[0]
                    config[key] = value
               except:
                    pass
     return config

def parse_chr_file(file_path):
     with open(file_path, 'rb') as file:
          content = file.read()
          content = content.decode('utf-16le')
     config = {
          'chart': {
               'expert': {
                    'inputs': {}},
               'window': {
                    'indicator': {},
                    'object': {}
               }}}
     current_section = []
     content = content[1:]
     lines = content.split('\n')
     for line in lines:
          try:
               #print(line[0])
               line = line[:-1]
               #print(line[-1])
               if line[0] == "<" and line[-1] == ">":
                    #print(line)
                    if "/" not in line:
                         current_section.append(line[1:-1].lower())
                    else:
                         current_section.remove(line[1:-1].lower().replace("/", ""))
                    #print(current_section)
               elif "=" in line and len(current_section) != 0:
                    #key, value = map(str.strip, line.split("=", 1)
                    #line = line.decode('utf-16le')
                    key, value = line.split("=")
                    #print(key,value)
                    if len(current_section) == 1:
                         config[current_section[0]][key] = value
                    if len(current_section) == 2:
                         config[current_section[0]][current_section[1]][key] = value
                    if len(current_section) == 3:
                         config[current_section[0]][current_section[1]][current_section[2]][key] = value
                    if len(current_section) == 4:
                         config[current_section[0]][current_section[1]][current_section[2]][current_section[3]][key] = value
          except Exception as e:
               #print(e)
               pass 
        

     return config

def loadSets(account_id):
    user_profile = os.environ['USERPROFILE']
    databaseFolder = os.path.join(user_profile, 'AppData', 'Local', 'Mt5TrackerDatabase')
    setsFolder = os.path.join(databaseFolder, "Sets", str(account_id))
    config = database.getConfig()
    terminalPath = ""
    accounts = database.getAccounts()
    for account in accounts:
        if account["login"] == account_id:
            terminalPath = account["terminalFilePath"]
        
    profileName = "MT5-Tracker-Profile"
    directory = os.getcwd()
    
    dataPath = tracker.getDataPath(account_id)
    powName = config["powName"]
    
    defaultChartPath = f"{directory}\\chart01.chr"
    chartNumber = 1
    
    ## Removing Current Profile
    if os.path.exists(f"{dataPath}\\MQL5\\Presets\\{profileName}"):
        for file in os.listdir(f"{dataPath}\\MQL5\\Presets\\{profileName}"):
            os.remove(f"{dataPath}\\MQL5\\Presets\\{profileName}\\{file}")
        os.removedirs(f"{dataPath}\\MQL5\\Presets\\{profileName}")
    if os.path.exists(f"{dataPath}\\MQL5\\Profiles\\Charts\\{profileName}"):
        for file in os.listdir(f"{dataPath}\\MQL5\\Profiles\\Charts\\{profileName}"):
            os.remove(f"{dataPath}\\MQL5\\Profiles\\Charts\\{profileName}\\{file}")
    else:
        os.makedirs(f"{dataPath}\\MQL5\\Profiles\\Charts\\{profileName}")
        
    currentSets = database.getSets(account_id)
    currentMagics = []
    for set in currentSets:
        currentMagics.append(set["magic"])
    
    for setFile in os.listdir(setsFolder):
        defaultConfig = parse_chr_file(defaultChartPath)
        temp = []
        magicNumber = setFile.split("_")[-1].replace(".set","")
        symbol = setFile.split(" ")[0]
        
        if magicNumber not in currentMagics:
            newSet = {
                "stats": {
                    "setName": setFile.replace(".set",""),
                    "strategy": "",
                    "magic": magicNumber,
                    "profit": 0,
                    "trades": 0,
                    "maxDrawdown": "-",
                    "profitFactor": 0,
                    "returnOnDrawdown": "-",
                    "daysLive": 0
                },
                "trades": [],
                "drawdown": [],
                "equity": []
            }
            database.insertSet(newSet, account_id)

        setConfig = parseSetFile(f"{setsFolder}\\{setFile}")
        defaultConfig["chart"]["expert"]["inputs"] = setConfig
        defaultConfig["chart"]["id"] = random.randint(100000000000000000, 999999999999999999)
        defaultConfig["chart"]["symbol"] = symbol
        defaultConfig["chart"]["expert"]["inputs"]["apiKey"] = config["powAPIKey"]
        defaultConfig["chart"]["expert"]["inputs"]["MAGIC_NUMBER"] = str(magicNumber)
        defaultConfig["chart"]["expert"]["inputs"]["StrategyDescription"] = setFile.replace(".set","")
        defaultConfig["chart"]["expert"]["inputs"]["TradeComment"] = setFile.replace(".set","")
        defaultConfig["chart"]["expert"]["name"] = config["powName"].replace(".ex5","")
        defaultConfig["chart"]["expert"]["path"] = f"Experts\\{powName}"
        defaultConfig["chart"]["expert"]["expertmode"] = 1

        output_chr_file_path = f'{dataPath}\\MQL5\\Profiles\\Charts\\{profileName}\\chart0{chartNumber}.chr'
        write_chr_file(output_chr_file_path, defaultConfig)
        chartNumber += 1
    
    terminalConfigPath = os.path.join(tracker.getDataPath(account_id), "config", "common.ini")
    controller.closeTerminal(terminalPath)
    terminalConfig = read_ini_file(terminalConfigPath)
    terminalConfig["Charts"]["ProfileLast"] = profileName
    terminalConfig["Experts"]["enabled"] = "1"
    terminalConfig["Experts"]["allowdllimport"] = "1"
    
    with open(terminalConfigPath, 'w') as configfile:
        terminalConfig.write(configfile)
    
def addCopier(masterAccountID, slaveAccountID, magicNumbers):
    user_profile = os.environ['USERPROFILE']
    databaseFolder = os.path.join(user_profile, 'AppData', 'Local', 'Mt5TrackerDatabase')
    
    
    masterTerminalPath = ""
    slaveTerminalPath = ""
    
    accounts = database.getAccounts()
    for account in accounts:
        if account["login"] == masterAccountID:
            masterTerminalPath = account["terminalFilePath"]
        if account["login"] == slaveAccountID:
            slaveTerminalPath = account["terminalFilePath"]
        
    profileName = "MT5-Tracker-Profile"
    directory = os.getcwd()
    
    masterDataPath = tracker.getDataPath(masterAccountID)
    slaveDataPath = tracker.getDataPath(slaveAccountID)

    
    masterChartPath = f"{directory}\\tradeSender.chr"
    slaveChartPath = f"{directory}\\tradeReceiver.chr"


    masterConfig = parse_chr_file(masterChartPath)
    masterConfig["chart"]["id"] = random.randint(100000000000000000, 999999999999999999)
    masterConfig["chart"]["symbol"] = "XAUUSD"
    masterConfig["chart"]["expert"]["inputs"]["Channel"] = f"{masterAccountID}-{slaveAccountID}"
    masterConfig["chart"]["expert"]["inputs"]["IncludeMagicNumbers"] = str(magicNumbers).replace("[","").replace("]","")
    
    slaveConfig = parse_chr_file(slaveChartPath)
    slaveConfig["chart"]["id"] = random.randint(100000000000000000, 999999999999999999)
    slaveConfig["chart"]["symbol"] = "XAUUSD"
    slaveConfig["chart"]["expert"]["inputs"]["Channel"] = f"{masterAccountID}-{slaveAccountID}"

    masterProfilePath = os.path.join(masterDataPath, "MQL5", "Profiles", "Charts", profileName)
    Path(masterProfilePath).mkdir(parents=True, exist_ok=True)
    masterChartNumber = len([f for f in os.listdir(masterProfilePath) if os.path.isfile(os.path.join(masterProfilePath, f))])
    masterChrFilePath = os.path.join(masterProfilePath, f"chart0{masterChartNumber}.chr")
    write_chr_file(masterChrFilePath, masterConfig)
    
    slaveProfilePath = os.path.join(slaveDataPath, "MQL5", "Profiles", "Charts", profileName)
    Path(slaveProfilePath).mkdir(parents=True, exist_ok=True)
    slaveChartNumber = len([f for f in os.listdir(slaveProfilePath) if os.path.isfile(os.path.join(slaveProfilePath, f))])
    slaveChrFilePath = os.path.join(slaveProfilePath, f"chart0{slaveChartNumber}.chr")
    write_chr_file(slaveChrFilePath, slaveConfig)
    

    
    
    terminalConfigPath = os.path.join(tracker.getDataPath(account_id), "config", "common.ini")
    controller.closeTerminal(terminalPath)
    terminalConfig = read_ini_file(terminalConfigPath)
    terminalConfig["Charts"]["ProfileLast"] = profileName
    terminalConfig["Experts"]["enabled"] = "1"
    terminalConfig["Experts"]["allowdllimport"] = "1"
    
    with open(terminalConfigPath, 'w') as configfile:
        terminalConfig.write(configfile)
    
    
        
def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    return encoding

def read_ini_file(file_path):
    try:
        encoding = detect_encoding(file_path)
        config = configparser.ConfigParser()
        config.read(file_path, encoding=encoding)
        return config
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



