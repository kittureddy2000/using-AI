from django.shortcuts import render

# Create your views here.
def stocks(request):
    return render(request, 'stocks/stocks_dashboard.html')

def stock(request, stock_id):
    return render(request, 'stocks/stock_details.html', {'stock_id': stock_id})