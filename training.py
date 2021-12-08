from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import DictVectorizer
import re
import sys
from nltk.corpus import stopwords
import nltk
from underthesea import word_tokenize
from sklearn.datasets import fetch_20newsgroups
from sklearn.naive_bayes import MultinomialNB
import seaborn as sns
sns.set()

vec = DictVectorizer()
text = []
label = []


def remove_html(txt):
    return re.sub(r'<[^>]*>', '', txt)


def text_preprocess(document):
    document = remove_html(document)
    pattern = re.compile(
        r'\b(' + r'|'.join(stopwords.words('english')) + r')\b\s*')
    document = pattern.sub('', document)
    document = word_tokenize(document, format="text")
    document = document.lower()
    document = re.sub(
        r'[^\s\wáàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệóòỏõọôốồổỗộơớờởỡợíìỉĩịúùủũụưứừửữựýỳỷỹỵđ_]', ' ', document)
    document = re.sub(r'\s+', ' ', document).strip()
    return document


for line in open('./data.txt', encoding="utf-8"):
    document = text_preprocess(line)
    words = document.strip().split(' ')
    label.append(words[0])
    words = words[1:]
    text.append(' '.join(words[0:]))
model = Pipeline([('vect', CountVectorizer(ngram_range=(1, 1),
                                           max_df=0.8,
                                           max_features=None)),
                  ('tfidf', TfidfTransformer()),
                  ('clf', MultinomialNB())
                  ])
model.fit(text, label)


def predict_category(s, label=label, model=model):
    s = text_preprocess(s)
    s = s.strip().split()
    pred = model.predict(s)
    return pred[0]


print(predict_category('science'))

sys.modules[__name__] == predict_category
