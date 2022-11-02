# --------------------------------------------------
#    Imports
# --------------------------------------------------
import model


# --------------------------------------------------
#    Functions
# --------------------------------------------------
def inject_quiz_id_user_id(func):
    """ decorator to inject quiz_id and user_id parameters """
    def wrapper(jsc, *args, **kwargs):
        user_id = model.get_user_id(jsc.user_auth_username, jsc.user_auth_method)
        try:
            quiz_id = jsc.select_get_selected_options('#select_quizzes_available')[0][0]
        except:
            quiz_id = None
        return func(jsc, quiz_id, user_id, *args, **kwargs)
    return wrapper
