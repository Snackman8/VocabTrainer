# --------------------------------------------------
#    Imports
# --------------------------------------------------
import datetime
import math
from enum import Enum
import pandas as pd
from model import engine, Base, Quiz, Session
from sqlalchemy import func, Boolean, Column, DateTime, ForeignKey, Integer, String


# ==================================================
#    Enumerations
# ==================================================
class ActivityId(Enum):
    QUIZ_START = 'QUIZ_START'
    QUIZ_START_MINI = 'QUIZ_START_MINI'
    QUIZ_END = 'QUIZ_END'
    QUIZ_QUESTION_CORRECT = 'QUIZ_QUESTION_CORRECT'
    QUIZ_QUESTION_INCORRECT = 'QUIZ_QUESTION_INCORRECT'


# ==================================================
#    Model
# ==================================================
def add_quiz_score(quiz_id, user_id, quiz_type, correct, total, elapsed_time, quiz_flipped):
    """ add a new quiz score for the user

        Args:
            quiz_id - id of the quiz to save the score for
            user_id - id of the user to save the score for
            correct - number of correct answers
            total - number of questions
            elapsed_time - total time for the quiz
            quiz_flipped - True if this is a flipped quiz, false otherwise
    """
    # special case for guest
    if user_id is None:
        user_id = 0

    session = Session()
    quiz_stat = QuizStat(quiz_id=quiz_id, user_id=user_id, stat_type='QUIZ_SCORE', key=quiz_type, value=f'{correct}/{total} {elapsed_time}', quiz_flipped=quiz_flipped)
    session.add(quiz_stat)
    session.commit()


def add_quiz_activity_stat(quiz_id, user_id, quiz_uid, question, activityId, quiz_flipped):
    """ add a new quiz question stat for the user

        Args:
            quiz_id - id of the quiz to save the stat for
            user_id - id of the user to save the stat for
            quiz_uid - uid of the current quiz being taken
            question - question to save state for
            activityId - See ActivityId enum
            quiz_flipped - True if this is a flipped quiz, false otherwise
    """
    # special case for guest
    if user_id is None:
        user_id = 0

    # add a new record
    session = Session()
    quiz_activity = QuizActivity(quiz_id=quiz_id, user_id=user_id, quiz_uid=quiz_uid, key=question, value=0, stat_type=activityId.value, quiz_flipped=quiz_flipped)
    session.add(quiz_activity)
    session.commit()


def add_quiz_question_stat(quiz_id, user_id, question, correct, quiz_flipped):
    """ add a new quiz question stat for the user

        Args:
            quiz_id - id of the quiz to save the stat for
            user_id - id of the user to save the stat for
            question - question to save state for
            correct - True if correct, False if not
            quiz_flipped - True if this is a flipped quiz, false otherwise
    """
    # special case for guest
    if user_id is None:
        user_id = 0

    # add a new record
    session = Session()
    quiz_stat = QuizStat(quiz_id=quiz_id, user_id=user_id, stat_type='QUIZ_QUESTION', key=question, value=f'{1 if correct else 0}', quiz_flipped=quiz_flipped)
    session.add(quiz_stat)
    session.commit()


def clearStatsForQuiz(quiz_id, user_id, quiz_flipped):
    """ handler for the Clear Stats For Quiz button.

        Remove stats for the given quiz / user
    """
    session = Session()
    quiz_stats = session.query(QuizStat).filter(QuizStat.user_id == user_id, QuizStat.quiz_id == quiz_id, QuizStat.stat_type=='QUIZ_QUESTION', quiz_flipped=quiz_flipped)
    quiz_stats.delete()
    session.commit()


def get_quiz_scores(user_id):
    """ return scores for a quiz by a user

        Args:
            user_id - id of the user to retrieve scores for

        Returns:
            list of dictionary of score results
    """
    # special case for guest
    if user_id is None:
        user_id = 0

    # query for records
    session = Session()
    quiz_scores = session.query(QuizStat, Quiz).join(QuizStat, Quiz.quiz_id == QuizStat.quiz_id).filter(QuizStat.user_id == user_id, QuizStat.stat_type=='QUIZ_SCORE').order_by(QuizStat.time_created.desc())

    # process results
    retval = []
    for r in quiz_scores.limit(10).all():
        elapsed_time = ''
        try:
            elapsed_time = int(r.QuizStat.value.partition(' ')[2])
            elapsed_time = str(math.ceil(elapsed_time / 60)) + ' mins'
            if elapsed_time == '1 mins':
                elapsed_time = '1 min'
        except:
            elapsed_time = ''

        d = {}
        d = {'name': r.Quiz.name,
             'quiz_type': r.QuizStat.key,
             'quiz_flipped': 'Flipped' if r.QuizStat.quiz_flipped else '',
             'time_created': r.QuizStat.time_created,
             'correct': int(r.QuizStat.value.partition(' ')[0].partition('/')[0]),
             'total': int(r.QuizStat.value.partition(' ')[0].partition('/')[2]),
             'elapsed_time': elapsed_time
             }
        d['percentage'] = 0
        try:
            d['percentage'] = round(d['correct'] / d['total'] * 100)
        except:
            pass
        retval.append(d)
    return retval


def get_quiz_question_stats(quiz_id, user_id, quiz_flipped):
    """ return scores for a quiz by a user

        Args:
            quiz_id - id of the quiz to retrieve scores for
            user_id - id of the user to retrieve scores for

        Returns:
            list of dictionary of score results
    """
    # special case for guest
    if user_id is None:
        user_id = 0

    # query for records
    session = Session()
    quiz_stats = session.query(QuizStat).filter(QuizStat.user_id == user_id, QuizStat.quiz_id == quiz_id, QuizStat.stat_type=='QUIZ_QUESTION', QuizStat.quiz_flipped==quiz_flipped)
    stats = {}
    for r in quiz_stats.all():
        if r.key not in stats:
            stats[r.key] = []
        stats[r.key].append(r)

    for k in stats:
        stats[k] = sorted(stats[k], key=lambda x: x.time_created)

    # process results
    retval = []
    for k in stats:
        d = {}
        d = {'question': k,
             'correct': sum([1 if x.value == '1' else 0 for x in stats[k][-5:]]),
             'total': len(stats[k][-5:])}
        d['percentage'] = 0
        try:
            d['percentage'] = round(d['correct'] / d['total'] * 100)
        except:
            pass
        retval.append(d)

    retval = sorted(retval, key=lambda x: (x['percentage'], x['question']))

    return retval


def bump_end_time(start_time, end_time):
    if start_time == end_time:
        return end_time + pd.Timedelta(seconds=30)
    else:
        return end_time


def get_user_activity(user_id):
    session = Session()
    start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=12)
    start_date = datetime.datetime(start_date.year, start_date.month, start_date.day, start_date.hour, start_date.minute, 0)
    end_date = start_date + datetime.timedelta(hours=12)
    if user_id is None:
        quiz_activity = session.query(QuizActivity, Quiz).join(QuizActivity, Quiz.quiz_id == QuizActivity.quiz_id).filter(QuizActivity.time_created >= start_date)
    else:
        quiz_activity = session.query(QuizActivity, Quiz).join(QuizActivity, Quiz.quiz_id == QuizActivity.quiz_id).filter(QuizActivity.user_id == user_id, QuizActivity.time_created >= start_date)

    data = []
    for qs in quiz_activity.all():
        d = datetime.datetime(qs.QuizActivity.time_created.year, qs.QuizActivity.time_created.month, qs.QuizActivity.time_created.day, qs.QuizActivity.time_created.hour, qs.QuizActivity.time_created.minute, 0)
        data.append([d, qs.QuizActivity.stat_type, qs.QuizActivity.quiz_uid, qs.Quiz.name])
        # time_created.append(d)
        # quiz_stat_type.append(qs.stat_type)
    df = pd.DataFrame(data, columns=['time_created', 'stat_type', 'quiz_uid', 'quiz_name'])
    df['time_created']= pd.to_datetime(df['time_created'])

    # compute the answers per minute
    df['activity'] = 1
    df_activity = df[df['stat_type'].isin(["QUIZ_QUESTION_CORRECT", "QUIZ_QUESTION_INCORRECT"])]
    ser = df_activity.groupby('time_created')['activity'].sum(numeric_only=True)
    ser = ser.sort_index()
    all_minutes_index = pd.date_range(start_date, end_date, freq='min')
    ser = ser.reindex(all_minutes_index, fill_value=0)

    # compute the quiz start and end times
    quiz_uids = df['quiz_uid'].unique()
    quiz_info = []
    for quid in quiz_uids:
        df2 = df[df['quiz_uid'] == quid]
        start = df2.iloc[0]
        end = df2.iloc[-1]

        quiz_name = start.quiz_name
        if start.stat_type == ActivityId.QUIZ_START_MINI.value:
            quiz_name = quiz_name + ' (M)'

        # scan for a break that is too long
        bad_end = None
        if ((df2['time_created'].shift(-1) - df2['time_created']) > pd.Timedelta(minutes=2)).any():
            bad_end = df2[(df2['time_created'].shift(-1) - df2['time_created']) > pd.Timedelta(minutes=2)].iloc[0]
            # append the good part of the quiz
            quiz_info.append([start.time_created, bump_end_time(start.time_created, bad_end.time_created), quiz_name, 'GOOD'])
            # append teh bad part of the quiz
            quiz_info.append([bad_end.time_created, bump_end_time(bad_end.time_created, end.time_created), '', 'BAD'])
        else:
            quiz_info.append([start.time_created, bump_end_time(start.time_created, end.time_created), quiz_name, 'GOOD'])

    return ser, quiz_info


# --------------------------------------------------
#    ORM Classes
# --------------------------------------------------
class QuizStat(Base):
    __tablename__ = "quiz_stats"
    quiz_stat_id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quiz.quiz_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    quiz_flipped = Column(Boolean)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
    stat_type = Column(String)
    key = Column(String)
    value = Column(String)

    def __repr__(self):
        return '<QuizStat(' + ','.join([f"""{x}={getattr(self, x)}""" for x in ['quiz_stat_id', 'quiz_id', 'user_id', 'stat_type', 'time_created', 'key', 'value']]) + ')>'


class QuizActivity(Base):
    __tablename__ = "quiz_activity"
    quiz_activity_id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quiz.quiz_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    quiz_uid = Column(Integer)
    quiz_flipped = Column(Boolean)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
    stat_type = Column(String)
    key = Column(String)
    value = Column(String)

    def __repr__(self):
        return '<QuizActivity(' + ','.join([f"""{x}={getattr(self, x)}""" for x in ['quiz_activity_id', 'quiz_id', 'user_id', 'quiz_uid', 'stat_type', 'time_created', 'key', 'value']]) + ')>'


# --------------------------------------------------
#    Init
# --------------------------------------------------
# create tables
Base.metadata.create_all(engine)

# ALTER TABLE quiz_activity ADD COLUMN quiz_flipped BOOLEAN NOT NULL DEFAULT 0;
# ALTER TABLE quiz_stats ADD COLUMN quiz_flipped BOOLEAN NOT NULL DEFAULT 0;
