from flask import request
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, SelectField 
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import ValidationError, DataRequired, Length
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from flask_babel import _, lazy_gettext as _l
from app.models import User, User_dataset, Data_subset, Analysis_result


class PostForm(FlaskForm):
    post = TextAreaField(('Say something'), validators=[DataRequired()])
    submit = SubmitField(('Submit'))

class UploadFileForm(FlaskForm):
    dataset = FileField(validators=[FileRequired(), FileAllowed(['csv'],'Alleen CSV bestanden')])
    data_name = StringField(('Naam van de dataset'), validators=[DataRequired()])
    submit = SubmitField(('Upload bestand'))

class SelectDatasetForm(FlaskForm):
    dataset = QuerySelectField('Dataset', get_label = 'dataset_name')
    submit = SubmitField(('Submit'))

class CreateSubsetForm(FlaskForm):
    subsetname = StringField(('Naam van de subset'), validators=[DataRequired()])
    targetvariable = QuerySelectField('Target variable')
    columnsincluded = QuerySelectMultipleField('Columns to include')
    submit = SubmitField(('Submit'))

class AnalyseForm(FlaskForm):
    analysisname = StringField(('Naam van de analyse'), validators=[DataRequired()])
    subset = QuerySelectField('Subset')
    submit = SubmitField(('Submit'))
