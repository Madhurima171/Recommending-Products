from flask import Flask, render_template, request, redirect, session, url_for
from db import get_connection
from recommender import recommend

app = Flask(__name__)
app.secret_key = "secret123"

@app.route('/')
def home():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['user_name'] = user['first_name']
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        return "Invalid Credentials"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        d = request.form
        if d['password'] != d['confirm_password']:
            return "Password mismatch"
        hashed = d['password']
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (first_name,last_name,phone,email,security_question,security_answer,username,password,role) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'user')",
            (d['first_name'], d['last_name'], d['phone'], d['email'], d['security_question'], d['security_answer'], d['email'], hashed)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cat = request.args.get('category')
    search = request.args.get('search')
    conn = get_connection()
    cursor = conn.cursor()
    if search:
        cursor.execute("SELECT * FROM products WHERE name LIKE %s", ('%' + search + '%',))
    elif cat:
        cursor.execute("SELECT * FROM products WHERE category=%s", (cat,))
    else:
        cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', products=products, categories=categories)

@app.route('/recommend', methods=['POST'])
def recommend_route():
    p_id = request.form.get('product')
    results = recommend(p_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM products WHERE id=%s", (p_id,))
    p_res = cursor.fetchone()
    p_name = p_res['name'] if p_res else "Product"
    
    if 'user_id' in session:
        cursor.execute(
            "INSERT INTO user_activity (user_id, product_id, action_type) VALUES (%s,%s,%s)",
            (session['user_id'], p_id, 'recommendation')
        )
        conn.commit()
    conn.close()
    return render_template('result.html', recommendations=results, product=p_name)

@app.route('/add_review', methods=['POST'])
def add_review():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    p_id = request.form['product_id']
    rating = request.form['rating']
    review = request.form['review']
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO product_reviews (user_id, product_id, rating, review) VALUES (%s,%s,%s,%s)",
        (session['user_id'], p_id, rating, review)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT products.name, COUNT(user_activity.id) AS total FROM user_activity JOIN products ON products.id = user_activity.product_id GROUP BY products.name ORDER BY total DESC LIMIT 5"
    )
    analytics = cursor.fetchall()
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = cursor.fetchall()
    conn.close()
    return render_template('admin/admin_dashboard.html', products=products, analytics=analytics)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_product():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        cat = request.form['category']
        desc = request.form['description']
        img = request.form['image']
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (name, category, description, image) VALUES (%s, %s, %s, %s)",
                (name, cat, desc, img)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('admin'))
        except Exception as e:
            print(f"Error adding product: {e}")
            return f"Error: {e}"
            
    return render_template('admin/add_product.html')

@app.route('/admin/delete/<int:id>')
def delete_product(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)