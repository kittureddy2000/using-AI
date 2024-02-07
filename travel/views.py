from django.shortcuts import render
import json
from django.conf import settings
import pandas as pd
from datetime import datetime
from .forms import FlightSearchForm
from django.core.cache import cache
from django.http import JsonResponse
import numpy as np
import os
from django.core.serializers.json import DjangoJSONEncoder
from .models import Airport
import requests

API_KEY = "606c319c2emsh19d3ef72bb27af5p15d1a1jsn05a920aeb3e1"
API_HOST = "sky-scrapper.p.rapidapi.com"
            
def load_airport_codes_into_cache():
    codes = list(Airport.objects.values_list('code', flat=True))
    cache.set('airport_codes', codes, timeout=None)  # 'None' timeout for indefinite caching
    
def validate_airport_code(request):
    code = request.GET.get('code', '').upper()
    print("Print Inside validate_airport_code  : " + code)

    isValid = Airport.objects.filter(code=code).exists()
    print("Is airport code valid  : " + str(isValid))
    
    return JsonResponse({'isValid': isValid})

class NumpyJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.int64):
            return int(obj)
        return super().default(obj)



# Create your views here.
# Define initial data as a dictionary
initial_data = {
    'departure_location': 'SFO',
    'arrival_location': 'HYD',
    # Add initial data for other fields as needed
    'departure_date': '2024-06-19',  # Use the appropriate date format
    'return_date': '2024-08-09',     # Use the appropriate date format
    # ...   
}

travel_columns = ['itin_id','itin_no','itin_total_price','itin_score','leg_id','leg_no','leg_hours','leg_minutes','leg_departure','leg_durationInMinutes',
               'leg_departure_formatted','leg_arrival','leg_arrival_formatted','leg_origin','leg_destination','seg_id','seg_no','seg_origin','seg_destination','seg_durationInMinutes',
                'leg_carriers_url','leg_carriers','leg_stopcount','seg_hours','seg_minutes','seg_departure_formatted','seg_arrival_formatted','seg_departure','seg_arrival','seg_flightNumber','seg_carrier']
 

def flatten_travel_json(itinerary_data):
    
    rows_list = []
    itin_no =1
    for itinerary in itinerary_data:
    
        itin_id = itinerary.get('id', 'Itinerary ID not available')
        itin_no = itin_no
        itin_total_price = itinerary.get('price', {}).get('formatted', 'Price not available')
        itin_score = itinerary.get('score', 'Score not available')

        leg_no = 1

        for leg in itinerary.get('legs', []):
            leg_duration = leg.get('durationInMinutes', 'Leg Duration not available')
            leg_hours, leg_minutes = divmod(leg_duration, 60)
            leg_departure = leg.get('departure', 'Leg Departure not available'),
            leg_arrival = leg.get('arrival', 'Leg Arrival not available')
            leg_departure_formatted = datetime.strptime(leg_departure[0], '%Y-%m-%dT%H:%M:%S').strftime('%I:%M %p')
            leg_arrival_formatted = datetime.strptime(leg_arrival, '%Y-%m-%dT%H:%M:%S').strftime('%I:%M %p')
            print(leg_departure_formatted)

            leg_id =  leg.get('id', 'Leg ID not available')
            leg_durationInMinutes = leg.get('durationInMinutes', 'Leg Duration not available')
            leg_stopcount = leg.get('stopCount', 'Legs Stopcount not available')
            leg_carriers_url = leg.get("carriers", {}).get("marketing", [])[0].get("logoUrl", "Carrier url not available")
            leg_carriers = leg.get("carriers", {}).get("marketing", [])[0].get("name", "Carrier name not available")
            leg_origin = leg.get("origin", {}).get("displayCode", "Origina name not available")
            leg_destination = leg.get("destination", {}).get("displayCode", "Destination name not available")
            print("leg_destination : " + leg_destination)

            seg_no = 1
            for segment in leg.get('segments', []):
                seg_departure = segment.get('departure', 'Segment Departure not available'),
                seg_arrival = segment.get('arrival', 'Segment Arrival not available'),
                seg_durationInMinutes = segment.get('durationInMinutes', 'Segment Duration not available'),
                seg_hours, seg_minutes = divmod(seg_durationInMinutes[0], 60)
                seg_departure_formatted = datetime.strptime(seg_departure[0], '%Y-%m-%dT%H:%M:%S').strftime('%I:%M %p')
                seg_arrival_formatted = datetime.strptime(seg_arrival[0], '%Y-%m-%dT%H:%M:%S').strftime('%I:%M %p')
                seg_origin= segment.get('origin', {}).get('displayCode', 'Segment Origin not available')
                seg_destination=segment.get('destination', {}).get('displayCode', 'Segment Destination not available')
                seg_durationInMinutes=  segment.get('durationInMinutes', 'Segment Duration not available')
                seg_flightNumber = segment.get('flightNumber', 'Segment Flight Number not available')
                seg_carrier = segment.get('marketingCarrier', {}).get('name', 'Segment Carrier not available')
                seg_id = segment.get('id', 'Segment ID not available')
                seg_no += 1
                new_row = {'itin_id':itin_id,'itin_no':itin_no,'itin_total_price':itin_total_price,'itin_score':itin_score,
                    'leg_id':leg_id,'leg_no':leg_no,'leg_hours':leg_hours,'leg_minutes':leg_minutes,'leg_departure':leg_departure,
                    'leg_departure_formatted':leg_departure_formatted,'leg_arrival':leg_arrival,'leg_durationInMinutes':leg_durationInMinutes,
                    'leg_arrival_formatted':leg_arrival_formatted,'leg_stopcount':leg_stopcount,'leg_carriers':leg_carriers,
                    'leg_origin':leg_origin, 'leg_destination':leg_destination,'seg_id':seg_id,
                    'seg_no':seg_no,'seg_origin':seg_origin,'seg_destination':seg_destination,'seg_durationInMinutes':seg_durationInMinutes,
                    'seg_hours':seg_hours,'leg_carriers_url':leg_carriers_url,'seg_minutes':seg_minutes,'seg_departure':seg_departure,
                    'seg_departure_formatted':seg_departure_formatted,'seg_arrival_formatted':seg_arrival_formatted,
                    'seg_arrival':seg_arrival,'seg_flightNumber':seg_flightNumber,'seg_carrier':seg_carrier}
                
                #print(new_row)
                rows_list.append(new_row)
                
            leg_no += 1

            
        itin_no += 1
        
    return rows_list

def create_nested_json(df_manual ):
    
    reconstructed_itineraries = []

    # # Use groupby to reconstruct the nested structure
    for itin_no, itin_group in df_manual.groupby('itin_no', sort=False):
        itinerary_dict = {
            'itin_id': itin_group.iloc[0]['itin_id'],
            'itin_no': itin_no,
            'itin_total_price': itin_group.iloc[0]['itin_total_price'],
            'itin_score': itin_group.iloc[0]['itin_score'],
            'legs': []
        }
        # print("itin_no : " + str(itin_no))
        # print("itin price : " + str(itin_group.iloc[0]['itin_total_price']))

        for leg_id, leg_group in itin_group.groupby('leg_id'):
            leg_dict = {
                'leg_id': leg_group.iloc[0]['leg_id'],
                'leg_no': leg_group.iloc[0]['leg_no'],
                'leg_departure': leg_group.iloc[0]['leg_departure'],
                'leg_departure_formatted': leg_group.iloc[0]['leg_departure_formatted'],
                'leg_arrival': leg_group.iloc[0]['leg_arrival'],
                'leg_arrival_formatted': leg_group.iloc[0]['leg_arrival_formatted'],
                'leg_hours': leg_group.iloc[0]['leg_hours'],
                'leg_minutes': leg_group.iloc[0]['leg_minutes'],
                'leg_durationInMinutes': leg_group.iloc[0]['leg_durationInMinutes'],
                'leg_stopcount': leg_group.iloc[0]['leg_stopcount'],
                'leg_carriers_url': leg_group.iloc[0]['leg_carriers_url'],
                'leg_carriers': leg_group.iloc[0]['leg_carriers'],
                'leg_origin': leg_group.iloc[0]['leg_origin'],
                'leg_destination': leg_group.iloc[0]['leg_destination'],
                'segments': []
            }

            for seg_no, segment in leg_group.iterrows():
                segment_dict = {
                    'seg_id': segment['seg_id'],
                    'seg_no': segment['seg_no'],
                    'seg_origin': segment['seg_origin'],
                    'seg_destination': segment['seg_destination'],
                    'seg_durationInMinutes': segment['seg_durationInMinutes'],
                    'seg_hours': segment['seg_hours'],
                    'seg_minutes': segment['seg_minutes'],
                    'seg_departure': segment['seg_departure'],
                    'seg_arrival': segment['seg_arrival'],
                    'seg_departure_formatted': segment['seg_departure_formatted'],
                    'seg_arrival_formatted': segment['seg_arrival_formatted'],
                    'seg_flightNumber': segment['seg_flightNumber'],
                    'seg_carrier': segment['seg_carrier'],
                }
                leg_dict['segments'].append(segment_dict)

            itinerary_dict['legs'].append(leg_dict)

        reconstructed_itineraries.append(itinerary_dict)

    
    return reconstructed_itineraries
def travel(request):
    
        # Initialize an empty DataFrame with specified columns
    df_manual = pd.DataFrame(columns=travel_columns)
    rows_list = []
        
    if request.method == 'POST':
        print("Inside Travel Function POST")
        flight_form = FlightSearchForm(request.POST)

        if flight_form.is_valid():
            # Handle the form data and perform the search logic
            trip_type = flight_form.cleaned_data['trip_type']
            class_of_service = flight_form.cleaned_data['class_of_service']
            passengers = flight_form.cleaned_data['passengers']
            class_of_service = flight_form.cleaned_data['class_of_service']
            departure_location = flight_form.cleaned_data['departure_location']
            arrival_location = flight_form.cleaned_data['arrival_location']
            departure_date = flight_form.cleaned_data['departure_date']
            return_date = flight_form.cleaned_data['return_date']
            # departure_entity_id = get_airport_code(departure_location)
            # arrival_entity_id = get_airport_code(arrival_location)
            
            departure_entity_id = "128668073"
            arrival_entity_id = "95673577"
            print("Inside Travel departure : " + departure_location)
            print("Inside Travel arrival : " + arrival_location)
            
            
        
            print(f"Trip Type: {trip_type}\n"
                f"Passengers: {passengers}\n"
                f"Class of Service: {class_of_service}\n"
                f"Departure Location: {departure_location}\n"
                f"Arrival Location: {arrival_location}\n"
                f"Departure Date: {departure_date}\n"
                f"Return Date: {return_date}")


            
            cache_key = 'travel_data'
            json_data = cache.get(cache_key)
            if not json_data:
                
                url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchFlights"

                querystring = {"originSkyId":departure_location,"destinationSkyId":arrival_location,"originEntityId":departure_entity_id,
                            "destinationEntityId":arrival_entity_id,"date":departure_date,"returnDate":return_date,
                            "adults":passengers,"currency":"USD","market":"en-US","countryCode":"US"}

                headers = {
                    "X-RapidAPI-Key": "606c319c2emsh19d3ef72bb27af5p15d1a1jsn05a920aeb3e1",
                    "X-RapidAPI-Host": "sky-scrapper.p.rapidapi.com"
                }
                
                response = requests.get(url, headers=headers, params=querystring)
                print("Cache is invalid")
                response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code
                json_data = response.json()        
                
                # with open('/Users/krishna.yadamakanti/Learning-and-developement/using-AI/samaanaiapps/travel/travel.json', 'r') as file:
                #      json_data = json.load(file)
                cache.set(cache_key, json_data, timeout=settings.CACHE_TIMEOUT)
    
                # print(json_data)
            
            itinerary_data = json_data["data"]["itineraries"]
            itin_no =1
            rows_list = flatten_travel_json(itinerary_data)
            df_manual = pd.DataFrame(rows_list, columns=travel_columns)
            #print(df_manual)
            df_manual.to_csv('output1.csv', index=False)    

        else:
            print("Form is not valid")
            print(flight_form.errors)  # This will print the errors to the console

    else:
        print("Inside GET")
        flight_form = FlightSearchForm(initial=initial_data)
        
        
    min_price = df_manual['itin_total_price'].min()
    max_price = df_manual['itin_total_price'].max()
    
    df_manual = df_manual.sort_values(by=['itin_no', 'leg_no'], ascending=[True, True])
    
    reconstructed_itineraries = []
    reconstructed_itineraries = create_nested_json(df_manual)
    
    context ={'data_for_template' : reconstructed_itineraries, "form": flight_form,"min_price":min_price,"max_price":max_price}
    
    return render(request, 'travel/travel.html',context)

def filter_sort(request):
    # Get filters from request
    print("Inside Filter function")
    stops = request.GET.get('stops')
    duration = request.GET.get('duration') 
    sort_by = request.GET.get('sort-by')

    print("stops :",stops)
    print("duration :",duration)
    print("sort_by : ",sort_by)  
    
 

    # Filter the queryset based on the filters
    cache_key = 'travel_data'
    json_data = cache.get(cache_key)
    # if not data:
        
    #     url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchFlights"

    #     querystring = {"originSkyId":departure_location,"destinationSkyId":arrival_location,"originEntityId":"95673577",
    #                  "destinationEntityId":"128668073","date":departure_date,"returnDate":return_date,
    #                  "adults":passengers,"currency":"USD","market":"en-US","countryCode":"US"}

    #      headers = {
    #          "X-RapidAPI-Key": "606c319c2emsh19d3ef72bb27af5p15d1a1jsn05a920aeb3e1",
    #          "X-RapidAPI-Host": "sky-scrapper.p.rapidapi.com"
    #      }
        
    #      response = requests.get(url, headers=headers, params=querystring)
    #     print("Cache is invalid")
    #      response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code
    #      data = response.json()        
        
    #     with open('/Users/krishna.yadamakanti/Learning-and-developement/using-AI/samaanaiapps/travel/travel.json', 'r') as file:
    #             json_data = json.load(file)
    #     cache.set(cache_key, data, timeout=settings.CACHE_TIMEOUT)   
    
    
    
    itinerary_data = json_data["data"]["itineraries"]
    rows_list = flatten_travel_json(itinerary_data)
    df_manual = pd.DataFrame(rows_list, columns=travel_columns)
    #print(df_manual)
    df_manual.to_csv('filter.csv', index=False)        

    if stops:
        print("stops is not empty : " + str(stops))
        stops = int(stops)
        df_manual = df_manual[df_manual['leg_stopcount'] == stops]
        #print(one_or_more_stops)
    if duration:
        print("duration is not empty")
    if sort_by:
        print("sort_by is not empty")


    # Assuming you want to sort by price (as an example)
    sort = request.GET.get('sort_by')
    if sort:
        if sort == 'price-low':
            print("price-low")
            df_manual = df_manual.sort_values(by=['itin_total_price','itin_no','leg_durationInMinutes'],ascending=[True,True, True])
        elif sort == 'price-high':
            print("price-high")
            df_manual = df_manual.sort_values(by=['itin_total_price','itin_no','leg_durationInMinutes'],ascending=[False,True, True])
            print(df_manual)
            
        elif sort == 'duration':
            print  ("duration")
            df_manual = df_manual.sort_values(by=['leg_durationInMinutes','itin_no','itin_total_price'],ascending=[True,True, True])
            
        elif sort == 'stops':
            print("stops")
            df_manual = df_manual.sort_values(by=['leg_stopcount','itin_no','itin_total_price'],ascending=[True,True, True])
            
        elif sort == 'score-high':
            print("stops")
            df_manual = df_manual.sort_values(by=['itin_score','itin_total_price'],ascending=[False, True])
            
        elif sort == 'score-low':
            print("stops")
            df_manual = df_manual.sort_values(by=['itin_score','itin_total_price'],ascending=[True, True])
    


    print("Before Consturcing nested json")
    reconstructed_itineraries = create_nested_json(df_manual)
    print("After Constructing nested json")
    print(type(reconstructed_itineraries))
    #print(reconstructed_itineraries)
        
    return JsonResponse({'data_for_template': reconstructed_itineraries}, encoder=NumpyJSONEncoder)


def get_airport_code(airport_code):
        #file_path = '/Users/krishna.yadamakanti/Downloads/response.json'
        # if os.path.exists(file_path):
        #     with open(file_path, 'r') as file:
        #         json_data = json.load(file)
        #         print("Json data : " + str(json_data["data"][0].get("skyId")) ) 
    
        url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport"
        querystring = {"query":airport_code}
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": API_HOST
        }
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code
        json_data = response.json()      

        data_list = []
        airport_sky_id = ""
        for item in json_data['data']:
            if (item['skyId'] == airport_code):
                airport_sky_id = item['navigation'].get('relevantFlightParams', {}).get('entityId', "")
                print("airport_sky_id : " + str(airport_sky_id))
                print("airport_sky_id : " + str(airport_sky_id)) 
            flat_data = {
                'Title': item['presentation'].get('title', ""),
                'Suggestion Title': item['presentation'].get('suggestionTitle', ""),
                'Subtitle': item['presentation'].get('subtitle', ""),
                'Navigation Entity ID': item['navigation'].get('entityId', ""),
                'Navigation Entity Type': item['navigation'].get('entityType', ""),
                'Navigation Localized Name': item['navigation'].get('localizedName', ""),
                'Flight Params SkyId': item['navigation'].get('relevantFlightParams', {}).get('skyId', ""),
                'Flight Params EntityId': item['navigation'].get('relevantFlightParams', {}).get('entityId', ""),
                'Flight Params FlightPlaceType': item['navigation'].get('relevantFlightParams', {}).get('flightPlaceType', ""),
                'Flight Params LocalizedName': item['navigation'].get('relevantFlightParams', {}).get('localizedName', ""),
                'Hotel Params EntityId': item['navigation'].get('relevantHotelParams', {}).get('entityId', ""),
                'Hotel Params EntityType': item['navigation'].get('relevantHotelParams', {}).get('entityType', ""),
                'Hotel Params LocalizedName': item['navigation'].get('relevantHotelParams', {}).get('localizedName', "")
            }
            data_list.append(flat_data)

        # Convert list of dictionaries into a DataFrame
        df = pd.DataFrame(data_list)
        print(df)
        df.to_csv('aiport.csv', index=False)    

        return airport_sky_id


    
    