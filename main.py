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
from sqlalchemy.orm import relationship
from flask_migrate import Migrate





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
migrate = Migrate(app, db)


# ******** DATABASE ********

##CREATE TABLE IN DB
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    location = db.Column(db.String(1000))
    phone = db.Column(db.String(1000))

    # bidirectional relationship with CartItems class
    cart_items = relationship("CartItems", back_populates="customer_name")

    items = relationship("Items", back_populates="customer")
    


db.create_all()

class Items(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image_url_1 = db.Column(db.String(1000), nullable=False)
    image_url_2 = db.Column(db.String(1000), nullable=False)
    image_url_3 = db.Column(db.String(1000), nullable=False)
    category= db.Column(db.String(100), nullable=False)

    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    customer = relationship("User", back_populates="items")
    
db.create_all()


class CartItems(db.Model):
    __tablename__ = "cart_items"
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(500), nullable=False)
    item_price = db.Column(db.Integer, nullable=False)

    # one to many relationship with User
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # create reference to the User object, the "comments" refers to the comments property in the User class.
    customer_name = relationship("User", back_populates="cart_items")
   

db.create_all()


# ********** FORMS  *********

# register form
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), email.utils.parseaddr])
    location= StringField("Location", validators=[DataRequired()])
    phone = StringField("Phone", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


# login form
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), email.utils.parseaddr])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


# add item to the data base
class AddItemForm(FlaskForm):
    name = StringField("Item name", validators=[DataRequired()])
    price = IntegerField("Item price", validators=[DataRequired()])
    img_url_1 = StringField("Item Image URL 1", validators=[DataRequired(), URL()])
    img_url_2 = StringField("Item Image URL 2", validators=[DataRequired(), URL()])
    img_url_3 = StringField("Item Image URL 3", validators=[DataRequired(), URL()])
    category= StringField("Category", validators=[DataRequired()])
    description = CKEditorField("Item description", validators=[DataRequired()])
    
    
    submit = SubmitField("Add Item")



# ********** ROUTES *********
@app.route('/')
def home():
    items = Items.query.all()
    cart_items = CartItems.query.filter_by(customer_id=current_user.get_id()).all()
    # add all the prices of the items in the cart
    total = 0   
    for item in cart_items:
        total += item.item_price


    total_items = len(cart_items)

    return render_template("index.html", total=total, items=items, ordered_items=cart_items, total_items=total_items, current_user=current_user)


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
            image_url_1=request.form.get("img_url_1"),
            image_url_2=request.form.get("img_url_2"),
            image_url_3=request.form.get("img_url_3"),
            category=request.form.get("category"),
            description=request.form.get("description")
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add.html", form=form)


# ******** EDIT ITEM ********
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



# ********** CART *********


@app.route('/to_cart/<int:item_id>')
def add_to_cart(item_id):
    selected_item = Items.query.get(item_id)

    ordered_item = CartItems(    
        item_name=selected_item.name,
        item_price=selected_item.price,
        customer_name=current_user,
    )
    db.session.add(ordered_item)
    db.session.commit()

    return redirect(url_for("home"))


@app.route('/cart')
def cart():
    ordered_items = CartItems.query.all()
    if not current_user.is_authenticated:
        flash("You need to login or register in order to purchase any item.")
        return redirect(url_for("login"))

    return render_template("cart.html", items=ordered_items, current_user=current_user)


@app.route("/delete_item/<int:item_id>")
def delete_item(item_id):
    item_to_delete = CartItems.query.get(item_id)
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for('cart'))


# ******* DELETE ITEM ********
@app.route("/delete/<int:item_id>")
@admin_only
def delete(item_id):
    item_to_delete = Items.query.get(item_id)
    db.session.delete(item_to_delete)
    db.session.commit()
    
    return redirect(url_for('home'))


# ********** LOGOUT *********
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, port=8000)




# TO LIST
# ADD RATING BY THE CUSTOMERS
