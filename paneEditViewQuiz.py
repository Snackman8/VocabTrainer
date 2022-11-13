""" code for the paneEditViewQuiz
    this is hooked into by the appSinglePageAppPlugin
"""

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import model
from utils import inject_quiz_id_user_id


# --------------------------------------------------
#    Functions
# --------------------------------------------------
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


# --------------------------------------------------
#    Init
# --------------------------------------------------
@inject_quiz_id_user_id
def init_pane(jsc, quiz_id, user_id):
    """ initialize the Edit / View Quiz Pane """
    # get the selected quiz
    quiz = model.get_quiz(quiz_id)

    # change the title to be editing or vieweing
    if quiz['owner_user_id'] == user_id:
        jsc['#paneEditViewQuiz .card-header'].html = f"""Editing Quiz "{quiz['name']}\""""
    else:
        jsc['#paneEditViewQuiz .card-header'].html = f"""Viewing Quiz "{quiz['name']}\""""

    # set the data for the quiz
    jsc['#paneEditViewQuiz textarea'].val = quiz['data']
    jsc['#chkCaseSensitive'].prop.checked = (quiz['flags'] & model.FLAG_CASE_SENSITIVE) != 0


    # disable the Save button if needed
    jsc['#paneEditViewQuiz button:contains("Save")'].prop.disabled = not model.is_quiz_owner(quiz_id, user_id)


# --------------------------------------------------
#    Handler Functions
# --------------------------------------------------
@inject_quiz_id_user_id
def cancelEdit(jsc, quiz_id, user_id):
    """ Handler for when the cancel button of the Edit / View Quiz Pane is clicked """
    jsc.show_pane('paneChooseQuiz')


@inject_quiz_id_user_id
def saveEdit(jsc, quiz_id, user_id):
    """ Handler for when the Save button of the Edit / View Quiz Pane is clicked """
    # save the edited quiz
    new_quiz_data = jsc['#paneEditViewQuiz textarea'].val
    flags = 0
    if jsc['#chkCaseSensitive'].prop.checked:
        flags = flags | model.FLAG_CASE_SENSITIVE
    quiz_problems = _validate_quiz_data(new_quiz_data)
    if quiz_problems is not None:
        # show the problems with the quiz data
        jsc.modal_alert(title='Quiz Data is not Valid',
                        body=quiz_problems)
    else:
        quiz = model.get_quiz(quiz_id)
        model.set_quiz(quiz_id, user_id, quiz['name'], new_quiz_data, flags=flags)
        jsc.show_pane('paneChooseQuiz')
