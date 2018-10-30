#IMPORTS
import os
import pandas as pd
from scipy import stats
from whoosh.analysis import *
import nltk
from nltk.stem import *
from collections import Counter

#SETTINGS
DIRECTORY = ""
OUTPUT_SPAM_LABELLED = os.path.join(DIRECTORY, "outputSpamLabelled.csv")

###functions to make:

#1 text preparation - reading in negative , cleaning, stemming, lemitizing,
# Make a new column and put it in there - may be a new function
def text_preparation ():
    feedbackCleaner = RegexTokenizer() | LowercaseFilter() | IntraWordFilter() \
                      | StopFilter() | StemFilter() | WordNetLemmatizer()

    num_records = 0

    survey_cols = ["Response", "ID", "Time", "Started", "Date Submitted",
                   "Status", "Language", "Referer", "Extended", "Referer", "User",
                   "Agent", "Extended", "User Agent", "Longitude", "Latitude",
                   "Country", "City", "State / Region", "Postal",
                   "Binary Sentiment", "OS", "Positive Feedback",
                   "Negative Feedback", "Relevant Site", "compound", "neg",
                   "neu", "pos", "Sites", "Issues", "Components", "Processed Feedback",
                   "IsSpam"]
    df = pd.read_csv(OUTPUT_SPAM_LABELLED, encoding="ISO-8859-1", nrows=num_records, usecols=survey_cols)
    print("Number of records to begin with: " + num_records)

    if df.empty: #need to handle empty case later
        print('DataFrame is empty!')
    else:
        print('Not empty!', df.shape)

    df['Output from spam_filter cleaning'] = df.apply(clean_feedback, axis=1)
    return df

def clean_feedback(df):
    feedbackCleaner = RegexTokenizer() | LowercaseFilter() | IntraWordFilter() \
                      | StopFilter() | StemFilter() | WordNetLemmatizer()
    for index, row in df.iterrows():
        combined = row['Positive Feedback'] + row['Negative Feedback']
        reprocessed = [token.text for token in feedbackCleaner(combined)]
    return ' '.join(set(reprocessed))

def get_top_words(df):
    tokenizer = RegexTokenizer()
    count = Counter()
    for index, row in df.iterrows():
        wordList = tokenizer.tokenize(row['Output from spam_filter cleaning'])
        count.update(wordList)
    finalWordList = [word for (word, freq) in count.most_common(2500)]
    return finalWordList

#2 feature extraction
def feature_extraction(df):
    tokenizer = RegexTokenizer()
    binary_appearance_df = []
    featureWords = get_top_words(df)
    for index, row in df.iterrows():
        wordList = tokenizer.tokenize(row['Output from spam_filter'])
        binary_appearance_df.append([1 if word in wordList else 0 for word in featureWords])
    X = pd.DataFrame(binary_appearance_df, columns=featureWords)
    return X

def get_qrel(df):
    qrel = []
    for index, row in df.iterrows():
        qrel.append(row['IsSpam'])
    y = pd.Dataframe(qrel)
    return y

#3 training the classifier + compute classifier accuracy on train/test
def train_spam_filter(X, y):
    ####CODE HERE
    k_train_results, k_test_results, classifier = k_cross_validate(X, y)

    # calculate the train mean and the 95% confidence interval for the list of results
    train_mean = np.mean(train_results)
    train_ci_low, train_ci_high = stats.t.interval(0.95, len(train_results) - 1, loc=train_mean,scale=stats.sem(train_results))

    # calculate the test mean and the 95% confidence interval for the list of results
    test_mean = np.mean(test_results)
    test_ci_low, test_ci_high = stats.t.interval(0.95, len(test_results) - 1, loc=test_mean, scale=stats.sem(test_results))
    return train_mean, train_ci_low, train_ci_high, test_mean, test_ci_low, test_ci_high

#3b k fold cross validation
def k_cross_validate(X, y, num_tests = 10):
    train_results = []
    test_results = []

    for i in range(num_tests):
        state = random.randint(1, 1000)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=state)
        clf = LogisticRegression(C=1.0).fit(X_train, y_train)
        y_train_predict = clf.predict(X_train)
        y_test_predict = clf.predict(X_test)
        train_accuracy = accuracy_score(y_train, y_train_predict)
        test_accuracy = accuracy_score(y_test, y_test_predict)
        train_results.append(train_accuracy)
        test_results.append(test_accuracy)

    return train_results, test_results, clf


