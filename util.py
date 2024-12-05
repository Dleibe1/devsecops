import os
import sys
import shutil

def substitutions(currdir, env): 
    if os.path.isdir(currdir):
        for file in os.listdir(currdir):
            substitutions(os.path.join(currdir, file), env)
    else:
        if currdir.endswith(".template"):
            print("Applying substitutions to " + currdir)
            with open(currdir, 'r') as f:
                templateText = f.read()
            for k, v in vars(env).items():
                templateText = templateText.replace(k, str(v))

def initializeFiles():
    if not os.path.isfile("env.py"):
        shutil.copy("env.py.example", "env.py")
        print("env.py file did not exist and has been created. Please edit it to update the necessary values, then re-run this script.")
        sys.exit(1)