import subprocess

print("  ___ ___ _____ ___    ___")
print(" / __/ __|_   _|_ _|  / __| __ __ _ _ _  _ _  ___ _ _")
print(" \__ \__ \ | |  | |   \__ \/ _/ _` | ' \| ' \/ -_) '_|")
print(" |___/___/ |_| |___|  |___/\__\__,_|_||_|_||_\___|_|")


print("Scanning for URLs")
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

print("\n\nTesting Blind SSTI with Posterior Injection and Rendering")
subprocess.run(['python', 'BlindPosterior.py', ' '.join(url_array)])

print("\n\nTesting Blind SSTI with Immediate Injection and Rendering")
subprocess.run(['python', 'BlindImmediate.py', ' '.join(url_array)])
