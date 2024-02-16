from django.shortcuts import render
import requests
import pandas as pd
from stocks.models import Stock
from django.shortcuts import render, redirect
from .forms import StockForm
import yfinance as yf

# Create your views here.
def stocks(request):
    return render(request, 'stocks/stocks_dashboard.html')

def stock_list(request):

    stocks = Stock.objects.all()
    
    stocks_data = []  # List to hold processed data

    for my_stock in stocks:
        print("Getting Details for Stock : " + my_stock.symbol)
        stock = yf.Ticker(my_stock.symbol)
        stock_info = stock.info
        stock_info['quantity'] = my_stock.quantity
        stock_info['data_purchased'] = my_stock.date_purchased
        stock_info['purchase_price'] = my_stock.purchase_price
        stocks_data.append(stock_info)

        print(my_stock.quantity)
        print(my_stock.date_purchased)
        print(my_stock.purchase_price)

        # stock_function = 'OVERVIEW' 
        # api_key="WS5FDNNG2T61OSD7"
        # url = 'https://www.alphavantage.co/query?function=' + stock_function + '&symbol=' + stock.symbol + '&apikey=' + api_key

        # r = requests.get(url)
        # stock_json = r.json()
        # print(stock_json)     
        # stocks_data.append(stock_json)
    stocks_df = pd.DataFrame(stocks_data)    
    print("stocks_df : ")
    print(stocks_df)    
    
    stock_records = stocks_df.to_dict('records')
    context = {'stocks': stock_records}
    
    return render(request, 'stocks/stocks_dashboard.html',context = context)



def add_stock(request):
    print("Inside add_stock request User : " + str(request.user))
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            stock = form.save(commit=False)
            # stock.user = request.user
            stock.save()
            return redirect('stocks:stock_list')
    else:
        form = StockForm()
    return render(request, 'stocks/add_stock.html', {'form': form})
