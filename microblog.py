from app import create_app, db, cli
from app.models import User,  User_dataset, Data_subset, Analysis_result, Dataset_columns, Task

app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Message': Message,
            'Notification': Notification, 'Task': Task}
