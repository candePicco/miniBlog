import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_migrate import Migrate
from models import db, Usuario, Post, Comentario, Categoria
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/miniBlog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave_super_secreta'

db.init_app(app)
migrate = Migrate(app, db)

# Context processor para hacer disponibles categorías en todas las plantillas
@app.context_processor
def inject_categorias():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return dict(categorias=categorias)

# Decorador para rutas que requieren login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Debés iniciar sesión para acceder a esta página.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    posts = Post.query.order_by(Post.fecha_creacion.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/crear_post', methods=['GET', 'POST'])
@login_required
def crear_post():
    if request.method == 'POST':
        titulo = request.form['titulo']
        contenido = request.form['contenido']
        usuario_id = session['usuario_id']
        post = Post(titulo=titulo, contenido=contenido, usuario_id=usuario_id)

        categorias_ids = request.form.getlist('categorias')
        if categorias_ids:
            categorias = Categoria.query.filter(Categoria.id.in_(categorias_ids)).all()
            post.categorias = categorias

        db.session.add(post)
        db.session.commit()
        flash("Post creado con éxito.", "success")
        return redirect(url_for('index'))

    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('nuevo_post.html', categorias=categorias)

@app.route('/eliminar_categoria/<int:categoria_id>', methods=['POST'])
def eliminar_categoria(categoria_id):
    categoria = Categoria.query.get_or_404(categoria_id)
    try:
        db.session.delete(categoria)
        db.session.commit()
        return redirect(url_for('listar_categorias'))
    except Exception as e:
        db.session.rollback()
        return f"Error eliminando categoría: {e}", 500




@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def ver_post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        if 'usuario_id' not in session:
            flash("Debés iniciar sesión para comentar.", "warning")
            return redirect(url_for('login'))

        texto = request.form['texto_comentario']
        usuario_id = session['usuario_id']
        comentario = Comentario(texto=texto, usuario_id=usuario_id, post_id=post.id)

        db.session.add(comentario)
        db.session.commit()
        flash("Comentario agregado.", "success")
        return redirect(url_for('ver_post', post_id=post.id))

    return render_template('ver_post.html', post=post)

@app.route('/usuarios')
def listar_usuarios():
    usuarios = Usuario.query.order_by(Usuario.nombre_usuario).all()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/comentarios')
def listar_comentarios():
    comentarios = Comentario.query.order_by(Comentario.fecha_creacion.desc()).all()
    return render_template('comentarios.html', comentarios=comentarios)

@app.route('/categorias')
def listar_categorias():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('categorias.html', categorias=categorias)

@app.route('/nuevo_comentario', methods=['GET', 'POST'])
@login_required
def nuevo_comentario():
    if request.method == 'POST':
        texto = request.form.get('texto')
        usuario_id = session['usuario_id']
        post_id = request.form.get('post_id')

        if texto and post_id:
            comentario = Comentario(texto=texto, usuario_id=usuario_id, post_id=int(post_id))
            db.session.add(comentario)
            db.session.commit()
            flash("Comentario creado correctamente.", "success")
            return redirect(url_for('ver_post', post_id=post_id))
        else:
            error = "Faltan datos para crear el comentario"
            return render_template('nuevo_comentario.html', error=error)

    posts = Post.query.order_by(Post.fecha_creacion.desc()).all()
    return render_template('nuevo_comentario.html', posts=posts)

@app.route('/nueva_categoria', methods=['GET', 'POST'])
@login_required
def nueva_categoria():
    if request.method == 'POST':
        nombre = request.form['nombre']
        categoria = Categoria(nombre=nombre)
        db.session.add(categoria)
        db.session.commit()
        flash("Categoría creada correctamente.", "success")
        return redirect(url_for('listar_categorias'))
    return render_template('nueva_categoria.html')

# --- Rutas para manejo de usuarios: registro, login, logout ---

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        correo = request.form['correo_electronico']
        contrasena = request.form['contrasena']
        confirmar = request.form['confirmar_contrasena']

        if contrasena != confirmar:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for('registro'))

        # Verificar que usuario o correo no existan
        existe = Usuario.query.filter(
            (Usuario.nombre_usuario == nombre_usuario) | 
            (Usuario.correo_electronico == correo)
        ).first()
        if existe:
            flash("El nombre de usuario o correo ya están registrados.", "danger")
            return redirect(url_for('registro'))

        usuario = Usuario(
            nombre_usuario=nombre_usuario,
            correo_electronico=correo,
        )
        # Guardar contraseña hasheada
        usuario.contrasena = generate_password_hash(contrasena)

        db.session.add(usuario)
        db.session.commit()
        flash("Registro exitoso. Ya podés iniciar sesión.", "success")
        return redirect(url_for('login'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasena = request.form['contrasena']

        usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if usuario and check_password_hash(usuario.contrasena, contrasena):
            session['usuario_id'] = usuario.id
            session['nombre_usuario'] = usuario.nombre_usuario
            flash(f"Bienvenido, {usuario.nombre_usuario}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)


