from app import create_app, db
from app.models import User,  User_dataset, Data_subset, Analysis_result, Dataset_columns, Task

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Task': Task}
