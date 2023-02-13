import subprocess

print("Testing Reflected SSTI")
#subprocess.run('python Reflected.py')

print("\n\nTesting Stored SSTI with Posterior Injection and Rendering")
subprocess.run('python StoredPosterior.py')

print("\n\nTesting Stored SSTI with Immediate Injection and Rendering")
#subprocess.run('python StoredImmediate.py')
