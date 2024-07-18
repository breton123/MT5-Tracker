import statistics
import MetaTrader5 as mt5
import datetime as datetime
import time, os, json, tracker, portalocker, loader
from datetime import datetime

user_profile = os.environ['USERPROFILE']
databaseFolder = os.path.join(user_profile, 'AppData', 'Local', 'Mt5TrackerDatabase')
lastTradeTime = 0
accounts = []

def loadConfig():
    with open(os.path.join(databaseFolder, 'config.json'),"r") as file:
        return json.load(file)

def updateAccountStatus(account, newStatus):
    account = str(account)
    try:
        file_path = os.path.join(databaseFolder, "Accounts", f"{account}.json")

        # Lock the file for reading and writing
        with open(file_path, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)

                # Read existing data from JSON file
                accountData = json.load(file)

                # Append new trade to the 'trades' list in the loaded JSON data
                accountData["status"] = newStatus

                # Move the file pointer to the beginning of the file to overwrite it
                file.seek(0)
                file.truncate()

                # Write updated data back to JSON file
                json.dump(accountData, file, indent=4)
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Task: (Insert Trade)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    except FileNotFoundError as e:
        errMsg = f"Account: {account}  Task: (Insert Trade)  FileNotFoundError: {e} - Unable to update status, file not found at {file_path}"
        print(errMsg)
        log_error(errMsg)
    except json.JSONDecodeError as e:
        errMsg = f"Account: {account}  Task: (Insert Trade)  JSONDecodeError: {e} - Error decoding JSON data from file at {file_path}"
        print(errMsg)
        log_error(errMsg)
    except KeyError as e:
        errMsg = f"Account: {account}  Task: (Insert Trade)  KeyError: {e} - 'status' key not found in JSON data"
        print(errMsg)
        log_error(errMsg)
    except Exception as e:
        errMsg = f"Account: {account}  Task: (Insert Trade)  Unexpected error: {e} occurred while updating status"
        print(errMsg)
        log_error(errMsg)


def getConfig():
    user_profile = os.environ['USERPROFILE']
    configFile = os.path.join(user_profile, 'AppData', 'Local', 'Mt5TrackerDatabase', 'config.json')
    if os.path.exists(configFile):
        with open(configFile, 'r') as f:
            return json.load(f)
    return {"powName": "", "powAPIKey": ""}

def getAccounts():
    accounts = []
    try:
        for file in os.listdir(os.path.join(databaseFolder, "Accounts")):
            file_path = os.path.join(databaseFolder, "Accounts", file)
            with open(file_path, "r") as f:
                try:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    accounts.append(json.load(f))
                finally:
                    portalocker.unlock(f)
    except portalocker.LockException as e:
        errMsg = f"Task: (Get Accounts)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    except FileNotFoundError as e:
        errMsg = f"Task: (Get Accounts)  Error: {e} - Accounts folder not found at {os.path.join(databaseFolder, 'Accounts')}"
        print(errMsg)
        log_error(errMsg)
    except Exception as e:
        errMsg = f"Task: (Get Accounts)  Unexpected error: {e} occurred while loading accounts"
        print(errMsg)
        log_error(errMsg)
    return accounts


def findSet(sets, magic):
    try:
        for data in sets:
            if str(data["stats"]["magic"]) == str(magic):
                return data
    except KeyError as e:
        errMsg = f"Task: (Find Set)  KeyError: {e} - Error accessing 'stats' or 'magic' key in set data"
        print(errMsg)
        log_error(errMsg)
    except Exception as e:
        errMsg = f"Task: (Find Set)  Unexpected error: {e} occurred while finding set for magic {magic}"
        print(errMsg)
        log_error(errMsg)

    return None

def getFrontendSets(account):
    account = str(account)
    sets = []
    try:
        folder_path = os.path.join(databaseFolder, account)
        if len(os.listdir(folder_path)) > 0:
            for file in os.listdir(folder_path):
                print(file)
                file_path = os.path.join(folder_path, file)
                with open(file_path, 'r') as jsonFile:
                    try:
                        portalocker.lock(jsonFile, portalocker.LOCK_SH)
                        data = json.load(jsonFile)
                        sets.append(data)
                    finally:
                        portalocker.unlock(jsonFile)
    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Task: (Get Frontend Sets)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    except FileNotFoundError as e:
        errMsg = f"Account: {account}  Task: (Get Frontend Sets)  FileNotFoundError: {e} - Account folder '{folder_path}' not found"
        print(errMsg)
        log_error(errMsg)
    except Exception as e:
        errMsg = f"Account: {account}  Task: (Get Frontend Sets)  Unexpected error: {e} occurred while loading frontend sets for account '{account}'"
        print(errMsg)
        log_error(errMsg)

    return sets

def getErrorLog():
    log_file_path = os.path.join(databaseFolder, "errorlog.txt")
    try:
        with open(log_file_path, "r") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)
                error_log = file.read()
            finally:
                portalocker.unlock(file)
        return error_log
    except FileNotFoundError:
        print(f"Error log file '{log_file_path}' not found.")
        return ""
    except IOError as e:
        print(f"Failed to read error log file: {e}")
        return ""
    except portalocker.LockException as e:
        print(f"Failed to acquire lock on error log file: {e}")
        return ""

def log_error(error_message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{current_time}] {error_message}\n"
    try:
        log_file_path = os.path.join(databaseFolder, "errorlog.txt")
        with open(log_file_path, "a") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)
                file.write(log_entry)
            finally:
                portalocker.unlock(file)
    except portalocker.LockException as e:
        print(f"Task: (Log Error)  Failed to acquire lock: {e}")
    except IOError as e:
        print(f"Task: (Log Error)  Failed to write to log file: {e}")

def resetErrorLog():
    with open(os.path.join(databaseFolder, 'errorlog.txt'), "w+") as file:
        file.write("")

def insertSet(newSet, account):
    account = str(account)
    try:
        # Attempt to retrieve the magic value
        magic = newSet["stats"]["magic"]
    except KeyError as e:
        errMsg = f"Account: {account}  Task: (Insert Set)  KeyError: {e} - 'stats' or 'magic' key not found in new set"
        print(errMsg)
        log_error(errMsg)
        magic = None

    if magic:
        # Construct the file path
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")

        # Check if the file already exists
        if os.path.exists(file_path):
            ## This error is fine
            errMsg = f"Account: {account}  Magic: {magic}  Task: (Insert Set)  Set file already exists at {file_path}"
            #print(errMsg)
            #log_error(errMsg)
        else:
            try:
                # Attempt to open and write to the file
                with open(file_path, "w+") as file:
                    try:
                        portalocker.lock(file, portalocker.LOCK_EX)
                        json.dump(newSet, file, indent=4)
                        file.flush()  # Ensure all data is written to disk
                        os.fsync(file.fileno())
                    except TypeError as e:
                        errMsg = f"Account: {account}  Magic: {magic}  Task: (Insert Set)  TypeError: {e} - An error occurred while encoding JSON data"
                        print(errMsg)
                        log_error(errMsg)
                    except json.JSONDecodeError as e:
                        errMsg = f"Account: {account}  Magic: {magic}  Task: (Insert Set)  JSONDecodeError: {e} - An error occurred while decoding JSON data"
                        print(errMsg)
                        log_error(errMsg)
                    finally:
                        portalocker.unlock(file)
            except portalocker.LockException as e:
                errMsg = f"Account: {account}  Magic: {magic}  Task: (Insert Set)  LockException: {e} - Failed to acquire lock for file {file_path}"
                print(errMsg)
                log_error(errMsg)
            except IOError as e:
                errMsg = f"Account: {account}  Magic: {magic}  Task: (Insert Set)  IOError: {e} - An error occurred while accessing the file system"
                print(errMsg)
                log_error(errMsg)
            except Exception as e:
                errMsg = f"Account: {account}  Magic: {magic}  Task: (Insert Set)  Unexpected error: {e}"
                print(errMsg)
                log_error(errMsg)
    else:
        errMsg = f"Account: {account}  Task: (Insert Set)  The magic key could not be retrieved, skipping file operations"
        print(errMsg)
        log_error(errMsg)


def createAccountFolder(account):
    account = str(account)
    try:
        folder_path = f"{databaseFolder}\\{account}"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    except FileNotFoundError as e:
        errMsg = f"Account: {account}  Task: (Create Accounts Folder)  FileNotFoundError: {e} - Unable to create account folder '{folder_path}', parent directory not found"
        print(errMsg)
        log_error(errMsg)
    except PermissionError as e:
        errMsg = f"Account: {account}  Task: (Create Accounts Folder)  PermissionError: {e} - Unable to create account folder '{folder_path}', permission denied"
        print(errMsg)
        log_error(errMsg)
    except Exception as e:
        errMsg = f"Account: {account}  Task: (Create Accounts Folder)  Unexpected error: {e} occurred while creating account folder '{folder_path}'"
        print(errMsg)
        log_error(errMsg)

def updateProfit(magic, profit, account):
    account = str(account)
    try:
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")

        # Lock the file for reading and writing
        with open(file_path, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)

                # Read existing data from JSON file
                set_data = json.load(file)

                # Update profit in the loaded JSON data
                set_data["stats"]["profit"] = profit

                # Move the file pointer to the beginning of the file to overwrite it
                file.seek(0)
                file.truncate()

                # Write updated data back to JSON file
                json.dump(set_data, file, indent=4)
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Profit)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    except FileNotFoundError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Profit)  FileNotFoundError: {e} - Unable to update profit for magic {magic}, file not found at {file_path}"
        print(errMsg)
        log_error(errMsg)
    except json.JSONDecodeError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Profit)  JSONDecodeError: {e} - Error decoding JSON data from file at {file_path}"
        print(errMsg)
        log_error(errMsg)
    except KeyError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Profit)  KeyError: {e} - 'stats' or 'profit' key not found in JSON data for magic {magic}"
        print(errMsg)
        log_error(errMsg)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Profit)  Unexpected error: {e} occurred while updating profit for magic {magic}"
        print(errMsg)
        log_error(errMsg)


     
def setExist(magic, account):
    account = str(account)
    try:
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")
        
        # Attempt to open the file for reading
        with open(file_path, "r") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_SH)  # Shared lock for reading
                return True
            finally:
                portalocker.unlock(file)
    except FileNotFoundError:
        # Handle the case where the file does not exist
        return False
    except Exception as e:
        # Log any unexpected errors
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Set Exist)  Error checking if set exists for magic {magic} and account {account}: {e}"
        print(errMsg)
        log_error(errMsg)
        return False

def insertTrade(magic, trade, account):
    account = str(account)
    try:
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")

        # Lock the file for reading and writing
        with open(file_path, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)

                # Read existing data from JSON file
                set_data = json.load(file)

                # Append new trade to the 'trades' list in the loaded JSON data
                set_data["trades"].append(trade)

                # Move the file pointer to the beginning of the file to overwrite it
                file.seek(0)
                file.truncate()

                # Write updated data back to JSON file
                json.dump(set_data, file, indent=4)
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Insert Trade)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    except FileNotFoundError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Insert Trade)  FileNotFoundError: {e} - Unable to insert trade for magic {magic}, file not found at {file_path}"
        print(errMsg)
        log_error(errMsg)
    except json.JSONDecodeError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Insert Trade)  JSONDecodeError: {e} - Error decoding JSON data from file at {file_path}"
        print(errMsg)
        log_error(errMsg)
    except KeyError as e:
        errMsg = f"Account: {account} Magic: {magic}   Task: (Insert Trade)  KeyError: {e} - 'trades' key not found in JSON data for magic {magic}"
        print(errMsg)
        log_error(errMsg)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Insert Trade)  Unexpected error: {e} occurred while inserting trade for magic {magic}"
        print(errMsg)
        log_error(errMsg)


     
def getSets(account):
    account = str(account)
    sets = []
    try:
        folder_path = os.path.join(databaseFolder, account)
        
        # Check if the account folder exists and has files
        if os.path.exists(folder_path) and len(os.listdir(folder_path)) > 0:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                
                # Attempt to load JSON data from each file
                with open(file_path, 'r') as jsonFile:
                    try:
                        portalocker.lock(jsonFile, portalocker.LOCK_SH)  # Shared lock for reading
                        data = json.load(jsonFile)
                        sets.append(data)
                    finally:
                        portalocker.unlock(jsonFile)
    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Task: (Get Sets)  LockException: {e} - Failed to acquire lock for file"
        print(errMsg)
        log_error(errMsg)
    except FileNotFoundError as e:
        errMsg = f"Account: {account}  Task: (Get Sets)  FileNotFoundError: {e} - Account folder '{folder_path}' not found"
        print(errMsg)
        log_error(errMsg)
    except json.JSONDecodeError as e:
        errMsg = f"Account: {account}  Task: (Get Sets)  JSONDecodeError: {e} - Error decoding JSON data from file '{file_path}'"
        print(errMsg)
        log_error(errMsg)
    except Exception as e:
        errMsg = f"Account: {account}  Task: (Get Sets)  Unexpected error: {e} occurred while loading sets for account '{account}'"
        print(errMsg)
        log_error(errMsg)
    
    return sets



def getFilterData(account):
    try:
        allSets = getFrontendSets(account)
        
        # Initialize data with large initial values for min and small for max
        data = {
            "minProfit": float('inf'),
            "maxProfit": 0,
            "minTrades": float('inf'),
            "maxTrades": 0,
            "minDrawdown": float('inf'),
            "maxDrawdown": 0,
            "minProfitFactor": float('inf'),
            "maxProfitFactor": 0,
            "minReturnOnDrawdown": float('inf'),
            "maxReturnOnDrawdown": 0,
            "minDaysLive": float('inf'),
            "maxDaysLive": 0,
            "minAvgDrawdown": float('inf'),
            "maxAvgDrawdown": 0,
            "minWinRate": float('inf'),
            "maxWinRate": 0
            
        }
        
        for set_data in allSets:
            profit = set_data["stats"]["profit"]
            trades = set_data["stats"]["trades"]
            maxDrawdown = set_data["stats"]["maxDrawdown"]
            profitFactor = set_data["stats"]["profitFactor"]
            returnOnDrawdown = set_data["stats"]["returnOnDrawdown"]
            daysLive = set_data["stats"]["daysLive"]
            avgDrawdown = set_data["stats"]["avgDrawdown"]
            winRate = set_data["stats"]["winRate"]
            
            try:
                winRate = int(winRate.replace("%",""))
            except:
                winRate = 0
            
            if winRate == "":
                winRate = 0
            
            # Handle cases where maxDrawdown, returnOnDrawdown, or daysLive may be "-"
            if maxDrawdown == "-":
                maxDrawdown = 0
            if avgDrawdown == "-":
                avgDrawdown = 0
            if returnOnDrawdown == "-":
                returnOnDrawdown = 0
            if not daysLive:
                daysLive = 0
            
            # Update minimum and maximum values
            try:
                data["minProfit"] = min(data["minProfit"], profit)
                try:
                    if float(data["minProfit"]) < 0:
                        data["minProfit"] = 0
                except:
                    data["minProfit"] = 0
                data["maxProfit"] = max(data["maxProfit"], profit)
                data["minTrades"] = min(data["minTrades"], trades)
                data["maxTrades"] = max(data["maxTrades"], trades)
                data["minDrawdown"] = min(data["minDrawdown"], maxDrawdown)
                data["maxDrawdown"] = max(data["maxDrawdown"], maxDrawdown)
                data["minProfitFactor"] = min(data["minProfitFactor"], profitFactor)
                data["maxProfitFactor"] = max(data["maxProfitFactor"], profitFactor)
                data["minReturnOnDrawdown"] = min(data["minReturnOnDrawdown"], returnOnDrawdown)
                data["maxReturnOnDrawdown"] = max(data["maxReturnOnDrawdown"], returnOnDrawdown)
                data["minDaysLive"] = min(data["minDaysLive"], daysLive)
                data["maxDaysLive"] = max(data["maxDaysLive"], daysLive)
                data["minAvgDrawdown"] = min(data["minAvgDrawdown"], avgDrawdown)
                data["maxAvgDrawdown"] = max(data["maxAvgDrawdown"], avgDrawdown)
                data["minWinRate"] = min(data["minWinRate"], winRate)
                data["maxWinRate"] = max(data["maxWinRate"], winRate)
            except:
                data["minProfit"] = 0
                data["maxProfit"] = 0
                data["minTrades"] = 0
                data["maxTrades"] = 0
                data["minDrawdown"] = 0
                data["maxDrawdown"] = 0
                data["minProfitFactor"] = 0
                data["maxProfitFactor"] = 0
                data["minReturnOnDrawdown"] = 0
                data["maxReturnOnDrawdown"] = 0
                data["minDaysLive"] = 0
                data["maxDaysLive"] = 0
                data["minAvgDrawdown"] = 0
                data["maxAvgDrawdown"] = 0
                data["minWinRate"] = 0
                data["maxWinRate"] = 0
        return data
    
    except Exception as e:
        errMsg = f"Error in getFilterData for account '{account}': {e}"
        print(errMsg)
        log_error(errMsg)
        data = {}
        data["minProfit"] = 0
        data["maxProfit"] = 0
        data["minTrades"] = 0
        data["maxTrades"] = 0
        data["minDrawdown"] = 0
        data["maxDrawdown"] = 0
        data["minProfitFactor"] = 0
        data["maxProfitFactor"] = 0
        data["minReturnOnDrawdown"] = 0
        data["maxReturnOnDrawdown"] = 0
        data["minDaysLive"] = 0
        data["maxDaysLive"] = 0
        data["minAvgDrawdown"] = 0
        data["maxAvgDrawdown"] = 0
        data["minWinRate"] = 0
        data["maxWinRate"] = 0
        return data

def getProfileSets(account, profile):
    dataPath = tracker.getDataPath(account)
    profilePath = os.path.join(dataPath, "MQL5", "Profiles", "Charts", profile)
    profileSets = []
    try:
        for chartFile in os.listdir(profilePath):
            print(chartFile)
            chartPath = os.path.join(dataPath, "MQL5", "Profiles", "Charts", profile, chartFile)
            try:
                print("made it here")
                chartConfig = loader.parse_chr_file(chartPath)
                print(chartConfig)
                chartData = {
                    "setName": chartConfig["chart"]["expert"]["inputs"]["StrategyDescription"],
                    "symbol": chartConfig["chart"]["symbol"],
                    "magic": chartConfig["chart"]["expert"]["inputs"]["MAGIC_NUMBER"]
                }
                profileSets.append(chartData)
            except:
                pass
    except Exception as e:
        print(f"Failed to get profile sets {e}")
        
    return profileSets

def getProfiles(account):
    dataPath = tracker.getDataPath(account)
    profilesPath = os.path.join(dataPath, "MQL5", "Profiles", "Charts")
    profiles = [d for d in os.listdir(profilesPath) if os.path.isdir(os.path.join(profilesPath, d))]
    return profiles

def getDrawdownGraphData(account):
    try:
        allSets = getFrontendSets(account)
        data = []
        
        for set_data in allSets:
            name = set_data["stats"]["setName"]
            new_trace = {"x": [], "y": [], "mode": "lines", "name": name}
            
            for item in set_data["drawdown"]:
                datetime_obj = datetime.fromtimestamp(item["time"])
                formatted_date_time = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
                new_trace["x"].append(formatted_date_time)
                new_trace["y"].append(item["drawdown"])
            
            data.append(new_trace)
        
        return data
    
    except KeyError as e:
        errMsg = f"Account: {account}  Task: (Get Drawdown Graph Data)  KeyError: {e} - Required key not found in set data"
        print(errMsg)
        log_error(errMsg)
        return None
    except Exception as e:
        errMsg = f"Account: {account} Task: (Get Drawdown Graph Data)   Error in getDrawdownGraphData for account '{account}': {e}"
        print(errMsg)
        log_error(errMsg)
        return None


def getEquityGraphData(account):
    try:
        allSets = getFrontendSets(account)
        data = []
        
        for set_data in allSets:
            name = set_data["stats"]["setName"]
            new_trace = {"x": [], "y": [], "mode": "lines", "name": name}
            
            for item in set_data["equity"]:
                datetime_obj = datetime.fromtimestamp(item["time"])
                formatted_date_time = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
                new_trace["x"].append(formatted_date_time)
                new_trace["y"].append(item["equity"])
            
            data.append(new_trace)
        
        return data
    
    except KeyError as e:
        errMsg = f"Account: {account}  Task: (Get Equity Graph Data)  KeyError: {e} - Required key not found in set data"
        print(errMsg)
        log_error(errMsg)
        return None
    
    except Exception as e:
        errMsg = f"Account: {account}  Task: (Get Equity Graph Data)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)
        return None



def updateProfitFactor(magic, account):
    account = str(account)
    try:
        newProfitFactor = tracker.getProfitFactor(magic)
        
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")
        
        # Lock the file for reading and writing
        with open(file_path, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)

                # Read existing data from JSON file
                set_data = json.load(file)

                # Update profit factor in the loaded data
                set_data["stats"]["profitFactor"] = newProfitFactor

                # Move the file pointer to the beginning of the file to overwrite it
                file.seek(0)
                file.truncate()

                # Write updated data back to JSON file
                json.dump(set_data, file, indent=4)
                
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())

            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Profit Factor)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    except FileNotFoundError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Profit Factor)  FileNotFoundError: {e} - File {file_path} not found while updating profit factor for magic {magic}"
        print(errMsg)
        log_error(errMsg)
    except KeyError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Profit Factor)  KeyError: {e} - Required key not found in set data while updating profit factor for magic {magic}"
        print(errMsg)
        log_error(errMsg)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Profit Factor)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)


def isTradeExists(trades, trade_id):
    try:
        # Ensure trade_id is treated as a string for comparison
        str_trade_id = str(trade_id)
        
        # Iterate through trades list
        for trade in trades:
            # Check if trade id matches
            if str(trade['id']) == str_trade_id:
                return True
        
        # If no match found, return False
        return False
    
    except Exception as e:
        errMsg = f"Task: (Is Trade Exists)  Error: {e}"
        print(errMsg)
        log_error(errMsg)
        return False


def updateDrawdown(magic, drawdown, time, account):
    account = str(account)
    try:
        
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")
        
        # Lock the file for reading and writing
        with open(file_path, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)

                # Read existing data from JSON file
                set_data = json.load(file)

                ## Updating average drawdown
                allDrawdown = []
                for setDrawdown in set_data["drawdown"]:
                    allDrawdown.append(setDrawdown["drawdown"])
                
                allDrawdown.append(drawdown)
                averageDrawdown = round(statistics.mean(allDrawdown),2)
                
                set_data["stats"]["avgDrawdown"] = averageDrawdown
                
                print(f"{magic} Average: {averageDrawdown}")
                
                # Append new drawdown data
                set_data["drawdown"].append({
                    "time": time,
                    "drawdown": drawdown
                })

                # Move the file pointer to the beginning of the file to overwrite it
                file.seek(0)
                file.truncate()

                # Write updated data back to JSON file
                json.dump(set_data, file, indent=4)
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Drawdown)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    except FileNotFoundError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Drawdown)  FileNotFoundError: {e} - File {file_path} not found while updating drawdown for magic {magic}"
        print(errMsg)
        log_error(errMsg)
    except KeyError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Drawdown)  KeyError: {e} - Required key not found in set data while updating drawdown for magic {magic}"
        print(errMsg)
        log_error(errMsg)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Drawdown)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)



def getDeposit(account):
    account = str(account)
    try:
        file_path = os.path.join(databaseFolder, "Accounts", f"{account}.json")
        if os.path.exists(file_path):
        # Lock the file for reading
            with open(file_path, "r") as file:
                try:
                    portalocker.lock(file, portalocker.LOCK_SH)  # Shared lock for reading
                        # Load account configuration
                    config = json.load(file)
                    return config.get("deposit", 0)  
                finally:
                    portalocker.unlock(file)
        else:
            errMsg = f"Task: (Get Deposit)  File {file_path} not found while getting deposit for account {account}"
            print(errMsg)
            log_error(errMsg)
            return 0  # Return a default value
            

    except portalocker.LockException as e:
        errMsg = f"Task: (Get Deposit)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
        return 0  # Return a default value
    
    except FileNotFoundError:
        errMsg = f"Task: (Get Deposit)  File {file_path} not found while getting deposit for account {account}"
        print(errMsg)
        log_error(errMsg)
        return 0  # Return a default value
    
    except KeyError as e:
        errMsg = f"Task: (Get Deposit)  KeyError: {e} - 'deposit' key not found in account configuration for account {account}"
        print(errMsg)
        log_error(errMsg)
        return 0  # Return a default value
    
    except Exception as e:
        errMsg = f"Task: (Get Deposit)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)
        return 0  # Return a default value


def updateEquity(magic, profit, time, account):
    account = str(account)
    try:
        # Calculate profit percentage based on absolute profit and deposit
        deposit = getDeposit(account)
        # Calculate new equity including historical profit and current profit
        historicalProfit = tracker.getHistoricalProfit(magic)
        equity = float(deposit) + float(historicalProfit) + float(profit)
        
        # Lock the file for reading and writing
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")
        with open(file_path, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)

                # Load the set JSON from file
                set_data = json.load(file)

                # Append new equity data to the "equity" list in the JSON
                set_data["equity"].append({
                    "time": time,
                    "equity": equity,
                    "profit": profit,
                })

                # Move the file pointer to the beginning of the file to overwrite it
                file.seek(0)
                file.truncate()

                # Write back the updated set JSON to file
                json.dump(set_data, file, indent=4)
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Equity)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    
    except FileNotFoundError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Equity)  FileNotFoundError: {e} - File {file_path} not found while updating equity for magic {magic}"
        print(errMsg)
        log_error(errMsg)
    
    except KeyError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Equity)  KeyError: {e} - Required key not found in set data while updating equity for magic {magic}"
        print(errMsg)
        log_error(errMsg)
    
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Equity)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)


          
def getSet(magic, account):
    account = str(account)
    try:
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")
        
        # Lock the file for reading
        with open(file_path, "r") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_SH)  # Shared lock for reading
                data = json.load(file)
                return data
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Get Set)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
        return {}
    
    except FileNotFoundError:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Get Set)  File {magic}.json not found"
        tracker.createSet(magic)
        print(errMsg)
        log_error(errMsg)
        return {}
    
    except KeyError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Get Set)  KeyError: {e} - Error accessing JSON data"
        print(errMsg)
        log_error(errMsg)
        return {}
    
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Get Set)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)
        return {}

    
def updateLotSizes(account, magic, lotSizes):
    account = str(account)
    try:
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")

        # Lock the file for reading and writing
        with open(file_path, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)

                # Load JSON data from file
                set_data = json.load(file)

                # Update daysLive in the loaded data
                set_data["stats"]["minLotSize"] = lotSizes["minLotSize"]
                set_data["stats"]["maxLotSize"] = lotSizes["maxLotSize"]
                set_data["stats"]["avgLotSize"] = lotSizes["avgLotSize"]

                # Move the file pointer to the beginning of the file to overwrite it
                file.seek(0)
                file.truncate()

                # Write updated data back to JSON file
                json.dump(set_data, file, indent=4)
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Task: (Update Lot Size)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    
    except FileNotFoundError:
        errMsg = f"Account: {account}  Task: (Update Lot Size)  File {magic}.json not found"
        print(errMsg)
        log_error(errMsg)
    
    except KeyError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Lot Size)  KeyError: {e} - Error accessing JSON data"
        print(errMsg)
        log_error(errMsg)
    
    except Exception as e:
        errMsg = f"Account: {account}  Task: (Update Lot Size)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)
 
def updateTradeTimes(account, magic, tradeTimes):
    account = str(account)
    try:
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")

        # Lock the file for reading and writing
        with open(file_path, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)

                # Load JSON data from file
                set_data = json.load(file)

                # Update daysLive in the loaded data
                set_data["stats"]["minTradeTime"] = tradeTimes["minTradeTime"]
                set_data["stats"]["maxTradeTime"] = tradeTimes["maxTradeTime"]
                set_data["stats"]["avgTradeTime"] = tradeTimes["avgTradeTime"]

                # Move the file pointer to the beginning of the file to overwrite it
                file.seek(0)
                file.truncate()

                # Write updated data back to JSON file
                json.dump(set_data, file, indent=4)
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Task: (Update Trade Times)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    
    except FileNotFoundError:
        errMsg = f"Account: {account}  Task: (Update Trade Times)  File {magic}.json not found"
        print(errMsg)
        log_error(errMsg)
    
    except KeyError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Trade Times)  KeyError: {e} - Error accessing JSON data"
        print(errMsg)
        log_error(errMsg)
    
    except Exception as e:
        errMsg = f"Account: {account}  Task: (Update Trade Times)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)       

def updateWinRate(account, magic, winRates):
    account = str(account)
    try:
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")

        # Lock the file for reading and writing
        with open(file_path, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)

                # Load JSON data from file
                set_data = json.load(file)

                # Update daysLive in the loaded data
                set_data["stats"]["winRate"] = winRates["winRate"]
                set_data["stats"]["wins"] = winRates["wins"]
                set_data["stats"]["losses"] = winRates["losses"]

                # Move the file pointer to the beginning of the file to overwrite it
                file.seek(0)
                file.truncate()

                # Write updated data back to JSON file
                json.dump(set_data, file, indent=4)
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Task: (Update Win Rate)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    
    except FileNotFoundError:
        errMsg = f"Account: {account}  Task: (Update Win Rate)  File {magic}.json not found"
        print(errMsg)
        log_error(errMsg)
    
    except KeyError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Win Rate)  KeyError: {e} - Error accessing JSON data"
        print(errMsg)
        log_error(errMsg)
    
    except Exception as e:
        errMsg = f"Account: {account}  Task: (Update Win Rate)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)
    
def getReturnOnDrawdown(magic, drawdown, account, profit):
    try:
        returnOnDrawdown = round(profit / abs(float(drawdown)), 2)
    except:
            returnOnDrawdown = "-"
    return returnOnDrawdown

def updateReturnOnDrawdown(magic, returnOnDrawdown, account):
    account = str(account)
    try:
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")

        # Lock the file for reading and writing
        with open(file_path, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)

                # Load JSON data from file
                set_data = json.load(file)

                # Update returnOnDrawdown in the loaded data
                set_data["stats"]["returnOnDrawdown"] = returnOnDrawdown

                # Move the file pointer to the beginning of the file to overwrite it
                file.seek(0)
                file.truncate()

                # Write updated data back to JSON file
                json.dump(set_data, file, indent=4)
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Return on Drawdown)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    
    except FileNotFoundError:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Return on Drawdown)  File {magic}.json not found"
        print(errMsg)
        log_error(errMsg)
    
    except KeyError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Return on Drawdown)  KeyError: {e} - Error accessing JSON data"
        print(errMsg)
        log_error(errMsg)
    
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Return on Drawdown)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)


def updateMaxDrawdown(magic, drawdown, account):
    account = str(account)
    try:
        file_path = os.path.join(databaseFolder, account, f"{magic}.json")

        # Lock the file for reading and writing
        with open(file_path, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)

                # Load JSON data from file
                set_data = json.load(file)

                # Update maxDrawdown in the loaded data
                set_data["stats"]["maxDrawdown"] = drawdown

                # Move the file pointer to the beginning of the file to overwrite it
                file.seek(0)
                file.truncate()

                # Write updated data back to JSON file
                json.dump(set_data, file, indent=4)
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Max Drawdown)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    
    except FileNotFoundError:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Max Drawdown)  File {magic}.json not found"
        print(errMsg)
        log_error(errMsg)
    
    except KeyError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Max Drawdown)  KeyError: {e} - Error accessing JSON data"
        print(errMsg)
        log_error(errMsg)
    
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Max Drawdown)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)



def updateDaysLive(account):
    account = str(account)
    try:
        magics = tracker.getAllMagics()
        for magic in magics:
            file_path = os.path.join(databaseFolder, account, f"{magic}.json")

            # Lock the file for reading and writing
            with open(file_path, "r+") as file:
                try:
                    portalocker.lock(file, portalocker.LOCK_EX)

                    # Load JSON data from file
                    set_data = json.load(file)

                    # Update daysLive in the loaded data
                    set_data["stats"]["daysLive"] = tracker.getDaysLive(magic)

                    # Move the file pointer to the beginning of the file to overwrite it
                    file.seek(0)
                    file.truncate()

                    # Write updated data back to JSON file
                    json.dump(set_data, file, indent=4)
                    file.flush()  # Ensure all data is written to disk
                    os.fsync(file.fileno())
                finally:
                    portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Account: {account}  Task: (Update Days Live)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    
    except FileNotFoundError:
        errMsg = f"Account: {account}  Task: (Update Days Live)  File {magic}.json not found"
        print(errMsg)
        log_error(errMsg)
    
    except KeyError as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Update Days Live)  KeyError: {e} - Error accessing JSON data"
        print(errMsg)
        log_error(errMsg)
    
    except Exception as e:
        errMsg = f"Account: {account}  Task: (Update Days Live)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)

def createAccount(account):
    try:
        account_login = account['login']
        accounts_folder = os.path.join(databaseFolder, "Accounts")
        
        # Check if the 'Accounts' folder exists, create it if it doesn't
        if not os.path.exists(accounts_folder):
            os.makedirs(accounts_folder)
        
        file_path = os.path.join(accounts_folder, f"{account_login}.json")

        # Lock the file for writing
        with open(file_path, "w+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)
                json.dump(account, file, indent=4)
                file.flush()  # Ensure all data is written to disk
                os.fsync(file.fileno())
            finally:
                portalocker.unlock(file)

    except portalocker.LockException as e:
        errMsg = f"Task: (Create Account)  LockException: {e} - Failed to acquire lock for file {file_path}"
        print(errMsg)
        log_error(errMsg)
    
    except FileNotFoundError:
        errMsg = f"Task: (Create Account)  Folder {file_path} not found"
        print(errMsg)
        log_error(errMsg)
    
    except Exception as e:
        errMsg = f"Task: (Create Account)  Unexpected error: {e}"
        print(errMsg)
        log_error(errMsg)

