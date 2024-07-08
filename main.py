from flask import Flask, redirect, render_template, jsonify, request, url_for
import MetaTrader5 as mt5  # Ensure you have the MetaTrader5 package installed
import threading, tracker, json, database, os, loader

app = Flask(__name__)
trackingAccounts = []

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'set'}

user_profile = os.environ['USERPROFILE']
configFile = os.path.join(user_profile, 'AppData', 'Local', 'Mt5TrackerDatabase', 'config.json')
    
@app.route('/<account_id>')
def account(account_id):
    sets = database.getFrontendSets(account_id)
    slaveAccounts = []
    accounts = database.getAccounts()
    for account in accounts:
        if account["type"] == "slave":
            slaveAccounts.append(account["login"])
    print(account_id)
    if len(sets) != 0:
        return render_template('account.html', sets=sets, drawdownData = database.getDrawdownGraphData(account_id), equityData = database.getEquityGraphData(account_id), filterData = database.getFilterData(account_id), accounts=slaveAccounts)
    else:
        return render_template('empty_account.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/set_loader')
def set_loader():
    accounts = database.getAccounts()
    accountIDs = []
    for account in accounts:
        accountIDs.append(account["login"])
    return render_template('uploadSets.html', sets=[], accounts=accountIDs)

def save_config(config):
    with open(configFile, 'w') as f:
        json.dump(config, f)

def load_config():
    if os.path.exists(configFile):
        with open(configFile, 'r') as f:
            return json.load(f)
    return {"powName": "", "powAPIKey": ""}

@app.route('/copy-to-account', methods=['POST'])
def copy_to_account():
    data = request.json
    account = data.get('account')
    magic_numbers = data.get('magicNumbers')
    print(magic_numbers)
    # Process the magic numbers and copy them to the selected account
    # Your logic here

    return jsonify(success=True, message="Magic numbers copied successfully")

@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        powName = request.form['powName']
        powAPIKey = request.form['powAPIKey']
        config = {"powName": powName, "powAPIKey": powAPIKey}
        save_config(config)
        return redirect(url_for('config'))

    config = load_config()
    return render_template('config.html', config=config)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return redirect(request.url)

    files = request.files.getlist('files[]')
    account = request.form["account"]
    #makeNew = bool(request.form["new"])

    user_profile = os.environ['USERPROFILE']
    setsFolder = os.path.join(user_profile, 'AppData', 'Local', 'Mt5TrackerDatabase', 'Sets')

    if not os.path.exists(setsFolder):
        os.makedirs(setsFolder)
        
    setsAccountFolder = os.path.join(user_profile, 'AppData', 'Local', 'Mt5TrackerDatabase', 'Sets', account)

    if not os.path.exists(setsAccountFolder):
        os.makedirs(setsAccountFolder)

    for file in files:
        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            file.save(os.path.join(setsAccountFolder, file.filename))

    loader.loadSets(account)
    
    return redirect(url_for('index'))

@app.route('/')
def index():
    accountManager()
    print(database.getAccounts())
    return render_template('index.html', accounts=database.getAccounts())

@app.route('/error_log')
def error_log():
    print(database.getErrorLog())
    return render_template('error_log.html', errors=database.getErrorLog())

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        if request.form['type'] == "master":
            status = "initializing"
        elif request.form['type'] == "slave":
            status = "waiting for master"
        else:
            status = "error"
        account_data = {
            'name': request.form['name'],
            'login': request.form['login'],
            'password': request.form['password'],
            'server': request.form['server'],
            'deposit': request.form['deposit'],
            'terminalFilePath': request.form['terminalFilePath'],
            'type': request.form['type'],
            'status': "initializing"
        }
        database.createAccount(account_data)
        return redirect(url_for('index'))
    return render_template('createAccount.html')

def accountManager():
    global trackingAccounts
    for account in database.getAccounts():
        if account["login"] not in trackingAccounts:
            if account["type"] == "master":
                trackerThread = threading.Thread(target=tracker.trackData, args=(account,)).start()
                trackingAccounts.append(account["login"])
            elif account["type"] == "slave":
                trackerThread = threading.Thread(target=tracker.trackData, args=(account,)).start()
                trackingAccounts.append(account["login"])


if __name__ == '__main__':
    accountManager()
    app.run(debug=True)
