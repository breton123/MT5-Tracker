import MetaTrader5 as mt5
import datetime as datetime
import time, os, json, database
from datetime import datetime

#databaseFolder = "C:\\Users\\Louis\\Desktop\\MetaTrader Controller\\database"
user_profile = os.environ['USERPROFILE']
databaseFolder = os.path.join(user_profile, 'AppData', 'Local', 'Mt5TrackerDatabase')
accounts = []
tickets = []

# establish MetaTrader 5 connection to a specified trading account
def openMt5(terminalFolder):
     global accounts
     if not mt5.initialize(terminalFolder):
          print("initialize() failed, error code =",mt5.last_error())
          quit()
     accounts.append(getAccount())

## Get current account number
def getAccount():
     account_info=mt5.account_info()
     number = account_info[0]
     return number

def getAllMagics():
    magics = []
    
    try:
        orders = mt5.history_deals_get(0, datetime.now())
        for order in orders:
            if order[6] not in magics:
                if str(order[6]) != "0":
                    magics.append(order[6])
    except Exception as e:
        errMsg = f"Task: (Get All Magics - History Deals)  Error retrieving historical deals: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return magics

    try:
        positions = mt5.positions_get()
        for position in positions:
            if position[6] not in magics:
                if str(position[6]) != "0":
                    magics.append(position[6])
    except Exception as e:
        errMsg = f"Task: (Get All Magics - Positions)  Error retrieving positions: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return magics

    return magics


def getHistoricalProfit(magic):
    totalProfit = 0
    
    try:
        magic = int(magic)
    except ValueError as e:
        errMsg = f"Task: (Get Historical Profit)  ValueError: {e} - Invalid magic number: {magic}"
        print(errMsg)
        database.log_error(errMsg)
        return round(totalProfit, 2)

    try:
        orders = mt5.history_deals_get(0, datetime.now())
    except Exception as e:
        errMsg = f"Magic: {magic}  Task: (Get Historical Profit)  Error retrieving historical deals: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return round(totalProfit, 2)

    for order in orders:
        try:
            orderMagic = order[6]
            if orderMagic == magic:
                profit = order[13]
                totalProfit += profit
        except KeyError as e:
            errMsg = f"Magic: {magic}  Task: (Get Historical Profit)  KeyError: {e} - Error accessing order details"
            print(errMsg)
            database.log_error(errMsg)
        except Exception as e:
            errMsg = f"Magic: {magic}  Task: (Get Historical Profit)  Unexpected error: {e}"
            print(errMsg)
            database.log_error(errMsg)

    return round(totalProfit, 2)


def getTradeAmount(magic):
    amount = 0
    
    try:
        magic = int(magic)
    except ValueError as e:
        errMsg = f"Task: (Get Trade Amount)  ValueError: {e} - Invalid magic number: {magic}"
        print(errMsg)
        database.log_error(errMsg)
        return amount

    try:
        orders = mt5.history_deals_get(0, datetime.now())
    except Exception as e:
        errMsg = f"Magic: {magic}  Task: (Get Trade Amount)  Error retrieving historical deals: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return amount

    for order in orders:
        try:
            orderMagic = order[6]
            if orderMagic == magic:
                amount += 1
        except KeyError as e:
            errMsg = f"Magic: {magic}  Task: (Get Trade Amount)  KeyError: {e} - Error accessing order details"
            print(errMsg)
            database.log_error(errMsg)
        except Exception as e:
            errMsg = f"Magic: {magic}  Task: (Get Trade Amount)  Unexpected error: {e}"
            print(errMsg)
            database.log_error(errMsg)

    return amount


def getDaysLive(magic):
    try:
        magic = int(magic)
    except ValueError as e:
        errMsg = f"Task: (Get Days Live)  ValueError: {e} - Invalid magic number: {magic}"
        print(errMsg)
        database.log_error(errMsg)
        return 0

    try:
        orders = mt5.history_deals_get(0, datetime.now())
    except Exception as e:
        errMsg = f"Magic: {magic}  Task: (Get Days Live)  Error retrieving historical deals: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return 0

    for order in orders:
        try:
            orderMagic = order[6]
            if orderMagic == magic:
                orderTime = order[2]
                date_time = datetime.fromtimestamp(orderTime)
                current_time = datetime.now()
                time_difference = current_time - date_time
                days_difference = time_difference.days
                return days_difference
        except KeyError as e:
            errMsg = f"Magic: {magic}  Task: (Get Days Live)  KeyError: {e} - Error accessing order details"
            print(errMsg)
            database.log_error(errMsg)
        except Exception as e:
            errMsg = f"Magic: {magic}  Task: (Get Days Live)  Unexpected error: {e}"
            print(errMsg)
            database.log_error(errMsg)

    return 0


def onOpen(account):
    try:
        database.createAccountFolder(account)
    except Exception as e:
        errMsg = f"Account: {account}  Task: (On Open)  Error creating account folder: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return

    try:
        magics = getAllMagics()
    except Exception as e:
        errMsg = f"Account: {account}  Task: (On Open)  Error retrieving magic numbers: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return

    try:
        sets = database.getSets(account)
    except Exception as e:
        errMsg = f"Account: {account}  Task: (On Open)  Error retrieving sets from database: {e}"
        print(errMsg)
        database.log_error(errMsg)
        sets = []

    for magic in magics:
        try:
            foundSet = database.findSet(sets, magic)
            if not foundSet:
                print(f"Creating set {magic}")
                createSet(magic)
        except Exception as e:
            errMsg = f"Account: {account}  Magic: {magic}  Task: (On Open)  Error creating set: {e}"
            print(errMsg)
            database.log_error(errMsg)


def getSetName(magic):
    setName = f"Unnamed set {magic}"
    
    try:
        magic = int(magic)
    except ValueError as e:
        errMsg = f"Task: (Get Set Name)  ValueError: {e} - Invalid magic number: {magic}"
        print(errMsg)
        database.log_error(errMsg)
        return setName

    try:
        orders = mt5.history_deals_get(0, datetime.now())
    except Exception as e:
        errMsg = f"Magic: {magic}  Task: (Get Set Name)  Error retrieving historical deals: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return setName

    for order in orders:
        try:
            orderMagic = order[6]
            if orderMagic == magic:
                print(order[16])
                if order[16] != "":
                    setName = order[16]
        except KeyError as e:
            errMsg = f"Magic: {magic}  Task: (Get Set Name)  KeyError: {e} - Error accessing order details"
            print(errMsg)
            database.log_error(errMsg)
        except Exception as e:
            errMsg = f"Magic: {magic}  Task: (Get Set Name)  Unexpected error: {e}"
            print(errMsg)
            database.log_error(errMsg)

    return setName


def createSet(magic):
    try:
        account = getAccount()
    except Exception as e:
        errMsg = f"Magic: {magic}  Task: (Create Set)  Error retrieving account: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return

    try:
        setName = getSetName(magic)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving set name: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return

    try:
        historicalProfit = round(getHistoricalProfit(magic), 2)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving historical profit: {e}"
        print(errMsg)
        database.log_error(errMsg)
        historicalProfit = 0

    try:
        tradeAmount = getTradeAmount(magic)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving trade amount: {e}"
        print(errMsg)
        database.log_error(errMsg)
        tradeAmount = 0

    try:
        profitFactor = getProfitFactor(magic)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving profit factor: {e}"
        print(errMsg)
        database.log_error(errMsg)
        profitFactor = 0

    try:
        daysLive = getDaysLive(magic)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving days live: {e}"
        print(errMsg)
        database.log_error(errMsg)
        daysLive = 0

    setData = {
        "stats": {
            "setName": setName,
            "strategy": "",
            "magic": magic,
            "profit": historicalProfit,
            "trades": tradeAmount,
            "maxDrawdown": "-",
            "profitFactor": profitFactor,
            "returnOnDrawdown": "-",
            "daysLive": daysLive
        },
        "trades": [],
        "drawdown": [],
        "equity": []
    }

    print(f"Inserting set {magic}")

    try:
        historicalTrades = addHistoricalTrades(magic)
        setData["trades"] = historicalTrades
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error adding historical trades: {e}"
        print(errMsg)
        database.log_error(errMsg)
        setData["trades"] = []

    try:
        database.insertSet(setData, account)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error inserting set into database: {e}"
        print(errMsg)
        database.log_error(errMsg)

            
def addHistoricalTrades(magic):
    trades = []
    
    try:
        magic = int(magic)
    except ValueError as e:
        errMsg = f"Task: (Add Historical Trades)  ValueError: {e} - Invalid magic number: {magic}"
        print(errMsg)
        database.log_error(errMsg)
        return trades

    try:
        orders = mt5.history_deals_get(0, datetime.now())
    except Exception as e:
        errMsg = f"Magic: {magic}  Task: (Add Historical Trades)  Error retrieving historical deals: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return trades

    for order in orders:
        try:
            orderMagic = order[6]
            if orderMagic == magic and order[8] == 4:
                orderTime = order[2]
                volume = order[9]
                price = order[10]
                profit = round(order[13], 2)
                symbol = order[15]
                newTrade = {
                     "id": order[0],
                    "time": orderTime,
                    "volume": volume,
                    "price": price,
                    "profit": profit,
                    "symbol": symbol,
                    "magic": magic
                }
                trades.append(newTrade)
                print(newTrade)
        except KeyError as e:
            errMsg = f"Magic: {magic}  Task: (Add Historical Trades)  KeyError: {e} - Error accessing order details"
            print(errMsg)
            database.log_error(errMsg)
        except Exception as e:
            errMsg = f"Magic: {magic}  Task: (Add Historical Trades)  Unexpected error: {e}"
            print(errMsg)
            database.log_error(errMsg)

    return trades


def updateHistoricalTrades():
    global tickets
    try:
        account = getAccount()
    except Exception as e:
        errMsg = f"Task: (Update Historical Trades)  Error getting account: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return
    
    try:
        orders = mt5.history_deals_get(0, datetime.now())
    except Exception as e:
        errMsg = f"Account: {account}  Task: (Update Historical Trades)  Error getting historical deals: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return
    
    for order in orders:
        try:
            orderMagic = order[6]
            if order[8] == 4:
                order_id = order[0]
                if order_id not in tickets:
                    try:
                        currentSet = database.getSet(orderMagic, account)
                    except Exception as e:
                        errMsg = f"Account: {account}  Magic: {orderMagic}  Task: (Update Historical Trades)  Error getting current set: {e}"
                        print(errMsg)
                        database.log_error(errMsg)
                        continue
                    
                    try:
                          currentTrades = currentSet["trades"]
                    except KeyError as e:
                        errMsg = f"Account: {account}  Magic: {orderMagic}  Task: (Update Historical Trades)  KeyError: {e} - 'trades' key not found in current set"
                        print(errMsg)
                        database.log_error(errMsg)
                        continue
                    
                    try:
                        if not database.isTradeExists(currentTrades, order_id):
                            orderTime = order[2]
                            volume = order[9]
                            price = order[10]
                            profit = round(order[13], 2)
                            symbol = order[15]
                            newTrade = {
                                "id": order_id,
                                "time": orderTime,
                                "volume": volume,
                                "price": price,
                                "profit": profit,
                                "symbol": symbol
                            }
                            database.insertTrade(orderMagic, newTrade, account)
                            database.updateProfitFactor(orderMagic, account)
                            database.updateProfit(orderMagic, getHistoricalProfit(orderMagic), account)
                            tickets.append(order_id)
                            print(f"New historical trade for {orderMagic}")
                        else:
                            tickets.append(order_id)
                    except Exception as e:
                        errMsg = f"Account: {account}  Magic: {orderMagic}  Task: (Update Historical Trades)  Error processing trade: {e}"
                        print(errMsg)
                        database.log_error(errMsg)
        except KeyError as e:
            errMsg = f"Account: {account}  Task: (Update Historical Trades)  KeyError: {e} - Error accessing order details"
            print(errMsg)
            database.log_error(errMsg)
        except Exception as e:
            errMsg = f"Account: {account}  Task: (Update Historical Trades)  Unexpected error: {e}"
            print(errMsg)
            database.log_error(errMsg)


def getProfitFactor(magic):
    try:
        magic = int(magic)
    except ValueError as e:
        errMsg = f"Task: (Get Profit Factor)  ValueError: {e} - Invalid magic number: {magic}"
        print(errMsg)
        database.log_error(errMsg)
        return None

    totalProfit = 0
    totalLoss = 0

    try:
        orders = mt5.history_deals_get(0, datetime.now())
    except Exception as e:
        errMsg = f"Magic: {magic}  Task: (Get Profit Factor)  Error retrieving historical deals: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return None

    for order in orders:
        try:
            orderMagic = order[6]
            if orderMagic == magic:
                profit = order[13]
                if profit >= 0:
                    totalProfit += profit
                else:
                    totalLoss += profit
        except KeyError as e:
            errMsg = f"Magic: {magic}  Task: (Get Profit Factor)  KeyError: {e} - Error accessing order details"
            print(errMsg)
            database.log_error(errMsg)
        except Exception as e:
            errMsg = f"Magic: {magic}  Task: (Get Profit Factor)  Unexpected error: {e}"
            print(errMsg)
            database.log_error(errMsg)

    try:
        if totalLoss == 0:
            return round(totalProfit, 2)
        else:
            return round(totalProfit / totalLoss, 2)
    except Exception as e:
        errMsg = f"Magic: {magic}  Task: (Get Profit Factor)  Error calculating profit factor: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return None


def getDrawdown():
    try:
        positions = mt5.positions_get()
    except Exception as e:
        errMsg = f"Task: (Get Drawdown)  Error getting positions: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return

    drawdown = {}
    profitList = {}
    currentTime = round(time.time())
    
    try:
        account = getAccount()
    except Exception as e:
        errMsg = f"Task: (Get Drawdown)  Error getting account: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return
    
    for position in positions:
        try:
            tradeid = position[7]
            tradeTime = position[1]
            magic = position[6]
            volume = position[9]
            profit = position[15]
            symbol = position[16]
            
            if magic not in profitList:
                profitList[magic] = profit
            else:
                profitList[magic] += profit
            
            if magic not in drawdown:
                drawdown[magic] = profit if profit < 0 else 0
            else:
                if profit < 0:
                    drawdown[magic] += profit
                else:
                    drawdown[magic] = max(0, drawdown[magic] + profit)
        except KeyError as e:
            errMsg = f"Account: {account}  Task: (Get Drawdown)  KeyError: {e} - Error accessing position details"
            print(errMsg)
            database.log_error(errMsg)
        except Exception as e:
            errMsg = f"Account: {account}  Task: (Get Drawdown)  Unexpected error: {e}"
            print(errMsg)
            database.log_error(errMsg)
    
    for magic in drawdown:
        try:
            currentDrawdown = round(drawdown[magic], 2)
            currentProfit = round(profitList[magic], 2)
            
            print(f"Uploading drawdown {currentDrawdown} and profit {currentProfit} for magic {magic}")
            database.updateDrawdown(magic, currentDrawdown, currentTime, account)
            database.updateEquity(magic, currentProfit, currentTime, account)
            
            try:
                setFile = database.getSet(magic, account)
            except Exception as e:
                errMsg = f"Account: {account}  Magic: {magic}  Task: (Get Drawdown)  Error getting set file: {e}"
                print(errMsg)
                database.log_error(errMsg)
                continue
            
            try:
                maxD = setFile["stats"]["maxDrawdown"]
            except KeyError as e:
                errMsg = f"Account: {account}  Magic: {magic}  Task: (Get Drawdown)  KeyError: {e} - 'maxDrawdown' key not found in set file"
                print(errMsg)
                database.log_error(errMsg)
                continue
            
            if maxD == "-":
                print(f"New Max Drawdown for {magic}")
                try:
                    returnOnDrawdown = database.getReturnOnDrawdown(magic, currentDrawdown, account)
                    database.updateMaxDrawdown(magic, currentDrawdown, account)
                    database.updateReturnOnDrawdown(magic, returnOnDrawdown, account)
                except Exception as e:
                    errMsg = f"Account: {account}  Magic: {magic}  Task: (Get Drawdown)  Error updating max drawdown or return on drawdown: {e}"
                    print(errMsg)
                    database.log_error(errMsg)
            elif currentDrawdown < float(maxD):
                print(f"New Max Drawdown for {magic}")
                try:
                    returnOnDrawdown = database.getReturnOnDrawdown(magic, currentDrawdown, account)
                    database.updateMaxDrawdown(magic, currentDrawdown, account)
                    database.updateReturnOnDrawdown(magic, returnOnDrawdown, account)
                except Exception as e:
                    errMsg = f"Account: {account}  Magic: {magic}  Task: (Get Drawdown)  Error updating max drawdown or return on drawdown: {e}"
                    print(errMsg)
                    database.log_error(errMsg)
        except Exception as e:
            errMsg = f"Account: {account}  Magic: {magic}  Task: (Get Drawdown)  Unexpected error: {e}"
            print(errMsg)
            database.log_error(errMsg)

def trackData(terminal):
    try:
        try:
            openMt5(terminal)
            account = getAccount()
        except Exception as e:
            errMsg = f"Account: {account}  Task: (Track Data)  Error opening MT5 terminal: {e}"
            print(errMsg)
            database.log_error(errMsg)
            return

        try:
            onOpen(account)
        except Exception as e:
            errMsg = f"Account: {account}  Task: (Track Data)  Error executing onOpen function: {e}"
            print(errMsg)
            database.log_error(errMsg)
            return
        time.sleep(5)
        while True:
            try:
                print("Checking Drawdowns")
                getDrawdown()
            except Exception as e:
                errMsg = f"Account: {account}  Task: (Track Data)  Error in getDrawdown: {e}"
                print(errMsg)
                database.log_error(errMsg)

            try:
                updateHistoricalTrades()
            except Exception as e:
                errMsg = f"Account: {account}  Task: (Track Data)  Error in updateHistoricalTrades: {e}"
                print(errMsg)
                database.log_error(errMsg)

            try:
                database.updateDaysLive(account)
            except Exception as e:
                errMsg = f"Account: {account}  Task: (Track Data)  Error updating days live: {e}"
                print(errMsg)
                database.log_error(errMsg)

            time.sleep(10)
    except Exception as e:
        errMsg = f"Account: {account}  Task: (Track Data)  Unexpected error: {e}"
        print(errMsg)
        database.log_error(errMsg)
