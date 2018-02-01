from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import md5
import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = "KeepItSecret"
mysql = MySQLConnector(app,'wall')
@app.route('/')
def index():
    if 'user_id' not in session:
        session['user_id']=[]
    return render_template('wall.html')

@app.route("/registration", methods=["POST"])
def registration():
    flag = True;
    for key in request.form:
        if len(request.form[key]) < 1:
            flag = False;
    if flag == False:
        flash("No empty entries")
    if str.isalpha(str(request.form['first_name'])) == False:
        flash("Your First name cannot contain any numbers")
    if str.isalpha(str(request.form['last_name'])) == False:
        flash("Your Last name cannot contain any numbers")
    if len(request.form['first_name']) < 2:
            flash("Your First name must have at least 2 characters")
    if len(request.form['last_name']) < 2:
            flash("Your Last name must have at least 2 characters")
    if len(request.form['password']) <= 8:
        flash("Password should be more than 8 characters")
    if re.search('\d.*[A-Z]|[A-Z].*\d', request.form['password'])==None:
        flash("Password must have at least 1 uppercase letter and 1 numeric value.")
    if request.form['password'] != request.form['confirm_password']:
        flash("Password and Password Confirmatioin should match")
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!") 
    if not session.has_key("_flashes"):
        password = md5.new(request.form['password']).hexdigest() 
        query = "INSERT INTO users (first_name, last_name, email, password) VALUES (:first_name, :last_name, :email, :password)"
        data = {
             'first_name': request.form['first_name'],
             'last_name': request.form['last_name'],
             'email': request.form['email'],
             'password': password
               }
        mysql.query_db(query, data)
        query = "SELECT id from users where id=last_insert_id()"
        user = mysql.query_db(query)[0]["id"]
        session['user_id'] = user
        print user
        return redirect('/wall_page')
    return redirect('/')

@app.route("/login", methods=["POST"])
def login():
    password = md5.new(request.form['password']).hexdigest()
    query = "SELECT * from users where email = :email"
    data = {
        'email': request.form['email'],
        }
    user = mysql.query_db(query,data)
    if user: #found the user
        if user[0]['password'] == password:
            session['user_id'] = user[0]['id']
            return redirect('/wall_page')
        else: 
            flash ("Password is wrong", "login_error")
    else:
        flash ("Email doesn't exist", "login_error")
    return redirect("/")

@app.route("/wall_page")
def wall_page():
    if 'user_id' in session: #check that the user is registered
        query = "SELECT * from users where id = :id;"
        data = {
            'id': session['user_id'],
            }
        user = mysql.query_db(query, data)
        query_messages = "select messages.id as 'mes_id', users.id as 'user_id', concat(users.first_name, ' ', users.last_name) as 'name', messages.created_at as 'date', messages.message as 'mes' from users join messages on messages.users_id = users.id order by date desc"
        messages = mysql.query_db(query_messages)
        query_comments = "select messages.id as 'mes_id', concat(users.first_name, ' ', users.last_name) as 'name',comments.created_at as 'date',comments.comment as 'com' from users join comments on comments.users_id = users.id join messages on comments.messages_id = messages.id"
        comments = mysql.query_db(query_comments)
        return render_template('wall_page.html', user_name = user[0]['first_name'], Messages = messages, Comments = comments)

@app.route("/post_message", methods = ["post"])
def post_message():
    query = "INSERT INTO messages (message, created_at, updated_at, users_id) VALUES (:message, now(), now(), :users_id )"
    data = {
            'message': request.form['message'],
            'users_id': session['user_id'],
            }
    mysql.query_db(query, data)
    return redirect("/wall_page")

@app.route("/delete_message/<mes_id>")
def delete_message(mes_id):
    query_delete_comments = "delete from comments where messages_id = :messages_id"
    data = {'messages_id': mes_id}
    mysql.query_db(query_delete_comments, data)
    query_delete_messages = "delete from messages where id = :id"
    data = {'id': mes_id}
    mysql.query_db(query_delete_messages, data)
    return redirect("/wall_page")

@app.route("/post_comment", methods = ["post"])
def post_comment():
    query = "INSERT INTO comments (comment, created_at, updated_at, users_id, messages_id) VALUES (:comment, now(), now(), :users_id, :messages_id)"
    data = {
            'comment': request.form['comment'],
            'users_id': session['user_id'],
            'messages_id': request.form['mes_id'],
            }
    mysql.query_db(query, data)
    return redirect("/wall_page")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(debug=True)



