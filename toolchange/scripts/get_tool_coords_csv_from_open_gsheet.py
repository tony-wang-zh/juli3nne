import requests

# this fetches tool post coordinates from an csv file with open access 

SPREADSHEET_ID = '1zRDNl76fYzoBgPhy8uw7BePsERJiiz6k2lMWA27DdNM'
GID = '0'  # the tab, 0 for default first tabb
LOCAL_CSV_FILE = "ToolPostCoords.csv"

# The direct CSV export URL
url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID}"

def download_config():
    print("Fetching configuration...")
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Save the content directly to a CSV file
        with open(LOCAL_CSV_FILE, 'wb') as file:
            file.write(response.content)
        print("Success! f{LOCAL_CSV_FILE} updated.")
    else:
        print(f"Failed to download the sheet. HTTP Status: {response.status_code}")

if __name__ == '__main__':
    download_config()