from flask import Flask, render_template, request, redirect, session, flash
import re, datetime
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key='alo'
bcrypt = Bcrypt(app)



@app.route("/")
def index():
    session['count_send'] = 0
    return render_template("index.html")


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')


@app.route('/process', methods=['POST'])
def add_info():
    is_valid = True
    if not EMAIL_REGEX.match(request.form['email']):  # test whether a field matches the pattern
        flash("Re-enter email", 'email_error')
        is_valid = False
    email=request.form['email']
    query = "SELECT * FROM friends WHERE email = %(email)s;"
    data = {"email": request.form["email"]}
    mysql = connectToMySQL('Private_wall')
    users_email=mysql.query_db(query, data)
    count=0
    for user_email in users_email:
        if user_email['email']==email:
            count+=1
    if count==0:
        pass
    if count!=0:
        flash("email exist")
        is_valid = False

    if len(request.form['first_name']) < 1:
        flash("re-enter first name",  'first')
        is_valid = False
    if len(request.form['last_name']) < 1:
        flash("re-enter last name",'last')
        is_valid = False
    if  len(request.form['password']) < 8:
        flash("password need 8 character", 'password1')
        is_valid = False
    if (request.form['password'])!= (request.form['password2']):
        flash("Password not match", 'password2')
        is_valid = False
    if not is_valid:
        return redirect("/")
    else:

        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        data = {
            'fn': request.form['first_name'],
            'ln': request.form['last_name'],
            'email': request.form['email'],
            'pw_hash': pw_hash
        }
        query='INSERT INTO friends(first_name, last_name, email, pw_hash) VALUES (%(fn)s, %(ln)s, %(email)s, %(pw_hash)s )'
        mysql=connectToMySQL('Private_wall')
        user_id = mysql.query_db(query, data)
        flash('success add user')
        return redirect(f'/success/{user_id}')


@app.route('/login', methods=['POST'])
def logged_in():
    mysql = connectToMySQL('Private_wall')
    query = "SELECT * FROM friends WHERE email = %(email)s;"
    data = {"email": request.form["email_log"]}
    result = mysql.query_db(query, data)
    if len(result) > 0:
        if bcrypt.check_password_hash(result[0]['pw_hash'], request.form['password_log']):
            session['userid'] = result[0]['id']
            user_id = session['userid']
            return redirect(f'/success/{user_id}')
    flash("You could not be logged in")
    return redirect("/")

@app.route('/success/<user_id>')
def success_log_in(user_id):
    query = (f'SELECT first_name from friends where id ={user_id}')
    mysql = connectToMySQL('Private_wall')
    user = mysql.query_db(query)
    user = user[0]['first_name']
    db = connectToMySQL('Private_wall')
    query1 = (f'SELECT first_name,id from friends')
    all_friends = db.query_db(query1)
    query2= (f'select * from (select created, friend_receive_id, message,message_id, friend_send_id, friends.first_name as send_name from (select messages.created_at as created, friends.id as friend_receive_id, '
             f'friends.first_name, messages.message, messages.friend_send_id,  messages.id as message_id  from friends left join messages on '
             f'friends.id=messages.friend_receive_id) as t join friends on '
             f'friends.id = friend_send_id) as p where friend_receive_id = {user_id}')
    mysql = connectToMySQL('Private_wall')
    messages = mysql.query_db(query2)
    count=0

    for message in messages:
        count+=1



    return render_template('index_wall.html',user=user, all_friends= all_friends, messages=messages, count= count)


@app.route('/send_message/<friend_id>', methods=["POST"])
def send(friend_id):
    data={
        'message':request.form['message'],
        'friend_receive_id':int(friend_id),
        'friend_send_id' : session['userid']
    }
    query = 'INSERT INTO messages (friend_receive_id, friend_send_id, message, created_at, updated_at) VALUES ( %(friend_receive_id)s, %(friend_send_id)s, %(message)s, NOW(), NOW())'
    mysql = connectToMySQL('Private_wall')
    mysql.query_db(query, data)
    user_id=session['userid']
    session['count_send']+=1
    return redirect(f'/success/{user_id}')

@app.route('/delete/message/<message_id>')
def delete(message_id):

    query = (f'DELETE FROM messages where id = {message_id}')
    mysql = connectToMySQL('Private_wall')
    mysql.query_db(query)
    user_id = session['userid']
    return redirect(f'/success/{user_id}')

@app.route('/logout')
def logout():
    flash('You have been log out')
    return redirect('/')



if __name__ == "__main__":
    app.run(debug=True)


