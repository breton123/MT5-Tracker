import configparser, os, subprocess, json
from datetime import datetime, timedelta
import chardet

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

def convert_set_to_ini(set_file_path, ini_file_path):
    try:
        # Detect the encoding of the .set file
        encoding = detect_encoding(set_file_path)
        
        # Read the .set file with the detected encoding
        with open(set_file_path, 'r', encoding=encoding) as set_file:
            lines = set_file.readlines()

        # Write to the .ini file
        with open(ini_file_path, 'w', encoding='utf-8') as ini_file:
            # Add the initial lines with the current date and time
            ini_file.write(f"; saved on {datetime.now().strftime('%Y.%m.%d %H:%M:%S')}\n")
            ini_file.write("; this file contains input parameters for testing/optimizing Banker v8 0312 expert advisor\n")
            ini_file.write("; to use it in the strategy tester, click Load in the context menu of the Inputs tab\n;\n")
            ini_file.write("[Tester]\n[TesterInputs]\n")

            # Iterate through the lines in the .set file and write to the .ini file
            for line in lines:
                if '||' in line:
                    key, value = line.split('=', 1)
                    value = value.split('||')[0].strip()
                    ini_file.write(f"{key.strip()}={value}\n")
                else:
                    ini_file.write(line.strip() + '\n')

        return ini_file_path

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
        
    return ini_file_path

def getTerminalPath():
    with open('config.json', "r") as json_data:
        userConfig = json.loads(json_data.read())
        json_data.close()
    dataPath = userConfig["dataPath"]
    with open(f"{dataPath}\\origin.txt", "r") as file:
        return file.read()

def runOptimization():
    directory = os.getcwd()
    with open('config.json', "r") as json_data:
        userConfig = json.loads(json_data.read())
        json_data.close()
    
    terminalPath = userConfig["terminalPath"]
    
    for symbol in userConfig["symbols"]:
        for fileName in os.listdir(f"{directory}\\opt files"):
            try:
                fileName = convert_set_to_ini(f"{directory}\\opt files\\{fileName}", f"{directory}\\ini files\\{fileName}".replace(".set",".ini"))
            except:
                fileName = f"{directory}\\ini files\\{fileName}".replace(".set",".ini")
                
            #encoding = detect_encoding(fileName)
            config = read_ini_file(fileName)
            strategy = fileName.split("\\")[-1].replace(".ini","")
            
            ## OPT SETTINGS
            config["Tester"]["Symbol"] = symbol
            config["Tester"]["FromDate"] = (datetime.today() - timedelta(weeks=4)).strftime('%Y.%m.%d')
            config["Tester"]["ToDate"] = datetime.today().strftime('%Y.%m.%d')
            config["Tester"]["Leverage"] = "100"
            config["Tester"]["Report"] = f"{symbol} {strategy}.htm"
            config["Tester"]["Deposit"] = "100000"
            config["Tester"]["ForwardMode"] = "2"
            config["Tester"]["ShutdownTerminal"] = "1"
            config["Tester"]["Model"] = "1"
            config["Tester"]["ReplaceReport"] = "1"
            config["Tester"]["Expert"] = userConfig["powName"]
            config["Tester"]["optimizationcriterion"] = "0"
            config["Tester"]["executionmode"] = "50"
            config["Tester"]["Period"] = "M1"
            config["Tester"]["optimization"] = "0"
            config["Tester"]["currency"] = "USD"
            config["Tester"]["profitinpips"] = "0"
            config.add_section("Common")
            config.set("Common","Login",userConfig["demoLogin"])
            config.set("Common","Password",userConfig["demoPassword"])
            
            ## BOT SETTINGS
            #config["TesterInputs"]["MAGIC_NUMBER"] = magic
            config["TesterInputs"]["StrategyDescription"] = f"{symbol} {strategy}"
            config["TesterInputs"]["TradeComment"] = f"{symbol} {strategy}"
            config["TesterInputs"]["apiKey"] = userConfig["powAPIKey"]
            
            
            with open(f'{directory}\\temp\\{symbol}-{strategy}.ini', 'w+') as configfile:
                config.write(configfile)
            # Make run fileS
            with open("temp\\batch.bat", "w+") as f:
                f.write(f'"{terminalPath}\\terminal64.exe" /config:"{directory}\\{symbol}-{strategy}.ini"')
            # Run Optimization
            process = subprocess.Popen('temp\\batch.bat',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            output = process.stdout.read()
            print(f"Finished Optimization for {symbol} {strategy}")

allSetsFolder = "C:\\Users\\louis\\Desktop\\Double 1k accounts\\Sets"


runOptimization()


#convert_set_to_ini("C:\\Users\\louis\\Desktop\\POW FILES 14th June\\Trend 1.set","C:\\Users\\louis\\Desktop\\POW FILES 14th June\\Trend 1.ini")