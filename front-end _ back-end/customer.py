from flask import Flask
import pymysql
import re
from flask import jsonify
from flask import flash, request
from werkzeug import generate_password_hash, check_password_hash
import binascii
import base64
import requests
from json import dumps
from flask import make_response
app = Flask(__name__)
import os
import sys
import traceback


import sqlite3
conn = sqlite3.connect('.db')

@app.route('/search/', methods=['POST'],endpoint='list_items')
def list_items():
	data=request.json["data"]
	latitude=data["latitude"]
	longitude=data["longitude"]
	search_item=data["product_name"]
	cursor = conn.execute("SELECT * from table where product_name=",search_item);
	dic={}
	li=[]
	cnt=1
	for row in cursor:
		dic={}
		dic["latitude"]=row[0]
		dic["longitude"]=row[1]
		dic["dist"]=(row[0]-latitude)^2+(row[1]-longitude)^
		dic["price"]=row[2]
		dic["quantity"]=row[3]
		dic["rating"]=row[4]
		dic["description"]=row[5]
		li.append(dic)
	sorted(li,key=itemgetter("dist"))
	jsonify(dic)
	return jsonify
	


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True, port=80)