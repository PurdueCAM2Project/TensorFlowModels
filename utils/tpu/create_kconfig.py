#!/usr/bin/env python3
import os
import subprocess
import sys
import glob

dir = os.path.dirname(__file__)
dest = os.path.join(dir, 'Kconfig')
# template = os.path.join(dir, 'Kconfig.template')
creds = os.path.join(dir, 'creds', '*.json')

username = input("Enter the project username (without @gmail.com): ")

if sys.stdin.isatty():
  credList = glob.glob(creds)
  if credList:
    for i, credFileName in enumerate(credList, 1):
      print(f"[{i}] {os.path.basename(credFileName)}")
    i = int(input("Select a credential file: "))
    AUTH_KEY = credList[i - 1]
  else:
    print("No credential files found. Please make an IAM key and save it to " +
        "the creds folder")
    exit(1)
else:
  AUTH_KEY = next(glob.iglob(creds))

command = ['gcloud', 'auth', 'activate-service-account', f'--key-file={AUTH_KEY}']
# if DRY_RUN:
#   command.insert(0, 'echo')
proc = subprocess.Popen(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
proc.communicate()

# with open(template) as tfile, open(dest, 'w') as dfile:
#   dfile.write(tfile.read().format(AUTH_KEY=repr(AUTH_KEY)))
with open('creds/default.txt', 'w') as dfile:
  print(username, file=dfile)
  print(AUTH_KEY, file=dfile)