import subprocess

print("  ___ ___ _____ ___    ___")
print(" / __/ __|_   _|_ _|  / __| __ __ _ _ _  _ _  ___ _ _")
print(" \__ \__ \ | |  | |   \__ \/ _/ _` | ' \| ' \/ -_) '_|")
print(" |___/___/ |_| |___|  |___/\__\__,_|_||_|_||_\___|_|")


print("\n\nTo test on pages secured by authentication, the scanner requires valid user credentials\n\n")

cred_choice = ""

while(True):
    cred_choice = input("Press 1 to input credentials or 2 to skip this step: ")

    if(cred_choice == "1" or cred_choice == "2"):
        break
    else:
        print("\nInvalid input, please try again\n\n")


cred_names = []
cred_vals = []
if(cred_choice == "1"):  # User decides to enter credentials
    counter = 1
    finished = False
    while(finished == False):  # Loop until user has entered all credentials
        print(f"\nCredential set {counter}\n==================")

        cred_name = ""
        while(True):  # Loop until valid input
            cred_name = input("Credential Name: ")
            if(len(cred_name) == 0):
                print("\nInvalid input, please try again\n\n")
            else:
                break

        cred_val = ""
        while(True):  # Loop until valid input
            cred_val = input("Credential Value: ")
            if(len(cred_val) == 0):
                print("\nInvalid input, please try again\n\n")
            else:
                break

        cred_names.append(cred_name)
        cred_vals.append(cred_val)
        counter+=1

        while(True):  # Check if user is finished from credential input
            stop_input = input("Have all credentials been inputted (y/n): ")
            if(stop_input == "y"):
                finished = True
                break
            elif(stop_input == "n"):
                break
            else:
                print("\nInvalid input, please try again\n\n")


print("\n\nScanning for URLs")
print("Please enter an entry point URL: ")
urls = subprocess.Popen(['python',  'URLFinder.py'], stdout=subprocess.PIPE)
encoded = urls.communicate()

url_string = encoded[0].decode("utf-8")

url_array = url_string.split("|")  # splitting the incoming string
url_array.pop(-1)   # removing the final element as it is not a URL


print("\n\nTesting Reflected SSTI")
subprocess.run(['python', 'Reflected.py', ' '.join(url_array)])

print("\n\nTesting Stored SSTI with Posterior Injection and Rendering")
subprocess.run(['python', 'StoredPosterior.py', ' '.join(url_array)])

print("\n\nTesting Stored SSTI with Immediate Injection and Rendering")
subprocess.run(['python', 'StoredImmediate.py', ' '.join(url_array)])

if(cred_choice == "1"):
    print("\n\nTesting Blind SSTI with Posterior Injection and Rendering")
    subprocess.run(['python', 'BlindPosterior.py', ' '.join(url_array), ' '.join(cred_names), ' '.join(cred_vals)])

    print("\n\nTesting Blind SSTI with Immediate Injection and Rendering")
    subprocess.run(['python', 'BlindImmediate.py', ' '.join(url_array)])

    print("\n\nTesting Authenticated Stored Posterior Injection and Rendering")
    subprocess.run(['python', 'AuthenticatedStoredPosterior.py', ' '.join(url_array), ' '.join(cred_names), ' '.join(cred_vals)])
