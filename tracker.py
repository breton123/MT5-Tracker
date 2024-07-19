import MetaTrader5 as mt5
import datetime as datetime
import time, os, json, database, controller, statistics
from datetime import datetime, timedelta

#databaseFolder = "C:\\Users\\Louis\\Desktop\\MetaTrader Controller\\database"
user_profile = os.environ['USERPROFILE']
databaseFolder = os.path.join(user_profile, 'AppData', 'Local', 'Mt5TrackerDatabase')
accounts = []
tickets = []

# establish MetaTrader 5 connection to a specified trading account
def openMt5(accountData):
     global accounts
     if not mt5.initialize(accountData["terminalFilePath"], login=int(accountData["login"]), password=accountData["password"], server=accountData["server"]):
          print("initialize() failed, error code =",mt5.last_error())
          quit()
     accounts.append(getAccount())

## Get current account number
def getAccount():
     account_info=mt5.account_info()
     number = account_info[0]
     return number

def getAllMagics(accountData):
    openMt5(accountData)
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


def getHistoricalProfit(magic, accountData):
    openMt5(accountData)
    account = accountData["login"]
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


def getTradeAmount(magic, account):
    openMt5(account)
    accountData = account
    account = account["login"]
    amount = 0
    try:
        orders = mt5.history_deals_get(0, datetime.now())
        for order in orders:
            order = order._asdict()
            if order["magic"] == magic:
                if order["reason"] == 4:
                    amount += 1  
        return amount     
    
    except Exception as e:
        errMsg = f"Task: (Get Trade Amount)  Error retrieving historical deals: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return amount


def getDaysLive(magic, accountData):
    openMt5(accountData)
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
    openMt5(account)
    accountData = account
    account = account["login"]
    try:
        database.createAccountFolder(account)
    except Exception as e:
        errMsg = f"Account: {account}  Task: (On Open)  Error creating account folder: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return

    try:
        magics = getAllMagics(accountData)
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
                createSet(magic, accountData)
        except Exception as e:
            errMsg = f"Account: {account}  Magic: {magic}  Task: (On Open)  Error creating set: {e}"
            print(errMsg)
            database.log_error(errMsg)


def getSetName(magic, accountData):
    openMt5(accountData)
    account = accountData["login"]

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
                if order[16] != "" and "[sl" not in order[16] and "[tp" not in order[16] and len(order[16]) > 5:
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


def createSet(magic, accountData):
    openMt5(accountData)
    account = accountData["login"]

    try:
        setName = getSetName(magic, accountData)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving set name: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return

    try:
        historicalProfit = round(getHistoricalProfit(magic, accountData), 2)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving historical profit: {e}"
        print(errMsg)
        database.log_error(errMsg)
        historicalProfit = 0

    try:
        tradeAmount = getTradeAmount(magic, accountData)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving trade amount: {e}"
        print(errMsg)
        database.log_error(errMsg)
        tradeAmount = 0

    try:
        profitFactor = getProfitFactor(magic, accountData)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving profit factor: {e}"
        print(errMsg)
        database.log_error(errMsg)
        profitFactor = 0

    try:
        daysLive = getDaysLive(magic, accountData)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving days live: {e}"
        print(errMsg)
        database.log_error(errMsg)
        daysLive = 0

    try:
        lotSizes = getLotSizes(magic, accountData)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving lot sizes: {e}"
        print(errMsg)
        database.log_error(errMsg)
        lotSizes = {
            "minLotSize": 0,
            "maxLotSize": 0,
            "avgLotSize": 0
        }

    try:
        winRate = getWinRate(magic, accountData)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving win rate: {e}"
        print(errMsg)
        database.log_error(errMsg)
        winRate = {
            "winRate": "0%",
            "wins": 0,
            "losses": 0
        }
        
    try:
        tradeTimes = getTradeTimes(magic, accountData)
    except Exception as e:
        errMsg = f"Account: {account}  Magic: {magic}  Task: (Create Set)  Error retrieving trade times: {e}"
        print(errMsg)
        database.log_error(errMsg)
        tradeTimes = {
            "minTradeTime": 0,
            "maxTradeTime": 0,
            "avgTradeTime": 0
        }
        
    setData = {
        "stats": {
            "setName": setName,
            "strategy": "",
            "magic": magic,
            "profit": historicalProfit,
            "trades": tradeAmount,
            "maxDrawdown": "-",
            "avgDrawdown": "-",
            "profitFactor": profitFactor,
            "returnOnDrawdown": "-",
            "minLotSize": lotSizes["minLotSize"],
            "maxLotSize": lotSizes["maxLotSize"],
            "avgLotSize": lotSizes["avgLotSize"],
            "winRate": winRate["winRate"],
            "wins": winRate["wins"],
            "losses": winRate["losses"],
            "minTradeTime": tradeTimes["minTradeTime"],
            "maxTradeTime": tradeTimes["maxTradeTime"],
            "avgTradeTime": tradeTimes["avgTradeTime"],
            "daysLive": daysLive
        },
        "trades": [],
        "drawdown": [],
        "equity": []
    }

    print(f"Inserting set {magic}")

    try:
        historicalTrades = addHistoricalTrades(magic, accountData)
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

            
def addHistoricalTrades(magic, accountData):
    openMt5(accountData)
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


def updateHistoricalTrades(account):
    global tickets
    openMt5(account)
    accountData = account
    account = account["login"]
    
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
                        currentSet = database.getSet(orderMagic, accountData)
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
                            database.updateProfitFactor(orderMagic, accountData)
                            database.updateProfit(orderMagic, getHistoricalProfit(orderMagic, accountData), account)
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


def getProfitFactor(magic, accountData):
    openMt5(accountData)
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


def getLotSizes(magic, account):
    lotSizes = []
    openMt5(account)
    account = account["login"]
    try:
        orders = mt5.history_deals_get(0, datetime.now())
        for order in orders:
            order = order._asdict()
            if order["magic"] == magic:
                lotSizes.append(order["volume"])
    except Exception as e:
        errMsg = f"Task: (Get All Magics - History Deals)  Error retrieving historical deals: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return {
            "minLotSize": 0,
            "maxLotSize": 0,
            "avgLotSize": 0
        }

    try:
        positions = mt5.positions_get()
        for position in positions:
            position = position._asdict()
            if position["magic"] == magic:
                lotSizes.append(position["volume"])
    except Exception as e:
        errMsg = f"Task: (Get All Magics - Positions)  Error retrieving positions: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return {
            "minLotSize": round(min(lotSizes),2),
            "maxLotSize": round(max(lotSizes),2),
            "avgLotSize": round(statistics.mean(lotSizes), 2)
        }

    try:
        return {
                "minLotSize": round(min(lotSizes),2),
                "maxLotSize": round(max(lotSizes),2),
                "avgLotSize": round(statistics.mean(lotSizes), 2)
            }
    except:
        return {
                "minLotSize": 0,
                "maxLotSize": 0,
                "avgLotSize": 0
            }

def getWinRate(magic, account):
    openMt5(account)
    accountData = account
    account = account["login"]
    wins = 0
    losses = 0
    trades = getTradeAmount(magic, accountData)
    try:
        orders = mt5.history_deals_get(0, datetime.now())
        for order in orders:
            order = order._asdict()
            if order["magic"] == magic:
                if order["reason"] == 4:
                    if order["profit"] >= 0:
                        wins += 1
                    elif order["profit"] < 0:
                        losses += 1          
    
    except Exception as e:
        errMsg = f"Task: (Get Win Rate - History Deals)  Error retrieving historical deals: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return {
            "winRate": "0%",
            "wins": 0,
            "losses": 0
        }
        
    try:
        return {
                "winRate": str(round((wins / trades)*100, 0)).replace(".0", "") + "%",
                "wins": wins,
                "losses": losses
            }
    except ZeroDivisionError as e:
        return {
                "winRate": "0%",
                "wins": wins,
                "losses": losses
            }

def getTradeTimes(magic, account):
    openMt5(account)
    account = account["login"]
    try:
        deals = mt5.history_deals_get(0, datetime.now())

        deals = [deal for deal in deals if deal.magic == magic]
        # Dictionary to track open times
        open_trades = {}
        trade_durations = []

        # Process each deal
        for deal in deals:
            ticket = deal.position_id
            if deal.reason == 3:
                # Trade opening
                open_trades[ticket] = deal.time
            else:
                # Trade closing
                if ticket in open_trades:
                    open_time = open_trades.pop(ticket)
                    close_time = deal.time
                    trade_duration = close_time - open_time
                    trade_durations.append(trade_duration)

        if len(trade_durations) == 0:
            return {
                "minTradeTime": 0,
                "maxTradeTime": 0,
                "avgTradeTime": 0
            }
        else:
            # Convert trade durations to timedeltas
            trade_durations = [timedelta(seconds=duration) for duration in trade_durations]
            
            def format_duration(duration):
                total_seconds = int(duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds_remainder = divmod(remainder, 60)
                if len(str(hours)) == 1:
                    hours = f"0{hours}"
                if len(str(minutes)) == 1:
                    minutes = f"0{minutes}"
                if len(str(seconds_remainder)) == 1:
                    seconds_remainder = f"0{seconds_remainder}"
                return f"{hours}:{minutes}:{seconds_remainder}"
            
            # Calculate min, max, and average trade duration
            min_trade_duration = format_duration(min(trade_durations))
            max_trade_duration = format_duration(max(trade_durations))
            avg_trade_duration = format_duration(sum(trade_durations, timedelta()) / len(trade_durations))
            
            
            return {
                "minTradeTime": min_trade_duration,
                "maxTradeTime": max_trade_duration,
                "avgTradeTime": avg_trade_duration
            }
    except Exception as e:
        print(f"Error: {e}")
        
        return {
            "minTradeTime": 0,
            "maxTradeTime": 0,
            "avgTradeTime": 0
        }
        


def getDrawdown(account):
    openMt5(account)
    accountData = account
    account = account["login"]
    try:
        positions = mt5.positions_get()
    except Exception as e:
        errMsg = f"Task: (Get Drawdown)  Error getting positions: {e}"
        print(errMsg)
        database.log_error(errMsg)
        return
    except Exception as e:
        print(e)

    drawdown = {}
    profitList = {}
    currentTime = round(time.time())
    
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
            
        except KeyError as e:
            errMsg = f"Account: {account}  Task: (Get Drawdown)  KeyError: {e} - Error accessing position details"
            print(errMsg)
            database.log_error(errMsg)
        except Exception as e:
            errMsg = f"Account: {account}  Task: (Get Drawdown)  Unexpected error: {e}"
            print(errMsg)
            database.log_error(errMsg)
    
    for magic in profitList:
        try:
            currentDrawdown = round(profitList[magic], 2)
            currentProfit = round(profitList[magic], 2)
            if float(currentDrawdown) > 0:
                currentDrawdown = 0
            
            print(f"Magic: {magic}  Drawdown: {currentDrawdown}  Profit: {currentProfit}")
            database.updateDrawdown(magic, currentDrawdown, currentTime, accountData)
            database.updateEquity(magic, currentProfit, currentTime, accountData)
            
            try:
                setFile = database.getSet(magic, accountData)
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
                historicalProfit = getHistoricalProfit(magic, accountData)
                try:
                    returnOnDrawdown = database.getReturnOnDrawdown(magic, currentDrawdown, account, historicalProfit)
                    database.updateMaxDrawdown(magic, currentDrawdown, account)
                    database.updateReturnOnDrawdown(magic, returnOnDrawdown, account)
                except Exception as e:
                    errMsg = f"Account: {account}  Magic: {magic}  Task: (Get Drawdown)  Error updating max drawdown or return on drawdown: {e}"
                    print(errMsg)
                    database.log_error(errMsg)
            elif currentDrawdown < float(maxD):
                print(f"New Max Drawdown for {magic}")
                historicalProfit = getHistoricalProfit(magic, accountData)
                try:
                    returnOnDrawdown = database.getReturnOnDrawdown(magic, currentDrawdown, account, historicalProfit)
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
    return currentTime

def getDataPath(account_id):
    terminalData = mt5.terminal_info()._asdict()
    return terminalData["data_path"]

def trackData(accountData):
    while True:
        try:
            try:
                openMt5(accountData)
                database.resetErrorLog()
                account = accountData["login"]
            except Exception as e:
                errMsg = f"Account: {account}  Task: (Track Data)  Error opening MT5 terminal: {e}"
                print(errMsg)
                database.log_error(errMsg)
                return

            try:
                onOpen(accountData)
            except Exception as e:
                errMsg = f"Account: {account}  Task: (Track Data)  Error executing onOpen function: {e}"
                print(errMsg)
                database.log_error(errMsg)
                return
            time.sleep(5)
            database.updateAccountStatus(account, "tracking")
            while True:
                try:
                    updateTime = getDrawdown(accountData)
                except Exception as e:
                    errMsg = f"Account: {account}  Task: (Track Data)  Error in getDrawdown: {e}"
                    print(errMsg)
                    database.log_error(errMsg)

                try:
                    updateHistoricalTrades(accountData)
                except Exception as e:
                    errMsg = f"Account: {account}  Task: (Track Data)  Error in updateHistoricalTrades: {e}"
                    print(errMsg)
                    database.log_error(errMsg)

                try:
                    database.updateDaysLive(accountData)
                except Exception as e:
                    errMsg = f"Account: {account}  Task: (Track Data)  Error updating days live: {e}"
                    print(errMsg)
                    database.log_error(errMsg)

                try:
                    for magic in getAllMagics(accountData):
                        trades = getTradeAmount(magic, accountData)
                        database.updateTradeAmount(account, magic, trades)
                except Exception as e:
                    errMsg = f"Account: {account}  Task: (Track Data)  Error updating lot sizes: {e}"
                    print(errMsg)
                    database.log_error(errMsg)

                    
                try:
                    for magic in getAllMagics(accountData):
                        database.updateLotSizes(account, magic, getLotSizes(magic, accountData))
                except Exception as e:
                    errMsg = f"Account: {account}  Task: (Track Data)  Error updating lot sizes: {e}"
                    print(errMsg)
                    database.log_error(errMsg)
                    
                try:
                    for magic in getAllMagics(accountData):
                        database.updateWinRate(account, magic, getWinRate(magic, accountData))
                except Exception as e:
                    errMsg = f"Account: {account}  Task: (Track Data)  Error updating win rate: {e}"
                    print(errMsg)
                    database.log_error(errMsg)
                    
                try:
                    for magic in getAllMagics(accountData):
                        database.updateTradeTimes(account, magic, getTradeTimes(magic, accountData))
                except Exception as e:
                    errMsg = f"Account: {account}  Task: (Track Data)  Error updating trade times: {e}"
                    print(errMsg)
                    database.log_error(errMsg)

                try:
                    if not controller.isTerminalOpen(accountData["terminalFilePath"]):
                        openMt5(accountData)
                except Exception as e:
                    errMsg = f"Account: {account}  Task: (Track Data)  Error updating days live: {e}"
                    print(errMsg)
                    database.log_error(errMsg)
                updateTime = datetime.fromtimestamp(updateTime)
                print(f"Latest Update: {updateTime}")
                time.sleep(10)
        except Exception as e:
            errMsg = f"Account: {account}  Task: (Track Data)  Unexpected error: {e}"
            print(errMsg)
            database.log_error(errMsg)
