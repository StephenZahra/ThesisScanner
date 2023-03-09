import subprocess

print("  ___ ___ _____ ___    ___")
print(" / __/ __|_   _|_ _|  / __| __ __ _ _ _  _ _  ___ _ _")
print(" \__ \__ \ | |  | |   \__ \/ _/ _` | ' \| ' \/ -_) '_|")
print(" |___/___/ |_| |___|  |___/\__\__,_|_||_|_||_\___|_|")

# print("Testing Reflected SSTI")
# subprocess.run('python Reflected.py')
#
print("\n\nTesting Stored SSTI with Posterior Injection and Rendering")
subprocess.run('python StoredPosterior.py')
#
# print("\n\nTesting Stored SSTI with Immediate Injection and Rendering")
# subprocess.run('python StoredImmediate.py')
#
# print("\n\nTesting Blind SSTI with Posterior Injection and Rendering")
# subprocess.run('python BlindPosterior.py')
