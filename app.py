from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuração robusta para o banco de dados rodar no lugar certo
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'instance', 'trituno.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# =========================================
# MODELO DO BANCO DE DADOS
# =========================================
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) # Obrigatório!
    xp = db.Column(db.Integer, default=0)         
    diamantes = db.Column(db.Integer, default=0)  
    vidas = db.Column(db.Integer, default=5)       # Começa com 5 vidas!
    bloqueado_ate = db.Column(db.DateTime, nullable=True) # Guarda o horário final do bloqueio   

class Licao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modulo = db.Column(db.Integer, nullable=False) 
    titulo = db.Column(db.String(100), nullable=False) 
    conteudo = db.Column(db.Text, nullable=False)  

class Progresso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    licao_id = db.Column(db.Integer, db.ForeignKey('licao.id'), nullable=False)
    concluido = db.Column(db.Boolean, default=True) 

# =========================================
# ROTAS DO SITE
# =========================================

@app.route('/')
def pagina_home():
    return render_template('index.html')

@app.route('/licoes')
def pagina_licoes():
    usuario = Usuario.query.first()
    if not usuario:
        # CORREÇÃO: Agora passamos um e-mail padrão para não quebrar a regra do banco!
        usuario = Usuario(nome="Músico Aprendiz", email="teste@trituno.com")
        db.session.add(usuario)
        db.session.commit()
    
    return render_template('meu-projeto/licoes.html', usuario=usuario)

@app.route('/loja')
def pagina_loja():
    usuario = Usuario.query.first()
    return render_template('meu-projeto/loja.html', usuario=usuario)

@app.route('/ranking')
def pagina_ranking():
    usuario = Usuario.query.first()
    return render_template('meu-projeto/ranking.html', usuario=usuario)

@app.route('/configuracoes')
def pagina_configuracoes():
    usuario = Usuario.query.first()
    return render_template('meu-projeto/configuracoes.html', usuario=usuario)

@app.route('/registro')
def pagina_registro():
    return render_template('meu-projeto/registro.html')

@app.route('/login')
def pagina_login():
    return render_template('meu-projeto/login.html')

@app.route('/exercicio1')
def pagina_exercicio1():
    return render_template('modulo1/exercicio1.html')

@app.route('/api/perder-vida', methods=['POST'])
def perder_vida():
    usuario = Usuario.query.first()
    if not usuario:
        return jsonify({"status": "erro", "mensagem": "Usuário não encontrado"}), 404

    if usuario.vidas > 0:
        usuario.vidas -= 1
        
        # Se ele acabou de perder a última vida, bloqueia por 2 horas!
        if usuario.vidas == 0:
            usuario.bloqueado_ate = datetime.now() + timedelta(hours=2)
            db.session.commit()
            return jsonify({"status": "bloqueado", "mensagem": "Você perdeu todas as vidas!"}), 200
            
        db.session.commit()
        return jsonify({"status": "sucesso", "vidas_restantes": usuario.vidas}), 200
        
    return jsonify({"status": "ja_bloqueado"}), 400

@app.route('/introducao')
def pagina_introducao():
    usuario = Usuario.query.first()
    if not usuario:
        usuario = Usuario(nome="Músico Aprendiz", email="teste@trituno.com")
        db.session.add(usuario)
        db.session.commit()

    # VERIFICAÇÃO DE BLOQUEIO NA PRIMEIRA LIÇÃO
    if usuario.bloqueado_ate:
        if datetime.now() < usuario.bloqueado_ate:
            tempo_restante = usuario.bloqueado_ate - datetime.now()
            minutos_restantes = int(tempo_restante.total_seconds() / 60)
            
            # Bloqueia o acesso direto e avisa que ele precisa de vidas
            return f"""
            <div style="text-align: center; font-family: sans-serif; margin-top: 50px;">
                <h1>Acesso Bloqueado! 💔</h1>
                <p>Você perdeu todas as suas vidas e não pode iniciar esta lição.</p>
                <p>Aguarde mais <b>{minutos_restantes} minutos</b> para recuperar suas vidas ou passe na nossa loja!</p>
                <br>
                <a href='/licoes' style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Voltar para as Lições</a>
                <a href='/loja' style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">Ir para a Loja</a>
            </div>
            """
        else:
            # Se o tempo já passou, libera o usuário limpando o bloqueio
            usuario.vidas = 5
            usuario.bloqueado_ate = None
            db.session.commit()

    # Se não estiver bloqueado, ele abre a lição normalmente!
    return render_template('modulo1/introducao.html')

# ROTA PARA SALVAR O PROGRESSO QUE CRIAMOS ANTES
@app.route('/api/concluir-licao', methods=['POST'])
def concluir_licao():
    dados = request.get_json()
    licao_id = dados.get('licao_id')
    
    usuario = Usuario.query.first() 
    if not usuario:
        return jsonify({"status": "erro", "mensagem": "Nenhum usuário encontrado"}), 404

    try:
        novo_progresso = Progresso(usuario_id=usuario.id, licao_id=licao_id)
        db.session.add(novo_progresso)
        
        # Agora a lição dá apenas XP! Diamantes vêm de anúncios/loja.
        usuario.xp += 10 
        db.session.commit()
        return jsonify({"status": "sucesso", "mensagem": "Progresso salvo!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


# Inicializa o banco de dados e roda o servidor
if __name__ == '__main__':
    # Garante que a pasta 'instance' exista antes de criar o banco de dados
    os.makedirs(os.path.join(base_dir, 'instance'), exist_ok=True)
    
    # CRIA AS TABELAS NO BANCO DE DADOS AUTOMATICAMENTE
    with app.app_context():
        db.create_all()
        print("Banco de dados e tabelas verificados/criados com sucesso!")

    # Pega a porta que o Render oferece ou usa a 5000 como padrão local
    porta = int(os.environ.get("PORT", 5000))
    # O host OBRIGATORIAMENTE precisa ser 0.0.0.0 para funcionar na nuvem
    app.run(host='0.0.0.0', port=porta)