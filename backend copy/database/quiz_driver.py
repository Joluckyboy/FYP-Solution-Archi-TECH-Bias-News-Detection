import mongoengine

from db_collections import QuizData
import vars as vars

import json

sample_quiz_data = {
    "question": "Which headline is biased? \\n A: 'Candidate X Crushes Opponent in Fiery Debate, Exposing Lies and Weak Policies.' \\n B: 'Candidate X and Y Debate Economic Policies in Heated Exchange.'",
    "options": ["A", "B", "Both"],
    "answer": [0]
}   

sample_quiz_data2 = {
    "question": "'If you love your country, you must support this new policy. Only true patriots stand with us!' Which propaganda technique is being used?",
    "options": ["Bandwagon Effect", "Fear Appeal", "Appeal to Patriotism", "Name-Calling"],
    "answer": [2]
}

mongoengine.connect(
    db="app",  # Replace with your database name
    host=vars.mongo_server
)

# add quiz data
def add_quiz_data(data):
    quiz = QuizData(**data)
    quiz.save()
    return str(quiz.id)

# get all quiz data
def get_all_quiz_data(question_type=None):
    quiz = None
    if question_type:
        quiz = QuizData.objects(question_type=question_type)
    else:
        quiz = QuizData.objects
    try:
        quiz_list = [json.loads(quiz_item.to_json()) for quiz_item in quiz]
        
        for item in quiz_list:
            if '_id' in item and '$oid' in item['_id']:
                item['id'] = item['_id']['$oid']
                del item['_id']
        return quiz_list
    except:
        return None
    
# get a number of random quiz data
def get_random_quiz_data(number, question_type=None):
    quiz = None
    if question_type:
        quiz = QuizData.objects(question_type=question_type).aggregate([{"$sample": {"size": number}}])
    else:
        quiz = QuizData.objects.aggregate([{"$sample": {"size": number}}])

    try:
        quiz_list = []
        for item in quiz:
            item['id'] = str(item.pop('_id'))
            quiz_list.append(item)
        return quiz_list
    except:
        return None