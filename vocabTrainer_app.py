# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import logging
import os
import random
from pylinkjs.PyLinkJS import run_pylinkjs_app
from sphinx.config import correct_copyright_year


# --------------------------------------------------
#    Constants
# --------------------------------------------------
ARGS = {}           # ARGS is filled in in the main
PANE_IDS = ['']     # PANE_ID is filled in during the ready callback
QUESTIONS_REMAINING = []
QUESTIONS_ANSWERED_INCORRECTLY = set()
CORRECT = None
REMEDIAL = None
RUNNING_TOTAL = None



# --------------------------------------------------
#    Business Logic
# --------------------------------------------------
def _delete_quiz(quiz_id):
    """ delete a quiz

        Args:
            quiz_id - id of the quiz to delete
    """
    # delete quiz data
    quiz_path = os.path.join(ARGS['data_path'], 'quizzes', quiz_id)
    if os.path.exists(quiz_path):
        os.remove(quiz_path)


def _get_quizzes_available():
    """ return list of available quizzes """
    # load available quizzes from quiz dir
    quiz_dir = os.path.join(ARGS['data_path'], 'quizzes')
    return sorted(os.listdir(quiz_dir))


def _get_quiz_data(quiz_id):
    """ get quiz data

        Args:
            quiz_id - id of the quiz to retrieve data for.  If the quiz does not exist, empty data will be returned

        Returns:
            quiz data in string form, pipe delimited between question and answer, \n delimited between questions
    """
    # load quiz data
    quiz_path = os.path.join(ARGS['data_path'], 'quizzes', quiz_id)
    if os.path.exists(quiz_path):
        f = open(quiz_path, 'r')
        s = f.read()
        f.close()
    else:
        s = ''
    return s


def _set_quiz_data(quiz_id, data, no_verify=False):
    """ set quiz data

        Args:
            quiz_id - id of the quiz to save data for.  If the quiz exists, it will be overwritten
            data - data to save
            no_verify - if set to True, will skip verification
    """
    # validate quiz data
    if not no_verify:
        if _validate_quiz_data(data) is not None:
            raise Exception('Invalid Quiz Data!')

    # save quiz data
    quiz_path = os.path.join(ARGS['data_path'], 'quizzes', quiz_id)
    f = open(quiz_path, 'w')
    f.write(data)
    f.close()


def _validate_quiz_data(quiz_data):
    """ validate the quiz data

        Args:
            quiz_data - quiz data to validate

        Returns:
            None if no error, if error a string describing the error
    """
    if len(quiz_data.strip()) == 0:
        return "Quiz can not be empty"

    for i, x in enumerate(quiz_data.split('\n')):
        if x.strip() == '':
            continue
        if len(x.strip().split('|')) != 2:
            return f'Data on Row {i} did not contain a pipe (|)<br><br><pre><code>{x.strip()}</code></pre>'
    return None


def _validate_quiz_id(quiz_id):
    """ validate the quiz id

        Args:
            quiz_id - quiz id to validate

        Returns:
            None if no error, if error a string describing the error
    """
    if quiz_id.strip() == '':
        return "Quiz name can not be empty!"

    quiz_path = os.path.join(ARGS['data_path'], 'quizzes', quiz_id)
    if os.path.exists(quiz_path):
        return f'A quiz with name of "{quiz_id}" already exists.  Edit the existing quiz instead.'

    return None


# --------------------------------------------------
#    Widget Logic
# --------------------------------------------------
def _get_selected_quiz(jsc):
    """ helper function to return the selected quiz

        Args:
            jsc - jsclient context

        Returns:
            the value of the selected quiz
     """
    return jsc.select_get_selected_option('#select_quizzes_available')


def _init_pane(jsc, pane_id):
    """ initializes a pane before showing

        Args:
            jsc - jsclient context
            pane_id - id of the pane to initialize
    """
    # globals
    global QUESTIONS_REMAINING
    global QUESTIONS_ANSWERED_INCORRECTLY
    global CORRECT
    global RUNNING_TOTAL
    global REMEDIAL

    # pane_quizzes_available
    if pane_id == 'pane_quizzes_available':
        # remove all current quizzes available
        jsc.select_remove_all_options('#select_quizzes_available')

        # populate with all the quizzes available
        quizzes = _get_quizzes_available()
        if len(quizzes) > 0:
            for quiz_name in quizzes:
                jsc.select_add_option('#select_quizzes_available', quiz_name, quiz_name)
            jsc.select_set_selected_option('#select_quizzes_available', quizzes[0])

    # pane_quizzes_available
    if pane_id == 'pane_taking_quiz':
        # show the questions and answer card
        jsc['#QuestionAndAnswer'].css.display = 'block'
        jsc['#QuestionsFinished'].css.display = 'none'

        # get the selected quiz and the selected quiz data
        quiz_id = _get_selected_quiz(jsc)
        jsc['#taking_quiz_title'].html = quiz_id
        quiz_data = _get_quiz_data(quiz_id)

        # parse the quiz data
        lines = quiz_data.split('\n')
        random.shuffle(lines)
        QUESTIONS_REMAINING = []
        for x in lines:
            if not x.strip() == '':
                f = [xx.strip() for xx in x.split('|')]
                QUESTIONS_REMAINING.append(list(f))
        QUESTIONS_ANSWERED_INCORRECTLY = set()
        CORRECT = 0
        RUNNING_TOTAL = 0
        REMEDIAL = 0
        _next_question(jsc)

    # pane_quizzes_available
    if pane_id == 'pane_editing_quiz':
        # get the selected quiz
        quiz_id = _get_selected_quiz(jsc)
        quiz_data = _get_quiz_data(quiz_id)
        jsc['#editing_quiz_title'].html = f'Editing Quiz "{quiz_id}"'
        jsc['#quiz_textarea'].val = quiz_data


def _next_question(jsc):
    jsc['#question'].html = QUESTIONS_REMAINING[0][0]
    jsc['#answer'].val= ''

    # refresh the progress bar!
    _refresh_progress_bar(jsc)


def _refresh_progress_bar(jsc):
    pbar_total = CORRECT + len(QUESTIONS_REMAINING) + REMEDIAL
    jsc['#pbar_correct'].css.width = f'{int(CORRECT * 100 / pbar_total)}%'
    jsc['#pbar_correct'].html = CORRECT
    jsc['#pbar_remaining'].css.width = f'{int(len(QUESTIONS_REMAINING) * 100 / pbar_total)}%'
    jsc['#pbar_remaining'].html = len(QUESTIONS_REMAINING)
    jsc['#pbar_remedial'].css.width = f'{int(REMEDIAL * 100 / pbar_total)}%'
    jsc['#pbar_remedial'].html = REMEDIAL

    if RUNNING_TOTAL == 0:
        percentage = '0%'
    else:
        percentage = f'{int((CORRECT * 100.0 / RUNNING_TOTAL))}%'
    jsc['#progress_text'].html = f'<h3>{percentage}</h3>Progress ({len(QUESTIONS_REMAINING)} left, {CORRECT} correct, {RUNNING_TOTAL - CORRECT} wrong, {REMEDIAL} remedial)'



def _show_pane(jsc, pane_id):
    _init_pane(jsc, pane_id)

    for pid in PANE_IDS:
        if pid == pane_id:
            jsc.eval_js_code(f"""$('#{pid}').css('display', 'block')""")
        else:
            jsc.eval_js_code(f"""$('#{pid}').css('display', 'none')""")


# --------------------------------------------------
#    JS Handlers
# --------------------------------------------------
def btn_clicked(jsc, btn_id):
    # ===== start quiz =====
    if btn_id == 'start_selected_quiz':
        _show_pane(jsc, 'pane_taking_quiz')

    # ===== create quiz =====
    elif btn_id == 'create_new_quiz':
        # Show the modal to ask for a new quiz name
        jsc.eval_js_code("""$('#modal_create_new_quiz').modal('show')""")
    elif btn_id == 'create_new_quiz_save':
        # get the new quiz name
        new_quiz_id = jsc['#new_quiz_name'].val.strip()
        # validate the quiz name
        quiz_id_problems = _validate_quiz_id(new_quiz_id)
        if quiz_id_problems is not None:
            # show the error message if the quiz name did not pass validation
            jsc['#modal_create_new_quiz_problem_message'].html = quiz_id_problems
            jsc.eval_js_code("""$('#modal_create_new_quiz_problem').modal('show')""")
        else:
            # create the new quiz
            _set_quiz_data(new_quiz_id, '', no_verify=True)
            # show the quizzes available pane to repopulate the quiz selection box
            _show_pane(jsc, 'pane_quizzes_available')
            # clear the selections and select the new quiz
            jsc.eval_js_code("""$("#select_quizzes_available").val([]);""")
            jsc.select_set_selected_option('#select_quizzes_available', new_quiz_id)
            # finally, show the editing pane
            _show_pane(jsc, 'pane_editing_quiz')

    # ===== edit quiz =====
    elif btn_id == 'edit_selected_quiz':
        # show the edit quiz pane
        _show_pane(jsc, 'pane_editing_quiz')
    elif btn_id == 'edit_selected_quiz_cancelled':
        # edit quiz cancelled, show the quizzes available pane
        _show_pane(jsc, 'pane_quizzes_available')
    elif btn_id == 'edit_selected_quiz_save':
        # save the edited quiz
        new_quiz_data = jsc['#quiz_textarea'].val
        quiz_problems = _validate_quiz_data(new_quiz_data)
        if quiz_problems is not None:
            # show the problems with the quiz data
            jsc['#quiz_data_problem_message'].html = quiz_problems
            jsc.eval_js_code("""$('#modal_quiz_data_problem').modal('show')""")
        else:
            quiz_id = _get_selected_quiz(jsc)
            _set_quiz_data(quiz_id, new_quiz_data)
            _show_pane(jsc, 'pane_quizzes_available')

    # ===== delete quiz =====
    elif btn_id == 'delete_selected_quiz':
        _delete_quiz(_get_selected_quiz(jsc))
        _show_pane(jsc, 'pane_quizzes_available')


    # ===== taking quiz =====
    elif btn_id == 'quiz_finished':
        _show_pane(jsc, 'pane_quizzes_available')


def check_answer(jsc):
    # globals
    global CORRECT
    global RUNNING_TOTAL
    global REMEDIAL
    global QUESTIONS_REMAINING
    global QUESTIONS_ANSWERED_INCORRECTLY

    # get the answer
    user_answer =jsc['#answer'].val

    # check if the answer is correct
    question = QUESTIONS_REMAINING[0][0]
    answer = QUESTIONS_REMAINING[0][1]
    jsc['#alert'].html = answer
    if user_answer == QUESTIONS_REMAINING[0][1]:
        # answer is correct!

        # hide the alert
        jsc['#alert'].css.visibility = 'hidden'

        # delete the question from the QUESTIONS_REMAINING
        QUESTIONS_REMAINING.pop(0)

        # check if this is the first time we have seen this question
        if question not in QUESTIONS_ANSWERED_INCORRECTLY:
            logging.info('Correct the first time')
            CORRECT = CORRECT + 1
            RUNNING_TOTAL = RUNNING_TOTAL + 1
        else:
            # if there is only one instance of this question, then we can remove it from the remedials LIST
            if QUESTIONS_REMAINING.count([question, answer]) == 0:
                logging.info('Correct for remedial')
                REMEDIAL = REMEDIAL - 1
            else:
                logging.info('Correct for reinforcement')
    else:
        # answer is wrong!

        # show the alert
        jsc['#alert'].css.visibility = ''
        jsc['#alert'].html = f'<h3>Wrong!  {answer}</h3>'

        # check if we have answered this question wrong before
        if question not in QUESTIONS_ANSWERED_INCORRECTLY:
            # first time we have seen this wrong question, so we can increment the total
            RUNNING_TOTAL = RUNNING_TOTAL + 1
            REMEDIAL = REMEDIAL + 1
            logging.info(f'Wrong the first time RUNNING_TOTAL={RUNNING_TOTAL} REMEDIAL={REMEDIAL}')

        # add this question to the set of questions answered incorrectly
        QUESTIONS_ANSWERED_INCORRECTLY.add(question)

        # check if there are 2 of this question already int he QUESTIONS_REMAINING
        # if there are, the user is bombing this question so keep asking until they get it right
        if QUESTIONS_REMAINING.count([question, answer]) < 2:
            logging.info('Wrong for remedial')
            # randomize the QUESTIONS_REMAINING so the wrong question will be asked again
            random.shuffle(QUESTIONS_REMAINING)
            # add a duplicate of this question as the next question to reinforce
            QUESTIONS_REMAINING.insert(0, [question, answer])
        else:
            logging.info('Wrong for reinforcement')


    # refresh the progress bar
    _refresh_progress_bar(jsc)

    # check if we are done
    if len(QUESTIONS_REMAINING) != 0:
        _next_question(jsc)
    else:
        jsc['#QuestionAndAnswer'].css.display = 'none'
        jsc['#QuestionsFinished'].css.display = 'block'
        jsc['#Finished_Stats'].html = f"<center>Quiz Finished!<br><br>Final Score: {int((CORRECT * 100.0 / RUNNING_TOTAL))}%"

    # duno
    for x in QUESTIONS_REMAINING:
        logging.info(x)


def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    # global variables
    global PANE_IDS

    # retrieve name of all elements with ui_pane class
    PANE_IDS = jsc.eval_js_code("""$('.ui_pane').map(function() {return this.id}).get()""")

    # shwo the first pane
    _show_pane(jsc, 'pane_quizzes_available')


# --------------------------------------------------
#    Main
# --------------------------------------------------
def main(args):
    # globals
    global ARGS

    # init the args
    ARGS = args.copy()

    # default values
    ARGS['data_path'] = ARGS.get('data_path', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data'))

    # start the thread and the app
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    logging.info(ARGS)
    run_pylinkjs_app(default_html='vocabTrainer_main.html')


if __name__ == '__main__':
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbosity", help="increase output verbosity")
    args = parser.parse_args()
    args = vars(args)

    # run the main
    main(args)
