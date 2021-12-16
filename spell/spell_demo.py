# # import the spell check module
# from spellcheck import SpellCheck

# # create an object
# spell_check = SpellCheck('words.txt')

# # set the string
# string_to_be_checked = "how many case in vietnam"
# spell_check.check(string_to_be_checked)

# # print suggestions and correction
# print(spell_check.suggestions()[0])
# print(spell_check.correct())

import csv
import io
import requests

url = 'https://raw.githubusercontent.com/BloombergGraphics/covid-vaccine-tracker-data/master/data/current-global.csv'

r = requests.get(url)
buff = io.StringIO(r.text)
dr = csv.DictReader(buff)
for row in dr:
    print(row)
