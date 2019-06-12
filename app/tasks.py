import json
import sys
import time
from flask import render_template
from rq import get_current_job
from app import create_app, db
from app.models import User,  User_dataset, Data_subset, Analysis_result, Dataset_columns, Task
from app.email import send_email

app = create_app()
app.app_context().push()

def example(seconds):
    print('Starting task')
    for i in range(seconds):
        print(i)
        time.sleep(1)
    print('Task completed')
    print('Ooms is een zieke baas en moetikeenriet.at is tering mooi')

def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()


def export_posts(user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = user.posts.count()
        for post in user.posts.order_by(Post.timestamp.asc()):
            data.append({'body': post.body,
                         'timestamp': post.timestamp.isoformat() + 'Z'})
            time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_posts)

        send_email('[Microblog] Your blog posts',
                sender=app.config['ADMINS'][0], recipients=[user.email],
                text_body=render_template('email/export_posts.txt', user=user),
                html_body=render_template('email/export_posts.html',
                                          user=user),
                attachments=[('posts.json', 'application/json',
                              json.dumps({'posts': data}, indent=4))],
                sync=True)
    except:
        _set_task_progress(100)
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())

def autoML_modelbuild():
    try:
        rij = Data_subset.query.filter(Data_subset.subset == str(current_user.id) + "-" + session['subsetselection'])
        target = rij[0].target_column
        predictors = rij[0].columns_subset
        tabel = str(current_user.id) + "-" + session['datasetinuse']
        #laad data van sql
        df = read_sql_table(tabel, db.engine)
    
        #verklein dataset obv subsetselectie
        predictors = predictors.replace('[', '')
        predictors = predictors.replace(']', '')
        predictors = predictors.split(", ")
    
        if target in predictors:
            df = df[predictors]
        else:
            print(type(predictors))
            predictors.append(target)
            df = df[predictors]

        #rename de targetvariable naar targetvariabele
        df.rename(columns={target: 'target'}, inplace=True)
        predictors = df.columns.values
        index = argwhere(predictors=='target')
        predictors = delete(predictors, index)
        dffeatures = df[predictors] 

        # Categorical boolean mask
        categorical_feature_mask = dffeatures.dtypes==object

        # filter categorical columns using mask and turn it into a list
        categorical_cols = dffeatures.columns[categorical_feature_mask].tolist()
        le = LabelEncoder()
        # apply le on categorical feature columns
        if len(categorical_cols) >= 1 :
            dffeatures[categorical_cols] = dffeatures[categorical_cols].apply(lambda col: le.fit_transform(col))

        #set train en validatieset op
        X_train, X_test, Y_train, Y_test = train_test_split(dffeatures, df.target, train_size = 0.75, test_size = 0.25)

        #zet classifier op
        tpot = TPOTClassifier(generations=5, population_size=40, cv=5, random_state=42, verbosity=2, max_time_mins = 0.49)
    
        #train model
        tpot.fit(X_train, Y_train)

        #print result
        r = tpot.score(X_test, Y_test)
        model = tpot.clean_pipeline_string

        subsetid = str(current_user.id) + "-" + str(session['subsetselection'])
        analysisresult = Analysis_result(subset_name = subsetid, analysis_name =session['analysisname'], analysis_score = r, analysis_model = str(model)  )
        db.session.add(analysisresult)
        db.session.commit()
        print('TPOT test completed')
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())