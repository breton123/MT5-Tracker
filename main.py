from flask import Flask, render_template, jsonify
import MetaTrader5 as mt5  # Ensure you have the MetaTrader5 package installed
import threading, tracker, json

app = Flask(__name__)

# Initialize connection to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

@app.route('/<account_id>')
def index(account_id):
    return render_template('account.html', sets=tracker.getFrontendSets(account_id), drawdownData = tracker.getDrawdownGraphData(account_id), equityData = tracker.getEquityGraphData(account_id))

@app.route('/')
def data():
    print(tracker.getAccounts())
    return render_template('index.html', accounts=tracker.getAccounts())

with open(f"config.json", "r") as file:
    config = json.load(file)

if __name__ == '__main__':
    for terminal in config["terminalFolders"]:
        trackerThread = threading.Thread(target=tracker.trackData, args=(terminal,)).start()
    app.run(debug=True)
