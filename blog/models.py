from neo4j.v1 import GraphDatabase, basic_auth, ResultError
from passlib.hash import bcrypt
from datetime import datetime
import os
import uuid
from flask import Flask, g, request, send_from_directory, abort, request_started

url = os.environ.get('GRAPHENEDB_URL', 'bolt://localhost')
username = os.environ.get('NEO4J_USERNAME')
password = os.environ.get('NEO4J_PASSWORD')

driver = GraphDatabase.driver(url, auth=basic_auth(username, str(password)))
app = Flask(__name__)

def get_db():
    if not hasattr(g, 'neo4j_db'):
        g.neo4j_db = driver.session()
    return g.neo4j_db

@app.teardown_appcontext
def close_db():
    if hasattr(g, 'neo4j_db'):
        g.neo4j_db.close()

class User:
    def __init__(self, username):
        self.username = username

    def find(self):
        db = get_db()
        print 'found ' + self.username
        results = db.run('''
            MATCH (user:User {username: {username}})
            RETURN user''', 
            {'username': self.username})
        try: 
            user = results.single()['user']
        except ResultError: 
            return False
        return serialize_user(user)

    def register(self, password):
        if not self.find():
            db = get_db()
            db.run('''
            CREATE (user:User {username: {username}, password: {password}})
            RETURN user''', 
            {'username': self.username, 'password':bcrypt.encrypt(password)})
            close_db()
            return True
        else:
            return False

    def verify_password(self, password):
        user = self.find()
        if user:
            return bcrypt.verify(password, user['password'])
        else:
            return False

    def add_post(self, title, tags, text):
        tags = [x.strip() for x in tags.lower().split(',')]
        db = get_db()
        db.run('''
            MATCH (user:User {username: {username}}) 
            CREATE (user)-[:PUBLISHED]->(post:Post {title:{title}, text:{text}, id:{id}, timestamp:{timestamp}, date:{date}})
            FOREACH ( tag IN {tags} | 
                MERGE (mytag:Tag {name:tag})
                CREATE (post)-[:TAGGED]->(mytag)
                )
            ''', 
            {'username': self.username, 'title':title, 'text':text, 'tags':tags,'id':str(uuid.uuid4()),'timestamp':timestamp(),'date':date()})

    def like_post(self, post_id):
        db = get_db()
        db.run('''
            MATCH (user:User {username:{username}}), (post:Post {id:{post_id}})
            MERGE (user)-[:LIKED]->(post)
            ''',
            {'username':self.username, 'post_id':post_id})

    def get_recent_posts(self):
        db = get_db()
        query = '''
        MATCH (user:User)-[:PUBLISHED]->(post:Post)-[:TAGGED]->(tag:Tag)
        WHERE user.username = {username}
        RETURN post, COLLECT(tag.name) AS tags
        ORDER BY post.timestamp DESC LIMIT 5
        '''
        return db.run(query, {'username':self.username})

    def get_similar_users(self):
        # Find three users who are most similar to the logged-in user
        # based on tags they've both blogged about.
        db = get_db()
        query = '''
        MATCH (you:User)-[:PUBLISHED]->(:Post)-[:TAGGED]->(tag:Tag),
              (they:User)-[:PUBLISHED]->(:Post)-[:TAGGED]->(tag)
        WHERE you.username = {username} AND you <> they
        WITH they, COLLECT(DISTINCT tag.name) AS tags
        ORDER BY SIZE(tags) DESC LIMIT 3
        RETURN they.username AS similar_user, tags
        '''
        return db.run(query, {'username':self.username})

    def get_commonality_of_user(self, other):
        # Find how many of the logged-in user's posts the other user
        # has liked and which tags they've both blogged about.
        db = get_db()
        result = db.run('''
        MATCH (they:User {username: {they} })
        MATCH (you:User {username: {you} })
        OPTIONAL MATCH (they)-[:PUBLISHED]->(:Post)-[:TAGGED]->(tag:Tag),
                       (you)-[:PUBLISHED]->(:Post)-[:TAGGED]->(tag)
        RETURN SIZE((they)-[:LIKED]->(:Post)<-[:PUBLISHED]-(you)) AS likes,
               COLLECT(DISTINCT tag.name) AS tags
        ''',{'they':other.username, 'you':self.username})

        for record in result:
            return {'likes':record['likes'],'tags':record['tags']}

def get_todays_recent_posts():
    db = get_db()
    result = db.run('''
    MATCH (user:User)-[:PUBLISHED]->(post:Post)-[:TAGGED]->(tag:Tag)
    WHERE post.date = {today}
    RETURN user.username AS username, post, COLLECT(tag.name) AS tags
    ORDER BY post.timestamp DESC LIMIT 5
    ''', {'today':date()})
    return [{
            'username':record['username'],
            'post':serialize_post(record['post']),
            'tags':record['tags'],} 
        for record in result]

def serialize_user(user):
    return {
        'username': user['username'],
        'password': user['password'],
    }

def serialize_post(post):
    return {
        'date': post['date'],
        'text': post['text'],
        'title': post['title'],
        'id': post['id'],
        'timestamp': post['timestamp'],
    }

def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()

def date():
    return datetime.now().strftime('%Y-%m-%d')
