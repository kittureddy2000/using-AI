
from django.http import HttpResponse
from .models import spinfo
import pandas as pd
from django.shortcuts import render, redirect
from django.forms import modelformset_factory
from .forms import SPInfoForm, SPReturnForm
from django.contrib import messages
from decimal import Decimal


# Create your views here.
def spreturn(request):
    
    initial_values = {
        'numYears': 3,
        'reccuringDeposit': 'No',
        'startingInvest': 1.0,
        'reccuringDepositAmount': 1.0
    }

    categories = []
    series_sp = []
    series_sp_DD = []
    form_values = {}

    ReturnInfo = {}
    SP500_divident = {}
    SP500 = {}

    if (request.method == "POST"):

        print("This is POST Request")
        form = SPReturnForm(request.POST)  # Create an instance of your form
        if form.is_valid():
            print("Form is Valid")
            number_of_year = form.cleaned_data.get('numYears')
            recurring_deposit = form.cleaned_data.get('reccuringDeposit')
            starting_investment = form.cleaned_data.get('startingInvest')
            recurring_deposit_amount = form.cleaned_data.get('reccuringDepositAmount')

    else:
        print("This is GET Request")
        form = SPReturnForm(initial=initial_values)  # This will initialize the form with the initial values
        number_of_year = initial_values["numYears"]
        recurring_deposit = initial_values["reccuringDeposit"]
        starting_investment = initial_values["startingInvest"]
        recurring_deposit_amount = initial_values["reccuringDepositAmount"]
        
    print("Number of Years : " + str(number_of_year))
    print("Starting Investment : " + str(starting_investment))
    print("Recurring Deposit : " + str(recurring_deposit))
    print("Recurring Deposit Amount : " + str(recurring_deposit_amount))

    spreturninfo90years = spinfo.objects.all()
    
    spreturn_data = spinfo.objects.values_list('year', 'spreturn', 'return_divident', named=True)
    # Creating dictionaries from the queryset
    SP500 = {data.year: data.spreturn for data in spreturn_data}
    SP500_dividend = {data.year: data.return_divident for data in spreturn_data}
    print("SP500 Data :" + SP500)
    print("SP500 Dividend Data :" + SP500_dividend)
    


    for start_year  in range(1928, 2021 - number_of_year):
        print("Starting Year : " + str(start_year))
        
        # totalReturnPercent = 0)
        yearly_return_DD = Decimal(starting_investment)
        yearly_return_SP = Decimal(starting_investment)
        principal = Decimal(starting_investment)
        recurring_deposit_amount = Decimal(recurring_deposit_amount)


        for year_offset in range(0, number_of_year):
    
            current_year = start_year + year_offset
            sp_return_DD = Decimal(SP500_dividend[current_year])
            sp_return = Decimal(SP500[current_year])

            if (recurring_deposit == 'Yes'):  # if reccurant deposit is true
               
                yearly_return_DD += (yearly_return_DD * sp_return_DD / Decimal(100)) + recurring_deposit_amount
                yearly_return_SP += (yearly_return_SP * sp_return / Decimal(100)) + recurring_deposit_amount
                principal += recurring_deposit_amount

            else:                
                yearly_return_DD += yearly_return_DD * sp_return_DD / Decimal(100)
                yearly_return_SP += yearly_return_SP * sp_return / Decimal(100)

        end_year = start_year + number_of_year - 1
        CGAR_DD = ((yearly_return_DD / Decimal(starting_investment)) ** (Decimal(1) / Decimal(number_of_year)) - Decimal(1))
        CGAR_SP = ((yearly_return_SP / Decimal(starting_investment)) ** (Decimal(1) / Decimal(number_of_year)) - Decimal(1))
                           
        ReturnInfo[start_year] = [end_year, round(yearly_return_SP, 2), round(yearly_return_DD, 2), round(CGAR_SP * 100, 2), round(CGAR_DD * 100, 2)]
        categories.append(start_year)
        series_sp.append(round(float(yearly_return_SP), 2))
        series_sp_DD.append(round(float(yearly_return_DD), 2))


    print("Categories")
    print(categories)
    print("Series SP")
    print(series_sp)
    print("Series SP DD")
    print(series_sp_DD)

    
    sp_df = pd.DataFrame.from_dict(ReturnInfo, orient='index',
                                   columns=['End_Year', 'SP_Return', 'SP_Return_Dividend', 'CGAR', 'CGAR_Dividend'])    


    # Calculate statistics
    sp_return_stats = {
        'sp_min': sp_df["SP_Return"].min(),
        'sp_max': sp_df["SP_Return"].max(),
        'sp_mean': round(sp_df["SP_Return"].mean(), 2),
        'sp_div_min': sp_df["SP_Return_Dividend"].min(),
        'sp_div_max': sp_df["SP_Return_Dividend"].max(),
        'sp_div_mean': round(sp_df["SP_Return_Dividend"].mean(), 2)
    }

    context = {
        'Returndict': ReturnInfo,
        'categories': categories,
        'SP': series_sp,
        'SP_DD': series_sp_DD,
        'number_of_year': number_of_year,
        'form': SPReturnForm,
        **sp_return_stats  # Merge dictionaries
    }

    return render(request, 'spreturn/spreturn.html', context)



def spreturn_insights(request):
    starting_investment = 1
    number_of_year = 10
    SP500_divident = {}
    SP500 = {}
    ReturnInfo = {}
    years_invest = []
    series_min = []
    series_avg = []
    series_max = []
    SPReturnSummary = {}

    # Load the SP return, SP divident return into local Dictionary
    spreturninfo90years = spinfo.objects.all()

    for each in spreturninfo90years:
        SP500_divident[each.year] = each.return_divident
        SP500[each.year] = each.spreturn
    # End - Load the SP return, SP divident return into local Dictionary

    for number_of_year in range(1,92) :
        ReturnInfo = {}
        for i in range(1930, 2021 - number_of_year + 1):
            # print("*****************************************")
            yearly_returnDD = float(starting_investment)
            yearly_returnSP = float(starting_investment)
            principal = yearly_returnDD

            for abc in range(0, number_of_year):

                spreturnDD = float(SP500_divident[abc + i])
                spreturn = float(SP500[abc + i])
                # print("For Year : " +  str( abc + i))

                yearly_returnDD = round(yearly_returnDD + spreturnDD * yearly_returnDD / 100, 3)
                yearly_returnSP = round(yearly_returnSP + spreturn * yearly_returnSP / 100, 3)

                if (abc == number_of_year - 1):
                    EndYear = abc + i

                    # averageReturn = totalReturnPercent / number_of_year
                    CGARDD = ((yearly_returnDD / starting_investment) ** (
                            1 / number_of_year) - 1)

                    CGARSP = ((yearly_returnSP / starting_investment) ** (
                            1 / number_of_year) - 1)

                    ReturnInfo[i] = [EndYear, round(yearly_returnSP, 2), round(yearly_returnDD, 2), round(CGARSP * 100, 2),
                                     round(CGARDD * 100, 2)]
        sp_df = pd.DataFrame.from_dict(ReturnInfo, orient='index',
                                       columns=['End_Year', 'SP_Return', 'SP_Return_Dividend', 'CGAR', 'CGAR_Dividend'])

        years_invest.append(number_of_year)
        series_min.append(sp_df["SP_Return_Dividend"].min())
        series_avg.append(sp_df["SP_Return_Dividend"].mean())
        series_max.append(sp_df["SP_Return_Dividend"].max())

        print("SP Return with Dividend min ")
        print(sp_df["SP_Return_Dividend"].min())
        print("SP Return  with Dividend Max ")
        print(sp_df["SP_Return_Dividend"].max())
        print("SP Return  with Dividend Mean ")
        print(sp_df["SP_Return_Dividend"].mean())
        SPReturnSummary[number_of_year] = [sp_df["SP_Return_Dividend"].min(),round(sp_df["SP_Return_Dividend"].mean(),2),sp_df["SP_Return_Dividend"].max()]

    context = {
        'SPReturnSummary': SPReturnSummary, 'years_invest': years_invest, 'series_min': series_min, 'series_avg': series_avg,
        'sp_df': sp_df,'series_max':series_max,'number_of_year': number_of_year}

    return render(request, 'sp_insights.html', context)


def add_sp_info(request):
    SPInfoFormSet = modelformset_factory(spinfo, form=SPInfoForm, extra=5)
    if request.method == 'POST':
        formset = SPInfoFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            return redirect('spreturn')  # Replace 'some-view' with your desired redirect view
    else:
        formset = SPInfoFormSet(queryset=spinfo.objects.none())

    return render(request, 'spreturn/spinfo_form.html', {'formset': formset})
