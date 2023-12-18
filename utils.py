from bs4 import BeautifulSoup
import requests
import json


async def check_url(seats, url):
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    data_element = soup.find(attrs={'data-enrollment': True})
    if not data_element:
        print("Could not find required element.")
        return
    data = json.loads(data_element['data-enrollment'])
    reserved = data.get("available", {}).get("enrollmentStatus", {}).get("openReserved", 0)
    enrolled = data.get("available", {}).get("enrollmentStatus", {}).get("enrolledCount", 0)
    max_enrolled = data.get("available", {}).get("enrollmentStatus", {}).get("maxEnroll", 0)
    return max_enrolled - enrolled - reserved
