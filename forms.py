from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp, ValidationError
from models import User

# Login Form
class LoginForm(FlaskForm):
    username = StringField(
        'Username', 
        validators=[DataRequired(), Length(min=3, max=64)]
    )
    password = PasswordField(
        'Password', 
        validators=[DataRequired(), Length(min=6)]
    )
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

# Registration Form
class RegisterForm(FlaskForm):
    username = StringField(
        'Username', 
        validators=[
            DataRequired(),
            Length(min=3, max=64),
            Regexp(
                '^[A-Za-z0-9_]+$', 
                message='Username can only contain letters, numbers, and underscores'
            )
        ]
    )
    email = StringField(
        'Email', 
        validators=[DataRequired(), Email(), Length(max=120)]
    )
    password = PasswordField(
        'Password', 
        validators=[DataRequired(), Length(min=6)]
    )
    password2 = PasswordField(
        'Confirm Password', 
        validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Register')

    # Custom validator for username
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already taken.')

    # Custom validator for email
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered.')

# System Call Form
class SystemCallForm(FlaskForm):
    command = StringField(
        'Command', 
        validators=[DataRequired()]
    )
    submit = SubmitField('Execute')

# Permission Form
class PermissionForm(FlaskForm):
    command_pattern = StringField(
        'Command Pattern', 
        validators=[DataRequired()]
    )
    description = StringField('Description')
    user_id = SelectField(
        'User', 
        coerce=int, 
        validators=[DataRequired()]
    )
    submit = SubmitField('Add Permission')