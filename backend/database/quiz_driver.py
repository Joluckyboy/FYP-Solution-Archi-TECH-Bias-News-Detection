from supabase_client import get_supabase_client
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

# Get Supabase client
supabase = get_supabase_client()

# add quiz data
def add_quiz_data(data):
    """Add a new quiz question to Supabase."""
    try:
        result = supabase.table("quiz_data").insert(data).execute()
        if result.data:
            return str(result.data[0]["id"])
        return None
    except Exception as e:
        print(f"Error adding quiz data: {e}")
        return None

# get all quiz data
def get_all_quiz_data(question_type=None):
    """Get all quiz questions, optionally filtered by question_type."""
    try:
        query = supabase.table("quiz_data").select("*")

        if question_type:
            query = query.eq("question_type", question_type)

        result = query.execute()

        # Transform data to match expected format
        quiz_list = []
        for item in result.data:
            quiz_item = {
                "id": str(item["id"]),
                "question": item["question"],
                "options": item["options"],
                "answer": item.get("answer"),
                "question_type": item["question_type"],
                "debrief": item.get("debrief")
            }
            quiz_list.append(quiz_item)

        return quiz_list
    except Exception as e:
        print(f"Error getting all quiz data: {e}")
        return None

# get a number of random quiz data
def get_random_quiz_data(number, question_type=None):
    """Get random quiz questions from Supabase."""
    try:
        # Note: Supabase doesn't have a direct random function in the Python client
        # We'll fetch all and then randomly select in Python
        query = supabase.table("quiz_data").select("*")

        if question_type:
            query = query.eq("question_type", question_type)

        result = query.execute()

        # Randomly sample the required number
        import random
        all_quiz = result.data

        if len(all_quiz) <= number:
            sampled_quiz = all_quiz
        else:
            sampled_quiz = random.sample(all_quiz, number)

        # Transform data to match expected format
        quiz_list = []
        for item in sampled_quiz:
            quiz_item = {
                "id": str(item["id"]),
                "question": item["question"],
                "options": item["options"],
                "answer": item.get("answer"),
                "question_type": item["question_type"],
                "debrief": item.get("debrief")
            }
            quiz_list.append(quiz_item)

        return quiz_list
    except Exception as e:
        print(f"Error getting random quiz data: {e}")
        return None
