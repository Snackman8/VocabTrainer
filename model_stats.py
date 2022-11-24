# --------------------------------------------------
#    Imports
# --------------------------------------------------
import datetime
import pandas as pd
from model import engine, Base, Quiz, Session
from sqlalchemy import func, Column, DateTime, ForeignKey, Integer, String


# ==================================================
#    Model
# ==================================================
def add_quiz_score(quiz_id, user_id, quiz_type, correct, total):
    """ add a new quiz score for the user

        Args:
            quiz_id - id of the quiz to save the score for
            user_id - id of the user to save the score for
            correct - number of correct answers
            total - number of questions
    """
    # special case for guest
    if user_id is None:
        user_id = 0

    session = Session()
    quiz_stat = QuizStat(quiz_id=quiz_id, user_id=user_id, stat_type='QUIZ_SCORE', key=quiz_type, value=f'{correct}/{total}')
    session.add(quiz_stat)
    session.commit()


def add_quiz_question_stat(quiz_id, user_id, question, correct):
    """ add a new quiz question stat for the user

        Args:
            quiz_id - id of the quiz to save the stat for
            user_id - id of the user to save the stat for
            question - question to save state for
            correct - True if correct, False if not
    """
    # special case for guest
    if user_id is None:
        user_id = 0

    # add a new record
    session = Session()
    quiz_stat = QuizStat(quiz_id=quiz_id, user_id=user_id, stat_type='QUIZ_QUESTION', key=question, value=f'{1 if correct else 0}')
    session.add(quiz_stat)
    session.commit()


def clearStatsForQuiz(quiz_id, user_id):
    """ handler for the Clear Stats For Quiz button.

        Remove stats for the given quiz / user
    """
    session = Session()
    quiz_stats = session.query(QuizStat).filter(QuizStat.user_id == user_id, QuizStat.quiz_id == quiz_id, QuizStat.stat_type=='QUIZ_QUESTION')
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
        d = {}
        d = {'name': r.Quiz.name,
             'quiz_type': r.QuizStat.key,
             'time_created': r.QuizStat.time_created,
             'correct': int(r.QuizStat.value.partition('/')[0]),
             'total': int(r.QuizStat.value.partition('/')[2]),
             }
        d['percentage'] = 0
        try:
            d['percentage'] = round(d['correct'] / d['total'] * 100)
        except:
            pass
        retval.append(d)
    return retval


def get_quiz_question_stats(quiz_id, user_id):
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
    quiz_stats = session.query(QuizStat).filter(QuizStat.user_id == user_id, QuizStat.quiz_id == quiz_id, QuizStat.stat_type=='QUIZ_QUESTION')
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


def get_user_activity(user_id):
    session = Session()
    start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3)
    start_date = datetime.datetime(start_date.year, start_date.month, start_date.day, start_date.hour, start_date.minute, 0)
    end_date = start_date + datetime.timedelta(hours=3, minutes=1)
    if user_id is None:
        quiz_stats = session.query(QuizStat).filter(QuizStat.stat_type=='QUIZ_QUESTION', QuizStat.time_created >= start_date)
    else: 
        quiz_stats = session.query(QuizStat).filter(QuizStat.user_id == user_id, QuizStat.stat_type=='QUIZ_QUESTION',
                                                    QuizStat.time_created >= start_date)
    time_created = []
    for qs in quiz_stats.all():
        d = datetime.datetime(qs.time_created.year, qs.time_created.month, qs.time_created.day, qs.time_created.hour, qs.time_created.minute, 0)
        time_created.append(d)
    df = pd.DataFrame(time_created, columns=['time_created'])
    df['time_created']= pd.to_datetime(df['time_created'])
    df['activity'] = 1
    ser = df.groupby('time_created').sum()
    ser = ser.sort_index()
    all_minutes_index = pd.date_range(start_date, end_date, freq='min')
    ser = ser.reindex(all_minutes_index, fill_value=0)
    
    return ser
    

# --------------------------------------------------
#    ORM Classes
# --------------------------------------------------
class QuizStat(Base):
    __tablename__ = "quiz_stats"
    quiz_stat_id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quiz.quiz_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
    stat_type = Column(String)
    key = Column(String)
    value = Column(String)

    def __repr__(self):
        return '<QuizStat(' + ','.join([f"""{x}={getattr(self, x)}""" for x in ['quiz_stat_id', 'quiz_id', 'user_id', 'stat_type', 'time_created', 'key', 'value']]) + ')>'


# --------------------------------------------------
#    Init
# --------------------------------------------------
# create tables
Base.metadata.create_all(engine)
