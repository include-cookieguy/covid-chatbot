from __future__ import unicode_literals
import json
import sys
import redis
import requests
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
    "Statistic",
    "Global"
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
    for num in range(0, 5):
        url = videos.select('iframe')[num]['src']
        soup_url = BeautifulSoup(requests.get(url).text, 'html.parser')
        title = prepareTitle(soup_url.title.text)
        column = CarouselColumn(
            title=title,
            text='views:' + str(r.incr(title)),
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
    res = requests.get('https://www.who.int/news-room/releases')
    soup = BeautifulSoup(res.text, 'html.parser')
    news = soup.find_all(
        'a', {'class': 'link-container'}, limit=5)  # choose 5 news
    for t in news:
        value = t.attrs
        title = value['aria-label']
        url = 'https://www.who.int/' + value['href']
        column = CarouselColumn(
            title=prepareTitle(title),
            # Calculate the views of News through redis.
            text='views:' + str(r.incr(title)),
            actions=[URITemplateAction(
                label='More',
                uri=url
            )]
        )
        result.append(column)
    carousel = TemplateSendMessage(
        alt_text="5 latest news",
        template=CarouselTemplate(
            columns=result
        )
    )
    result_text = 'Find more information about coronavirus, please click: ' \
                  'https://www.who.int/emergencies/diseases/novel-coronavirus-2019 '
    result = [carousel, TextSendMessage(text=result_text)]
    return result


def getStatistic(countryName):
    if countryName == 'Global' or countryName == 'World' or countryName == None:
        res = requests.get(
            'https://corona.lmao.ninja/v2/all/')
        world = json.loads(res.text)
        result_text = 'Global Covid data: ' + \
            '\nCases: ' + str(world['cases']) + \
            '\nToday cases: ' + str(world['todayCases']) + \
            '\nDeaths: ' + str(world['deaths']) + \
            '\nToday deaths: ' + str(world['todayDeaths']) + \
            '\nRecovered: ' + str(world['recovered']) + \
            '\nToday recovered: ' + str(world['todayRecovered'])
        flagUrl = 'https://www.nasa.gov/sites/default/files/1-bluemarble_west.jpg'
        flag = ImageSendMessage(
                        original_content_url=flagUrl,
                        preview_image_url=flagUrl)
        result = [flag, TextSendMessage(text=result_text)]
    else:
        result = []
        res = requests.get(
            'https://corona.lmao.ninja/v2/countries/' + countryName)
        country = json.loads(res.text)
        print(country)
        result_text = 'Country: ' + \
            country['country'] + \
            "\nCases: " + str(country['cases']) + \
            "\nTodayCases: " + str(country['todayCases']) + \
            "\nDeaths: " + str(country['deaths']) + \
            "\nTodayDeaths: " + str(country['todayDeaths']) + \
            "\nRecovered: " + str(country['recovered']) + \
            "\nTodayRecovered: " + str(country['todayRecovered'])
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
    for num in range(1, 6):
        myths_image = myths.select('.link-container')[num]
        url = myths_image['href']
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
            actions=[URITemplateAction(
                label='Go to donate',
                uri='https://covid19responsefund.org/'
            )]
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
        MessageTemplateAction(label='Statistic', text='Statistic'),
        MessageTemplateAction(label='Main Menu', text='Menu'),
    ])
    template_message = TemplateSendMessage(  # TemplateSendMessage -> send box
        alt_text='Menu3', template=buttons_template)
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
        line_bot_api.reply_message(
            event.reply_token, [
                ImageSendMessage(
                    original_content_url='https://www.who.int/images/default-source/health-topics/coronavirus/social'
                                         '-media-squares/blue-1.tmb-1920v.png?sfvrsn=3d15aa1c_1 ',
                    preview_image_url='https://www.who.int/images/default-source/health-topics/coronavirus/social'
                                      '-media-squares/blue-1.tmb-1920v.png?sfvrsn=3d15aa1c_1 '
                ),
                ImageSendMessage(
                    original_content_url='https://www.who.int/images/default-source/health-topics/coronavirus/social'
                                         '-media-squares/blue-2.tmb-1920v.png?sfvrsn=2bc43de1_1 ',
                    preview_image_url='https://www.who.int/images/default-source/health-topics/coronavirus/social'
                                      '-media-squares/blue-2.tmb-1920v.png?sfvrsn=2bc43de1_1 '
                ),
            ])
    elif predict_res == 'Protect others':
        line_bot_api.reply_message(
            event.reply_token, [
                ImageSendMessage(
                    original_content_url='https://www.who.int/images/default-source/health-topics/coronavirus/social'
                                         '-media-squares/blue-3.tmb-1920v.png?sfvrsn=b1ef6d45_1',
                    preview_image_url='https://www.who.int/images/default-source/health-topics/coronavirus/social'
                                      '-media-squares/blue-3.tmb-1920v.png?sfvrsn=b1ef6d45_1'),
                ImageSendMessage(
                    original_content_url='https://www.who.int/images/default-source/health-topics/coronavirus/social'
                                         '-media-squares/blue-4.tmb-1920v.png?sfvrsn=a5317377_5',
                    preview_image_url='https://www.who.int/images/default-source/health-topics/coronavirus/social'
                                      '-media-squares/blue-4.tmb-1920v.png?sfvrsn=a5317377_5')
            ])
    elif predict_res == 'Outbreak news':
        msg = 'This is the latest news about COVID-2019, what kinds of information you want to know? '
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
    elif predict_res == 'Statistic' or predict_res == 'Global':
        spell_check = SpellCheck('spell\words.txt')
        spell_check.check(event.message.text)

        line_bot_api.reply_message(
            event.reply_token, getStatistic(spell_check.suggestions()[0]))
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

    print('data: ', data)
    print('location: ', locations)

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
