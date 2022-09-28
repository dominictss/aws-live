from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'
cursor = db_conn.cursor()

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route("/about", methods=['GET', 'POST'])
def about():
    return render_template('about.html')

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    return render_template('contact.html')

@app.route("/employees", methods=['GET', 'POST'])
def employees():
    cursor.execute("SELECT * FROM employee")
    employeesData = cursor.fetchall()
    print(employeesData)
    return render_template('employees.html', data = employeesData, bucket=bucket)

@app.route("/employees-details", methods=['GET', 'POST'])
def employeesDetail():
    if request.method == 'POST':
      data = request.form["edit"]
      print(data)
      cursor.execute("SELECT * FROM employee WHERE emp_id="+data)
      employeesData = cursor.fetchone()
      print(employeesData)
      return render_template('employees-details.html', data = employeesData, bucket=bucket)

@app.route("/saveEmployee", methods=['POST'])
def saveEmployee():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']

    update_employee = "UPDATE employee SET first_name = %s, last_name = %s, pri_skill = %s, location = %s WHERE emp_id = %s"
    try:
        cursor.execute(update_employee, (first_name,last_name,pri_skill,location,emp_id))
        cursor.execute("SELECT * FROM employee")
        employeesData = cursor.fetchall()
        print(employeesData)
    finally:
        print("all modification done...")
    return render_template('employees.html', data = employeesData,  bucket=bucket)

@app.route("/deleteEmployee", methods=['POST'])
def deleteEmployee():
    emp_id = request.form['delete']
    try:
        cursor.execute("DELETE FROM employee WHERE emp_id="+emp_id)
        cursor.execute("SELECT * FROM employee")
        employeesData = cursor.fetchall()
        print(employeesData)
    finally:
        print("all modification done...")
    return render_template('employees.html', data = employeesData,  bucket=bucket)

@app.route("/services", methods=['GET', 'POST'])
def services():
    return render_template('services.html')

@app.route("/servicesdone", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
