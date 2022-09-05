from crypt import methods
from distutils.log import error
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField
from wtforms.validators import DataRequired, URL
import email
from flask_bootstrap import Bootstrap
from distutils.log import error
from flask_ckeditor import CKEditor, CKEditorField
from functools import wraps





app = Flask(__name__)
Bootstrap(app)
ckeditor = CKEditor(app)

# configuration of login manager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# pyhton decorator to allow only the admin to access the page
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)        
    return decorated_function


app.config['SECRET_KEY'] = 'qwertyuiopasdfghjklzxcvbnm'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ******** DATABASE ********

##CREATE TABLE IN DB
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    location = db.Column(db.String(1000))

#Line below only required once, when creating DB. 
db.create_all()

class Items(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    price = db.Column(db.String(1000), nullable=False)
    image_url = db.Column(db.String(1000), nullable=False)
    category= db.Column(db.String(100), nullable=False)
    
db.create_all()



# ******** cart ********
# class Cart():
#     def __init__(self):
#         self.items = []
#         self.total = 0
#         self.quantity = 0

#     def add_item(self, item):
#         self.items.append(item)
#         self.total += float(item.price)
#         self.quantity += 1

#     def remove_item(self, item):
#         self.items.remove(item)
#         self.total -= float(item.price)
#         self.quantity -= 1

#     def clear_cart(self):
#         self.items = []
#         self.total = 0
#         self.quantity = 0



# ********** FORMS  *********

# register form
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), email.utils.parseaddr])
    location= StringField("Location", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("sign me up")


# login form
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), email.utils.parseaddr])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")

# add item to the data base
class AddItemForm(FlaskForm):
    name = StringField("Item name", validators=[DataRequired()])
    price = StringField("Item price", validators=[DataRequired()])
    img_url = StringField("Item Image URL", validators=[DataRequired(), URL()])
    category= StringField("Category", validators=[DataRequired()])
    description = CKEditorField("Item description", validators=[DataRequired()])
    
    
    submit = SubmitField("Submit Item")




# ********** ROUTES *********
@app.route('/')
def home():
    items = Items.query.all()
    return render_template("index.html", items=items)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if request.method == "POST":
    
        # check if email already exists in db
        email = request.form.get("email")
        if User.query.filter_by(email=email).first():
            flash("Email already exists!")
            return redirect(url_for("register", error=error))
        else:
            # hashing a password
            hash_and_salted_password = generate_password_hash(
                request.form.get('password'),
                method='pbkdf2:sha256',
                salt_length=8
            )

            new_user = User(
                email=request.form.get('email'),
                name=request.form.get('name'),
                password=hash_and_salted_password,
                location=request.form.get('location')
            )

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)

            return redirect(url_for("home"))

    return render_template("register.html", form=form)


@app.route('/login',  methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for("home", name=user.name))
            else:
                flash("Please check your password")
                return redirect(url_for("login", error=error))
        else:
            flash("Please check your email!")
            return redirect(url_for("login", error=error))
        
    return render_template("login.html", form=form)


@app.route('/add', methods=["GET", "POST"])
@admin_only
def add():
    form = AddItemForm()
    if request.method == "POST":
        new_item = Items(
            name=request.form.get("name"),
            price=request.form.get("price"),
            image_url=request.form.get("img_url"),
            category=request.form.get("category"),
            description=request.form.get("description")
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add.html", form=form)


@app.route("/edit<int:item_id>", methods=["GET", "POST"])
def edit(item_id):
    item = Items.query.get(item_id)
    edit_form = AddItemForm(
        name=item.name,
        price=item.price,
        img_url=item.image_url,
        category=item.category,
        description=item.description
    )
    if edit_form.validate_on_submit():
        item.name = edit_form.name.data
        item.price = edit_form.price.data
        item.image_url = edit_form.img_url.data
        item.category = edit_form.category.data
        item.description = edit_form.description.data    
        db.session.commit()
        return redirect(url_for("home", item_id=item_id))
    return render_template("edit.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route('/description/<int:item_id>')
def description(item_id):
    requested_item = Items.query.get(item_id)
    return render_template("description.html", item=requested_item, current_user=current_user)


# ********** cart *********

# @app.route("/add_to_cart/<int:item_id>")
# def add_to_cart(item_id):
#     item = Items.query.get(item_id)
#     if item:
#         existing_item = Cart.query.filter_by(item_id=item_id, ordered=False).first()
#         if existing_item:
#             existing_item.quantity += 1
#             db.session.commit()
#             flash("This item quantity was updated.")
#             return redirect(url_for("home"))
#         else:
#             new_item = Cart(item_id=item_id, quantity=1)
#             db.session.add(new_item)
#             db.session.commit()
#             flash("This item was added to your cart.")
#             return redirect(url_for("home"))
#     else:
#         flash("This item does not exist.")
#         return redirect(url_for("home"))



@app.route('/cart/<int:item_id>')
def cart(item_id):
    selected_item = Items.query.get(item_id)
    if selected_item not in current_user.cart:
        current_user.cart.append(selected_item)
        db.session.commit()

    return render_template("cart.html", current_user=current_user)


@app.route("/delete/<int:item_id>")
@admin_only
def delete(item_id):
    item_to_delete = Items.query.get(item_id)
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)




# TO LIST
# ADD RATING BY THE CUSTOMERS
# DESCRIPTION OF THE ITEM
# ADD TO CART