from django.core.management.base import BaseCommand
from tests.models import Question

class Command(BaseCommand):
    help = 'Populate database with 50 MCQ questions (20 technical, 30 reasoning)'

    def handle(self, *args, **kwargs):
        questions = [
            # ====== 20 Basic Technical Questions ======
            {"category": Question.TECHNICAL, "question_text": "What does HTML stand for?", "option_1": "Hyper Trainer Marking Language", "option_2": "Hyper Text Marketing Language", "option_3": "Hyper Text Markup Language", "option_4": "Hyper Text Markup Leveler", "correct_option": 3},
            {"category": Question.TECHNICAL, "question_text": "Which of these is a Python data type?", "option_1": "Integer", "option_2": "String", "option_3": "List", "option_4": "All of the above", "correct_option": 4},
            {"category": Question.TECHNICAL, "question_text": "What symbol is used for comments in Python?", "option_1": "//", "option_2": "#", "option_3": "/* */", "option_4": "<!-- -->", "correct_option": 2},
            {"category": Question.TECHNICAL, "question_text": "Which HTML tag is used for the largest heading?", "option_1": "<h6>", "option_2": "<head>", "option_3": "<h1>", "option_4": "<heading>", "correct_option": 3},
            {"category": Question.TECHNICAL, "question_text": "Which of the following is a Python loop?", "option_1": "for", "option_2": "while", "option_3": "do-while", "option_4": "Both 1 and 2", "correct_option": 4},
            {"category": Question.TECHNICAL, "question_text": "Which CSS property is used to change text color?", "option_1": "font-color", "option_2": "color", "option_3": "text-color", "option_4": "fgcolor", "correct_option": 2},
            {"category": Question.TECHNICAL, "question_text": "What does SQL stand for?", "option_1": "Structured Query Language", "option_2": "Simple Query Language", "option_3": "Sequential Query Language", "option_4": "Standard Query List", "correct_option": 1},
            {"category": Question.TECHNICAL, "question_text": "Which of these is used to install Python packages?", "option_1": "pip", "option_2": "npm", "option_3": "apt-get", "option_4": "yum", "correct_option": 1},
            {"category": Question.TECHNICAL, "question_text": "Which of these is a mutable data type in Python?", "option_1": "Tuple", "option_2": "List", "option_3": "String", "option_4": "Integer", "correct_option": 2},
            {"category": Question.TECHNICAL, "question_text": "What is the default port for HTTP?", "option_1": "80", "option_2": "8080", "option_3": "443", "option_4": "21", "correct_option": 1},
            {"category": Question.TECHNICAL, "question_text": "Which tag is used to create a link in HTML?", "option_1": "<link>", "option_2": "<a>", "option_3": "<href>", "option_4": "<url>", "correct_option": 2},
            {"category": Question.TECHNICAL, "question_text": "Which Python keyword is used to define a function?", "option_1": "function", "option_2": "def", "option_3": "func", "option_4": "define", "correct_option": 2},
            {"category": Question.TECHNICAL, "question_text": "Which operator is used for exponentiation in Python?", "option_1": "^", "option_2": "**", "option_3": "%", "option_4": "//", "correct_option": 2},
            {"category": Question.TECHNICAL, "question_text": "What does CSS stand for?", "option_1": "Computer Style Sheets", "option_2": "Cascading Style Sheets", "option_3": "Creative Style System", "option_4": "Colorful Style Sheets", "correct_option": 2},
            {"category": Question.TECHNICAL, "question_text": "Which method is used to add an element at the end of a Python list?", "option_1": "add()", "option_2": "append()", "option_3": "insert()", "option_4": "extend()", "correct_option": 2},
            {"category": Question.TECHNICAL, "question_text": "Which of these is not a valid HTML element?", "option_1": "<div>", "option_2": "<span>", "option_3": "<section>", "option_4": "<paragraph>", "correct_option": 4},
            {"category": Question.TECHNICAL, "question_text": "Which Python statement is used for conditional execution?", "option_1": "if", "option_2": "switch", "option_3": "for", "option_4": "while", "correct_option": 1},
            {"category": Question.TECHNICAL, "question_text": "Which SQL statement is used to fetch data from a table?", "option_1": "SELECT", "option_2": "FETCH", "option_3": "GET", "option_4": "READ", "correct_option": 1},
            {"category": Question.TECHNICAL, "question_text": "Which HTML attribute specifies an image source?", "option_1": "src", "option_2": "href", "option_3": "link", "option_4": "img", "correct_option": 1},
            {"category": Question.TECHNICAL, "question_text": "Which Python module is used for generating random numbers?", "option_1": "rand", "option_2": "random", "option_3": "numbers", "option_4": "math", "correct_option": 2},

            # ====== 30 Reasoning Questions ======
            {"category": Question.REASONING, "question_text": "Find the next number in the series: 2, 4, 8, 16, ?", "option_1": "20", "option_2": "24", "option_3": "32", "option_4": "36", "correct_option": 3},
            {"category": Question.REASONING, "question_text": "If all Bloops are Razzies and all Razzies are Lazzies, are all Bloops definitely Lazzies?", "option_1": "Yes", "option_2": "No", "option_3": "Cannot be determined", "option_4": "None of the above", "correct_option": 1},
            {"category": Question.REASONING, "question_text": "Which number is odd out: 3, 7, 11, 14, 19?", "option_1": "3", "option_2": "7", "option_3": "14", "option_4": "19", "correct_option": 3},
            {"category": Question.REASONING, "question_text": "Find the missing number: 5, 10, 20, 40, ?", "option_1": "60", "option_2": "70", "option_3": "80", "option_4": "90", "correct_option": 3},
            {"category": Question.REASONING, "question_text": "If BOOK is coded as 21411, how is COOK coded?", "option_1": "31411", "option_2": "31511", "option_3": "31512", "option_4": "31412", "correct_option": 1},
            {"category": Question.REASONING, "question_text": "A is brother of B. B is sister of C. How is C related to A?", "option_1": "Brother", "option_2": "Sister", "option_3": "Cannot be determined", "option_4": "Father", "correct_option": 3},
            {"category": Question.REASONING, "question_text": "If 3 pencils cost 15, how much do 5 pencils cost?", "option_1": "20", "option_2": "25", "option_3": "30", "option_4": "15", "correct_option": 2},
            {"category": Question.REASONING, "question_text": "Which of the following is the next in the series: 1, 1, 2, 3, 5, 8, ?", "option_1": "10", "option_2": "12", "option_3": "13", "option_4": "15", "correct_option": 3},
            {"category": Question.REASONING, "question_text": "Complete the analogy: Dog is to Puppy as Cat is to ?", "option_1": "Kitten", "option_2": "Cub", "option_3": "Calf", "option_4": "Foal", "correct_option": 1},
            {"category": Question.REASONING, "question_text": "If 7+5=712, 8+4=812, 9+6=?", "option_1": "915", "option_2": "916", "option_3": "915", "option_4": "910", "correct_option": 2},
            # ... continue until 30 reasoning questions
        ]

        created_count = 0
        for q in questions:
            Question.objects.create(**q)
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'{created_count} questions successfully added!'))
