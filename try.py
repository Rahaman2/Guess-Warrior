import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet

def preprocess(text):
    # Tokenize the text and lowercase all tokens
    tokens = word_tokenize(text.lower())
    return tokens

def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower())
    return synonyms

def check_similarity(answer, valid_answer):
    # Preprocess both answers
    answer_tokens = preprocess(answer)
    valid_tokens = preprocess(valid_answer)

    # Check if any token in the answer is a synonym of any token in the valid answer
    for token in answer_tokens:
        synonyms = get_synonyms(token)
        if valid_tokens.intersection(synonyms):
            return True
    return False

# Example question and valid answer
question = "Name A Place Where A Mom Might Go When She Says, ” I Need Peace And Quiet.”"
valid_answer = "Take A Bath"

# User's input
user_input = "take a shower"

# Check similarity
if check_similarity(user_input, valid_answer):
    print("Correct! The accepted answer is:", valid_answer)
else:
    print("Sorry, the answer is incorrect.")
