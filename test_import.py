import sys

print("Python executable:", sys.executable)
print("Python path:", sys.path)
try:
    import google.oauth2.flow
    print ("Imported the google libraries")
except Exception as e:
    print("Error loading libraries" + str(e))
try:
    import google_auth_oauthlib
    print ("Imported the google_auth_oauthlib libraries")
except Exception as e:
    print("Error loading google_auth_oauthlib libraries" + str(e))