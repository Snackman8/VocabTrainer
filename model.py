# --------------------------------------------------
#    Imports
# --------------------------------------------------
import os
from sqlalchemy import create_engine, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# ==================================================
#    Exceptions
# ==================================================
class DisplayNameExistsException(Exception):
    pass


class UserExistsException(Exception):
    pass


class UserNotFoundException(Exception):
    pass


# ==================================================
#    Model
# ==================================================
def create_user(display_name, auth_username, auth_method):
    """ create a new user

        Throws DisplayNameExistsException if the display name exists already
        Throws UserExistsEception if the auth_user_name and auth_method already exists for a user

        Args:
            display_name - display name for this new user, i.e. Bob
            auth_username - authentication user name, i.e user@example.com
            auth_method - authentication method, i.e. Google OAuth2

        Returns:
            user_id of the new user
    """
    # check if this user exists already
    if get_user_id(auth_username, auth_method) is not None:
        raise UserExistsException()

    # check if this displayname exists already
    if is_display_name_in_use(display_name):
        raise DisplayNameExistsException()

    # create the user
    session = Session()
    user = User(auth_username=auth_username, auth_method=auth_method)
    session.add(user)
    session.flush()
    user_id = get_user_id(auth_username, auth_method, session)

    # create the display name
    userprop = UserProps(user_id = user_id, key = 'display_name', value = display_name)
    session.add(userprop)
    session.commit()

    # success!
    return user_id


def get_user_props(user_id):
    """ return information about the user

        Args:
            user_id - user id of the user to return information on

        Returns:
            Dictionary with key being user_id, value is a dictionary of properties
    """
    # retrieve the users
    session = Session()

    # get properties
    retval = {}
    props = session.query(UserProps).filter(User.user_id == user_id)
    for p in props:
        retval[p.key] = p.value
    return retval


def get_user_id(auth_user_name, auth_method, session=None):
    """ retrieve the user id for a user

        Throws UserNotFound if the user does not exist

        Args:
            auth_user_name - authentication user name for the user
            auth_method - authentication method for the user
            session - use precreated session if provided, otherwise create a new session

        Returns:
            user id for the user
    """
    # retrieve the users
    if session is None:
        session = Session()
    users = session.query(User).filter(User.auth_username == auth_user_name, User.auth_method == auth_method)

    # sanity check
    if users.count() > 1:
        raise Exception(f"More than one user found for this username and authentication method ({auth_username}/{auth_nethod})")

    if users.count() == 0:
        return None

    # success!
    return users.first().user_id


# def get_quiz_ids(user_id):
#     """ retrieve list of quiz names available
#
#         Args:
#             user_id - if None, returns all quiz names, otherwise only the quizzes that are owned by user_id
#
#         Returns:
#             list of quiz_ids
#     """
#     pass
#
#
# def get_quizzes(quiz_ids, fields):
#     """ return information about each quiz in the list of quiz_ids
#
#         Args:
#             quiz_ids - list of quiz ids to return information for
#             fields - fields to return, ['owner', 'name', 'data'].  If none, returns all fields
#
#         Returns:
#             Dictionary with key being quiz_id, value is a dictionary of properties
#     """
#     pass


def is_display_name_in_use(display_name):
    session = Session()
    collisions = session.query(UserProps).filter(UserProps.key == 'display_name', UserProps.value == display_name)
    if collisions.count() != 0:
        return True
    return False


def set_user_prop(user_id, key, value):
    """ set a property for a user

        Args:
            user_id - user id of the user to set the property for
            key - key of the property to set
            value - value of the property to set
    """
    # retrieve the users
    session = Session()

    # verify user exists
    if session.query(User).filter(User.user_id == user_id).count() == 0:
        raise UserNotFound()

    # delete the existing property if it exsts
    userprops = session.query(UserProps).filter(UserProps.user_id == user_id, UserProps.key == key)
    userprops.delete()

    # create a new property
    userprop = UserProps(user_id=user_id, key=key, value=value)
    session.add(userprop)

    # commit
    session.commit()


# ==================================================
#    SQLAlchemy Implementation
# ==================================================
"""
    Create Record
    ==================================================
    session = Session()
    user = User(display_name='a', auth_username='b', auth_method='c')
    session.add(user)
    session.commit()

    Retrieve Record
    ==================================================
    session = Session()
    users = session.query(User).filter(User.auth_method == 'c')

    Update Record
    ==================================================
    session = Session()
    users = session.query(User).filter(User.auth_method == 'c')
    users.update({'display_name': 'xxx'})
    session.commit()

    Delete Record
    ==================================================
    session = Session()
    users = session.query(User).filter(User.auth_method == 'c')
    users.delete()
    session.commit()
"""


# --------------------------------------------------
#    Globals
# --------------------------------------------------
db_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'db')
db_path = os.path.join(db_dir, 'VocabTrainer.db')
Base = declarative_base()
engine = None
Session = None


# --------------------------------------------------
#    ORM Classes
# --------------------------------------------------
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    auth_username = Column(String)
    auth_method = Column(String)


    def __repr__(self):
        return '<User(' + ','.join([f"""{x}={getattr(self, x)}""" for x in ['user_id', 'auth_username', 'auth_method']]) + ')>'


class UserProps(Base):
    __tablename__ = "user_props"
    user_prop_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    key = Column(String)
    value = Column(String)

    def __repr__(self):
        return '<User(' + ','.join([f"""{x}={getattr(self, x)}""" for x in ['user_prop_id', 'user_id', 'key', 'value']]) + ')>'


# --------------------------------------------------
#    Init
# --------------------------------------------------
# create the database path
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# craete the engien and the Session class
engine = create_engine("sqlite:///" + db_path)
Session = sessionmaker(bind = engine)

# create tables
Base.metadata.create_all(engine)
