import configparser
import os, json, shutil, random, tracker, database, controller
from pathlib import Path
import chardet

def write_chr_file(file_path, config):
    with open(file_path, 'w+') as file:
        file.write("<chart>\n")
        write_chart_section(file, config['chart'])
        file.write("</chart>\n")

        
def write_chart_section(file, chart):
    file.write(f"id={chart['id']}\n")
    file.write(f"symbol={chart['symbol']}\n")
    file.write(f"description={chart['description']}\n")
    file.write(f"period_type={chart['period_type']}\n")
    file.write(f"period_size={chart['period_size']}\n")
    file.write(f"digits={chart['digits']}\n")
    file.write(f"tick_size={chart['tick_size']}\n")
    file.write(f"position_time={chart['position_time']}\n")
    file.write(f"scale_fix={chart['scale_fix']}\n")
    file.write("\n")
    write_expert_section(file, chart['expert'])
    write_window_section(file, chart['window'])

def write_expert_section(file, expert):
    file.write("<expert>\n")
    file.write(f"name={expert['name']}\n")
    file.write(f"path={expert['path']}\n")
    file.write(f"expertmode={expert['expertmode']}\n")
    write_inputs_section(file, expert['inputs'])
    file.write("</expert>\n\n")


def write_inputs_section(file, inputs):
    file.write("<inputs>\n=\n")
    for key, value in inputs.items():
        file.write(f"{key}={value}\n")
    file.write("</inputs>\n")


def write_window_section(file, window):
    file.write("<window>\n")
    write_indicator_section(file, window['indicator'])
    write_object_section(file, window['object'])
    file.write("</window>\n\n")


def write_indicator_section(file, indicator):
    file.write("<indicator>\n")
    for key, value in indicator.items():
        file.write(f"{key}={value}\n")
    file.write("</indicator>\n")

def write_object_section(file, obj):
    file.write("<object>\n")
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
    with open(file_path, 'r') as file:
        lines = file.readlines()

    config = {
        'chart': {
            'expert': {
                'inputs': {}
            },
            'window': {
                'indicator': {},
                'object': {}
            }
        }
    }

    current_section = None  # Track the current section we are parsing
    current_inputs = None   # Track if we are in the 'inputs' section

    for line in lines:
        line = line.strip()
        if line.startswith('<chart>'):
            current_section = 'chart'
        elif line.startswith('<expert>'):
            current_section = 'expert'
        elif line.startswith('<inputs>'):
            current_section = 'inputs'
            current_inputs = config['chart']['expert']['inputs']
        elif line.startswith('<window>'):
            current_section = 'window'
        elif line.startswith('<indicator>'):
            current_section = 'indicator'
        elif line.startswith('<object>'):
            current_section = 'object'
        elif line.startswith('</'):
            current_section = None
        elif '=' in line and current_section:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if current_section == 'chart':
                if key == 'id':
                    config['chart']['id'] = int(value)
                elif key == 'symbol':
                    config['chart']['symbol'] = value
                elif key == 'description':
                    config['chart']['description'] = value
                elif key == 'period_type':
                    config['chart']['period_type'] = int(value)
                elif key == 'period_size':
                    config['chart']['period_size'] = int(value)
                elif key == 'digits':
                    config['chart']['digits'] = int(value)
                elif key == 'tick_size':
                    config['chart']['tick_size'] = float(value)
                elif key == 'position_time':
                    config['chart']['position_time'] = int(value)
                elif key == 'scale_fix':
                    config['chart']['scale_fix'] = int(value)
            elif current_section == 'expert':
                if key == 'name':
                    config['chart']['expert']['name'] = value
                elif key == 'path':
                    config['chart']['expert']['path'] = value
                elif key == 'expertmode':
                    config['chart']['expert']['expertmode'] = int(value)
            elif current_section == 'indicator':
                config['chart']['window']['indicator'][key] = value
            elif current_section == 'object':
                config['chart']['window']['object'][key] = value
            elif current_section == 'inputs' and current_inputs is not None:
                current_inputs[key] = value

    return config


def doesProfileExist(dataPath, profileName):
    try:
        profilePath = os.path.join(dataPath, 'MQL5', 'Profiles', 'Charts', profileName)
        amountOfCharts = len([f for f in os.listdir(profilePath) if os.path.isfile(os.path.join(profilePath, f))])
        return amountOfCharts
    except:
        return False
        

def loadSets(account_id, profileName):
    user_profile = os.environ['USERPROFILE']
    databaseFolder = os.path.join(user_profile, 'AppData', 'Local', 'Mt5TrackerDatabase')
    setsFolder = os.path.join(databaseFolder, "Sets", str(account_id), profileName)
    config = database.getConfig()
    terminalPath = ""
    accounts = database.getAccounts()
    for account in accounts:
        if account["login"] == account_id:
            terminalPath = account["terminalFilePath"]
        
    directory = os.getcwd()
    
    dataPath = tracker.getDataPath(account_id)
    powName = config["powName"]
    defaultChartPath = f"{directory}\\chart01.chr"
    chartNumber = 1

    chartsPath = os.path.join(dataPath, 'MQL5', 'Profiles', 'Charts', profileName)

    if os.path.isdir(chartsPath):
        chartNumber = len([f for f in os.listdir(chartsPath) if os.path.isfile(os.path.join(chartsPath, f))])
    else:
        os.makedirs(chartsPath)
        chartNumber = 1
        
    currentSets = database.getSets(account_id)
    currentMagics = []
    for set in currentSets:
        try:
            currentMagics.append(set["magic"])
        except:
            pass
    
    for setFile in os.listdir(setsFolder):
        defaultConfig = parse_chr_file(defaultChartPath)
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
    masterChartNumber = len([f for f in os.listdir(masterProfilePath) if os.path.isfile(os.path.join(masterProfilePath, f))]) + 1
    masterChrFilePath = os.path.join(masterProfilePath, f"chart0{masterChartNumber}.chr")
    write_chr_file(masterChrFilePath, masterConfig)
    
    slaveProfilePath = os.path.join(slaveDataPath, "MQL5", "Profiles", "Charts", profileName)
    Path(slaveProfilePath).mkdir(parents=True, exist_ok=True)
    slaveChartNumber = len([f for f in os.listdir(slaveProfilePath) if os.path.isfile(os.path.join(slaveProfilePath, f))]) + 1
    slaveChrFilePath = os.path.join(slaveProfilePath, f"chart0{slaveChartNumber}.chr")
    write_chr_file(slaveChrFilePath, slaveConfig)
    
    
    masterTerminalConfigPath = os.path.join(tracker.getDataPath(masterAccountID), "config", "common.ini")
    controller.closeTerminal(masterTerminalPath)
    masterTerminalConfig = read_ini_file(masterTerminalConfigPath)
    masterTerminalConfig["Charts"]["ProfileLast"] = profileName
    masterTerminalConfig["Experts"]["enabled"] = "1"
    masterTerminalConfig["Experts"]["allowdllimport"] = "1"
    with open(masterTerminalConfigPath, 'w') as configfile:
        masterTerminalConfig.write(configfile)
        
    slaveTerminalConfigPath = os.path.join(tracker.getDataPath(slaveAccountID), "config", "common.ini")
    controller.closeTerminal(slaveTerminalPath)
    slaveTerminalConfig = read_ini_file(slaveTerminalConfigPath)
    slaveTerminalConfig["Charts"]["ProfileLast"] = profileName
    slaveTerminalConfig["Experts"]["enabled"] = "1"
    slaveTerminalConfig["Experts"]["allowdllimport"] = "1"
    with open(slaveTerminalConfigPath, 'w') as configfile:
        slaveTerminalConfig.write(configfile)
    
    
        
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



