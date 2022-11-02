# --------------------------------------------------
#    Imports
# --------------------------------------------------
# standard
import argparse
import logging
# app
import model
from pylinkjs.PyLinkJS import run_pylinkjs_app
from pylinkjs.plugins.authGoogleOAuth2Plugin import pluginGoogleOAuth2
from pylinkjs.plugins.authDevAuthPlugin import pluginDevAuth
from pylinkjs.plugins.appSinglePageAppPlugin import pluginSinglePageApp
# panes
import paneLoading, paneChooseQuiz, paneEditViewQuiz, paneTakingQuiz


# --------------------------------------------------
#    JS Handlers
# --------------------------------------------------
def change_display_name(jsc):
    """ called when the change display name menu option is clicked """
    # retrieve the display name
    user_id = model.get_user_id(jsc.user_auth_username, jsc.user_auth_method)
    display_name = model.get_user_props(user_id)['display_name']

    # open the offcanvas
    jsc['#new_display_name'].val = display_name
    jsc.eval_js_code("""$("#new_display_name").removeClass("is-invalid")""")
    jsc.eval_js_code("""(new bootstrap.Offcanvas($('#offcanvasUpdateDisplayName').get(0))).show();""")
    jsc['#new_display_name_feedback'].html = f''


def change_display_name_ok(jsc):
    """ called when the change display name ok button is clicked """
    # retrieve the display name
    user_id = model.get_user_id(jsc.user_auth_username, jsc.user_auth_method)
    display_name = model.get_user_props(user_id)['display_name']
    
    # check if the new display_name is valid
    new_display_name = jsc['#new_display_name'].val.strip()
    if (new_display_name != display_name) and model.is_display_name_in_use(new_display_name):
        jsc.eval_js_code("""$("#new_display_name").addClass("is-invalid")""")
        jsc['#new_display_name_feedback'].html = f'{new_display_name} is not available'
        return
    else:
        # save
        model.set_user_prop(user_id, 'display_name', new_display_name)
        jsc.eval_js_code("""$('.offcanvas').offcanvas('hide');""")

        # update the display name
        display_name = new_display_name
        if display_name != jsc.user_auth_username:
            display_name = display_name + f" ({jsc.user_auth_username})"
        jsc['#userdropdown button span'].html = display_name
        
        # update the paneChooseQuiz to show the new display name
        jsc.show_pane('paneChooseQuiz')


def popstate(jsc, state, target):
    """ called when the webpage is transitioned to using the back or forward buttons on the browser.

        For single page apps, the state should be used to change the state of the page to mimic a back
        or forward button page movement

        Args:
            state - state of the page to transition to, i.e. "show_login"
            target - target url the page is transitioning to, i.e. "https://www.myapp.com/"
    """
    jsc.show_pane(state.get('pane'))


def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    # show login button or user dropdown
    if jsc.user_auth_username is not None:
        # retrieve the user
        user_id = model.get_user_id(jsc.user_auth_username, jsc.user_auth_method)
        if user_id is None:
            # create new user since this user does not exist
            # loop to avoid display_name collisions
            suffix = 0
            while True:
                display_name = jsc.user_auth_username.strip()
                if suffix != 0:
                    display_name = f"{display_name}{suffix}"
                suffix = suffix + 1
                try:
                    user_id = model.create_user(display_name, jsc.user_auth_username, jsc.user_auth_method)
                    break
                except model.DisplayNameExistsException:
                    pass

        # retrieve the display name
        display_name = model.get_user_props(user_id)['display_name']
        if display_name != jsc.user_auth_username:
            display_name = display_name + f" ({jsc.user_auth_username})"

        # show the correct dropdown
        jsc['#userdropdown'].css.display = 'block'
        jsc['#login_button'].css.display = 'none'
        jsc['#userdropdown button span'].html = display_name
        jsc['#btn_New_Quiz'].prop.disabled = ''
    else:
        jsc['#userdropdown'].css.display = 'none'
        jsc['#login_button'].css.display = 'block'
        jsc['#btn_New_Quiz'].prop.disabled = 'true'

    # disable the edit and delete buttons
    jsc['#btn_Delete_Quiz'].prop.disabled = 'true'

    # show the first pane
    jsc.show_pane('paneChooseQuiz')


def reconnect(jsc, *args):
    """ called if the client loses connection to the server and manages to reconnect """
    # reset to the first pane
    jsc.show_pane('paneChooseQuiz')


# --------------------------------------------------
#    Main
# --------------------------------------------------
def main(args):
    # init the args
    args = args.copy()

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
                                         redirect_url=f'{args["oauth2_redirect_url"]}:{port}/login')
    elif args['auth_method'] == 'DevAuth':
        auth_plugin = pluginDevAuth()

    # init as a single page app
    spa_plugin = pluginSinglePageApp(panes = [paneLoading, paneChooseQuiz, paneEditViewQuiz, paneTakingQuiz])

    # run the application
    run_pylinkjs_app(default_html='vocabTrainer_main.html',
                     port=port,
                     plugins=[auth_plugin, spa_plugin],
                     extra_settings=args)


if __name__ == '__main__':
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--auth_method', help='authentication method', choices=['GoogleOAuth2', 'DevAuth'], default='GoogleOAuth2')
    parser.add_argument('--oauth2_clientid', help='google oath2 client id')
    parser.add_argument('--oauth2_redirect_url', help='google oath2 redirect url', default='http://localhost')
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
