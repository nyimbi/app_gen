from flask import render_template, request, redirect, url_for, flash
from flask_appbuilder import SimpleFormView, expose
from flask_appbuilder.forms import DynamicForm
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired
from .models import UserProfile
from . import appbuilder, db

class Step1Form(DynamicForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    company_name = StringField('Company Name', validators=[DataRequired()])
    job_title = StringField('Job Title', validators=[DataRequired()])

class Step2Form(DynamicForm):
    industry = SelectField('Industry', choices=[
        ('tech', 'Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    company_size = SelectField('Company Size', choices=[
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-1000', '201-1000 employees'),
        ('1000+', '1000+ employees')
    ], validators=[DataRequired()])

class Step3Form(DynamicForm):
    use_case = TextAreaField('How do you plan to use our product?', validators=[DataRequired()])

class OnboardingWizardView(SimpleFormView):
    route_base = "/onboarding"

    @expose('/', methods=['GET', 'POST'])
    def onboarding(self):
        step = request.args.get('step', '1')
        if step == '1':
            form = Step1Form()
            if form.validate_on_submit():
                session['step1_data'] = form.data
                return redirect(url_for('OnboardingWizardView.onboarding', step='2'))
            return render_template('wizard/step1.html', form=form)
        elif step == '2':
            form = Step2Form()
            if form.validate_on_submit():
                session['step2_data'] = form.data
                return redirect(url_for('OnboardingWizardView.onboarding', step='3'))
            return render_template('wizard/step2.html', form=form)
        elif step == '3':
            form = Step3Form()
            if form.validate_on_submit():
                # Combine all steps data and save to database
                user_data = {**session.get('step1_data', {}), **session.get('step2_data', {}), **form.data}
                user_profile = UserProfile(**user_data)
                db.session.add(user_profile)
                db.session.commit()
                flash('Onboarding completed successfully!', 'success')
                return redirect(url_for('IndexView.index'))
            return render_template('wizard/step3.html', form=form)

appbuilder.add_view(OnboardingWizardView, "Onboarding Wizard", icon="fa-magic", category="Onboarding")