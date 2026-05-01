from array import *
import random
import sys
import csv
import os
#from get_coords import access_google_drive, get_spreadsheet_id, download_sheet

SPEEDPICKUP = []
SPEEDDROPOFF = []
PICKUP = []
DROPOFF = [] 
sheet_name = 'ToolPostCoords'
csv_file = 'ToolPostCoords'

# Pull latest tool post coords from Google Drive as .csv
# drive, sheets = access_google_drive()
# sheet_id = get_spreadsheet_id(drive, sheet_name)
# download_sheet(sheets, sheet_id, sheet_name)

SPEEDPICKUP = SPEEDDROPOFF = [1500,500,500,500,1000,1000,1000]
Z_MOVE_HEIGHT = 175 # move Z up for moving when not printing

with open('toolchange/scripts/ToolPostCoords.csv', newline='') as csvfile:
    coordreader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in coordreader:
        if row[0].isdigit():
            #Parse Pickup and Dropoff Coordinates
            PICKUP.append(row[2:9])
            DROPOFF.append(row[10:19])
        if row[0] == 'Speed (F):':
            try:
                float(row[2])
                #Parse Pickup and Dropoff Speed
                SPEEDPICKUP = row[2:9]
                SPEEDDROPOFF = row[10:19]
            except ValueError:
                print("no vlaid speed line found, using default speed")


#Default values
folderName = "toolchange/generatedTCgcode"
os.makedirs(folderName, exist_ok=True)

print("Generating from ToolPostCoords.csv")

for i in range(len(PICKUP)):
    # skipping empty lines 
    try:
        float(PICKUP[i][1])
        print(f"generating tool change gcode block for tool {i + 1}")
    except ValueError:
        print(f"no value for tool {i  + 1}, skipping")
        continue

    #Pickup tool
    f = open(folderName + "/tool_pick_" + str(i+1) + ".gcode", 'w+')
    
    # Retract U axis
    f.write("G28 U0 F1000;\n")
    f.write("G01 X"+str(PICKUP[i][1])+ " Y"+str(PICKUP[i][2])+ " Z"+str(PICKUP[i][0])+" F"+str(SPEEDPICKUP[0])+"; insert comment\n")
    f.write("G01 Y"+str(PICKUP[i][3])+" Z"+str(PICKUP[i][0])+" F"+str(SPEEDPICKUP[1])+"; picking tool "+str(i+1)+" \n")
    f.write("G01 Y"+str(PICKUP[i][3])+" Z"+str(PICKUP[i][4])+" F"+str(SPEEDPICKUP[2])+"; insert comment\n")
    f.write("G01 Y"+str(PICKUP[i][5])+" Z"+str(PICKUP[i][6])+" F"+str(SPEEDPICKUP[3])+"; insert comment\n")
    f.write(f"G01 Y{float(PICKUP[i][5]) + 30} F1000; move away for more space\n")
    f.write(f"G01 Z{Z_MOVE_HEIGHT}; lift Z up to clear existing print\n")
    f.close()


    #Dropoff Tool
    f = open(folderName + "/tool_drop_" + str(i+1) + ".gcode", 'w+')
    # Retract U axis
    
    f.write("G28 U0 F1000;\n")
    f.write(f"G01 Z{Z_MOVE_HEIGHT}; lift Z up to clear existing print\n")
    f.write("G01 Z"+str(DROPOFF[i][0])+";\n")
    # G01 X1 Y1 Z1 F4000
    f.write("G01 X"+str(DROPOFF[i][1])+" Y"+str(DROPOFF[i][2])+" F"+str(SPEEDDROPOFF[0])+"; get in front of proper tool post\n")
    # G01 Y2 F500
    f.write("G01 Y"+str(DROPOFF[i][3])+" Z"+str(DROPOFF[i][4])+" F"+str(SPEEDDROPOFF[1])+"; dropping tool "+str(i+1)+" \n")
    # G01 Y3 Z2 F500
    f.write("G01 Y"+str(DROPOFF[i][5])+" Z"+str(DROPOFF[i][6])+" F"+str(SPEEDDROPOFF[2])+"; insert comment\n")
    # G01 Y4 Z3 F500
    f.write("G01 Y"+str(DROPOFF[i][7])+" Z"+str(DROPOFF[i][8])+" F"+str(SPEEDDROPOFF[3])+"; insert comment\n")

    # G01 Y1 F4000
    f.write(f"G01 Y{float(DROPOFF[i][7]) + 30} F1000; move away for more space\n")

    f.close()
