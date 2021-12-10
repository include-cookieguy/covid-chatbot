from sklearn.naive_bayes import MultinomialNB
import seaborn as sns; sns.set()
from nltk.tokenize import word_tokenize
import nltk
from nltk.corpus import stopwords
import re
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

vec = DictVectorizer()
text = []
label = []
def remove_html(txt):
    return re.sub(r'<[^>]*>', '', txt)
def text_preprocess(document):
    document = remove_html(document)
    pattern = re.compile(r'\b(' + r'|'.join(stopwords.words('english')) + r')\b\s*')
    document = pattern.sub('', document)
    document = word_tokenize(document)
    document = ' '.join(document[0:])
    document = document.lower()
    document = re.sub(r'[^\s\wáàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệóòỏõọôốồổỗộơớờởỡợíìỉĩịúùủũụưứừửữựýỳỷỹỵđ_]',' ',document)
    document = re.sub(r'\s+', ' ', document).strip()
    return document
for line in open('.\data.txt', encoding="utf-8"):
    document = text_preprocess(line)
    # print(document)
    words = document.strip().split(' ')
    label.append(words[0])
    words = words[1:]
    text.append(' '.join(words[0:]))
model_1 = Pipeline([('vect', CountVectorizer(ngram_range=(1,1),
                                             max_df=0.8,
                                             max_features=None)),
                     ('tfidf', TfidfTransformer()),
                     ('clf', MultinomialNB())
                    ])
model_1.fit(text, label)

model_2 = Pipeline([('vect', CountVectorizer(ngram_range=(1,1),
                                             max_df=0.8,
                                             max_features=None)),
                     ('tfidf', TfidfTransformer()),
                     ('clf', SVC(gamma='scale'))
                    ])
model_2.fit(text, label)

model_3 = Pipeline([('vect', CountVectorizer(ngram_range=(1,1),
                                             max_df=0.8,
                                             max_features=None)),
                     ('tfidf', TfidfTransformer()),
                     ('clf', LogisticRegression(solver='lbfgs', 
                                                multi_class='auto',
                                                max_iter=10000))
                    ])
model_3.fit(text, label)

def predict_category(s, label=label, model_1=model_1, model_2=model_2, model_3=model_3):
    s = text_preprocess(s)
    pred_1 = model_1.predict([s])
    pred_2 = model_2.predict([s])
    pred_3 = model_3.predict([s])
    print(pred_1[0], pred_2[0], pred_3[0])
    return pred_2[0]