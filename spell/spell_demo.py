# import the spell check module
from spellcheck import SpellCheck

# create an object
spell_check = SpellCheck('words.txt')

# set the string
string_to_be_checked = "enlan is the country which I want to see the satistic cases"
spell_check.check(string_to_be_checked)

# print suggestions and correction
print(spell_check.suggestions())
print(spell_check.correct())
