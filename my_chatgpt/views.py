from openai import OpenAI
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_http_methods(["POST"])
def chatgpt_response(request):
    user_prompt = request.POST.get('prompt')
    print(user_prompt)
    client = OpenAI(api_key=os.getenv('MY_CHATGPT_KEY'))
    completion = client.chat.completions.create(
      model="gpt-4-turbo-preview",
      messages=[
        {"role": "system", "content": "You are a Priciple developer who has extensive knowledge in software"},
        {"role": "user", "content": user_prompt}
      ]
    )

    # Extracting the content from the completion object
    response_content = completion.choices[0].message.content
    
    
    # Returning the content in a serializable format
    return JsonResponse({'response': response_content})

def chat_gpt(request):
    return render(request, 'my_chatgpt/chatgpt.html')
