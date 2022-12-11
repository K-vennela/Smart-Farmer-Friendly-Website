from flask import Flask
import re
from flask import jsonify
from flask import flash, request
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
import datetime
# conn = sqlite3.connect('Shehack.sqlite3')

	
def unique_transaction_id():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')

@app.route('/order/', methods=['POST'],endpoint='order')
def order():
    data=request.get_json()
    
    pr_id=data["product_id"]
    quantity=data["quantity"]
    order_timestamp=data["timestamp"]
    t_id = unique_transaction_id()
    print(pr_id)
    with sqlite3.connect('Shehack.sqlite3') as conn:
        quantity=float(quantity)
        cur = conn.cursor()
        cur.execute("INSERT into Transactions (TransactionId, ProductId, Quantity, OrderTimestamp) VALUES (?,?,?,?);", [t_id,pr_id,quantity,order_timestamp])

        cur.execute("SELECT RemainingQuantity from Products where ProductId=?",[str(pr_id)])
        remaining_quantity = cur.fetchall()
        print(remaining_quantity)
        remaining_quantity=float(remaining_quantity[0][0])-quantity
        cur.execute("UPDATE Products SET RemainingQuantity=? where ProductId=? ",[str(remaining_quantity),str(pr_id)])
        cur.execute("SELECT SoldQuantity from Products where ProductId=?",[str(pr_id)])
        sold_quantity= cur.fetchall()
        sold_quantity=float(sold_quantity[0][0])+quantity
        cur.execute("UPDATE Products SET SoldQuantity=? where ProductId=? ",[str(sold_quantity),str(pr_id)])
        conn.commit()
    return t_id


@app.route('/comparison_on_farmsize/', methods=['POST'], endpoint='comparison_on_farmsize')
def comparison_on_farmsize():

    data = request.get_json()

    f_id = data["farmer_id"]

    with sqlite3.connect('Shehack.sqlite3') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * from Farmers where FarmerId=?",str(f_id))
        farmer=cur.fetchall()
        
        farmer_id,farmer_name,latitude,longitude,land_area,farmerrating=farmer[0]
        # print(farmer_id,farmer_name,latitude,longitude,land_area,farmerrating)

        cur.execute("SELECT FarmerId from Farmers where LandArea<=?",[str(float(land_area)+1000)])
        less_area = cur.fetchall()
        less_area = [ i[0] for i in less_area ]
        # print(less_area)

        cur.execute("SELECT * from Products where FarmerId")
        all_products=cur.fetchall()
        # print(all_products)
        to_check=[]
        for i in all_products:
            if i[0] in less_area:
                to_check.append(i)
        # print(to_check)

        amt=dict()
        for i in to_check:
            if i[0] in amt:
                amt[i[0]]+=(float(i[3])*float(i[5]))
            else:
                amt[i[0]]=(float(i[3])*float(i[5]))
        # print(amt)

        farmers_to_learn_from =[]
        for i in amt.keys():
            if i!=farmer_id and amt[i]>=amt[farmer_id]:
                farmers_to_learn_from.append(i)

        # print(farmers_to_learn_from)

        cur.execute("SELECT * from Farmers")
        all_farmers = cur.fetchall()

        result = dict()

        for i in all_farmers:
            if i[0] in farmers_to_learn_from:
                i_farmer_id,i_farmer_name,i_latitude,i_longitude,i_land_area,i_farmerrating=i
                result[i[0]]={"farmer_name":i_farmer_name,"latitude":i_latitude,"longitude":i_longitude,"land_area":i_land_area,"farmerrating":i_farmerrating}
                # print(result)
                result[i[0]]["products"]=[]
                for j in all_products:
                    if j[0] ==i[0]:
                        result[i[0]]["products"].append({"product_name":j[2],"price":j[3],"amount":float(j[5])*float(j[3]),"Description":j[7],"rating":j[8]})
                sorted(result[i[0]]["products"],key=itemgetter("amount"),reverse=True)
        print(result)
    return jsonify(result)

    
@app.route('/product_compare/', methods=['POST'], endpoint='product_compare')
def product_compare():
    with sqlite3.connect('Shehack.sqlite3') as conn:
        cur = conn.cursor()
        data=request.get_json()
        farmer_id=data["farmer_id"]
        product_name=data["product_name"]

        cur.execute("SELECT FarmerId,ProductId,Price,Rating,Description from Products where ProductName=? and FarmerId!=?",[str(product_name), str(farmer_id)])
        cursor = cur.fetchall()
        li=[]
        for i in cursor:
            farmer_id=i[0]
            dic={}
            dic["product_id"]=i[1]
            dic["price"]=i[2]
            dic["product_rating"]=i[3]
            dic["description"]=i[4]
            cur.execute("SELECT * from Farmers where FarmerId=?",[str(farmer_id)])
            cursor1=cur.fetchall()
            cursor1 = cursor1[0]
            dic["farmer_name"]=cursor1[1]
            dic["farmer_latitude"]=cursor1[2]
            dic["farmer_longitude"]=cursor1[3]
            dic["farmer_area"]=cursor1[4]
            dic["farmer_rating"]=cursor1[5]
            li.append(dic)
    return jsonify(li)


@app.route('/new_farmer/',methods=['POST'], endpoint='new_farmer')
def new_farmer():
    data = request.get_json()

    farmer_name = data["farmer_name"]
    lat = data["latitude"]
    lon = data["longitude"]
    land_area = data["land_area"]
    rating = '0'

    with sqlite3.connect('Shehack.sqlite3') as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) from Farmers")
        num = cur.fetchall()
        num = int(num[0][0])
        farmer_id = num+1
        cur.execute("INSERT into Farmers (FarmerId,FarmerName,Latitude,Longitude,LandArea,FarmerRating) VALUES (?,?,?,?,?,?)",[farmer_id,farmer_name,lat,lon,land_area,rating])
        conn.commit()
    return jsonify({"FarmerId":farmer_id})

@app.route('/new_product/',methods=['POST'], endpoint='new_product')
def new_product():
    with sqlite3.connect('Shehack.sqlite3') as conn:
        cur = conn.cursor()
        data=request.get_json()
        farmer_id=data["farmer_id"]
        remaining_quantity=data["remaining_quantity"]
        product_name=data["product_name"]
        price=data["price"]
        sold_quantity=data["sold_quantity"]
        expiry_date=data["expiry_date"]
        description=data["description"]
        rating='0'
        cur.execute("SELECT count(*) from Products")
        num=cur.fetchall()
        new_id=int(num[0][0])+1
        product_id=new_id
        cur.execute("INSERT INTO Products (FarmerId, ProductId, ProductName, Price, RemainingQuantity, SoldQuantity, ExpiryDate,Description, Rating) VALUES (?,?,?,?,?,?,?,?,?);",[farmer_id, product_id, product_name, price, remaining_quantity, sold_quantity, expiry_date,description, rating])
        conn.commit()
    return jsonify({"farmer_id":farmer_id,"product_id":product_id})

import statsmodels
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAXResults
from matplotlib.figure import Figure
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from flask import Response
from flask import send_file

def get_plot(pred_uc,pred_ci,product_name):
    filename="new_"+product_name+".csv"
    fields = ['Modal_Price', 'Price_Date']
    df= pd.read_csv(filename,skipinitialspace=True, usecols=fields)
    df.Price_Date = pd.to_datetime(df.Price_Date, errors='coerce')
    df=df.set_index('Price_Date')
    y=df.copy()
    y = y['Modal_Price'].resample('MS').mean()
    y = y.fillna(y.bfill())
    print(y)

    #fig = Figure()

    ax = y.plot(label='observed', figsize=(20, 15))
    pred_uc.predicted_mean.plot(ax=ax, label='Forecast')
    ax.fill_between(pred_ci.index,
                    pred_ci.iloc[:, 0],
                    pred_ci.iloc[:, 1], color='k', alpha=.25)
    ax.set_xlabel('Date')
    ax.set_ylabel('CROP PRICE')

    plt.legend()
    bytes_image= io.BytesIO()
    plt.savefig(bytes_image,format='png')
    bytes_image.seek(0)
    plt.clf()
    plt.cla()
    return bytes_image

@app.route('/price_predict/', methods=['GET','POST'], endpoint='price_predict')
def price_predict():
    product_name = request.args.get("product_name")
    num_steps = int(request.args.get("num_steps"))
    loaded=SARIMAXResults.load(product_name+".pkl")

    pred_uc = loaded.get_forecast(steps=num_steps)
    pred_ci = pred_uc.conf_int()
    print(pred_ci)

    bytes_obj = get_plot(pred_uc,pred_ci,product_name)

    #return send_file(bytes_obj,attachment_filename='plot.png',mimetype='image/png')
    return "Done"


def stackedbar(farmerid):
    with sqlite3.connect('Shehack.sqlite3') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * from Products where FarmerId=?",farmerid)
        products=cur.fetchall()
        print(products)
    A=[]
    B=[]
    x_lab=[]
    for i in products:
        A.append(i[4])
        B.append(i[5])
        x_lab.append(i[2]+i[1])
    print(A,B,x_lab)

    fig = plt.figure(facecolor="white")
    
    ax = fig.add_subplot(1, 1, 1)
    bar_width = 0.5
    bar_l = np.arange(1, len(A)+1)
    tick_pos = [i + (bar_width / 2) for i in bar_l]
    
    ax1 = ax.bar(bar_l, A, width=bar_width, label="RemainingQuantity", color="green")
    ax2 = ax.bar(bar_l, B, bottom=A, width=bar_width, label="SoldQuantity", color="blue")
    ax.set_ylabel("Quantity", fontsize=18)
    ax.set_xlabel("Product", fontsize=18)
    ax.legend(loc="best")
    plt.xticks(tick_pos, x_lab, fontsize=16)
    plt.yticks(fontsize=16)
    
    for r1, r2 in zip(ax1, ax2):
        h1 = r1.get_height()
        h2 = r2.get_height()
        plt.text(r1.get_x() + r1.get_width() / 2., h1 / 2., "%d" % h1, ha="center", va="center", color="white", fontsize=16, fontweight="bold")
        plt.text(r2.get_x() + r2.get_width() / 2., h1 + h2 / 2., "%d" % h2, ha="center", va="center", color="white", fontsize=16, fontweight="bold")
    
    #plt.show()
    bytes_image= io.BytesIO()
    plt.savefig(bytes_image,format='png')
    bytes_image.seek(0)
    return bytes_image
  
@app.route('/product_graph/', methods=['GET','POST'], endpoint='product_graph')
def product_graph():
    farmer_id = request.args.get("farmer_id")

    bytes_obj=stackedbar(farmer_id)
    #return send_file(bytes_obj,attachment_filename='plot.png',mimetype='image/png')
    return "done"

from operator import itemgetter
@app.route('/search/', methods=['POST'],endpoint='list_items')
def list_items():
	data= request.get_json()
	print(data)
	latitude=data["latitude"]
	longitude=data["longitude"]
	search_item=data["product_name"]
	li=[]
	with sqlite3.connect('Shehack.sqlite3') as conn:
		cursor = conn.execute("SELECT Latitude,Longitude,Price,FarmerRating,RemainingQuantity,Description,FarmerName,ProductId from Products,Farmers where ProductName='"+search_item+"' and Farmers.FarmerId=Products.FarmerId");
		for row in cursor:
			dic={}
			dic["latitude"]=row[0]
			dic["longitude"]=row[1]
			dic["dist"]=pow(float(row[0])-latitude,2)+pow(float(row[1])-longitude,2)
			dic["price"]=row[2]
			dic["quantity"]=row[4]
			dic["rating"]=row[3]
			dic["description"]=row[5]
			dic["farmername"]=row[6]
			dic["productid"]=row[7]
			li.append(dic)
	#conn.close()
	sorted(li,key=itemgetter("dist"))
	cnt=1
	result={}
	for i in li:
		result[str(cnt)]=i
		cnt+=1
	print(jsonify(result))
	return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True, port=5000)