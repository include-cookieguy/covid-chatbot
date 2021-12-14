# import the spell check module
from spellcheck import SpellCheck

# create an object
spell_check = SpellCheck('spell\words.txt')

# set the string
string_to_be_checked = "vietnam is the country which I want to see the satistic cases"
spell_check.check(string_to_be_checked)

# print suggestions and correction
print(spell_check.suggestions()[0])
print(spell_check.correct())
