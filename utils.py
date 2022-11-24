# --------------------------------------------------
#    Imports
# --------------------------------------------------
import model
import model_stats


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


def init_activity_chart(jsc, chart_name):
    options = {'type': 'line',
               'data': {
                   'labels': [''],
                   'datasets': [{
                       'label': 'x',
                       'data': [1]}]},
               'options': {
                   'scales': {
                       'xAxes': [{'type': 'time',
                                  'time': {
                                      'tooltipFormat': 'YYYY-MM-DD HH:mm',
                                      'displayFormats': {'minute': 'HH:mm'}
                                      },
                                  'ticks': {
                                      'minRotation': 30,
                                      'autoSkip': 1,
                                      'maxTicksLimit': 12}}],
                       'yAxes': [{'ticks': {'reverse': 0}}]
                       }
                   }
               }
    jsc.eval_js_code(f"""init_chart('{chart_name}', {options});""")

def refresh_activity_chart(jsc, chart_name, user_id):

    activity = model_stats.get_user_activity(user_id)


    data = {'labels': list(activity.index.strftime('%Y-%m-%d %H:%M:%S')),
            'datasets': [{
                'label': 'Answers / Min',
                'data': list(activity['activity']),
                'borderWidth': 1}]
            }

    jsc.eval_js_code(f"""update_chart('{chart_name}', {data});""")
