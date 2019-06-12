from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app, session
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from numpy import argwhere, delete
from pandas import read_csv, read_sql_table, DataFrame
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from tpot import TPOTClassifier
from app import db
from app.main.forms import UploadFileForm, SelectDatasetForm, CreateSubsetForm, AnalyseForm
from app.models import User,  User_dataset, Data_subset, Analysis_result, Dataset_columns, Task
from app.main import bp


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', title=_('Home'))

@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadFileForm()
    if form.validate_on_submit():
        #upload dataset
        df = read_csv(form.dataset.data)
        columns = df.columns.values
        datasetid =  User_dataset.query.count() + 1
        datasetname = str(current_user.id) + "-" + str(form.data_name.data)
        df.to_sql(con=db.engine, index_label='id', name=str(current_user.id) + "-" + str(form.data_name.data), if_exists='replace', index = False)
        data_user = User_dataset(user_id=current_user.id, dataset = datasetname, dataset_name=str(form.data_name.data))
        db.session.add(data_user)

        for column in columns:
            c = Dataset_columns(dataset_name= datasetname, column_name=column )
            db.session.add(c)

        db.session.commit()
        return redirect(url_for('main.index'))
    
    return(render_template('upload.html', form=form))


@bp.route('/dataforsubsetcreation', methods=['GET', 'POST'])
@login_required
def preprocessing_dataset_choice():
    form = SelectDatasetForm()
    form.dataset.query = User_dataset.query.filter(current_user.id == User_dataset.user_id)

    if form.validate_on_submit():
        session['datasetinuse'] = str(current_user.id) + "-" + str(form.dataset.data)
        return redirect(url_for('main.preprocessing_targetvariable_choice'))

    return render_template('datasetselect.html', form = form)

@bp.route('/settargetclass', methods = ['GET', 'POST'])
@login_required
def preprocessing_targetvariable_choice():
    form = CreateSubsetForm()
    targettable = session['datasetinuse']
    columnselection = Dataset_columns.query.filter(Dataset_columns.dataset_name == str(targettable))
    form.targetvariable.query = columnselection
    form.columnsincluded.query = columnselection

    if form.validate_on_submit():
        data_subset = Data_subset(dataset_name=targettable, subset =  str(current_user.id) + "-" + str(form.subsetname.data), subset_name = str(form.subsetname.data),  columns_subset = str(form.columnsincluded.data), target_column = str(form.targetvariable.data))
        db.session.add(data_subset)
        db.session.commit()
        return redirect(url_for('main.index'))

    return(render_template('selecttargetvariable.html', form = form))

@bp.route('/datasetforsubsetselection', methods=['GET', 'POST'])
@login_required
def subset_dataset_choice():
    form = SelectDatasetForm()
    form.dataset.query = User_dataset.query.filter(current_user.id == User_dataset.user_id)

    if form.validate_on_submit():
        session['datasetinuse'] = str(form.dataset.data)
        return redirect(url_for('main.select_subset'))

    return render_template('datasetselect.html', form = form)



@bp.route('/selectsubset', methods = ['GET', 'POST'])
@login_required
def select_subset():
    form = AnalyseForm()

    dataset = str(current_user.id) + "-" + session['datasetinuse']
    query = Data_subset.query.join(User_dataset, User_dataset.user_id==current_user.id).filter(Data_subset.dataset_name == dataset).all()
    form.subset.query = query

    if form.validate_on_submit():
        session['subsetselection'] = str(form.subset.data)
        session['analysisname'] = str(form.analysisname.data)
        return redirect(url_for('main.analysis'))

    return render_template('subsetselect.html', form = form)

@bp.route('/AutoML')
@login_required
def analysis():
    current_user.launch_task('autoML_modelbuild', _('Launching example tasks'))
    flash(_('Your model is being generated, the results will be available in the results page in 5 minutes'))
    
    return redirect(url_for('main.index'))


@bp.route('/datasetoverview')
@login_required
def dataset_overview():
    page = request.args.get('page', 1, type=int)
    datasets = current_user.my_datasets().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.dataset_overview', page=datasets.next_num) \
        if datasets.has_next else None
    prev_url = url_for('main.dataset_overview', page=datasets.prev_num) \
        if datasets.has_prev else None
    return render_template('datasetsoverview.html', object=_('Dataset'),  datasets=datasets.items, next_url=next_url, prev_url=prev_url)

@bp.route('/subsetoverview')
@login_required
def subset_overview():
    page = request.args.get('page', 1, type=int)
    subsets = current_user.my_subsets().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.subset_overview', page=subsets.next_num) \
        if subsets.has_next else None
    prev_url = url_for('main.subset_overview', page=subsets.prev_num) \
        if subsets.has_prev else None
    return render_template('subsetsoverview.html', object=_('Dataset'),  subsets=subsets.items, next_url=next_url, prev_url=prev_url)

    #TODO select subsets based on dataset

@bp.route('/resultsoverview')
@login_required
def result_overview():
    page = request.args.get('page', 1, type=int)
    results = current_user.my_results().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.result_overview', page=results.next_num) \
        if results.has_next else None
    prev_url = url_for('main.result_overview', page=results.prev_num) \
        if results.has_prev else None
    print(current_user.my_results().all())
    return render_template('resultsoverview.html', object=_('Dataset'),  results=results.items, next_url=next_url, prev_url=prev_url)

@bp.route('/tasks')
@login_required
def execute_tasks():
    current_user.launch_task('example', _('Launching example tasks'))
    return redirect(url_for('main.index', username=current_user.username))