from .views import app
from .models import driver

session = driver.session()
session.run("CREATE CONSTRAINT ON (n:User) ASSERT n.username IS UNIQUE;")
session.run("CREATE CONSTRAINT ON (n:Tag) ASSERT n.name IS UNIQUE;")
session.run("CREATE CONSTRAINT ON (n:Post) ASSERT n.id IS UNIQUE;")
session.close()
