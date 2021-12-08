import requests
from flask import Flask, render_template
URL = "https://discover.search.hereapi.com/v1/discover"
latitude = 21.2749
longitude = 106.1933
# Acquire from developer.here.com
api_key = 'Ax3DtY2b-3EWyh1do9xI2d8tpRq5-gmPIA4D-Mm0d8M'
query = 'hospital'
limit = 5

PARAMS = {
    'apikey': api_key,
    'q': query,
    'limit': limit,
    'at': '{},{}'.format(latitude, longitude)
}

# sending get request and saving the response as response object
r = requests.get(url=URL, params=PARAMS)
data = r.json()


hospitalOne = data['items'][0]['title']
hospitalOne_address = data['items'][0]['address']['label']
hospitalOne_latitude = data['items'][0]['position']['lat']
hospitalOne_longitude = data['items'][0]['position']['lng']


hospitalTwo = data['items'][1]['title']
hospitalTwo_address = data['items'][1]['address']['label']
hospitalTwo_latitude = data['items'][1]['position']['lat']
hospitalTwo_longitude = data['items'][1]['position']['lng']

hospitalThree = data['items'][2]['title']
hospitalThree_address = data['items'][2]['address']['label']
hospitalThree_latitude = data['items'][2]['position']['lat']
hospitalThree_longitude = data['items'][2]['position']['lng']


hospitalFour = data['items'][3]['title']
hospitalFour_address = data['items'][3]['address']['label']
hospitalFour_latitude = data['items'][3]['position']['lat']
hospitalFour_longitude = data['items'][3]['position']['lng']

hospitalFive = data['items'][4]['title']
hospitalFive_address = data['items'][4]['address']['label']
hospitalFive_latitude = data['items'][4]['position']['lat']
hospitalFive_longitude = data['items'][4]['position']['lng']

app = Flask(__name__)


@app.route('/')
def map_func():
    return render_template('map.html',
                           latitude=latitude,
                           longitude=longitude,
                           apikey=api_key,
                           oneName=hospitalOne,
                           OneAddress=hospitalOne_address,
                           oneLatitude=hospitalOne_latitude,
                           oneLongitude=hospitalOne_longitude,
                           twoName=hospitalTwo,
                           twoAddress=hospitalTwo_address,
                           twoLatitude=hospitalTwo_latitude,
                           twoLongitude=hospitalTwo_longitude,
                           threeName=hospitalThree,
                           threeAddress=hospitalThree_address,
                           threeLatitude=hospitalThree_latitude,
                           threeLongitude=hospitalThree_longitude,
                           fourName=hospitalFour,
                           fourAddress=hospitalFour_address,
                           fourLatitude=hospitalFour_latitude,
                           fourLongitude=hospitalFour_longitude,
                           fiveName=hospitalFive,
                           fiveAddress=hospitalFive_address,
                           fiveLatitude=hospitalFive_latitude,
                           fiveLongitude=hospitalFive_longitude
                           )


if __name__ == '__main__':
    app.run(debug=False)
