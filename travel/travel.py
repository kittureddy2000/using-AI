import os
import json
import pandas as pd

# Function to print all keys and values in the JSON data
def print_keys(data, prefix=''):
    
    with open('/Users/krishna.yadamakanti/Learning-and-developement/using-AI/samaanaiapps/travel/travel.json', 'r') as file:
    data = json.load(file)

    itinerary_data = data["data"]["itineraries"]
    #print(type(itinerary_data))
    flattened_data = []
    
    for itinerary in itinerary_data:
        print('************************************')
        itin_total_price = itinerary.get('price', {}).get('formatted', 'Price not available')
        itin_id = itinerary.get('id', 'Itinerary ID not available')
        itin_score = itinerary.get('score', 'Score not available')          
        
        #print( "itin_id : " + itin_id)
        #print( "itin_total_price : " + itin_total_price)
        #print( "itin_score : " + str(itin_score))
        
        for legs in itinerary.get('legs', []):
            leg_id = legs.get('id', 'Legs ID not available')
            leg_departure = legs.get('departure', 'Legs Departure not available')
            leg_arrival = legs.get('arrival', 'Legs Arrival not available')
            leg_durationInMinutes = legs.get('durationInMinutes', 'Legs Duration not available')
            leg_stopcount = legs.get('stopCount', 'Legs Stopcount not available')
            leg_carriers = legs.get("carriers", {}).get("marketing", [])[0].get("name", "Carrier name not available")
            leg_origin = legs.get("origin", {}).get("displayCode", "Origina name not available")
            leg_destination = legs.get("destination", {}).get("displayCode", "Destination name not available")
            
            
            #print( "leg_id : " + leg_id)
            #print( "leg_departure : " + leg_departure)
            #print( "leg_arrival : " + leg_arrival)
            #print( "leg_durationInMinutes : " + str(leg_durationInMinutes))
            #print( "leg_stopcount : " + str(leg_stopcount))
            #print( "leg_carriers : " + leg_carriers)
            #print( "leg_origin : " + leg_origin)
            #print( "leg_destination : " + leg_destination)
            
                
            for segment in legs.get('segments', []):
                seg_id= segment.get('id', 'Segment ID not available')
                seg_origin = segment.get('origin', {}).get('displayCode', 'Segment Origin not available')
                seg_destination = segment.get('destination', {}).get('displayCode', 'Segment Destination not available')
                seg_durationInMinutes = segment.get('durationInMinutes', 'Segment Duration not available')
                seg_departure = segment.get('departure', 'Segment Departure not available')
                seg_arrival = segment.get('arrival', 'Segment Arrival not available')
                seg_flightNumber = segment.get('flightNumber', 'Segment Flight Number not available')
                seg_carrier = segment.get('marketingCarrier', {}).get('name', 'Segment Carrier not available')
                
                #print( "segment id : " + segment.get('id', 'Segment ID not available')) 
                #print( "seg_origin : " + seg_origin)
                #print( "seg_destination : " + seg_destination)
                #print( "seg_durationInMinutes : " + str(seg_durationInMinutes))
                #print( "seg_departure : " + seg_departure )
                #print( "seg_arrival : " + seg_arrival )
                #print( "seg_flightNumber : " + seg_flightNumber )
                print( "seg_carrier : " + seg_carrier )
                
                flat_structure = {
                    "itin_no" : itinerary_data.index(itinerary)+1,
                    #'itin_id' : itin_id,
                    'itin_total_price' : itin_total_price,
                    'itin_score' :itin_score,
                    #'leg_id' : leg_id,
                    'leg_origin' : leg_origin,
                    'leg_destination' : leg_destination,
                    'leg_departure' : leg_departure,
                    'leg_arrival' : leg_arrival,
                    'leg_durationInMinutes' : leg_durationInMinutes,
                    'leg_stopcount' : leg_stopcount,
                    'leg_carriers' : leg_carriers,
                    #'seg_id': seg_id,
                    'seg_origin' : seg_origin   ,
                    'seg_destination' : seg_destination,
                    'seg_carrier' : seg_carrier,
                    'seg_durationInMinutes' : seg_durationInMinutes,
                    'seg_departure' : seg_departure,
                    'seg_arrival' : seg_arrival,
                    'seg_flightNumber' : seg_flightNumber,
                }
                #print(flat_structure)
                
        flattened_data.append(flat_structure)
        # Create a DataFrame
    
    df = pd.DataFrame(flattened_data) 
    # print("Head")
    # print(df.head(1))
    # print("Tail")
    # print(df.tail(1))
    # print("shape")
    # print(df.shape)
    # print("columns")
    # print(df.columns)
    # print("dtypes")
    # print(df.dtypes )
    print("describe")
    print(df.describe() )
    # print("info")
    # print(df.info())
    #print(df)
    df.to_csv('travel.csv', index=False)    

def main():
    # Read from the JSON file
    print("Current Working Directory:", os.getcwd())
    with open('/Users/krishna.yadamakanti/Learning-and-developement/using-AI/samaanaiapps/travel/travel.json', 'r') as file:
        data = json.load(file)

    # Print all keys and values
    print_keys(data)

if __name__ == "__main__":
    main()
