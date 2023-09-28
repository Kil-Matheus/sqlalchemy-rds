from fastapi import FastAPI, Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.templating import Jinja2Templates
import jwt
import uvicorn
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

# Minhas configurações do meu RDS AWS
db_endpoint = 'db-kil-aws.cjnhjmmgmsdy.us-east-1.rds.amazonaws.com'
db_username = 'postgres'
db_password = 'admin123'
db_name = 'postgres'

#Conexao com o banco de dados
engine = create_engine(f'postgresql://{db_username}:{db_password}@{db_endpoint}/{db_name}')

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuario'
    username = Column(String, primary_key=True)
    senha = Column(String)

# Crie a tabela no banco de dados (isto só precisa ser feito uma vez)
Base.metadata.create_all(bind=engine)

# Crie uma sessão SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

#Verifica se Existe a coluna no banco de dados
inspector = inspect(engine)
if 'usuario' not in inspector.get_table_names():
    # A tabela não existe, então vamos criá-la
    Base.metadata.create_all(bind=engine)

    #Novo usuário
    novo_usuario = Usuario(username='Kil Matheus', senha='Kil123')

    # Adicionar o novo usuário à sessão
    db.add(novo_usuario)

    # Confirmar a transação para inserir o usuário no banco de dados
    db.commit()

# Certifique-se de fechar a sessão quando terminar
db.close()

#JWT
SECRET_KEY = '96195d62f35e6015ca2ac7e676ad3377'
ALGORITHM = 'HS256'

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request):
    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        print(username, password)

        # Realiza a consulta ao banco de dados usando SQLAlchemy
        user = db.query(Usuario).filter(Usuario.username == username).first()

        if user and user.senha == password:
            # Gera um token JWT válido por um período específico (por exemplo, 30 minutos)
            expires = datetime.utcnow() + timedelta(minutes=30)
            payload = {
                "user": username,
                "exp": expires
            }
            jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

            return {"access_token": jwt_token}
        else:
            return {"error": "Invalid username or password"}
        
    except SQLAlchemyError as e:
        return JSONResponse(content={"error": f"Database error: {e}"}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)