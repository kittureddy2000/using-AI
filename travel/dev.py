def get_airport_code(request, airport_code):
    # Assuming the JSON file's content is static or not dependent on `airport_code` in this example
    file_path = '/Users/krishna.yadamakanti/Downloads/response.json'
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            json_data = json.load(file)
        return JsonResponse(json_data)
    else:
        return JsonResponse({'error': 'File not found'}, status=404)
