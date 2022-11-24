""" code for the paneTakingQuiz
    this is hooked into by the appSinglePageAppPlugin
"""

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import logging
import random
import sys
import model
import model_stats
import random
from utils import inject_quiz_id_user_id, refresh_activity_chart


# --------------------------------------------------
#    Functions
# --------------------------------------------------
@inject_quiz_id_user_id
def check_answer(jsc, quiz_id, user_id):
    """
        checks if the answer in the UI is correct for the question.  Also updates the metrics

        Internal logic

        if correct:
            * pop from stack
            if this question was not previously wrong:
                @ CORRECT++
            else:
                @ REMEDIAL--

        if wrong:
            * append to end of stack
            if this question was not previously wrong:
                @ WRONG++
                @ REMEDIAL++
            * add to previously wrong set
            @ REMEDIAL++
    """
    # get the answer
    user_answer =jsc['#answer'].val

    # check if the answer is correct
    question = jsc.tag["QUESTIONS_REMAINING"][0][0]
    answer = jsc.tag["QUESTIONS_REMAINING"][0][1]
    jsc['#alert'].html = answer

    # check for correctness based on flags
    correct = False
    if jsc.tag["QUIZ_FLAGS"] & model.FLAG_CASE_SENSITIVE:
        correct = user_answer.strip() == jsc.tag["QUESTIONS_REMAINING"][0][1].strip()
    else:
        correct = user_answer.strip().lower() == jsc.tag["QUESTIONS_REMAINING"][0][1].strip().lower()

    # handle correct or incorrect
    if correct:
        # answer is correct, so hide the alert
        jsc['#alert'].css.visibility = 'hidden'

        # delete the question from the QUESTIONS_REMAINING
        jsc.tag["QUESTIONS_REMAINING"].pop(0)

        # check if this is the first time we have seen this question
        if question not in jsc.tag["QUESTIONS_ANSWERED_INCORRECTLY"]:
            logging.info('Correct the first time')
            jsc.tag["CORRECT"] = jsc.tag["CORRECT"] + 1

            # update the stats
            model_stats.add_quiz_question_stat(quiz_id, user_id, question, correct=True)
        else:
            jsc.tag["REMEDIAL"] = jsc.tag["REMEDIAL"] - 1

        # update activity stats
        model_stats.add_quiz_activity_stat(quiz_id, user_id, jsc.tag['QUIZ_UID'], question, model_stats.ActivityId.QUIZ_QUESTION_CORRECT)                
    else:
        # answer is wrong, so show the alert
        jsc['#alert'].css.visibility = ''
        jsc['#alert'].html = f'Incorrect!  {answer}<br>Your Answer: {user_answer}'

        # add another copy of this question to the end of the stack
        jsc.tag['QUESTIONS_REMAINING'].append([question, answer])

        # check if we have answered this question wrong before
        if question not in jsc.tag["QUESTIONS_ANSWERED_INCORRECTLY"]:
            # first time we have seen this wrong question, so we can increment the total
            jsc.tag["WRONG"] = jsc.tag["WRONG"] + 1
            jsc.tag["REMEDIAL"] = jsc.tag["REMEDIAL"] + 1

        # update the stats
        model_stats.add_quiz_question_stat(quiz_id, user_id, question, correct=False)

        # add this question to the set of questions answered incorrectly
        jsc.tag["QUESTIONS_ANSWERED_INCORRECTLY"].add(question)
        jsc.tag["REMEDIAL"] = jsc.tag["REMEDIAL"] + 1

        # update activity stats
        model_stats.add_quiz_activity_stat(quiz_id, user_id, jsc.tag['QUIZ_UID'], question, model_stats.ActivityId.QUIZ_QUESTION_INCORRECT)                

    # refresh the progress bar
    refresh_progress_bar(jsc)

    # check if we are done
    if len(jsc.tag["QUESTIONS_REMAINING"]) != 0:
        next_question(jsc)
    else:
        running_total = jsc.tag["CORRECT"] + jsc.tag["WRONG"]
        jsc['#QuestionAndAnswer'].css.display = 'none'
        jsc['#QuestionsFinished'].css.display = 'block'
        jsc['#Finished_Stats'].html = f"<center>Quiz Finished!<br><br>Final Score: {int((jsc.tag['CORRECT'] * 100.0 / running_total))}%"

        # update the stats
        model_stats.add_quiz_score(quiz_id, user_id, jsc.tag['QUIZ_TYPE'], jsc.tag['CORRECT'], jsc.tag['CORRECT'] + jsc.tag['WRONG'])
        model_stats.add_quiz_activity_stat(quiz_id, user_id, jsc.tag['QUIZ_UID'], '', model_stats.ActivityId.QUIZ_END)        

    # refresh the activity chart    
    refresh_activity_chart(jsc, 'activitychart_taking', user_id)


def next_question(jsc):
    """ setup the UI to show the next question """
    jsc['#question'].html = jsc.tag["QUESTIONS_REMAINING"][0][0]
    jsc['#answer'].val= ''
    jsc['#btn_skip'].html = f'Skip ({jsc.tag["SKIPS_LEFT"]})'
    if jsc.tag["SKIPS_LEFT"] > 0:
        jsc['#btn_skip'].prop.disabled = ''
    else:
        jsc['#btn_skip'].prop.disabled = 'true'

    # refresh the progress bar!
    refresh_progress_bar(jsc)


def refresh_progress_bar(jsc):
    """ refresh the progress bar to show the current metrics """
    pbar_total = jsc.tag["CORRECT"] + jsc.tag["WRONG"] + len(jsc.tag['QUESTIONS_REMAINING'])
    jsc['#pbar_correct'].css.width = f'{int(jsc.tag["CORRECT"] * 100 / pbar_total)}%'
    jsc['#pbar_correct'].html = jsc.tag["CORRECT"]
    jsc['#pbar_remaining'].css.width = f'{int(len(jsc.tag["QUESTIONS_REMAINING"]) * 100 / pbar_total)}%'
    jsc['#pbar_remaining'].html = len(jsc.tag["QUESTIONS_REMAINING"])
    jsc['#pbar_remedial'].css.width = f'{int(jsc.tag["REMEDIAL"] * 100 / pbar_total)}%'
    jsc['#pbar_remedial'].html = jsc.tag["REMEDIAL"]

    running_total = jsc.tag["CORRECT"] + jsc.tag["WRONG"]
    if running_total == 0:
        percentage = '0%'
    else:
        percentage = f'{int((jsc.tag["CORRECT"] * 100.0 / running_total))}%'
    jsc['#progress_text'].html = f'<h3>{percentage}</h3>Progress ({len(jsc.tag["QUESTIONS_REMAINING"])} left, {jsc.tag["CORRECT"]} correct, {jsc.tag["WRONG"]} wrong, {jsc.tag["REMEDIAL"]} remedial)'

    # special case if we are done
    if len(jsc.tag['QUESTIONS_REMAINING']) == 0:
        jsc['#pbar_remedial'].css.width = f'{int(jsc.tag["WRONG"] * 100 / pbar_total)}%'
        jsc['#pbar_remedial'].html = jsc.tag["WRONG"]


# --------------------------------------------------
#    Handler Functions
# --------------------------------------------------
@inject_quiz_id_user_id
def init_pane(jsc, quiz_id, user_id, **kwargs):
    # init the activity chart    
    refresh_activity_chart(jsc, 'activitychart_taking', user_id)
    
    # init a quiz_uid
    jsc.tag['QUIZ_UID'] = random.randint(0, sys.maxsize)
    
    # show the questions and answer card
    jsc['#QuestionAndAnswer'].css.display = 'block'
    jsc['#QuestionsFinished'].css.display = 'none'
    jsc['#alert'].css.visibility = 'hidden'

    # get the selected quiz and the selected quiz data
    quiz = model.get_quiz(quiz_id)
    jsc['#paneTakingQuiz h5'].html = 'Taking Quiz ' + quiz['name']
    quiz_data = quiz['data']

    # parse the quiz data
    lines = quiz_data.split('\n')

    # chop for mini quiz
    jsc.tag['QUIZ_TYPE'] = ''
    if kwargs.get('mini_quiz', False):
        jsc.tag['QUIZ_TYPE'] = 'Mini'
        data = {}
        for x in lines:
            if not x.strip() == '':
                data[x.split('|')[0].strip()] = x

        quiz_stats = model_stats.get_quiz_question_stats(quiz_id, user_id)

        # find questions we have no stats for
        data_no_stats = dict(data)
        for stat in quiz_stats:
            if stat['question'] in data_no_stats:
                del data_no_stats[stat['question']]

        # load questions with no stats first
        mini_quiz_lines = {}
        for k, v in data_no_stats.items():
            if len(mini_quiz_lines) >= 5:
                break
            if k not in mini_quiz_lines:
                print('Adding question because no stats', k)
                mini_quiz_lines[k] = v

        # then load questions with bad stats
        for stat in quiz_stats:
            if len(mini_quiz_lines) >= 5:
                break
            if stat['question'] in data:
                print('Adding question because bad stat', stat['question'])
                mini_quiz_lines[stat['question']] = data[stat['question']]
        lines = list(mini_quiz_lines.values())

    # error if there are no questions
    if len(lines) == 0:
        jsc.show_pane('paneChooseQuiz')
        raise Exception('Error!  There are no questions for this quiz')

    # shuffle the lines
    random.shuffle(lines)

    jsc.tag['QUESTIONS_REMAINING'] = []
    for x in lines:
        if not x.strip() == '':
            f = [xx.strip() for xx in x.split('|')]
            jsc.tag['QUESTIONS_REMAINING'].append(list(f))
    jsc.tag["QUESTIONS_ANSWERED_INCORRECTLY"] = set()
    jsc.tag["CORRECT"] = 0
    jsc.tag["WRONG"] = 0
    jsc.tag["REMEDIAL"] = 0
    jsc.tag["QUIZ_FLAGS"] = quiz['flags']
    jsc.tag["SKIPS_LEFT"] = max(1, int(len(jsc.tag['QUESTIONS_REMAINING']) / 25))

    # start the quiz stat
    if jsc.tag['QUIZ_TYPE'] == 'Mini':
        model_stats.add_quiz_activity_stat(quiz_id, user_id, jsc.tag['QUIZ_UID'], '', model_stats.ActivityId.QUIZ_START_MINI)
    else:
        model_stats.add_quiz_activity_stat(quiz_id, user_id, jsc.tag['QUIZ_UID'], '', model_stats.ActivityId.QUIZ_START)

    # call next question to show the first question
    next_question(jsc)


@inject_quiz_id_user_id
def finished(jsc, quiz_id, user_id):
    """ handler for the OK button shown when the quiz is finished """
    jsc.show_pane('paneChooseQuiz')


@inject_quiz_id_user_id
def skip(jsc, quiz_id, user_id, **kwargs):
    jsc.tag["SKIPS_LEFT"] = jsc.tag["SKIPS_LEFT"] - 1
    q = jsc.tag['QUESTIONS_REMAINING'].pop(0)
    jsc.tag['QUESTIONS_REMAINING'].append(q)
    next_question(jsc)
