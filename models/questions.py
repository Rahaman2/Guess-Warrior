import csv
import random
import requests

class Questions:


    def __init__(self) -> None:
        # self.file_name = file_name
        # self.__parent_Folder = 'csv/'
        self.current_question = "no questions has been set"
        self.__current_question_list = []
        self.Score  = 0
        
        
    def __dictionary_initializer(self) -> dict:
        pass


    def __is_question_used(self, question:str) -> bool:
        
        return True

    def __initialize_question_list(self) -> list:
        pass
    
    def generate_question(self) -> str:
        """Gets a question from the csv file and returns it as a generated question"""
        with open(f'models/csv/questions.csv', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            chosen_row = random.randint(1, 1063)
            for i, row in enumerate(list(csv_reader)):
                if i == chosen_row:
                    print(f"Chose from row: {i}")
                    self.current_question = row[0]
                    self.__current_question_list = row
        return self.current_question

    

    def get_question(self) -> str:
        return self.current_question
    

    def question_dict(self) -> dict:
        """returns a dictionary mapping answer to score of the currently selected question"""    
        answers_and_scores =  self.__current_question_list[1:]
        print(self.current_question)
        question_dict = {}

        while len(answers_and_scores) > 0:
            question_dict[answers_and_scores[0]] = answers_and_scores[1]
            answers_and_scores.pop(0)
            answers_and_scores.pop(0)
        return question_dict
    


    def eval_user_answer(self, user_answer:str, answers:dict, question:str):
        """Checks sementics of answers"""

        url = "https://cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com/v1/chat/completions"
        prompt = ""

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": f"This is a family fued game. Your tasks is to compare the given answers (as a python dictionary) to the users given answer and see if they mean the same thing. If they mean the same thing your response should strictly be the matching answer from the list of answers I will provide (should match the key and not the the value of the dictionay) if it doesnt it should simply return the phrase (wrong answer) without the brackets . The functionality of the application, greatly depends on this feature so it is of utmost importance that you adhere to this. response should the the most likely matching answer only. Be considerate as possible in terms of matching answers. do not add a sentence or anything else. answers [ {answers}] users answer [{user_answer}] question [{question}]"
                }
            ],
            "model": "gpt-4-turbo-2024-04-09",
            "max_tokens": 100,
            "temperature": 0.9
        }
        headers = {
            "x-rapidapi-key": "10eff2ac28mshf1927d6a85dbf38p15fd16jsna437eba8f6c5",
            "x-rapidapi-host": "cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        answer_on_evaluation = response.json()["choices"][0]["message"]["content"]
        
        return answer_on_evaluation
        
        

    


# def run_game():
#     """runs the game"""
#     game_questions = Questions()

#     is_on = True
#     while(is_on):
#         question = game_questions.generate_question()
#         answers = game_questions.question_dict()
#         print(answers)   
#         answer = input("Enter your answer\n > ")
#         game_questions.eval_user_answer(answer, answers, question); 


# if __name__ == "__main__":
#     run_game()