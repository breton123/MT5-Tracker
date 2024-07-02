import MetaTrader5 as mt5
import datetime as datetime
import time, os, json
from datetime import datetime

#databaseFolder = "C:\\Users\\Louis\\Desktop\\MetaTrader Controller\\database"
user_profile = os.environ['USERPROFILE']
databaseFolder = os.path.join(user_profile, 'AppData', 'Local', 'Mt5TrackerDatabase')
lastTradeTime = 0
accounts = []
# establish MetaTrader 5 connection to a specified trading account
def openMt5(terminalFolder):
     global accounts
     if not mt5.initialize(terminalFolder):
          print("initialize() failed, error code =",mt5.last_error())
          quit()
     accounts.append(getAccount())


def getAccounts():
     global accounts
     return accounts

## Returns set from magic
def findSet(sets, magic):
     for data in sets:
          if str(data["stats"]["magic"]) == str(magic):
               return data

## Get current account number
def getAccount():
     account_info=mt5.account_info()
     number = account_info[0]
     return number

## Returns list of sets for account as jsons
def getFrontendSets(account):
     sets = []
     try:
          if len(os.listdir(f"{databaseFolder}\\{account}")) > 0:
               for file in os.listdir(f"{databaseFolder}\\{account}"):
                    with open(f"{databaseFolder}\\{account}\\{file}", 'r') as jsonFile:
                         data = json.load(jsonFile)
                         sets.append(data)
     except:
          pass
     return sets

## Returns list of sets for account as jsons
def getSets():
     account = getAccount()
     sets = []
     try:
          if len(os.listdir(f"{databaseFolder}\\{account}")) > 0:
               for file in os.listdir(f"{databaseFolder}\\{account}"):
                    with open(f"{databaseFolder}\\{account}\\{file}", 'r') as jsonFile:
                         data = json.load(jsonFile)
                         sets.append(data)
     except:
          pass
     return sets


def setLastTradeTime():
     global lastTradeTime
     try:
          allSets = getSets()
          if len(allSets) == 0:
               return lastTradeTime
          for set in allSets:
               for trade in set["trades"]:
                    if trade["time"] > lastTradeTime:
                         lastTradeTime = trade["time"]
          return lastTradeTime
     except:
          lastTradeTime = 0
          return 0

    

## Calculate initial deposit on the account
def getDeposit():
     account_info=mt5.account_info()
     balance = account_info[10]
     profit = account_info[12]
     return balance - profit

## Returns list of all magic numbers
def getAllMagics():
    magics = []
    orders = mt5.history_deals_get(0, datetime.now())
    for order in orders:
        if order[6] not in magics:
            if str(order[6]) != "0":
                magics.append(order[6])
    positions = mt5.positions_get()
    for position in positions:
        if position[6] not in magics:
            if str(position[6]) != "0":
                magics.append(position[6])
    return magics

## Inserts one set into the database
def insertSet(newSet):
     account = getAccount()
     magic = newSet["stats"]["magic"]
     if os.path.exists(f"{databaseFolder}\\{account}\\{magic}.json"):
          print(f"Set file already exists")
     else:
          with open(f"{databaseFolder}\\{account}\\{magic}.json", "w+") as file:
               json.dump(newSet, file, indent=4)

## Returns historical profit for magic
def getHistoricalProfit(magic):
    totalProfit = 0
    orders = mt5.history_deals_get(0, datetime.now())
    for order in orders:
        orderMagic = order[6]
        if orderMagic == magic:
            profit = order[13]
            totalProfit += profit
    return round(totalProfit,2)

## Returns number of trades
def getTradeAmount(magic):
    amount = 0
    orders = mt5.history_deals_get(0, datetime.now())
    for order in orders:
            orderMagic = order[6]
            if orderMagic == magic:
                amount += 1
    return amount

def getDaysLive(magic):
    magic = int(magic)
    orders = mt5.history_deals_get(0, datetime.now())
    for order in orders:
        orderMagic = order[6]
        if orderMagic == magic:
          orderTime = order[2]
          date_time = datetime.fromtimestamp(orderTime)
          current_time = datetime.now()
          time_difference = current_time - date_time
          days_difference = time_difference.days
          return days_difference

def createAccount():
     account = getAccount()
     if not os.path.exists(f"{databaseFolder}\\{account}"):
          os.makedirs(f"{databaseFolder}\\{account}")


## Adds any new sets to the database
def onOpen():
     global lastTradeTime
     setLastTradeTime()
     createAccount()
     print(lastTradeTime)
     magics = getAllMagics()
     sets = getSets()
     for magic in magics:
          foundSet = findSet(sets, magic)
          if not foundSet:
               print(f"Creating set {magic}")
               createSet(magic)
          
            
## Returns all historical trades
def addHistoricalTrades(magic):
     trades = []
     magic = int(magic)
     orders = mt5.history_deals_get(0, datetime.now())
     for order in orders:
          orderMagic = order[6]
          if orderMagic == magic:
               if order[8] == 4:
                    orderTime = order[2]
                    volume = order[9]
                    price = order[10]
                    profit = round(order[13],2)
                    symbol = order[15]
                    newTrade = {
                         "time": orderTime,
                         "volume": volume,
                         "price": price,
                         "profit": profit,
                         "symbol": symbol,
                         "magic": magic
                    }
                    trades.append(newTrade)
                    print(newTrade)
                    #print(f"Inserting historical trade for {magic}")
     return trades

def updateProfit(magic, profit):
     account = getAccount()
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "r") as file:
          set = json.load(file)
     set["stats"]["profit"] = profit
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "w+") as file:
          json.dump(set, file, indent=4)

def createSet(magic):
     setData ={
          "stats": {
               "setName": f"Unnamed set {magic}",
               "strategy": "",
               "magic": magic,
               "profit": round(getHistoricalProfit(magic),2),
               "trades": getTradeAmount(magic),
               "maxDrawdown": "-",
               "profitFactor": getProfitFactor(magic),
               "returnOnDrawdown": "-",
               "daysLive": getDaysLive(magic)
          }, 
          "trades": [],
          "drawdown": [],
          "equity": []}
     print(f"Inserting set {magic}")
     historicalTrades = addHistoricalTrades(magic)
     setData["trades"] = historicalTrades
     insertSet(setData)

def setExist(magic):
     account = getAccount()
     try:
          with open(f"{databaseFolder}\\{account}\\{magic}.json", "r") as file:
               return True
     except:
          return False

def insertTrade(magic, trade):
     if not setExist(magic):
          createSet(magic)
     account = getAccount()
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "r") as file:
          set = json.load(file)
     set["trades"].append(trade)
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "w+") as file:
          json.dump(set, file, indent=4)

def getDrawdownGraphData(account):
     allSets = getFrontendSets(account)
     data = []
     for set in allSets:
          name = set["stats"]["setName"]
          newTrace = {"x": [], "y": [], "mode": "lines", "name": name}
          for item in set["drawdown"]:
               datetime_obj = datetime.fromtimestamp(item["time"])
               formatted_date_time = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
               newTrace["x"].append(formatted_date_time)
               newTrace["y"].append(item["drawdown"])
          data.append(newTrace)
     return data

def getEquityGraphData(account):
     allSets = getFrontendSets(account)
     data = []
     for set in allSets:
          name = set["stats"]["setName"]
          newTrace = {"x": [], "y": [], "mode": "lines", "name": name}
          for item in set["equity"]:
               datetime_obj = datetime.fromtimestamp(item["time"])
               formatted_date_time = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
               newTrace["x"].append(formatted_date_time)
               newTrace["y"].append(item["equity"])
          data.append(newTrace)
     return data

def updateProfitFactor(magic):
     newProfitFactor = getProfitFactor(magic)
     account = getAccount()
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "r") as file:
          set = json.load(file)
     set["stats"]["profitFactor"] = newProfitFactor
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "w+") as file:
          json.dump(set, file, indent=4)

def isTradeExists(trades, time):
     for trade in trades:
          if trade['time'] == time:
               return True
     return False

def updateHistoricalTrades():
    global lastTradeTime
    newTrades = []
    orders = mt5.history_deals_get(lastTradeTime, datetime.now())
    for order in orders:
        orderMagic = order[6]
        if order[8] == 4:
            orderTime = order[2]
            if orderTime > lastTradeTime:
               volume = order[9]
               price = order[10]
               profit = round(order[13],2)
               symbol = order[15]
               newTrade = {
               "time": orderTime,
               "volume": volume,
               "price": price,
               "profit": profit,
               "symbol": symbol
               } 
               currentSet = getSet(orderMagic)
               if not currentSet:
                    createSet(orderMagic)
                    currentSet = getSet(orderMagic)
                    currentTrades = currentSet["trades"]
               else:
                    currentTrades = currentSet["trades"]
               if not isTradeExists(currentTrades, orderTime):
                    newTrades.append(newTrade)
                    insertTrade(orderMagic, newTrade)
                    updateProfitFactor(orderMagic)
                    updateProfit(orderMagic, getHistoricalProfit(orderMagic))
                    lastTradeTime = orderTime
                    print(f"New historical trade for {orderMagic}")
    
    if len(newTrades) != 0:
        newLastTradeTime = 0
        for trade in newTrades:
            if trade["time"] > newLastTradeTime:
                newLastTradeTime = trade["time"]
        lastTradeTime = newLastTradeTime
    print(lastTradeTime)


def getProfitFactor(magic):
    magic = int(magic)
    totalProfit = 0
    totalLoss = 0
    orders = mt5.history_deals_get(0, datetime.now())
    for order in orders:
        orderMagic = order[6]
        if orderMagic == magic:
            profit = order[13]
            if profit >= 0:
                totalProfit += profit
            else:
                totalLoss += profit
    if totalLoss == 0:
        return round(totalProfit, 2)
    else:
        return round(totalProfit / totalLoss,2)

def updateDrawdown(magic, drawdown, time):
     if not setExist(magic):
          createSet(magic)
     account = getAccount()
     drawdownPercentage = round((abs(drawdown) / getDeposit()) * 100,2)
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "r") as file:
          set = json.load(file)
     set["drawdown"].append({
          "time": time,
          "drawdown": drawdown,
          "drawdownPercentage": drawdownPercentage
     })
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "w+") as file:
          json.dump(set, file, indent=4)

def updateEquity(magic, profit, time):
     if not setExist(magic):
          createSet(magic)
     account = getAccount()
     profitPercentage = round((abs(profit) / getDeposit()) * 100,2)
     equity = getDeposit() + getHistoricalProfit(magic) + profit 
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "r") as file:
          set = json.load(file)
     set["equity"].append({
          "time": time,
          "equity": equity,
          "profit": profit,
          "profitPercentage": profitPercentage
     })
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "w+") as file:
          json.dump(set, file, indent=4)

def getSet(magic):
     account = getAccount()
     try:
          with open(f"{databaseFolder}\\{account}\\{magic}.json", "r") as file:
               data = json.load(file)
               return data
     except:
          return False

def getDrawdown():
     positions = mt5.positions_get()
     drawdown = {}
     profitList = {}
     currentTime = round(time.time())
     for position in positions:
          tradeid = position[7]
          tradeTime = position[1]
          magic = position[6]
          volume = position[9]
          profit = position[15]
          symbol = position[16]
          
          if magic not in profitList:
               profitList[magic] = profit
          else:
               profitList[magic] = profitList[magic] + profit
          
          if magic not in drawdown:
               if profit < 0:
                    drawdown[magic] = profit
               else:
                    drawdown[magic] = 0
          else:
               if profit < 0:
                    drawdown[magic] = drawdown[magic] + profit
               else:
                    if (drawdown[magic] + profit) > 0:
                         drawdown[magic] = 0
                    else:
                         drawdown[magic] = drawdown[magic] + profit
          
     
     for magic in drawdown:
          print(f"Uploading drawdown {round(drawdown[magic],2)} and profit {round(profitList[magic],2)} for magic {magic}")
          currentDrawdown = round(drawdown[magic],2)
          currentProfit = round(profitList[magic],2)
          updateDrawdown(magic, currentDrawdown, currentTime)
          updateEquity(magic, currentProfit, currentTime)
          setFile = getSet(magic)
          maxD = setFile["stats"]["maxDrawdown"]
          if maxD == "-":
               print(f"New Max Drawdown for {magic}")
               returnOnDrawdown = getReturnOnDrawdown(magic, currentDrawdown)
               updateMaxDrawdown(magic, currentDrawdown)
               updateReturnOnDrawdown(magic, returnOnDrawdown)
          elif currentDrawdown < float(maxD):
               print(f"New Max Drawdown for {magic}")
               returnOnDrawdown = getReturnOnDrawdown(magic, currentDrawdown)
               updateMaxDrawdown(magic, currentDrawdown)
               updateReturnOnDrawdown(magic, returnOnDrawdown)

def getReturnOnDrawdown(magic, drawdown):
    setFile = getSet(magic)
    profit = setFile["stats"]["profit"]
    returnOnDrawdown = round(profit / abs(float(drawdown)),2)
    return returnOnDrawdown

def updateReturnOnDrawdown(magic, returnOnDrawdown):#
     account = getAccount()
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "r") as file:
          set = json.load(file)
     set["stats"]["returnOnDrawdown"] = returnOnDrawdown
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "w+") as file:
          json.dump(set, file, indent=4)

def updateMaxDrawdown(magic, drawdown):#
     account = getAccount()
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "r") as file:
          set = json.load(file)
     set["stats"]["maxDrawdown"] = drawdown
     with open(f"{databaseFolder}\\{account}\\{magic}.json", "w+") as file:
          json.dump(set, file, indent=4)

def updateDaysLive():
     account = getAccount()#
     magics = getAllMagics()
     for magic in magics:
          with open(f"{databaseFolder}\\{account}\\{magic}.json", "r") as file:
               set = json.load(file)
          set["stats"]["daysLive"] = getDaysLive(magic)
          with open(f"{databaseFolder}\\{account}\\{magic}.json", "w+") as file:
               json.dump(set, file, indent=4)

def trackData(terminal):
     try:
          openMt5(terminal)
          onOpen()
          setLastTradeTime()
          while True:
               print("Checking Drawdowns")
               getDrawdown()
               updateHistoricalTrades()
               updateDaysLive()
               time.sleep(10)
     except:
          print("Error")
