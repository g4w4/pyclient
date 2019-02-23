import sys
import os.path
import datetime

def write_log(keyword,data):
    log = "{} : {} --> {}".format(str(datetime.datetime.today()),keyword,data)
    with open("./logs.txt", 'a+') as f:
        f.write(log+'\n')
        f.close()
    print(log); 

