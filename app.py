from __future__ import unicode_literals
import json
import random
import sys
from nltk.util import pr
import redis
import requests
import csv
import io
from bs4 import BeautifulSoup
import googlemaps
from argparse import ArgumentParser
from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookParser)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, VideoMessage, FileMessage, StickerMessage,
    LocationMessage, MessageAction, QuickReply, QuickReplyButton, LocationAction,
    ImageSendMessage, ImageCarouselTemplate,  LocationSendMessage,
    CarouselColumn, ImageCarouselColumn, URITemplateAction, TemplateSendMessage,
    CarouselTemplate, FollowEvent, MessageTemplateAction,
    ButtonsTemplate,
)
from training import predict_category
from spell.spellcheck import SpellCheck

# google_maps
GOOGLE_API_KEY = 'AIzaSyBVR6SZshxLMkuCqfctP-qpYoM0PpRHkcM'

# redis database
REDIS_HOST = 'localhost'
REDIS_PASSWORD = None
REDIS_PORT = 6379

# line bot
LINE_CHANNEL_SECRET = '03ee235dbfd1933bec1794e374e9eca8'
LINE_CHANNEL_ACCESS_TOKEN = 'JeXHXi+mRu4EbCjbginNHVDwvL01VXATrJI3jzUn7Brw45/FH6RwfEg512kZzv9THeN2W28ZJUzQPbDIzxp9zBeCHmN0Zk62CZF1mAM0u/y6I8UoBLcBpFRDZcqVzbl1Gpc9WRaVjL6TNovwWw9taQdB04t89/1O/w1cDnyilFU='

# deploy heroku
PORT = ''

# get google API
google_api_key = GOOGLE_API_KEY
gmaps = googlemaps.Client(key=google_api_key)
# Get Redis host,password and port
HOST = REDIS_HOST
PWD = REDIS_PASSWORD
PORT = REDIS_PORT

arr_predict = [
    "Menu",
    "Popular science",
    "Precaution",
    "More knowledge",
    "Wash your hand",
    "Protect others",
    "Outbreak news",
    "Situation report",
    "Latest news",
    "Myth busters",
    "Emergency & Donate",
    "Find hospital",
    "Donate",
    "Country",
    "Global",
    "Statistic",
]


pool = redis.ConnectionPool(host=HOST, password=PWD,
                            port=PORT, decode_responses=True)
r = redis.Redis(connection_pool=pool)

app = Flask(__name__)
# Get Line channel secret and token
channel_secret = LINE_CHANNEL_SECRET
channel_access_token = LINE_CHANNEL_ACCESS_TOKEN

heroku_port = PORT

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

# GET VACCINE API
url = 'https://raw.githubusercontent.com/BloombergGraphics/covid-vaccine-tracker-data/master/data/current-global.csv'
responseVaccine = requests.get(url)


@app.route("/callback", methods=['POST'])
def callback():
    global events
    # confirm that request was sent from LINE
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if isinstance(event, FollowEvent):
            handle_greeting(event)
        if not isinstance(event, MessageEvent):
            continue
        if isinstance(event.message, TextMessage):
            handle_TextMessage(event)
        if isinstance(event.message, ImageMessage):
            handle_ImageMessage(event)
        if isinstance(event.message, VideoMessage):
            handle_VideoMessage(event)
        if isinstance(event.message, FileMessage):
            handle_FileMessage(event)
        if isinstance(event.message, StickerMessage):
            handle_StickerMessage(event)
        if isinstance(event.message, LocationMessage):
            handle_LocationMessage(event)
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
    return 'OK'


# handle greeting event
def handle_greeting(event):
    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(
                text='Hello! This is your healthcare chatbot\uDBC0\uDC8D. How can I help you?'
            ),
            MainMenu(),
        ])


# handle preparetitle to limit the length of title
def prepareTitle(text):
    result = text[:37] + "..." if len(text) > 40 else text
    result = "{}".format(result)
    return result


# handle getPrecaution function
def getPrecaution():
    buttons_template = ButtonsTemplate(text='Precautions:', actions=[
        MessageTemplateAction(label='Wash your hand', text='Wash your hand'),
        MessageTemplateAction(label='Protect others', text='Protect others'),
    ])
    template_message = TemplateSendMessage(
        alt_text='Precautions', template=buttons_template)
    return template_message


# handle getMoreKnowledge function
def getMoreKnowledge():
    result = []
    res = requests.get(
        'https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public/videos')
    soup = BeautifulSoup(res.text, 'html.parser')
    videos = soup.find('div', attrs={'id': 'PageContent_C054_Col01'})
    div_text = videos.find_all(
        'div', attrs={'class': 'section-heading'}, limit=5)
    for num in range(0, 5):
        url = videos.select('iframe')[num]['src']
        soup_url = BeautifulSoup(requests.get(url).text, 'html.parser')
        title_temp = div_text[num].findChild().getText()
        title = prepareTitle(title_temp)
        column = CarouselColumn(
            title=title,
            text=title,
            actions=[
                URITemplateAction(
                    label='More',
                    uri=url
                ),
            ]
        )
        result.append(column)
    carousel = TemplateSendMessage(
        alt_text="5 more pieces of knowledge",
        template=CarouselTemplate(
            columns=result
        )
    )
    result_text = 'Find more videos about coronavirus, please click: ' \
                  'https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public/videos '
    result = [carousel, TextSendMessage(text=result_text)]
    return result


# handle getReport function
def getReport():
    res = requests.get(
        'https://www.who.int/emergencies/diseases/novel-coronavirus-2019/situation-reports')
    soup = BeautifulSoup(res.text, 'html.parser')
    sreport = soup.find_all('a', attrs={'target': '_blank'})[5]
    report = str('https://www.who.int' + sreport['href'])
    return report


# handle getNews function
def getNews():
    result = []
    arr_img = ['https://indaily.com.au/wp-content/uploads/2020/06/20200606001472614645-original-min-scaled.jpg', 'https://images.financialexpress.com/2021/11/Shanghai-Railway-Station-Reuters-photo.jpg',
               'https://img.rasset.ie/001a10bf-600.jpg', 'https://news.mit.edu/sites/default/files/styles/news_article__image_gallery/public/images/202005/covid-19-4971811_MITGOVLAB.png?itok=VvUib4z9']
    res = requests.get(
        'https://www.cbc.ca/news/covid-19')
    soup = BeautifulSoup(res.text, 'html.parser')
    div_news = soup.find('div', attrs={
        'class': 'contentArea'})
    a_news = div_news.find_all('a', attrs={'class': 'card'}, limit=6)
    for a_tag in a_news:
        value = a_tag.attrs
        url = 'https://www.cbc.ca/news' + value['href']
        img_div = a_tag.find('div', attrs={'class': 'placeholder'})
        img_src = img_div.find('img')['src']
        title_temp = a_tag.find('h3', attrs={'class': 'headline'}).getText()
        desc_tag = a_tag.find('div', attrs={'class': 'description'})
        if desc_tag == None:
            desc_temp = title_temp
        else:
            desc_temp = desc_tag.getText()

        if img_div == None:
            img_src = random.choice(arr_img)
        title_news = title_temp[:37] + \
            "..." if len(title_temp) > 40 else title_temp
        desc_news = desc_temp[:37] + \
            "..." if len(desc_temp) > 40 else desc_temp
        column = CarouselColumn(
            title=title_news,
            # Calculate the views of News through redis.
            thumbnail_image_url=img_src,
            text=desc_news,
            actions=[URITemplateAction(
                label='More',
                uri=url
            )]
        )
        result.append(column)
    carousel = TemplateSendMessage(
        alt_text="6 latest news",
        template=CarouselTemplate(
            columns=result
        )
    )
    result_text = 'Find more information about coronavirus, please click: ' \
                  'https://www.cbc.ca/news/covid-19'
    result = [carousel, TextSendMessage(text=result_text)]
    return result


def getStatistic(countryName):
    res = requests.get(
        'https://corona.lmao.ninja/v2/countries/' + countryName)
    buff = io.StringIO(responseVaccine.text)
    dr = csv.DictReader(buff)
    if countryName == 'Global' or countryName == 'World':
        totalDose = 0
        peopleDose = 0
        completeDose = 0
        for row in dr:
            totalDose += int(row['dosesAdministered'])
            if row['peopleVaccinated'] == '':
                peopleDose += 0
            else:
                peopleDose += int(row['peopleVaccinated'])
            if row['completedVaccination'] == '':
                completeDose += 0
            else:
                completeDose += int(row['completedVaccination'])

        res = requests.get(
            'https://corona.lmao.ninja/v2/all/')
        world = json.loads(res.text)
        result_text = 'Global Covid data: ' + \
            "\n------ CASES ------" + \
            '\nCases: ' + str(world['cases']) + \
            '\nToday cases: ' + str(world['todayCases']) + \
            '\nDeaths: ' + str(world['deaths']) + \
            '\nToday deaths: ' + str(world['todayDeaths']) + \
            '\nRecovered: ' + str(world['recovered']) + \
            '\nToday recovered: ' + str(world['todayRecovered']) + \
            "\n------ VACCINE ------" + \
            "\nDose Administered: " + str(totalDose) + \
            "\nPeople Vaccinated: " + str(peopleDose) + \
            "\nCompleted Vaccination: " + \
            str(completeDose)
        flagUrl = 'https://www.nasa.gov/sites/default/files/1-bluemarble_west.jpg'
        flag = ImageSendMessage(
            original_content_url=flagUrl,
            preview_image_url=flagUrl)
        result = [flag, TextSendMessage(text=result_text)]
    else:
        result = []
        dict_country = {}
        for row in dr:
            if row['name'] == countryName:
                dict_country = row

        country = json.loads(res.text)
        result_text = 'Country: ' + \
            country['country'] + \
            "\n------ CASES ------" + \
            "\nCases: " + str(country['cases']) + \
            "\nTodayCases: " + str(country['todayCases']) + \
            "\nDeaths: " + str(country['deaths']) + \
            "\nTodayDeaths: " + str(country['todayDeaths']) + \
            "\nRecovered: " + str(country['recovered']) + \
            "\nTodayRecovered: " + str(country['todayRecovered']) + \
            "\n------ VACCINE ------" + \
            "\nDose Administered: " + str(dict_country['dosesAdministered']) + \
            "\nPeople Vaccinated: " + str(dict_country['peopleVaccinated']) + \
            "\nCompleted Vaccination: " + \
            str(dict_country['completedVaccination'])
        flag = ImageSendMessage(
            original_content_url=country['countryInfo']['flag'],
            preview_image_url=country['countryInfo']['flag'])
        result = [flag, TextSendMessage(text=result_text)]
    return result


# handle getMythBusters function
def getMythBusters():
    result = []
    res = requests.get(
        'https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public/myth-busters')
    soup = BeautifulSoup(res.text, 'html.parser')
    myths = soup.find('div', attrs={'id': 'PageContent_C003_Col01'})
    # choose five myth busters
    for num in range(1, 8):
        myths_image = myths.select('.link-container')[num]
        url = myths_image['href']
        check = url.split(':')[0]
        if check != 'https':
            continue
        column = ImageCarouselColumn(
            image_url=str(url),
            action=URITemplateAction(label='Details', uri=url))
        result.append(column)
    carousel = TemplateSendMessage(
        alt_text="5 myth busters",
        template=ImageCarouselTemplate(
            columns=result
        )
    )
    result_text = 'Find more information about myth busters, please click: ' \
                  'https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public/myth-busters '
    result = [carousel, TextSendMessage(text=result_text)]
    return result


# handle getDonate function
def getDonate():
    carousel = TemplateSendMessage(
        alt_text="Donate",
        template=ButtonsTemplate(
            title='Help Fight Coronavirus',
            text='This donation is for COVID-19 Solidarity Response Fund',
            actions=[
                URITemplateAction(
                    label='Donate to WHO',
                    uri='https://covid19responsefund.org/'
                ),
                URITemplateAction(
                    label='Donate to Africa',
                    uri='http://feedafricafoundation.org/?gclid=Cj0KCQiAnuGNBhCPARIsACbnLzpD-Jm-9pIjrbRqJVyusgvxcGTHwPpAgfP71BOhDr0SUVBbp-YOgO8aAoyREALw_wcB'
                ),
                URITemplateAction(
                    label='Donate to Covid Fund',
                    uri='https://quyvacxincovid19.gov.vn/eng'
                )
            ]
        )
    )
    result_text = 'Attention! This donation is from WHO(World Health Organization) and has nothing to do with the ' \
                  'chatbot, find more information please click: ' \
                  'https://www.who.int/emergencies/diseases/novel-coronavirus-2019/donate '
    result = [TextSendMessage(text=result_text), carousel]
    return result


# handle MainMenu
def MainMenu():
    buttons_template = ButtonsTemplate(text='Main services', actions=[
        MessageTemplateAction(label='1 Popular Science',
                              text='Popular science'),
        MessageTemplateAction(label='2 Outbreak News', text='Outbreak news'),
        MessageTemplateAction(label='3 Emergency & Donate',
                              text='Emergency & Donate'),
        MessageTemplateAction(label='4 Statistic',
                              text='Statistic'),
    ])
    template_message = TemplateSendMessage(
        alt_text='Menu', template=buttons_template)
    return template_message


# handle sub Menu1
def Menu1():
    buttons_template = ButtonsTemplate(text='1 Popular science', actions=[
        MessageTemplateAction(label='Precaution', text='Precaution'),
        MessageTemplateAction(label='More Knowledge', text='More knowledge'),
        MessageTemplateAction(label='Main Menu', text='Menu'),
    ])
    template_message = TemplateSendMessage(
        alt_text='Menu1', template=buttons_template)
    return template_message


# handle sub Menu2
def Menu2():
    buttons_template = ButtonsTemplate(text='2 News about COVID-2019', actions=[
        MessageTemplateAction(label='Situation Report',
                              text='Situation report'),
        MessageTemplateAction(label='Latest News', text='Latest news'),
        MessageTemplateAction(label='Myth Busters', text='Myth busters'),
        MessageTemplateAction(label='Main Menu', text='Menu'),
    ])
    template_message = TemplateSendMessage(
        alt_text='Menu2', template=buttons_template)
    return template_message


# handle sub Menu3
def Menu3():
    buttons_template = ButtonsTemplate(text='Emergency & Donate', actions=[
        MessageTemplateAction(label='Find Hospital', text='Find hospital'),
        MessageTemplateAction(label='Donate', text='Donate'),
        MessageTemplateAction(label='Main Menu', text='Menu'),
    ])
    template_message = TemplateSendMessage(  # TemplateSendMessage -> send box
        alt_text='Menu3', template=buttons_template)
    return template_message

# handle sub Statistic menu


def StatisticMenu():
    buttons_template = ButtonsTemplate(text='Statistic', actions=[
        MessageTemplateAction(label='Global statistic', text='Global'),
        # MessageTemplateAction(label='Country Statistic', text='Country'),
    ])
    template_message = TemplateSendMessage(  # TemplateSendMessage -> send box
        alt_text='StatisticMenu', template=buttons_template)
    return template_message


# Handler function for Text Message
def handle_TextMessage(event):
    print(event.message.text)
    predict_index = int(predict_category(event.message.text))
    predict_res = arr_predict[predict_index]

    if predict_res == 'Menu':
        msg = 'This is main menu: '
        menu = MainMenu()
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(msg),  # TextSendMessage -> send message
                menu]
        )
    elif predict_res == 'Popular science':
        msg = 'This is popular Science knowledge about COVID-2019, what kinds of information you want to know?'
        menu = Menu1()  # Menu1
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(msg),
                menu]
        )
    elif predict_res == 'Precaution':
        line_bot_api.reply_message(
            event.reply_token, getPrecaution()
        )
    elif predict_res == 'More knowledge':
        line_bot_api.reply_message(
            event.reply_token, getMoreKnowledge())
    elif predict_res == 'Wash your hand':
        arr = ['https://cdnimgen.vietnamplus.vn/uploaded/unvjsai/2020_02_18/20200215_vnboyteruatay3blucnao_c_dn_h84_eng_h84.jpg', 'https://www.jdch.com/-/media/jdch/images/blog/handwashing-infographic.ashx?h=563&w=450&la=en&hash=A992CCDDFB83A70741FC34FA6065A0D3&fbclid=IwAR1r5nQa0aJa1KeQwHRFS7HGizHCum6XfDhYJvybQz2qOWr1WoGAyCq1e5A', 'https://www.who.int/images/default-source/health-topics/coronavirus/social'
               '-media-squares/blue-1.tmb-1920v.png?sfvrsn=3d15aa1c_1', 'https://www.who.int/images/default-source/health-topics/coronavirus/social'
               '-media-squares/blue-2.tmb-1920v.png?sfvrsn=2bc43de1_1', 'https://www.afro.who.int/sites/default/files/2020-04/Screen%20Shot%202020-04-30%20at%2015.17.10.png', 'https://www.mandela.ac.za/www-new/media/Store/images/corona/NMU-COVID-19-Hands.jpg']
        image1 = random.choice(arr)
        image2 = random.choice(arr)
        while (image2 == image1):
            image2 = random.choice(arr)
        line_bot_api.reply_message(
            event.reply_token, [
                ImageSendMessage(
                    original_content_url=image1,
                    preview_image_url=image1),
                ImageSendMessage(
                    original_content_url=image2,
                    preview_image_url=image2)
            ])
    elif predict_res == 'Protect others':
        arr = ['https://www.who.int/images/default-source/health-topics/coronavirus/social'
               '-media-squares/blue-3.tmb-1920v.png?sfvrsn=b1ef6d45_1', 'https://i0.wp.com/iufap.blog/wp-content/uploads/2020/05/protect-yourself.jpeg?fit=909%2C1280&ssl=1', 'https://www.who.int/images/default-source/health-topics/coronavirus/visiting-family.tmb-549v.jpg?sfvrsn=e4652390_11', 'https://ditmasrehab.com/wp-content/uploads/2020/05/Ditmas-Park-COVID-19-Protection-01.jpg?fbclid=IwAR3fNiXtuLNb6kczUKL5wdRf_Wrbnb9cuph8kCTCtnxEWZidkAoEjVd1T48', 'https://www.cdh-malawi.com/images/CoVID-19_-_New_Brief-3-1.jpg', 'https://www.who.int/images/default-source/wpro/infographics/coronavirus-(covid-19)/transmission-slide11.png?sfvrsn=93eea205_0&fbclid=IwAR0C5UzblqLUC8giDF2H9Xuv_5EU60wrq1SXxA3DnxddCWy9MFEb1agwch8', 'https://www.skokie.org/ImageRepository/Document?documentID=4666']
        image1 = random.choice(arr)
        image2 = random.choice(arr)
        while (image2 == image1):
            image2 = random.choice(arr)
        line_bot_api.reply_message(
            event.reply_token, [
                ImageSendMessage(
                    original_content_url=image1,
                    preview_image_url=image1),
                ImageSendMessage(
                    original_content_url=image2,
                    preview_image_url=image2)
            ])
    elif predict_res == 'Outbreak news':
        msg = 'This is the outbreak news about COVID-2019, what kinds of information you want to know? '
        menu = Menu2()  # Menu2
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(msg),
                menu])
    elif predict_res == 'Situation report':
        msg1 = 'This is the latest situation report, please click:' + getReport()
        msg2 = 'Find more reports please click: https://www.who.int/emergencies/diseases/novel-coronavirus-2019' \
               '/situation-reports '
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(msg1),
                TextSendMessage(msg2)])
    elif predict_res == 'Latest news':
        line_bot_api.reply_message(
            event.reply_token, getNews())
    elif predict_res == 'Myth busters':
        line_bot_api.reply_message(
            event.reply_token, getMythBusters())
    elif predict_res == 'Emergency & Donate':
        line_bot_api.reply_message(
            event.reply_token, Menu3())  # Menu3
    elif predict_res == 'Find hospital':
        msg = 'Please send your location, thanks.'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text=msg,
            quick_reply=QuickReply(items=[QuickReplyButton(
                action=LocationAction(label='Send your location'),
            )])))
    elif predict_res == 'Donate':
        line_bot_api.reply_message(
            event.reply_token, getDonate())
    elif predict_res == 'Statistic':
        line_bot_api.reply_message(
            event.reply_token, StatisticMenu())
    elif predict_res == 'Country':
        spell_check = SpellCheck('spell\words.txt')
        spell_check.check(event.message.text)
        if len(spell_check.suggestions()) == 0:
            line_bot_api.reply_message(
                event.reply_token, getStatistic('Global'))
        else:
            line_bot_api.reply_message(
                event.reply_token, getStatistic(spell_check.suggestions()[0]))
    elif predict_res == 'Global':
        line_bot_api.reply_message(
            event.reply_token, getStatistic('Global'))
    else:
        msg = "Sorry! I don't understand. What kind of the following information you want to know?"
        line_bot_api.reply_message(
            event.reply_token, [TextSendMessage(
                text=msg,
                quick_reply=QuickReply(items=[
                    QuickReplyButton(action=MessageAction(
                        label='1 Popular Science',
                        text='Popular science')),
                    QuickReplyButton(action=MessageAction(
                        label='2 Outbreak News',
                        text='Outbreak news')),
                    QuickReplyButton(action=MessageAction(
                        label='3 Emergency & Donate',
                        text='Emergency & Donate')),
                ]))]
        )


# Handler function for Location Message
def handle_LocationMessage(event):
    # use redis to set the user's latitude
    r.set('my_lat', event.message.latitude)
    # use redis to set the user's longitude
    r.set('my_lon', event.message.longitude)
    mylat = float(r.get('my_lat'))
    mylng = float(r.get('my_lon'))

    response = requests.post(
        'https://morning-lake-40448.herokuapp.com/',
        json={"longitude": mylat, "latitude": mylng}
    )
    data = response.json()

    # print(data)
    locations = []
    for i, ele in enumerate(data):
        temp = LocationSendMessage(
            title=ele['title'],
            address=ele['address'],
            latitude=ele['latitude'],
            longitude=ele['longitude'],
        )
        locations.append(temp)

    result_text = '3 hospital around you'

    # Line khong cho gui qua 5 phan tu trong 1 tin nhan
    result = [
        TextSendMessage(text=result_text),
        locations[0],
        locations[1],
        locations[2],
    ]

    line_bot_api.reply_message(event.reply_token, result)


# Handler function for Sticker Message
def handle_StickerMessage(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="Nice sticker!")
    )


# Handler function for Image Message
def handle_ImageMessage(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="Nice image!")
    )


# Handler function for Video Message
def handle_VideoMessage(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="Nice video!")
    )


# Handler function for File Message
def handle_FileMessage(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="Nice file!")
    )


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(host='0.0.0.0', debug=options.debug, port='3000')
