#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

# XXX: The Database URI should be in the format of:
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "wh2500"
DB_PASSWORD = "9111"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://" + DB_USER + ":" + DB_PASSWORD + "@" + DB_SERVER + "/proj1part2"

#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)

# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request

    The variable g is globally accessible
    """
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback;
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

    See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
    """
    data = []
    context = dict(data=data)
    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("index.html", **context)


#
# This is an example of a different path.  You can see it at
#
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#

# Example of adding new data to the database
# @app.route('/login')
# def login():
#    abort(401)
#    this_is_never_executed()

@app.route('/members', methods=["GET"])
def get_members():
    cursor = g.conn.execute("SELECT * FROM Members")
    data = []
    for result in cursor:
        info = {'member_id': result['member_id'], 'firstname': result['firstname'], 'lastname': result['lastname']}
        data.append(info)
    cursor.close()
    count = {}
    count['size'] = len(data)

    cursor = g.conn.execute("SELECT Count(*) as count FROM Events")
    result = cursor.fetchone()
    eventcount = {'count': result['count']}
    cursor.close()

    cursor = g.conn.execute("SELECT Count(*) as count FROM Expenses")
    result = cursor.fetchone()
    expensecount = {'count': result['count']}
    cursor.close()

    context = dict(data=data, count=count, event_count=eventcount, expense_count=expensecount)
    return render_template("member.html", **context)


@app.route('/individual', methods=['GET'])
def get_individual():
    member_id = int(request.args.get('member_id'))

    data = {}
    sql_query = 'SELECT * FROM Members WHERE member_id =%s'
    cursor = g.conn.execute(sql_query, (member_id,))

    if cursor.rowcount == 0:
        data = {'exists': False, 'member_id': member_id}
        context = dict(data=data)
        return render_template("individual.html", **context)

    result = cursor.fetchone()
    cursor.close()
    data = {'exists': True, 'member_id': result['member_id'], 'firstname': result['firstname'],
            'lastname': result['lastname'], 'email': result['email'], 'position': result['position'],
            'tshirt_size': result['tshirt_size'], 'phone_number': result['phone_number']}

    major_id = result['major_id']
    zipcode = result['zipcode']

    sql_query = 'SELECT * FROM Majors WHERE major_id =%s'
    cursor = g.conn.execute(sql_query, (major_id,))

    result = cursor.fetchone()
    cursor.close()
    data['major_id'] = result['major_id']
    data['name'] = result['name']
    data['department'] = result['department']
    data['college'] = result['college']

    sql_query = 'SELECT * FROM Zipcodes WHERE zipcode =%s'
    cursor = g.conn.execute(sql_query, (zipcode,))
    result = cursor.fetchone()
    cursor.close()
    data['zipcode'] = zipcode
    data['type'] = result['type']
    data['city'] = result['city']
    data['county'] = result['county']
    data['state'] = result['state']
    data['short_state'] = result['short_state']

    context = dict(data=data)
    return render_template("individual.html", **context)


@app.route('/budgets', methods=['GET'])
def get_budgets():
    cursor = g.conn.execute("SELECT * FROM Budgets")
    data = []
    for result in cursor:
        info = {"budget_id": result["budget_id"], "category": result["category"], "remaining": result["remaining"],
                "amount": result["amount"], "event_status": result["event_status"]}
        data.append(info)
    cursor.close()
    count = {}
    count['size'] = len(data)
    context = dict(data=data, count=count)
    return render_template("budgets.html", **context)


@app.route('/individual_budget', methods=["GET"])
def get_individual_budget():
    budget_id = int(request.args.get("budget_id"))

    data = {}
    sql_query = "SELECT * FROM Budgets WHERE budget_id=%s"
    cursor = g.conn.execute(sql_query, (budget_id,))

    if cursor.rowcount == 0:
        data = {"exists": False, "budget_id": budget_id}
        context = dict(data=data)
        return render_template("individual_budget.html", **context)

    result = cursor.fetchone()
    cursor.close()
    data = {"exists": True, "budget_id": result["budget_id"], "category": result["category"], "spent": result["spent"],
            "remaining": result["remaining"],
            "amount": result["amount"], "event_status": result["event_status"]}

    sql_query = "SELECT e.event_id, e.name, e.date, e.type, e.notes, e.location, e.status FROM Events AS e, Has AS h, Budgets AS b WHERE e.event_id = h.event_id AND h.budget_id = b.budget_id AND b.budget_id=%s"
    cursor = g.conn.execute(sql_query, (budget_id,))
    events = []
    for result in cursor:
        info = {"event_id": result["event_id"], "name": result["name"], "date": result["date"], "type": result["type"],
                "notes": result["notes"], "location": result["location"], "status": result["status"]}
        events.append(info)
    cursor.close()
    event_count = len(events)

    context = dict(data=data, events=events, event_count=event_count)

    return render_template("individual_budget.html", **context)


@app.route('/expenses', methods=["GET"])
def get_expenses():
    cursor = g.conn.execute("SELECT * FROM Expenses")
    data = []
    for result in cursor:
        info = {"expense_id": result["expense_id"], "description": result["description"], "date": result["date"],
                "cost": result["cost"]}
        data.append(info)
    cursor.close()

    count = {}
    count['size'] = len(data)
    context = dict(data=data, count=count)

    return render_template("expenses.html", **context)


@app.route('/individual_expense', methods=["GET"])
def get_individual_expense():
    expense_id = int(request.args.get("expense_id"))

    data = {}
    sql_query = "SELECT * FROM Expenses WHERE expense_id=%s"
    cursor = g.conn.execute(sql_query, (expense_id,))

    if cursor.rowcount == 0:
        data = {"exists": False, "expense_id": expense_id}
        context = dict(data=data)
        return render_template("individual_expense.html", **context)

    result = cursor.fetchone()
    cursor.close()

    data = {"exists": True, "expense_id": result["expense_id"], "description": result["description"],
            "date": result["date"], "cost": result["cost"]}

    sql_query = "SELECT b.budget_id, b.category, b.remaining, b.amount FROM Expenses AS e, Budgets AS b WHERE e.budget_id = b.budget_id AND e.expense_id=%s"
    cursor = g.conn.execute(sql_query, (expense_id,))
    result = cursor.fetchone()
    cursor.close()

    budget = {"budget_id": result["budget_id"], "category": result["category"], "remaining": result["remaining"],
              "amount": result["amount"]}

    sql_query = "SELECT m.member_id, m.firstname, m.lastname FROM Members AS m, Incurs AS i WHERE m.member_id = i.member_id AND i.expense_id=%s"
    cursor = g.conn.execute(sql_query, (expense_id,))
    result = cursor.fetchone()
    cursor.close()

    member = {"member_id": result["member_id"], "firstname": result["firstname"], "lastname": result["lastname"]}

    context = dict(data=data, budget=budget, member=member)
    return render_template("individual_expense.html", **context)


@app.route('/zipcodes', methods=["GET"])
def get_zipcodes():
    cursor = g.conn.execute("SELECT * FROM Zipcodes ORDER BY zipcode ASC")
    data = []
    for result in cursor:
        info = {'zipcode': result['zipcode'], 'type': result['type'], 'city': result['city'],
                'county': result['county'], 'state': result['state'], 'short_state': result['short_state']}
        data.append(info)
    cursor.close()
    context = dict(data=data)
    return render_template("zipcodes.html", **context)


@app.route('/majors', methods=["GET"])
def get_majors():
    cursor = g.conn.execute("SELECT * FROM Majors ORDER BY major_id ASC")
    data = []
    for result in cursor:
        info = {'major_id': result['major_id'], 'name': result['name'], 'department': result['department'],
                'college': result['college']}
        data.append(info)
    cursor.close()
    context = dict(data=data)
    return render_template("majors.html", **context)


# Example of adding new data to the database
@app.route('/add_member', methods=['POST'])
def add_member():
    firstname = request.form['first_name']
    lastname = request.form['last_name']
    email = request.form['email']
    position = request.form['position']
    tshirt_size = request.form['tshirt_size']
    phone_number = request.form['phone_number']
    major_name = request.form['major_name']
    department = request.form['department']
    college = request.form['college']
    zipcode = request.form['zipcode']
    address_type = request.form['address_type']
    city = request.form['city']
    county = request.form['county']
    state = request.form['state']
    short_state = request.form['short_state']

    sql_query = 'SELECT COUNT(*) AS count FROM Members'
    cursor = g.conn.execute(sql_query)
    result = int(cursor.fetchone()['count'])
    member_id = result + 1

    sql_query = 'SELECT * FROM Majors WHERE name=%s AND department=%s AND college=%s'
    cursor = g.conn.execute(sql_query, (major_name, department, college,))

    major_id = 0
    if cursor.rowcount != 0:
        major_id = int(cursor.fetchone()['major_id'])
        cursor.close()
    else:
        sql_query = 'SELECT COUNT(*) AS count FROM Majors'
        cursor = g.conn.execute(sql_query)
        major_id = int(cursor.fetchone()['count']) + 1
        cursor.close()

        sql_query = 'INSERT INTO Majors(major_id, name, department, college) VALUES (%s, %s, %s, %s)'
        cursor = g.conn.execute(sql_query, (major_id, major_name, department, college,))
        cursor.close()

    sql_query = 'SELECT * FROM Zipcodes WHERE zipcode=%s'
    cursor = g.conn.execute(sql_query, (zipcode,))

    if cursor.rowcount != 0:
        cursor.close()
    else:
        cursor.close()
        sql_query = 'INSERT INTO Zipcodes(zipcode, type, city, county, state, short_state) VALUES (%s, %s, %s, %s, %s, %s)'
        cursor = g.conn.execute(sql_query, (zipcode, address_type, city, county, state, short_state,))
        cursor.close()

    sql_query = 'INSERT INTO Members(member_id, major_id, zipcode, firstname, lastname, email, position, tshirt_size, phone_number) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
    cursor = g.conn.execute(sql_query, (
    member_id, major_id, zipcode, firstname, lastname, email, position, tshirt_size, phone_number,))
    cursor.close()
    return redirect('/members')


@app.route('/members_list', methods=["GET"])
def get_members_lists():
    major_name = request.args.get('major_name')
    limit = request.args.get('page_limit')
    sql_query = 'SELECT * FROM Members INNER JOIN Majors ON Members.major_id = Majors.major_id AND Majors.name =%s LIMIT %s'
    cursor = g.conn.execute(sql_query, (major_name, limit,))
    data2 = {}
    data2['exists'] = True
    data2['major'] = major_name

    if cursor.rowcount == 0:
        cursor.close()
        data2['exists'] = False
        context = dict(data2=data2)
        return render_template("members_list.html", **context)
    else:
        data = []
        for result in cursor:
            info = {}
            info['member_id'] = result['member_id']
            info['first_name'] = result['firstname']
            info['last_name'] = result['lastname']
            info['email'] = result['email']
            info['position'] = result['position']
            info['tshirt_size'] = result['tshirt_size']
            info['phone_number'] = result['phone_number']
            data.append(info)
        cursor.close()
        context = dict(data=data, data2=data2)
        return render_template("members_list.html", **context)


@app.route('/members_list_zipcode', methods=["GET"])
def get_members_lists_zipcodes():
    state = request.args.get('state')
    limit = request.args.get('page_limit')
    sql_query = 'SELECT * FROM Members INNER JOIN Zipcodes ON Members.zipcode = Zipcodes.zipcode AND Zipcodes.state =%s LIMIT %s'
    cursor = g.conn.execute(sql_query, (state, limit,))
    data2 = {}
    data2['exists'] = True
    data2['state'] = state

    if cursor.rowcount == 0:
        cursor.close()
        data2['exists'] = False
        context = dict(data2=data2)
        return render_template("member_list_zipcode.html", **context)
    else:
        data = []
        for result in cursor:
            info = {}
            info['member_id'] = result['member_id']
            info['first_name'] = result['firstname']
            info['last_name'] = result['lastname']
            info['email'] = result['email']
            info['position'] = result['position']
            info['tshirt_size'] = result['tshirt_size']
            info['phone_number'] = result['phone_number']
            data.append(info)
        cursor.close()
        context = dict(data=data, data2=data2)
        return render_template("member_list_zipcode.html", **context)


@app.route('/fees', methods=["GET"])
def get_fees():
    cursor = g.conn.execute("SELECT * FROM Fees")
    data = []
    for result in cursor:
        info = {'fee_id': result['fee_id'], 'date': result['date'], 'amount': result['amount'],
                'source': result['source'], 'notes': result['notes']}
        data.append(info)
    cursor.close()
    count = {}
    count['size'] = len(data)
    context = dict(data=data, count=count)
    return render_template("fees.html", **context)


@app.route('/fee_individual', methods=["GET"])
def get_individual2():
    fee_id = request.args.get('fee_id')
    sql_query = 'SELECT * FROM Pays INNER JOIN Fees ON Pays.fee_id = Fees.fee_id INNER JOIN Members ON Pays.member_id = Members.member_id WHERE Pays.fee_id =%s'
    cursor = g.conn.execute(sql_query, (fee_id,))

    data2 = {'exists': True, 'fee_id': fee_id}

    if cursor.rowcount == 0:
        cursor.close()
        data2['exists'] = False
        context = dict(data2=data2)
        return render_template("fee_individual.html", **context)
    else:
        result = cursor.fetchone()

        info = {}
        info['member_id'] = result['member_id']
        info['first_name'] = result['firstname']
        info['last_name'] = result['lastname']
        info['email'] = result['email']
        info['position'] = result['position']
        info['tshirt_size'] = result['tshirt_size']
        info['phone_number'] = result['phone_number']

        cursor.close()
        context = dict(data=info, data2=data2)
        return render_template("fee_individual.html", **context)


@app.route('/fees_by_member', methods=["GET"])
def get_fees_by_member():
    member_id_2 = request.args.get('member_id_2')
    sql_query = 'SELECT Fees.fee_id as fee_id, Fees.date as date, Fees.amount as amount, Fees.source as source, Fees.notes as notes FROM Pays INNER JOIN Fees ON Pays.fee_id = Fees.fee_id INNER JOIN Members ON Pays.member_id = Members.member_id WHERE Members.member_id =%s'
    cursor = g.conn.execute(sql_query, (member_id_2,))

    data2 = {'exists': True, 'member_id': member_id_2}

    if cursor.rowcount == 0:
        data2['exists'] = False
        context = dict(data2=data2)
        return render_template("fee_by_member.html", **context)

    else:
        data = []
        for result in cursor:
            info = {'fee_id': result['fee_id'], 'date': result['date'], 'amount': result['amount'],
                    'source': result['source'], 'notes': result['notes']}
            data.append(info)
        cursor.close()
        count = {}
        count['size'] = len(data)
        context = dict(data=data, count=count, data2=data2)
        return render_template("fee_by_member.html", **context)


# Example of adding new data to the database
@app.route('/add_fee', methods=['POST'])
def add_fee():
    member_id_3 = request.form['member_id_3']
    amount = request.form['amount']
    date = request.form['date']

    fee_id = 0

    sql_query = 'SELECT COUNT(*) AS count FROM Fees'
    cursor = g.conn.execute(sql_query)
    result = cursor.fetchone()
    cursor.close()
    fee_id = int(result['count']) + 1

    sql_query = 'INSERT INTO Fees(fee_id, date, amount, source, notes) VALUES(%s, %s,%s,%s,%s)'
    cursor = g.conn.execute(sql_query, (fee_id, date, amount, 'DUES', 'Member Dues'))
    cursor.close()

    sql_query = 'INSERT INTO Pays(member_id, fee_id) VALUES(%s, %s)'
    cursor = g.conn.execute(sql_query, (member_id_3, fee_id))
    cursor.close()

    return redirect('/members')


@app.route('/events', methods=['GET'])
def get_events():
    sql_query = 'SELECT * FROM Events ORDER BY event_id ASC'
    cursor = g.conn.execute(sql_query)
    data = []
    for result in cursor:
        info = {'event_id': result['event_id'], 'name': result['name'], 'date': result['date'], 'type': result['type'],
                'notes': result['notes'], 'location': result['location'], 'status': result['status']}
        data.append(info)
    cursor.close()
    count = {}
    count['size'] = len(data)
    context = dict(data=data, count=count)
    return render_template("events.html", **context)


@app.route('/individual_event', methods=['GET'])
def get_individual_event():
    event_id = request.args.get('event_id')
    data2 = {'event_id': event_id}
    sql_query = 'SELECT * FROM Events WHERE event_id=%s'
    cursor = g.conn.execute(sql_query, (event_id,))
    result = cursor.fetchone()
    cursor.close()
    info = {'event_id': result['event_id'], 'name': result['name'], 'date': result['date'], 'type': result['type'],
            'notes': result['notes'], 'location': result['location'], 'status': result['status']}
    context = dict(data=info, data2=data2)
    return render_template("individual_event.html", **context)


# Example of adding new data to the database
@app.route('/add_event', methods=['POST'])
def add_event():
    event_name = request.form['event_name']
    event_date = request.form['event_date']
    event_type = request.form['event_type']
    event_notes = request.form['event_notes']
    event_location = request.form['event_location']
    event_status = 'open'

    event_id = 0

    sql_query = 'SELECT COUNT(*) AS count FROM Events'
    cursor = g.conn.execute(sql_query)
    result = cursor.fetchone()
    cursor.close()
    event_id = int(result['count']) + 1

    sql_query = 'INSERT INTO Events(event_id, name, date, type, notes, location, status) VALUES(%s, %s,%s,%s,%s, %s, %s)'
    cursor = g.conn.execute(sql_query,
                            (event_id, event_name, event_date, event_type, event_notes, event_location, event_status))
    cursor.close()

    return redirect('/events')


# Example of adding new data to the database
@app.route('/budget_by_event', methods=['GET'])
def get_budget_by_event():
    event_id = request.args.get('event_id_2')
    sql_query = 'SELECT * FROM Has INNER JOIN Budgets ON Has.budget_id = Budgets.budget_id WHERE Has.event_id =%s'
    cursor = g.conn.execute(sql_query, (event_id,))

    data = []
    data2 = {'exists': True}

    if cursor.rowcount == 0:
        cursor.close()
        data2['exists'] = False
        data2['event_id'] = event_id
        context = dict(data2=data2)
        return render_template("budget_by_event.html", **context)
    else:
        for result in cursor:
            info = {'budget_id': result['budget_id'], 'category': result['category'], 'spent': result['spent'],
                    'remaining': result['remaining'], 'amount': result['amount'],
                    'event_status': result['event_status']}
            data.append(info)
        cursor.close()
        context = dict(data=data, data2=data2)
        return render_template("budget_by_event.html", **context)


@app.route('/events_by_member', methods=['GET'])
def get_events_by_member():
    member_id = request.args.get('member_id_3')
    sql_query = 'SELECT * FROM Events INNER JOIN Attends ON Events.event_id = Attends.event_id INNER JOIN Members ON Attends.member_id = Members.member_id WHERE Members.member_id=%s'
    cursor = g.conn.execute(sql_query, (member_id,))

    data = []
    data2 = {'exists': True, 'member_id': member_id}

    if cursor.rowcount == 0:
        cursor.close()
        data2['exists'] = False
        context = dict(data2=data2)
        return render_template("events_by_member.html", **context)
    else:
        for result in cursor:
            info = {'event_id': result['event_id'], 'date': result['date'], 'type': result['type'],
                    'notes': result['notes'], 'location': result['location'], 'status': result['status']}
            data.append(info)
        cursor.close()
        context = dict(data2=data2, data=data)
        return render_template("events_by_member.html", **context)


@app.route('/expenses_by_member', methods=['GET'])
def get_expenses_by_member():
    member_id = request.args.get('member_id_4')
    sql_query = 'SELECT Expenses.expense_id AS expense_id, Expenses.description AS description, Expenses.date AS date, Expenses.cost AS cost FROM Incurs INNER JOIN Members ON Incurs.member_id = Members.member_id INNER JOIN Expenses ON Incurs.expense_id = Expenses.expense_id WHERE Members.member_id =%s'
    cursor = g.conn.execute(sql_query, (member_id,))

    data = []
    data2 = {'exists': True, 'member_id': member_id}

    if cursor.rowcount == 0:
        cursor.close()
        data2['exists'] = False
        context = dict(data2=data2)
        return render_template("expenses_by_member.html", **context)
    else:
        data2['sum'] = 0.0
        for result in cursor:
            info = {'expense_id': result['expense_id'], 'description': result['description'], 'date': result['date'],
                    'cost': result['cost']}
            data2['sum'] += float(info['cost'])
            data.append(info)
        cursor.close()
        context = dict(data2=data2, data=data)
        return render_template("expenses_by_member.html", **context)


@app.route('/budget_by_fee', methods=['GET'])
def get_budgets_by_fees():
    fee_id_2 = request.args.get('fee_id_2')
    sql_query = 'SELECT Budgets.budget_id AS budget_id, Budgets.category AS category, Budgets.spent AS spent, Budgets.remaining AS remaining, Budgets.amount AS amount, Budgets.event_status AS event_status FROM Supports INNER JOIN Budgets ON Budgets.budget_id = Supports.budget_id INNER JOIN Fees ON Supports.fee_id = Fees.fee_id WHERE Fees.fee_id =%s'
    cursor = g.conn.execute(sql_query, (fee_id_2,))

    data2 = {'exists': True, 'fee_id': fee_id_2}

    if cursor.rowcount == 0:
        cursor.close()
        data2['exists'] = False
        context = dict(data2=data2)
        return render_template("budget_by_fee.html", **context)
    else:
        result = cursor.fetchone()
        info = {'budget_id': result['budget_id'], 'category': result['category'], 'spent': result['spent'],
                'remaining': result['remaining'], 'amount': result['amount'], 'event_status': result['event_status']}
        cursor.close()
        context = dict(data2=data2, data=info)
        return render_template("budget_by_fee.html", **context)




@app.route('/add_member_attend_events', methods=['POST'])
def get_add_member_attend_events():

    member_id = request.form['member_id_5']
    event_id = request.form['event_id_5']

    sql_query = 'SELECT * FROM Attends WHERE member_id =%s AND event_id =%s'
    cursor = g.conn.execute(sql_query, (member_id, event_id, ))

    data2 = {'status': False}
    if cursor.rowcount != 0:
        cursor.close()
    else:
        cursor.close()
        sql_query = 'INSERT INTO Attends(member_id, event_id) VALUES (%s, %s)'
        cursor = g.conn.execute(sql_query, (member_id, event_id, ))
        data2['status'] = True
        cursor.close()
    context = dict(data2=data2)
    return render_template("statuspage.html", **context)


@app.route('/add_member_incur_expense', methods=['POST'])
def get_add_member_incur_expense():

    member_id = request.form['member_id_6']
    expense_id = request.form['expense_id']

    sql_query = 'SELECT * FROM Incurs WHERE member_id =%s AND expense_id =%s'
    cursor = g.conn.execute(sql_query, (member_id, expense_id,))

    data2 = {'status': False}
    if cursor.rowcount != 0:
        cursor.close()
    else:
        cursor.close()
        sql_query = 'INSERT INTO Incurs(member_id, expense_id) VALUES (%s, %s)'
        cursor = g.conn.execute(sql_query, (member_id, expense_id,))
        data2['status'] = True
        cursor.close()
    context = dict(data2=data2)
    return render_template("statuspage.html", **context)



if __name__ == "__main__":
    import click


    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using

            python server.py

        Show the help text using

            python server.py --help

        """

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


    run()