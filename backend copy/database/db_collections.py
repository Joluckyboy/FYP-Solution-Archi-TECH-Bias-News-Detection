from mongoengine import Document, StringField, IntField, DictField, ListField

# Define the schema for the collection
class NewsData(Document):
    url = StringField(required=True)
    title = StringField(required=False)
    content = StringField(required=False)

    sentiment_result = DictField(required=False)
    emotion_result = DictField(required=False)
    propaganda_result = DictField(required=False)
    factcheck_result = ListField(DictField(), required=False)
    summarise_result = StringField(required=False)
    data_summary = DictField(required=False)

class QuizData(Document):
    question = StringField(required=True)
    options = ListField(StringField(), required=True)
    answer = ListField(IntField(), required=False)
    question_type = StringField(required=True)
    debrief = StringField(required=False)
