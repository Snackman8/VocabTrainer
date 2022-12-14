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


def refresh_activity_chart(jsc, chart_name, user_id):

    activity, quiz_info = model_stats.get_user_activity(user_id)

    options = {'type': 'line',
               'data': {
                   'labels': list(activity.index.strftime('%Y-%m-%d %H:%M:%S')),
                   'datasets': [{
                       'label': 'Answers / Min',
                       'data': list(activity),
                       'borderColor': '#55bae7',
                       'backgroundColor': '#55bae7',
                       'pointBackgroundColor': "#55bae7",
                       'pointBorderColor': "#55bae7",
                       'pointHoverBackgroundColor': "#55bae7",
                       'pointHoverBorderColor': "#55bae7",
                       'pointRadius': 4,
                       'borderWidth': 2}]},
               'options': {
                   'animation': {'duration': 0},
                   'scales': {
                       'xAxis': {'type': 'time',
                                 'time': {
                                     'tooltipFormat': 'YYYY-MM-DD HH:mm',
                                     'displayFormats': {'minute': 'HH:mm', 'second': 'HH:mm'}},
                                 'min': list(activity.index.strftime('%Y-%m-%d %H:%M:%S'))[-120],
                                 'grid': {'display': 1,
                                          'color': 'rgba(230, 230, 230, 0.5)'},
                                 'ticks': {
                                     'autoSkip': 1,
                                     'maxTicksLimit': 12}},
                       'yAxis': {'min': 0,
                                 'grid': {'display': 1,
                                          'color': 'rgba(230, 230, 230, 0.5)'},
                                 'ticks': {'reverse': 0,
                                           'beginAtZero': 1,
                                           'stepSize': 1}}
                       },
                   'plugins': {
                       'autocolors': 0,
                       'annotation': {},
                    'zoom': {
                        'limits': {'x': {'min': list(activity.index.strftime('%Y-%m-%d %H:%M:%S'))[0],
                                         'max': list(activity.index.strftime('%Y-%m-%d %H:%M:%S'))[-1]}},
                        'pan': {'mode': 'x', 'enabled': 1},
                        'zoom': {'mode': 'x', 'wheel': {'enabled': 1,}},
                        }
                    }
                   }
               }

    annotations = {}
    for i, qi in enumerate(quiz_info):
        if qi[3] == 'GOOD':
            if i % 2:
                background_color = 'rgba(64, 64, 200, 0.25)'
            else:
                background_color = 'rgba(64, 200, 64, 0.25)'


            annotations[f'box{i}'] = {'type': 'box',
                                      'xMin': qi[0].strftime('%Y-%m-%d %H:%M:%S'),
                                      'xMax': qi[1].strftime('%Y-%m-%d %H:%M:%S'),
                                      'backgroundColor': background_color,
                                      'borderWidth': 0,
                                      'label': {'content': qi[2], 'display': 1, 'rotation': -90,
                                                'font': {'size': 12}}}
        else:
            annotations[f'box{i}'] = {'type': 'box',
                                      'xMin': qi[0].strftime('%Y-%m-%d %H:%M:%S'),
                                      'xMax': qi[1].strftime('%Y-%m-%d %H:%M:%S'),
                                      'yMin': 0,
                                      'yMax': 1,
                                      'backgroundColor': 'rgba(255, 0, 0, 0.25)',
                                      'borderWidth': 0}

    options['options']['plugins']['annotation']['annotations'] = annotations

    jsc.eval_js_code(f"""update_chart('{chart_name}', {options});""")
