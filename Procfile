web: flask db upgrade; flask translate compile; gunicorn microblog:app; release: flask db upgrade 
worker: rq worker -u $REDIS_URL microblog-tasks
