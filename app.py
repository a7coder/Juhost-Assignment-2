from flask import Flask, render_template, request, redirect, session,make_response
import mysql.connector
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key ='InternA7coder'
# MySQL connection configuration
mysql = mysql.connector.connect(
    host="sql12.freemysqlhosting.net",
    user="sql12629011",
    password="RzlzHmeUy8",
    database="sql12629011",
    port=3306
   
)

# cursor = mysql.cursor()
# cursor.execute("Drop table users ,Orderinfo,orderitem")

def create_dummy_user():
    cursor = mysql.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id VARCHAR(255) Primary Key, password VARCHAR(255),mobile varchar(10), name varchar(50))")

    cursor.execute("CREATE TABLE IF NOT EXISTS Orderitem (order_id INT AUTO_INCREMENT PRIMARY KEY, order_date DATE, item VARCHAR(255), count VARCHAR(10), weight VARCHAR(50), requests VARCHAR(50))")

    cursor.execute("CREATE TABLE IF NOT EXISTS Orderinfo (S_No INT AUTO_INCREMENT PRIMARY KEY, order_id INT, user_id VARCHAR(255), FOREIGN KEY (order_id) REFERENCES Orderitem(order_id), FOREIGN KEY (user_id) REFERENCES users(id))")

    cursor.execute("INSERT INTO users VALUES(%s,%s,%s,%s)",('1234', 'password','7777777777','Ram'))
    cursor.execute("INSERT INTO users VALUES(%s,%s,%s,%s)",('1111', 'admin','8777777777','Admin'))
    cursor.execute("INSERT INTO users VALUES(%s,%s,%s,%s)",('7452', 'password','9777777777','Shyam'))
    mysql.commit()
    cursor.close()

# create_dummy_user()


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    id = request.form['id']
    password = request.form['password']
    
    cursor = mysql.cursor()
    cursor.execute("SELECT * FROM users WHERE id=%s AND password=%s", (id, password))
    user = cursor.fetchone()
    cursor.close()
    
    if user:
        session['user_id'] = id
        print('Success Login')
        return redirect('/order-form')
    else:
        return 'Invalid credentials!'


@app.route('/chpass', methods=['GET', 'POST'])
def change_password():

    if request.method == 'POST':
        mobile = request.form['mobile']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        print(mobile)
        # Check if new password and confirm password match
        if new_password == confirm_password:
            cursor = mysql.cursor()
            cursor.execute("SELECT * FROM users WHERE mobile=%s",(mobile,))
            user = cursor.fetchone()
            # print('User is ',user)
            if user:
                stored_mobile = user[2]  # Assuming mobile number is stored in the third column

                if mobile == stored_mobile:
                    # Update the password in the database
                    # hashed_password = generate_password_hash(new_password)

                    cursor.execute("UPDATE users SET password=%s WHERE mobile=%s", (new_password, mobile))
                    mysql.commit()

                    return redirect('/')
                else:
                    return 'Please enter the correct mobile number!'
            else:
                return 'User not found!'
        else:
            return 'New password and confirm password do not match!'
    else:
        return render_template('changePass.html')


@app.route('/order-form', methods=['GET', 'POST'])
def order_form():
    if 'user_id' not in session:
        # print('User not Log in')
        return redirect('/')
    
    user_id = session['user_id']
    cursor = mysql.cursor()
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    # print('USer is ',user)
    if user:
        company = user_id  # Assuming company is stored in the fourth column
        order_owner = user[3]  # Assuming order owner name is stored in the fifth column
        # print(company,order_owner)


    if request.method == 'POST':
        order_date = request.form['order_date']
        item = request.form['item']
        ea_count = request.form['ea_count']
        weight = request.form['weight']
        requests = request.form['requests']

        # Get the company and order owner details from the users table based on the user_id
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            company = user_id  

            order_owner = user[3]  
            cursor = mysql.cursor()
            cursor.execute("INSERT INTO Orderitem (order_date, item, count, weight, requests) VALUES (%s, %s,%s, %s, %s)",
                           (order_date, item, ea_count, weight, requests))

            cursor.execute("SELECT order_id FROM Orderitem ORDER BY order_id DESC LIMIT 1")
            order_id = cursor.fetchone()[0]
         
            cursor.execute("INSERT INTO Orderinfo (order_id, user_id) VALUES (%s, %s)", (order_id, user_id))

            
            mysql.commit()
            cursor.close()

            return 'Order submitted successfully!'
        else:
            return 'User not found!'
    else:
        return render_template('orderForm.html',company=company,owner=order_owner)

@app.route('/view_orders')
def view_orders():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect('/')

    # Fetch orders for the logged-in user from the Orderitem table
    user_id = session['user_id']
    cursor = mysql.cursor()
    cursor.execute("SELECT * FROM Orderitem WHERE order_id In (Select order_id from Orderinfo where user_id = %s) ", (user_id,))
    orders = cursor.fetchall()
    cursor.close()

    # Render the orders template and pass the fetched orders as a parameter
    return render_template('viewOrder.html', orders=orders)


@app.route('/admin',)
def admin():
    # Check if user is logged in
    if 'user_id' not in session :
        return redirect('/')
    if'user_id'  in session and  session['user_id']!='1111':
        return redirect('/')
    # Fetch orders for the logged-in user from the Orderitem table
    user_id = session['user_id']
    cursor = mysql.cursor()
    cursor.execute("SELECT Orderinfo.user_id, Orderitem.order_id, order_date, item, count, weight, requests, users.name "
                   "FROM Orderitem "
                   "JOIN Orderinfo ON Orderitem.order_id = Orderinfo.order_id "
                   "JOIN users ON users.id = Orderinfo.user_id")
    orders = cursor.fetchall()

    cursor.close()
    # Render the orders template and pass the fetched orders as a parameter
    return render_template('admin.html', orders=orders)

@app.route('/export-csv', methods=['POST'])
def export_csv():
    if 'user_id' not in session :
        return redirect('/')
    if'user_id'  in session and  session['user_id']!='1111':
        return redirect('/')
    
    cursor = mysql.cursor(dictionary=True)
    cursor.execute("SELECT Orderinfo.user_id, Orderitem.order_id, order_date, item, count, weight, requests, users.name "
                   "FROM Orderitem "
                   "JOIN Orderinfo ON Orderitem.order_id = Orderinfo.order_id "
                   "JOIN users ON users.id = Orderinfo.user_id")
    orders = cursor.fetchall()
    cursor.close()

    # Create a CSV file
    csv_data = []
    for order in orders:
        csv_data.append([order['user_id'], order['order_id'], order['order_date'], order['item'], order['count'],
                         order['weight'], order['requests'], order['name']])

    # Create a StringIO object to write CSV data
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(['User ID', 'Order ID', 'Order Date', 'Item', 'Count', 'Weight', 'Requests', 'Name'])
    writer.writerows(csv_data)

    # Set the response headers for file download
    response = make_response(csv_buffer.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=orders.csv'
    response.headers['Content-Type'] = 'text/csv'

    return response

if __name__ == '__main__':
    app.run()

