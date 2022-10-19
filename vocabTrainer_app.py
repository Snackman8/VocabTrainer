# --------------------------------------------------
#    Imports
# --------------------------------------------------
import argparse
import logging
import os
import random
import db
from pylinkjs.PyLinkJS import run_pylinkjs_app
from pylinkjs.plugins.authGoogleOAuth2Plugin import pluginGoogleOAuth2
from pylinkjs.plugins.authDevAuthPlugin import pluginDevAuth


# --------------------------------------------------
#    Business Logic
# --------------------------------------------------
def _delete_quiz(quiz_path, quiz_id):
    """ delete a quiz

        Args:
            quiz_path - path to quiz directory
            quiz_id - id of the quiz to delete
    """
    # delete quiz data
    quiz_path = os.path.join(quiz_path, quiz_id)
    if os.path.exists(quiz_path):
        os.remove(quiz_path)


def _get_quizzes_available(quiz_path):
    """ return list of available quizzes

        Args:
            quiz_path - path to quiz directory
    """
    # load available quizzes from quiz dir
    return sorted(os.listdir(quiz_path))


def _get_quiz_data(quiz_path, quiz_id):
    """ get quiz data

        Args:
            quiz_path - path to quiz directory
            quiz_id - id of the quiz to retrieve data for.  If the quiz does not exist, empty data will be returned

        Returns:
            quiz data in string form, pipe delimited between question and answer, \n delimited between questions
    """
    # load quiz data
    quiz_path = os.path.join(quiz_path, quiz_id)
    if os.path.exists(quiz_path):
        f = open(quiz_path, 'r')
        s = f.read()
        f.close()
    else:
        s = ''
    return s


def _set_quiz_data(quiz_path, quiz_id, data, no_verify=False):
    """ set quiz data

        Args:
            quiz_path - path to quiz directory
            quiz_id - id of the quiz to save data for.  If the quiz exists, it will be overwritten
            data - data to save
            no_verify - if set to True, will skip verification
    """
    # validate quiz data
    if not no_verify:
        if _validate_quiz_data(data) is not None:
            raise Exception('Invalid Quiz Data!')

    # save quiz data
    quiz_path = os.path.join(quiz_path, quiz_id)
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
            return f'Data on Row {i + 1} did not contain a pipe (|)<br><br><pre><code>{x.strip()}</code></pre>'
    return None


def _validate_quiz_id(quiz_path, quiz_id):
    """ validate the quiz id

        Args:
            quiz_path - path to quiz directory
            quiz_id - quiz id to validate

        Returns:
            None if no error, if error a string describing the error
    """
    if quiz_id.strip() == '':
        return "Quiz name can not be empty!"

    quiz_path = os.path.join(quiz_path, 'quizzes', quiz_id)
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
    # return the value of the first selected option
    return jsc.select_get_selected_options('#select_quizzes_available')[0][0]


def _init_pane(jsc, pane_id, **kwargs):
    """ initializes a pane before showing

        Args:
            jsc - jsclient context
            pane_id - id of the pane to initialize
    """
    # pane_quizzes_available
    if pane_id == 'pane_quizzes_available':
        # load the quiz ids as the options and select the first item
        quizzes = _get_quizzes_available(jsc.tag['quiz_path'])
        quiz_options = [list(x) for x in zip(quizzes, quizzes)]
        jsc.select_set_options('#select_quizzes_available', quiz_options)
        jsc.select_set_selected_options('#select_quizzes_available', quizzes[0])

    # pane_quizzes_available
    if pane_id == 'pane_taking_quiz':
        # show the questions and answer card
        jsc['#QuestionAndAnswer'].css.display = 'block'
        jsc['#QuestionsFinished'].css.display = 'none'

        # get the selected quiz and the selected quiz data
        quiz_id = _get_selected_quiz(jsc)
        jsc['#taking_quiz_title'].html = quiz_id
        quiz_data = _get_quiz_data(jsc.tag['quiz_path'], quiz_id)

        # parse the quiz data
        lines = quiz_data.split('\n')
        random.shuffle(lines)

        # chop for mini quiz
        if 'questions' in kwargs:
            lines = lines[:kwargs['questions']]

        jsc.tag['QUESTIONS_REMAINING'] = []
        for x in lines:
            if not x.strip() == '':
                f = [xx.strip() for xx in x.split('|')]
                jsc.tag['QUESTIONS_REMAINING'].append(list(f))
        jsc.tag["QUESTIONS_ANSWERED_INCORRECTLY"] = set()
        jsc.tag["CORRECT"] = 0
        jsc.tag["RUNNING_TOTAL"] = 0
        jsc.tag["REMEDIAL"] = 0
        _next_question(jsc)

    # pane_quizzes_available
    if pane_id == 'pane_editing_quiz':
        # get the selected quiz
        quiz_id = _get_selected_quiz(jsc)
        quiz_data = _get_quiz_data(jsc.tag['quiz_path'], quiz_id)
        jsc['#editing_quiz_title'].html = f'Editing Quiz "{quiz_id}"'
        jsc['#quiz_textarea'].val = quiz_data


def _next_question(jsc):
    jsc['#question'].html = jsc.tag["QUESTIONS_REMAINING"][0][0]
    jsc['#answer'].val= ''

    # refresh the progress bar!
    _refresh_progress_bar(jsc)


def _refresh_progress_bar(jsc):
    pbar_total = jsc.tag["CORRECT"] + len(jsc.tag["QUESTIONS_REMAINING"]) + jsc.tag["REMEDIAL"]
    jsc['#pbar_correct'].css.width = f'{int(jsc.tag["CORRECT"] * 100 / pbar_total)}%'
    jsc['#pbar_correct'].html = jsc.tag["CORRECT"]
    jsc['#pbar_remaining'].css.width = f'{int(len(jsc.tag["QUESTIONS_REMAINING"]) * 100 / pbar_total)}%'
    jsc['#pbar_remaining'].html = len(jsc.tag["QUESTIONS_REMAINING"])
    jsc['#pbar_remedial'].css.width = f'{int(jsc.tag["REMEDIAL"] * 100 / pbar_total)}%'
    jsc['#pbar_remedial'].html = jsc.tag["REMEDIAL"]

    if jsc.tag["RUNNING_TOTAL"] == 0:
        percentage = '0%'
    else:
        percentage = f'{int((jsc.tag["CORRECT"] * 100.0 / jsc.tag["RUNNING_TOTAL"]))}%'
    jsc['#progress_text'].html = f'<h3>{percentage}</h3>Progress ({len(jsc.tag["QUESTIONS_REMAINING"])} left, {jsc.tag["CORRECT"]} correct, {jsc.tag["RUNNING_TOTAL"] - jsc.tag["CORRECT"]} wrong, {jsc.tag["REMEDIAL"]} remedial)'



def _show_pane(jsc, pane_id, **kwargs):
    _init_pane(jsc, pane_id, **kwargs)

    for pid in jsc.tag['PANE_IDS']:
        if pid == pane_id:
            jsc.eval_js_code(f"""$('#{pid}').css('display', 'block')""")
        else:
            jsc.eval_js_code(f"""$('#{pid}').css('display', 'none')""")

    # change the history state since this is a Single Page App
    jsc.eval_js_code(f"""history.pushState({{'pane': '{pane_id}'}}, '', '/')""")


# --------------------------------------------------
#    JS Handlers
# --------------------------------------------------
def btn_clicked_change_display_name(jsc, btn_id):
    # retrieve the display name
    session = db.Session()
    users = session.query(db.User).filter(db.User.auth_username == jsc.user_name, db.User.auth_method == jsc.user_auth_method)
    display_name = users.first().display_name

    # open the offcanvas
    jsc['#new_display_name'].val = display_name
    jsc.eval_js_code("""(new bootstrap.Offcanvas($('#offcanvasUpdateDisplayName').get(0))).show();""")


def btn_clicked(jsc, btn_id):
    # ===== start quiz =====
    if btn_id == 'start_selected_quiz':
        _show_pane(jsc, 'pane_taking_quiz')
    elif btn_id == 'start_mini_quiz_10':
        _show_pane(jsc, 'pane_taking_quiz', questions=10)
    elif btn_id == 'start_mini_quiz_20':
        _show_pane(jsc, 'pane_taking_quiz', questions=20)

    # ===== create quiz =====
    elif btn_id == 'create_new_quiz':
        # Show the modal to ask for a new quiz name
        jsc.modal_input(title='Type in the name of the new quiz below',
                        hint='New Quiz Name',
                        callback="""onclick="call_py('btn_clicked', 'create_new_quiz_save');" """)

    elif btn_id == 'create_new_quiz_save':
        # get the new quiz name
        new_quiz_id = jsc.modal_input_get_text()

        # validate the quiz name
        quiz_id_problems = _validate_quiz_id(new_quiz_id)
        if quiz_id_problems is not None:
            jsc.modal_alert(title='Quiz name is not valid',
                            body=quiz_id_problems)
        else:
            # create the new quiz
            _set_quiz_data(jsc.tag['quiz_path'], new_quiz_id, '', no_verify=True)
            # show the quizzes available pane to repopulate the quiz selection box
            _show_pane(jsc, 'pane_quizzes_available')
            # clear the selections and select the new quiz
            jsc.eval_js_code("""$("#select_quizzes_available").val([]);""")
            jsc.select_set_selected_options('#select_quizzes_available', new_quiz_id)
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
            jsc.modal_alert(title='Quiz Data is not Valid',
                            body=quiz_problems)
        else:
            quiz_id = _get_selected_quiz(jsc)
            _set_quiz_data(jsc.tag['quiz_path'], quiz_id, new_quiz_data)
            _show_pane(jsc, 'pane_quizzes_available')

    # ===== delete quiz =====
    elif btn_id == 'delete_selected_quiz':
        # show a modal confirming that the user really wants to delete the quiz
        jsc.modal_confirm(title="Delete Quiz Confirmation",
                          body="Are you sure you want to delete this quiz? This can not be undone!",
                          callback="""onclick="call_py('btn_clicked', 'delete_selected_quiz_confirmed')" """)

    elif btn_id == 'delete_selected_quiz_confirmed':
        _delete_quiz(jsc.tag['quiz_path'], _get_selected_quiz(jsc))
        _show_pane(jsc, 'pane_quizzes_available')

    # ===== taking quiz =====
    elif btn_id == 'quiz_finished':
        _show_pane(jsc, 'pane_quizzes_available')


def check_answer(jsc):
    # get the answer
    user_answer =jsc['#answer'].val

    # check if the answer is correct
    question = jsc.tag["QUESTIONS_REMAINING"][0][0]
    answer = jsc.tag["QUESTIONS_REMAINING"][0][1]
    jsc['#alert'].html = answer
    if user_answer == jsc.tag["QUESTIONS_REMAINING"][0][1]:
        # answer is correct!

        # hide the alert
        jsc['#alert'].css.visibility = 'hidden'

        # delete the question from the QUESTIONS_REMAINING
        jsc.tag["QUESTIONS_REMAINING"].pop(0)

        # check if this is the first time we have seen this question
        if question not in jsc.tag["QUESTIONS_ANSWERED_INCORRECTLY"]:
            logging.info('Correct the first time')
            jsc.tag["CORRECT"] = jsc.tag["CORRECT"] + 1
            jsc.tag["RUNNING_TOTAL"] = jsc.tag["RUNNING_TOTAL"] + 1
        else:
            # if there is only one instance of this question, then we can remove it from the remedials LIST
            if jsc.tag["QUESTIONS_REMAINING"].count([question, answer]) == 0:
                logging.info('Correct for remedial')
                jsc.tag["REMEDIAL"] = jsc.tag["REMEDIAL"] - 1
            else:
                logging.info('Correct for reinforcement')
    else:
        # answer is wrong!

        # show the alert
        jsc['#alert'].css.visibility = ''
        jsc['#alert'].html = f'<h3>Wrong!  {answer}</h3>'

        # check if we have answered this question wrong before
        if question not in jsc.tag["QUESTIONS_ANSWERED_INCORRECTLY"]:
            # first time we have seen this wrong question, so we can increment the total
            jsc.tag["RUNNING_TOTAL"] = jsc.tag["RUNNING_TOTAL"] + 1
            jsc.tag["REMEDIAL"] = jsc.tag["REMEDIAL"] + 1
            logging.info(f'Wrong the first time RUNNING_TOTAL={jsc.tag["RUNNING_TOTAL"]} REMEDIAL={jsc.tag["REMEDIAL"]}')

        # add this question to the set of questions answered incorrectly
        jsc.tag["QUESTIONS_ANSWERED_INCORRECTLY"].add(question)

        # check if there are 2 of this question already int he QUESTIONS_REMAINING
        # if there are, the user is bombing this question so keep asking until they get it right
        if jsc.tag["QUESTIONS_REMAINING"].count([question, answer]) < 2:
            logging.info('Wrong for remedial')
            # randomize the QUESTIONS_REMAINING so the wrong question will be asked again
            random.shuffle(jsc.tag["QUESTIONS_REMAINING"])
            # add a duplicate of this question as the next question to reinforce
            jsc.tag["QUESTIONS_REMAINING"].insert(0, [question, answer])
        else:
            logging.info('Wrong for reinforcement')


    # refresh the progress bar
    _refresh_progress_bar(jsc)

    # check if we are done
    if len(jsc.tag["QUESTIONS_REMAINING"]) != 0:
        _next_question(jsc)
    else:
        jsc['#QuestionAndAnswer'].css.display = 'none'
        jsc['#QuestionsFinished'].css.display = 'block'
        jsc['#Finished_Stats'].html = f"<center>Quiz Finished!<br><br>Final Score: {int((jsc.tag['CORRECT'] * 100.0 / jsc.tag['RUNNING_TOTAL']))}%"


def popstate(jsc, state, target):
    """ called when the webpage is transitioned to using the back or forward buttons on the browser.

        For single page apps, the state should be used to change the state of the page to mimic a back
        or forward button page movement

        Args:
            state - state of the page to transition to, i.e. "show_login"
            target - target url the page is transitioning to, i.e. "https://www.myapp.com/"
    """
    _show_pane(jsc, state.get('pane'))


def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    # retrieve name of all elements with ui_pane class
    jsc.tag['PANE_IDS'] = jsc.eval_js_code("""$('.ui_pane').map(function() {return this.id}).get()""")

    # show login button or user dropdown
    if jsc.user_name is not None:
        # add this user to the database if needed
        session = db.Session()
        users = session.query(db.User).filter(db.User.auth_username == jsc.user_name, db.User.auth_method == jsc.user_auth_method)
        if users.count() == 0:
            user = db.User(display_name=jsc.user_name, auth_username=jsc.user_name, auth_method=jsc.user_auth_method)
            session.add(user)
            session.commit()

        # retrieve the display name
        users = session.query(db.User).filter(db.User.auth_username == jsc.user_name, db.User.auth_method == jsc.user_auth_method)
        display_name = users.first().display_name
        if display_name != jsc.user_name:
            display_name = display_name + f" ({jsc.user_name})"

        # show the correct dropdown
        jsc['#userdropdown'].css.display = 'block'
        jsc['#login_button'].css.display = 'none'
        jsc['#userdropdown button span'].html = display_name
    else:
        jsc['#userdropdown'].css.display = 'none'
        jsc['#login_button'].css.display = 'block'

    # shwo the first pane
    _show_pane(jsc, 'pane_quizzes_available')


# --------------------------------------------------
#    Main
# --------------------------------------------------
def main(args):
    # init the args
    args = args.copy()

    # default values
    args['data_path'] = args.get('data_path', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data'))
    args['quiz_path'] = args.get('quiz_path', os.path.join(args['data_path'], 'quizzes'))

    # start the thread and the app
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    logging.info(args)

    # default port
    port = 8300

    # init the auth method
    if args['auth_method'] == 'GoogleOAuth2':
        # init the google oauth2 plugin
        auth_plugin = pluginGoogleOAuth2(client_id=args['oauth2_clientid'],
                                         secret=args['oauth2_secret'],
                                         port=port)
    elif args['auth_method'] == 'DevAuth':
        auth_plugin = pluginDevAuth()

    # run the application
    run_pylinkjs_app(default_html='vocabTrainer_main.html',
                     port=port,
                     plugins=[auth_plugin],
                     extra_settings=args)


if __name__ == '__main__':
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--auth_method', help='authentication method', choices=['GoogleOAuth2', 'DevAuth'], default='GoogleOAuth2')
    parser.add_argument('--oauth2_clientid', help='google oath2 client id')
    parser.add_argument('--oauth2_secret', help='google oath2 secret')
    parser.add_argument("--verbosity", help="increase output verbosity")
    args = parser.parse_args()
    args = vars(args)

    # sanity check
    if args['auth_method'] == 'GoogleOAuth2':
        if (args['oauth2_clientid'] is None) or (args['oauth2_secret'] is None):
            parser.error("auth_method of GoogleOAuth2 requires --oauth2_clientid and --oauth2_secret")

    # run the main
    main(args)
