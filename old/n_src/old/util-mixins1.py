from datetime import datetime
from typing import List

import sqlalchemy as sa
from sqlalchemy import inspect, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import String, Text
from sqlalchemy_utils import TSVectorType
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import TSVectorType
from sqlalchemy.sql import func
from sqlalchemy import inspect, event
from sqlalchemy.types import String, Text
from datetime import datetime, timedelta
from statistics import mean, median, mode, stdev
from collections import Counter

# Work across both SQLAlchemy 1.x and 2.0
try:
    # SQLAlchemy 2.0
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    SQLALCHEMY_2 = True
except ImportError:
    # SQLAlchemy 1.x
    from sqlalchemy.ext.declarative import declared_attr
    SQLALCHEMY_2 = False

class UtilMixinBase:
    @classmethod
    def create_table(cls, table_name, *args, **kwargs):
        if inspect(sa.engine).has_table(table_name):
            return
        table = sa.Table(table_name, sa.MetaData(), *args, **kwargs)
        table.create(sa.engine)

class TagMixin(UtilMixinBase):
    @declared_attr
    def __tablename__(cls):
        return f"{cls.__name__.lower()}_tags"

    @classmethod
    def __declare_last__(cls):
        if not hasattr(cls, 'nx_tags'):
            cls.create_table('nx_tags',
                sa.Column('id', sa.Integer, primary_key=True),
                sa.Column('name', sa.String(50), unique=True, nullable=False)
            )
            
            cls.create_table(cls.__tablename__,
                sa.Column('id', sa.Integer, primary_key=True),
                sa.Column('tag_id', sa.Integer, sa.ForeignKey('nx_tags.id')),
                sa.Column('record_id', sa.Integer, sa.ForeignKey(f'{cls.__tablename__}.id'))
            )

        if SQLALCHEMY_2:
            cls.tags: Mapped[List['NxTag']] = relationship('NxTag', secondary=cls.__tablename__, backref='tagged_records')
        else:
            cls.tags = relationship('NxTag', secondary=cls.__tablename__, backref='tagged_records')

    @classmethod
    def find_by_tag(cls, session, tag_name):
        return session.query(cls).join(cls.tags).filter(NxTag.name == tag_name).all()





class RateMixin(UtilMixinBase):
    @declared_attr
    def __tablename__(cls):
        return f"{cls.__name__.lower()}_rates"

    @classmethod
    def __declare_last__(cls):
        cls.create_table(cls.__tablename__,
                         sa.Column('id', sa.Integer, primary_key=True),
                         sa.Column('record_id', sa.Integer, sa.ForeignKey(f'{cls.__tablename__}.id')),
                         sa.Column('user_id', sa.Integer, sa.ForeignKey('ab_user.id')),
                         sa.Column('rate', sa.Integer),
                         sa.Column('comment', sa.Text),
                         sa.Column('created_at', sa.DateTime, default=datetime.utcnow)
                         )

        if SQLALCHEMY_2:
            cls.rates: Mapped[List['Rate']] = relationship('Rate', backref='rated_record')
        else:
            cls.rates = relationship('Rate', backref='rated_record')

    @hybrid_property
    def average_rate(self):
        return mean(rate.rate for rate in self.rates) if self.rates else 0

    @hybrid_property
    def min_rate(self):
        return min(rate.rate for rate in self.rates) if self.rates else None

    @hybrid_property
    def max_rate(self):
        return max(rate.rate for rate in self.rates) if self.rates else None

    @hybrid_property
    def median_rate(self):
        return median(rate.rate for rate in self.rates) if self.rates else None

    @hybrid_property
    def mode_rate(self):
        return mode(rate.rate for rate in self.rates) if self.rates else None

    @hybrid_property
    def rate_std_dev(self):
        return stdev(rate.rate for rate in self.rates) if len(self.rates) > 1 else 0

    @hybrid_property
    def total_rates(self):
        return len(self.rates)

    def get_rate_distribution(self):
        rates = [rate.rate for rate in self.rates]
        return dict(Counter(rates))

    def get_rate_trend(self, days=30):
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        trend = {}
        for rate in self.rates:
            if start_date <= rate.created_at <= end_date:
                date_key = rate.created_at.date()
                if date_key in trend:
                    trend[date_key].append(rate.rate)
                else:
                    trend[date_key] = [rate.rate]

        return {date: mean(rates) for date, rates in trend.items()}

    def get_recent_comments(self, limit=5):
        return sorted(
            [(rate.comment, rate.created_at) for rate in self.rates if rate.comment],
            key=lambda x: x[1],
            reverse=True
        )[:limit]

    def get_sentiment_analysis(self):
        # This is a placeholder. In a real-world scenario, you'd use a NLP library
        # like NLTK or a service like AWS Comprehend for sentiment analysis
        positive_words = set(['good', 'great', 'excellent', 'amazing', 'love'])
        negative_words = set(['bad', 'poor', 'terrible', 'awful', 'hate'])

        sentiments = {'positive': 0, 'negative': 0, 'neutral': 0}

        for rate in self.rates:
            if rate.comment:
                words = set(rate.comment.lower().split())
                if words & positive_words:
                    sentiments['positive'] += 1
                elif words & negative_words:
                    sentiments['negative'] += 1
                else:
                    sentiments['neutral'] += 1

        return sentiments

    @classmethod
    def get_top_rated(cls, session, limit=10):
        return session.query(cls).order_by(cls.average_rate.desc()).limit(limit).all()

    @classmethod
    def get_most_reviewed(cls, session, limit=10):
        return session.query(cls).order_by(cls.total_rates.desc()).limit(limit).all()


class Rate(DeclarativeBase if SQLALCHEMY_2 else object):
    __tablename__ = 'rates'

    if SQLALCHEMY_2:
        id: Mapped[int] = mapped_column(primary_key=True)
        rate: Mapped[int] = mapped_column(sa.Integer)
        comment: Mapped[str] = mapped_column(sa.Text, nullable=True)
        created_at: Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.utcnow)
    else:
        id = sa.Column(sa.Integer, primary_key=True)
        rate = sa.Column(sa.Integer)
        comment = sa.Column(sa.Text, nullable=True)
        created_at = sa.Column(sa.DateTime, default=datetime.utcnow)




class CommentMixin(UtilMixinBase):
    @declared_attr
    def __tablename__(cls):
        return f"{cls.__name__.lower()}_comments"

    @classmethod
    def __declare_last__(cls):
        cls.create_table(cls.__tablename__,
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('record_id', sa.Integer, sa.ForeignKey(f'{cls.__tablename__}.id')),
            sa.Column('user_id', sa.Integer, sa.ForeignKey('ab_user.id')),
            sa.Column('content', sa.Text),
            sa.Column('created_at', sa.DateTime, default=datetime.utcnow)
        )

        if SQLALCHEMY_2:
            cls.comments: Mapped[List['Comment']] = relationship('Comment', backref='commented_record')
        else:
            cls.comments = relationship('Comment', backref='commented_record')

class OrderableMixin(UtilMixinBase):
    if SQLALCHEMY_2:
        order: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    else:
        order = sa.Column(sa.Integer, nullable=False, default=0)

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, 'before_insert')
        def set_default_order(mapper, connection, target):
            if target.order == 0:
                max_order = connection.scalar(sa.select([func.max(cls.order)]))
                target.order = (max_order or 0) + 1

class SearchableMixin(UtilMixinBase):
    @classmethod
    def __declare_last__(cls):
        searchable_columns = []
        for column in cls.__table__.columns:
            if isinstance(column.type, (String, Text)):
                searchable_columns.append(column.name)

        if searchable_columns:
            cls.search_vector = sa.Column(TSVectorType(*searchable_columns))

            @event.listens_for(cls, 'before_insert')
            @event.listens_for(cls, 'before_update')
            def update_search_vector(mapper, connection, target):
                search_terms = ' '.join(str(getattr(target, col)) for col in searchable_columns if getattr(target, col))
                target.search_vector = search_terms

    @classmethod
    def search(cls, session, query, limit=None, offset=None):
        if not hasattr(cls, 'search_vector'):
            raise AttributeError(f"Model {cls.__name__} does not have a search_vector")

        search_query = session.query(cls).filter(cls.search_vector.match(query))

        if limit is not None:
            search_query = search_query.limit(limit)
        if offset is not None:
            search_query = search_query.offset(offset)

        return search_query.all()

    @classmethod
    def get_searchable_columns(cls):
        return [column.name for column in cls.__table__.columns if isinstance(column.type, (String, Text))]

class NxTag(DeclarativeBase if SQLALCHEMY_2 else object):
    __tablename__ = 'nx_tags'
    
    if SQLALCHEMY_2:
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False)
    else:
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(50), unique=True, nullable=False)



class Comment(DeclarativeBase if SQLALCHEMY_2 else object):
    __tablename__ = 'comments'
    
    if SQLALCHEMY_2:
        id: Mapped[int] = mapped_column(primary_key=True)
        content: Mapped[str] = mapped_column(sa.Text)
        created_at: Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.utcnow)
    else:
        id = sa.Column(sa.Integer, primary_key=True)
        content = sa.Column(sa.Text)
        created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
