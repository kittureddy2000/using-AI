from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import pandas as pd
from stocks.models import Stock
from .forms import StockForm
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

@login_required
def stocks(request):
    return render(request, 'stocks/stocks_dashboard.html')

@login_required
def stock_list(request):
    # Fetch the user's stocks from the database
    stocks = Stock.objects.filter(user=request.user)
    stocks_data = []

    # Loop through each user stock and fetch fresh info from yfinance
    for my_stock in stocks:
        logger.debug(f"Getting Details for Stock: {my_stock.symbol}")
        try:
            stock = yf.Ticker(my_stock.symbol)
            stock_info = stock.info
            stock_info['quantity'] = my_stock.quantity
            stock_info['date_purchased'] = my_stock.date_purchased
            stock_info['purchase_price'] = my_stock.purchase_price
            stocks_data.append(stock_info)
        except Exception as e:
            logger.error(f"Error fetching data for {my_stock.symbol}: {str(e)}")
            # You could append some default data here if desired

    # Convert collected data to a DataFrame, then to a dictionary for the template
    if stocks_data:
        stocks_df = pd.DataFrame(stocks_data)
        stock_records = stocks_df.to_dict('records')
    else:
        stock_records = []

    context = {'stock_list': stock_records}
    return render(request, 'stocks/stocks_dashboard.html', context=context)

@login_required
def add_stock(request):
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            stock = form.save(commit=False)
            stock.user = request.user
            stock.save()
            return redirect('stocks:stock_list')
    else:
        form = StockForm()
    return render(request, 'stocks/add_stock.html', {'form': form})
