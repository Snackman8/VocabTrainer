""" code for the paneChooseQuiz
    this is hooked into by the appSinglePageAppPlugin
"""

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import datetime
import functools
import json
import model
import model_stats
from utils import inject_quiz_id_user_id


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def _validate_quiz_name(user_id, quiz_name):
    """ validate the quiz name

        Args:
            quiz_name - quiz name to validate

        Returns:
            None if no error, if error a string describing the error
    """
    quiz_name = quiz_name.strip()
    if quiz_name == '':
        return "Quiz name can not be empty!"

    quiz_ids = model.get_quiz_ids(user_id)
    quizzes = model.get_quizzes(quiz_ids, ['name', 'owner_user_id'])
    for q in quizzes.values():
        if (q['name'] == quiz_name) and q['owner_user_id'] == user_id:
            return f'A quiz you own with name of "{quiz_name}" already exists.  Edit the existing quiz instead.'

    return None


# --------------------------------------------------
#    Init
# --------------------------------------------------
@inject_quiz_id_user_id
def init_pane(jsc, quiz_id, user_id):
    """ called by the appSinglePageAppPlugin framework to handle initialization of this pane """
    quiz_ids = model.get_quiz_ids(None)
    quizzes = model.get_quizzes(quiz_ids, ['name', 'owner_user_name', 'owner_user_id'])

    # manually build the optgroups
    preferred_option_value = None
    html = '<optgroup label="Your quizzes">\n'
    for k, v in quizzes.items():
        if v['owner_user_id'] == user_id:
            html += f"""<option value={k}>{v['name']} ({v['owner_user_name']})</option>"""
            if preferred_option_value is None:
                preferred_option_value = k
    html += '<optgroup label="Other Quizzes">\n'
    for k, v in quizzes.items():
        if v['owner_user_id'] != user_id:
            html += f"""<option value={k}>{v['name']} ({v['owner_user_name']})</option>"""
            if preferred_option_value is None:
                preferred_option_value = k

    # set the option groups
    jsc['#select_quizzes_available'].html = html

    # select the appropriate item
    if jsc.tag.get('preferred_selected_quiz', None) in quizzes:
        preferred_option_value = jsc.tag['preferred_selected_quiz']
    if preferred_option_value:
        jsc.select_set_selected_options('#select_quizzes_available', preferred_option_value)

    # refresh the button states
    selectionChanged(jsc)

    if user_id is not None:
        jsc['#btn_New_Quiz'].prop.disabled = ''
        jsc['#btn_Delete_Quiz'].prop.disabled = ''
        jsc['#btn_Clear_Stats_For_Quiz'].prop.disabled = ''
    else:
        jsc['#btn_New_Quiz'].prop.disabled = 'true'
        jsc['#btn_Delete_Quiz'].prop.disabled = 'true'
        jsc['#btn_Clear_Stats_For_Quiz'].prop.disabled = 'true'

    # update the stats
    data = model_stats.get_quiz_scores(user_id)
    date_handler = lambda obj: (
        obj.isoformat()
        if isinstance(obj, (datetime.datetime, datetime.date))
        else None
    )
    json_data = json.dumps(data, default=date_handler)
    if user_id is None:
        display_name = 'Guest'
    else:
        display_name = model.get_user_props(user_id)['display_name']
    jsc['#quiz_scores_label'].html = 'Quiz Scores for ' + display_name
    jsc.eval_js_code(f"""populate_quiz_scores('{json_data}')""")

    # hide or show the alert
    jsc['#alert_login'].css.display = '' if user_id is None else 'none'

# --------------------------------------------------
#    Handler Functions
# --------------------------------------------------
@inject_quiz_id_user_id
def clearStatsForQuiz(jsc, quiz_id, user_id):
    """ handler for the Clear Stats For Quiz button.

        Remove stats for the given quiz / user
    """
    # show a modal confirming that the user really wants to delete the quiz
    jsc.modal_confirm(title="Clear Stats Confirmation",
                      body="Are you sure you want to clear the stats for this quiz? This can not be undone!",
                      callback="""onclick="call_py('paneChooseQuiz.clearStatsForQuizConfirmed')" """)


@inject_quiz_id_user_id
def clearStatsForQuizConfirmed(jsc, quiz_id, user_id):
    """ handler for after OK of clear stats for quiz has been clicked """
    model_stats.clearStatsForQuiz(quiz_id, user_id)
    jsc.show_pane('paneChooseQuiz')


@inject_quiz_id_user_id
def deleteQuiz(jsc, quiz_id, user_id):
    """ handler for Delete Quiz Button """
    # show an error message if the user is not the owner of the quiz
    if not model.is_quiz_owner(quiz_id, user_id):
        jsc.modal_alert(title='Action not allowed',
                        body='You can not delete this quiz because you are not the owner')
        return

    # show a modal confirming that the user really wants to delete the quiz
    jsc.modal_confirm(title="Delete Quiz Confirmation",
                      body="Are you sure you want to delete this quiz? This can not be undone!",
                      callback="""onclick="call_py('paneChooseQuiz.deleteQuizConfirmed')" """)


@inject_quiz_id_user_id
def deleteQuizConfirmed(jsc, quiz_id, user_id):
    """ handler for Delete Quiz OK Button """
    quiz = model.get_quiz(quiz_id)
    if quiz['owner_user_id'] != user_id:
        jsc.modal_alert(title='Action not allowed',
                        body='You can not delete this quiz because you are not the owner')
        return
    model.delete_quiz(quiz_id)
    jsc.show_pane('paneChooseQuiz')


@inject_quiz_id_user_id
def editQuiz(jsc, quiz_id, user_id):
    """ handler for Edit / View Quiz Button """
    # show the edit quiz pane
    jsc.show_pane('paneEditViewQuiz')


@inject_quiz_id_user_id
def newQuiz(jsc, quiz_id, user_id):
    """ handler New Quiz Button """
    # Show the modal to ask for a new quiz name
    jsc.modal_input(title='Type in the name of the new quiz below',
                    hint='New Quiz Name',
                    callback="""onclick="call_py('paneChooseQuiz.newQuizSave');" """)


@inject_quiz_id_user_id
def newQuizSave(jsc, quiz_id, user_id):
    """ handler New Quiz Save Button """
    # get the new quiz name
    new_quiz_name = jsc.modal_input_get_text().strip()

    # validate the quiz name
    quiz_name_problems = _validate_quiz_name(user_id, new_quiz_name)
    if quiz_name_problems is not None:
        jsc.modal_alert(title='Quiz name is not valid',
                        body=quiz_name_problems)
    else:
        # create the new quiz
        new_quiz_id = model.set_quiz(None, user_id, new_quiz_name, '')

        # show the quizzes available pane to repopulate the quiz selection box
        jsc.show_pane('paneChooseQuiz')

        # clear the selections and select the new quiz
        jsc.eval_js_code("""$("#select_quizzes_available").val([]);""")
        jsc.select_set_selected_options('#select_quizzes_available', new_quiz_id)
        jsc.tag['preferred_selected_quiz'] = new_quiz_id

        # finally, show the editing pane
        jsc.show_pane('paneEditViewQuiz')


@inject_quiz_id_user_id
def selectionChanged(jsc, quiz_id, user_id):
    """ handler for when the selection changes in the quiz list box """
    # save the newly selected item as the preferred option
    jsc.tag['preferred_selected_quiz'] = int(quiz_id) if quiz_id is not None else None

    # if we are in guest mode, disable new quiz button
    jsc['#btn_New_Quiz'].prop.disabled = {True: 'true', False: ''}[user_id is None]

    # if the user owns the selected quiz we can enable the edit and the delete
    if model.is_quiz_owner(quiz_id, user_id):
        jsc['#btn_Edit_Quiz'].html = 'Edit Quiz'
        jsc['#btn_Delete_Quiz'].prop.disabled = ''
    else:
        jsc['#btn_Edit_Quiz'].html = 'View Quiz'
        jsc['#btn_Delete_Quiz'].prop.disabled = 'true'

    # update the stats
    data = model_stats.get_quiz_question_stats(quiz_id, user_id)
    date_handler = lambda obj: (
        obj.isoformat()
        if isinstance(obj, (datetime.datetime, datetime.date))
        else None
    )
    json_data = json.dumps(data, default=date_handler)

    if user_id is None:
        display_name = 'Guest'
    else:
        display_name = model.get_user_props(user_id)['display_name']

    if quiz_id is not None:
        jsc['#quiz_stats_label'].html = 'Quiz Stats for ' + model.get_quiz(quiz_id)['name']
    json_data = json_data.replace("'", "\\'")
    jsc.eval_js_code(f"""populate_quiz_stats('{json_data}')""")


@inject_quiz_id_user_id
def startQuiz(jsc, quiz_id, user_id):
    """ handler for the Start Quiz Button """
    jsc.show_pane('paneTakingQuiz')


@inject_quiz_id_user_id
def startMiniQuiz(jsc, quiz_id, user_id):
    """ handler for the Start Mini Quiz Button """
    jsc.show_pane('paneTakingQuiz', mini_quiz=True)
