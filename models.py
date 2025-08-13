from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    correo_electronico = db.Column(db.String(120), unique=True, nullable=False)
    contrasena = db.Column(db.String(256), nullable=False)

    posts = db.relationship('Post', backref='autor', lazy=True)
    comentarios = db.relationship('Comentario', backref='autor', lazy=True)

    def set_contrasena(self, password):
        self.contrasena = generate_password_hash(password)

    def check_contrasena(self, password):
        return check_password_hash(self.contrasena, password)

    def __repr__(self):
        return f'<Usuario {self.nombre_usuario}>'

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    comentarios = db.relationship('Comentario', backref='post', lazy=True, order_by="Comentario.fecha_creacion.desc()")
    categorias = db.relationship('Categoria', secondary='post_categoria', back_populates='posts')

    def __repr__(self):
        return f'<Post {self.titulo}>'

class Comentario(db.Model):
    __tablename__ = 'comentarios'

    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    def __repr__(self):
        return f'<Comentario {self.id} en Post {self.post_id}>'

class Categoria(db.Model):
    __tablename__ = 'categorias'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    posts = db.relationship('Post', secondary='post_categoria', back_populates='categorias')

    def __repr__(self):
        return f'<Categoria {self.nombre}>'

post_categoria = db.Table('post_categoria',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('categoria_id', db.Integer, db.ForeignKey('categorias.id'), primary_key=True)
)
