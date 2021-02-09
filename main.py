import requests
import logging
import random
import os
import copy
from telegram.ext import Updater, CommandHandler, MessageHandler, InlineQueryHandler
from telegram.ext.filters import Filters
from telegram import InlineQueryResultArticle as Article, InputTextMessageContent as In
from PIL import ImageFont, ImageOps, ImageDraw, Image
from googletrans import Translator
from bs4 import BeautifulSoup

with open('token.txt', 'r') as file:
    BOT_TOKEN=file.read()

#(154,181,202)
#(236,230,234)
#(220,110,51)
#(254,113,207)
#(1,205,255)
#(6,255,161)
#(186,103,255)
#(255,251,151)

CONSTANTS = {
             'RU_DICTIONARY_PATH':       ['ru_1000.txt',                                    'путь к ru словарю для команды /words (/dicts, чтобы посмотреть доступные)'],
             'EN_DICTIONARY_PATH':       ['en_8000.txt',                                    'путь к en словарю для команды /words (/dicts, чтобы посмотреть доступные)'],
             'FONT_PATH':                ['chogokubosogothic_5.ttf',                        'путь к шрифту (/fonts чтобы посмотреть доступные)'],
             'IMAGE_BORDER':             ['200',                                            'ширина рамки в пикселях'],
             'IMAGE_BORDER_FILL':        ['(0,0,0)',                                        'цвет рамки RGB'],
             'IMAGE_TEXT_POS':           ['(int(image.width/2), int(image.height-100))',    '(х,у) координаты якоря текста (может быть любым выражением)'],
             'IMAGE_TEXT_ALIGN':         ['center',                                         'выравнивание текста (left/center/right)'],
             'IMAGE_TEXT_ANCHOR':        ['mm',                                             'код расположения якоря текста (/anchors чтобы посмотреть доступные)'],
             'IMAGE_TEXT_FILL':          ['(255,255,255)',                                  'цвет текста RGB'],
             'FONT_SIZE':                ['60',                                             'размер шрифта'],
             'STROKE_SIZE':              ['2',                                              'ширина шрифта']
             }
CONSTANTS_DEF = copy.deepcopy(CONSTANTS)
#creating gtranslator client
translator = Translator()
#requests session
session = requests.session()
session.max_redirects = 1000
session.headers = {'User-Agent': 'Mozilla/5.0'}
#creating a Bot entry
updater = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher
#logging just in case
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
#font to use in process_image
def load_font():
    global fontutf8
    fontutf8 = ImageFont.truetype('fonts/'+CONSTANTS['FONT_PATH'][0], eval(CONSTANTS['FONT_SIZE'][0]))



#loading dictionary
def load_dicts():
    global dictionary
    dictionary = [[],[]]
    with open('dicts/'+CONSTANTS['RU_DICTIONARY_PATH'][0], encoding='utf-8') as file:
        line = file.readline()
        while line:
            dictionary[0].append(line[:-1])
            line = file.readline()
    with open('dicts/'+CONSTANTS['EN_DICTIONARY_PATH'][0]) as file:
        line = file.readline()
        while line:
            dictionary[1].append(line[:-1])
            line = file.readline()



def start(update, context):
    context.bot.send_message(update.effective_chat.id, text='hello! send me a text and attach a picture to it and i will generate a captioned picture!')

def textandimage(update, context):
    global CONSTANTS
    cache = copy.deepcopy(CONSTANTS)
    #when user sends photo with a caption to a bot
    text = update.message.caption
    text = parse_const(text)
    load_font()
    image = context.bot.getFile(update.message.photo[-1].file_id)
    image_id = f'img/{random.randint(100000,999999)}.jpg'
    image.download(image_id)
    process_image(image_id, text)
    CONSTANTS = copy.deepcopy(cache)
    load_font
    context.bot.send_photo(update.effective_chat.id, photo=open(image_id, 'rb'))

def words(update, context):
    #/words command
    text = update.message.text
    if text == '/words ru':
        words = []
        context.bot.send_message(update.effective_chat.id, text='подглядываю в Reverso Context...')
        for i in range(10):
            word = random.choice(dictionary[0])
            req = session.get("https://context.reverso.net/translation/russian-english/"+word, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(req.text, 'lxml')
            sentences1 = [x.text.strip() for x in soup.find_all('a', {'class':'translation'})[1:] if '\n' in x.text]
            words.append(f'{word.upper()} - {", ".join(sentences1)}\n')
        context.bot.send_message(update.effective_chat.id, text=u'\n'.join(words))
    elif text == '/words en':
        words = []
        context.bot.send_message(update.effective_chat.id, text='подглядываю в Reverso Context...')
        for i in range(10):
            word = random.choice(dictionary[1])
            req = session.get("https://context.reverso.net/translation/english-russian/"+word, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(req.text, 'lxml')
            sentences1 = [x.text.strip() for x in soup.find_all('a', {'class':'translation'})[1:] if '\n' in x.text]
            words.append(f'{word.upper()} - {", ".join(sentences1)}\n')
        context.bot.send_message(update.effective_chat.id, text=u'\n'.join(words))
    else:
        help_words(update, context)

def inline(update, context):
    #inline translation handler
    query = update.inline_query.query
    if not query:
        return

    #sending a request to reverso context (the output works only for single words for some reason)
    request = query.replace(' ','+')
    req = requests.get("https://context.reverso.net/translation/russian-english/"+request, headers={'User-Agent': 'Mozilla/5.0'})
    #parsing reverso context responce
    soup = BeautifulSoup(req.text, 'lxml')
    sentences1 = [x.text.strip() for x in soup.find_all('a', {'class':'translation'})[1:] if '\n' in x.text]
    #translating with Google Translator just in case reverso didn't send anything useful
    translation = []
    results = []
    translation = translator.translate(query, dest='en').text
    results.append(Article(id=random.randint(0,1000000000000),
                           title=translation,
                           input_message_content=In(translation),
                           description=translator.translate(translation, dest='ru').text,
                           thumb_url='https://images.theconversation.com/files/93616/original/image-20150902-6700-t2axrz.jpg'))
    #in case if reverso's responce had a words in it, we should add them to a results
    if sentences1:
        for i in sentences1:
            results.append(Article(id=random.randint(0,1000000000000),
                                   title=i, input_message_content=In(i),
                                   description=translator.translate(i, dest='ru').text,
                                   thumb_url='https://apprecs.org/gp/images/app-icons/300/24/com.softissimo.reverso.context.jpg'))
    context.bot.answer_inline_query(update.inline_query.id, results)

def process_image(image, text):
    name = image
    image = Image.open(name)
    image = ImageOps.expand(image, border=eval(CONSTANTS['IMAGE_BORDER'][0]), fill=eval(CONSTANTS['IMAGE_BORDER_FILL'][0]))
    draw = ImageDraw.Draw(image)
    draw.text(eval(CONSTANTS['IMAGE_TEXT_POS'][0]),
              text,
              anchor=CONSTANTS['IMAGE_TEXT_ANCHOR'][0],
              font=fontutf8,
              fill=eval(CONSTANTS['IMAGE_TEXT_FILL'][0]),
              align=CONSTANTS['IMAGE_TEXT_ALIGN'][0],
              stroke_width = eval(CONSTANTS['STROKE_SIZE'][0]))
    image.save(name)

def change_const(update, context):
    global CONSTANTS
    text = update.message.text
    if text == '/const defaults':
        CONSTANTS = copy.deepcopy(CONSTANTS_DEF)
        load_dicts()
        load_font()
        return
    elif text =='/const':
        output = 'ИЗМЕНИТЬ КОНСТАНТЫ:\n/const const:КОНСТАНТА_1=ЗНАЧЕНИЕ_1;КОНСТАНТА_2=ЗНАЧЕНИЕ_2;ит.д.//\nнапример: /const const:IMAGE_TEXT_FILL=(255,0,255)//\nзначения поумолчанию /const defaults\n\n'
        for constant in CONSTANTS.keys():
            output += f'{constant} = {CONSTANTS[constant][0]} ({CONSTANTS[constant][1]})\n\n'
        context.bot.send_message(update.effective_chat.id, text=output)
    parse_const(text)

#format is const:KWARG1=VALUE1;KWARG2=VALUE2// and so on
def parse_const(string):
    flag=False
    if 'const:' in string and '//' in string:
        if 'DICTIONARY' in string: flag=True
        text = string[:string.find('const:')]+string[string.find('//')+2:]
        const = string[string.find('const:')+6:string.find('//')]
        const = const.split(';')
        for con in const:
            var, val = con.split('=')
            CONSTANTS[var][0]=val
    else:
        text = string
    if flag:
        load_dicts()
    return(text)

def help_dicts(update, context):
    text = '\n'.join(os.listdir('dicts/'))
    context.bot.send_message(update.effective_chat.id, text=text)

#/fonts
def help_fonts(update, context):
    text = '\n'.join(os.listdir('fonts/'))
    context.bot.send_message(update.effective_chat.id, text=text)

#/anchors
def help_anchors(update, context):
    context.bot.send_photo(update.effective_chat.id, photo='https://ibb.co/cY16CCH')
    context.bot.send_photo(update.effective_chat.id, photo='https://ibb.co/BqX9mcM')

def help_words(update, context):
    context.bot.send_message(update.effective_chat.id, text='/words ru - список из 10 русских слов с переводом на английский\n/words en список из 10 английских слов с переводом на русский')

load_dicts()
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('words', words))
dispatcher.add_handler(CommandHandler('const', change_const))
dispatcher.add_handler(CommandHandler('fonts', help_fonts))
dispatcher.add_handler(CommandHandler('anchors', help_anchors))
dispatcher.add_handler(CommandHandler('dicts', help_dicts))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(MessageHandler((Filters.photo), textandimage))
dispatcher.add_handler(InlineQueryHandler(inline))
updater.start_polling()
