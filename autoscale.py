import pyrax
import time
import os
import subprocess
import datetime as dt
import socket

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("environment")
pyrax.set_credential_file(creds_file, "LON")

au = pyrax.autoscale
cs = pyrax.cloudservers
cm = pyrax.cloud_monitoring

CARBON_SERVER = '127.0.0.1'
CARBON_PORT = 2003

def get_au_scale_group(au,name):
  for sg in au.list():
    if name == sg.name:
      return sg
    raise Exception("AutoScaling group not found")

def calculate_average(data):
  average = []
  for i in range(0,len(data)):
    average.append(data[j]['average'])
    return(sum(average) / float(len(average)))

def get_average_data(entity,check,duration):
  start_time=dt.datetime.now()-dt.timedelta(minutes=duration)
  end_time=dt.datetime.now()
  data=cm.get_metric_data_points(entity,check,'1m',start_time,end_time,resolution='FULL')
  #print(data)
  return(calculate_average(data))
  

while True:
  sg=get_au_scale_group(au,"Prod_AutoScale")
  nodes_list=sg.get_state()['active']
  data=cm.get_overview()
  average=[]
  for i in range(0, len(data.values()[0])):
   if data.values()[0][i]['entity']['uri'].rsplit('/',1)[1] in nodes_list:
     entity_id=data.values()[0][i]['entity']['id']
     checks=data.values()[0][i]['checks']
     for j in range(0, len(checks)):
       if checks[j]['label'] == 'AverageLoad':
         average.append(get_average_data(entity_id,checks[j]['id'],2))
         break

  average_load = sum(average) / float(len(average))
  print"Time is: ",dt.datetime.now()," Node list: ",nodes_list, " Average Load: ",average_load

  # Send data to Graphite
  message1 = 'AutoScaling.Production.AverageLoad %f %d\n' % (average_load, int(time.time()))
  message2 = 'AutoScaling.Production.TotalNodes %d %d\n' % (len(nodes_list), int(time.time()))
  sock = socket.socket()
  sock.connect((CARBON_SERVER, CARBON_PORT))
  sock.sendall(message1)
  sock.sendall(message2)
  sock.close()

  time.sleep(120)
