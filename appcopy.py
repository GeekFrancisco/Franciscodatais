import sqlite3
import random
import string
from faker import Faker

# Inicializando o Faker para gerar dados aleatórios
fake = Faker()

# Função para gerar uma string aleatória
def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Função para criar uma base de dados e popular com 1000 linhas de dados
def create_db(database_name, tables_and_columns):
    conn = sqlite3.connect(database_name)  # Conectando ao banco de dados
    cursor = conn.cursor()

    # Criando e populando todas as tabelas no mesmo banco de dados
    for table_name, columns, data_generator in tables_and_columns:
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({", ".join(columns)})')
        
        # Gerando 1000 linhas de dados aleatórios
        for _ in range(1000):
            cursor.execute(f'INSERT INTO {table_name} ({", ".join([col.split()[0] for col in columns])}) VALUES ({", ".join(["?" for _ in columns])})', data_generator())
        
    # Salvar e fechar o banco de dados
    conn.commit()
    conn.close()

# Funções para gerar dados para cada tabela

def generate_car_data():
    return (
        fake.company(),            # Marca
        fake.word(),               # Modelo
        random.randint(2000, 2023), # Ano
        random.choice(['Sedan', 'SUV', 'Hatchback', 'Coupe', 'Convertible']),  # Tipo
        round(random.uniform(15000, 100000), 2),  # Preço
        random.choice(['Gasolina', 'Diesel', 'Elétrico', 'Híbrido']),  # Combustível
        random.randint(0, 500000),  # Quilometragem
        random.choice(['Novo', 'Usado']),  # Condição
        fake.date_this_decade(),    # Data de fabricação
        fake.color_name()           # Cor
    )

def generate_person_data():
    return (
        fake.name(),
        fake.email(),
        fake.phone_number(),
        fake.address().replace('\n', ' '),
        fake.city(),
        fake.state(),
        random.randint(18, 100),  # Idade
        fake.job(),
        fake.date_of_birth(minimum_age=18, maximum_age=100),  # Data de nascimento
        random.choice(['Solteiro', 'Casado', 'Divorciado', 'Viúvo'])  # Estado civil
    )

def generate_client_data():
    return (
        fake.company(),
        fake.name(),
        fake.address().replace('\n', ' '),
        fake.city(),
        fake.state(),
        fake.phone_number(),
        fake.email(),
        fake.date_this_decade(),
        random.randint(1000, 50000),  # Valor da compra
        random.choice(['Ativo', 'Inativo'])  # Status
    )

def generate_animal_data():
    return (
        fake.first_name(),
        fake.last_name(),
        random.choice(['Cachorro', 'Gato', 'Coelho', 'Passarinho', 'Hamster']),
        random.randint(1, 20),  # Idade do animal
        random.choice(['Macho', 'Fêmea']),
        random.choice(['Raça 1', 'Raça 2', 'Raça 3', 'Raça 4']),
        fake.color_name(),  # Cor do animal
        random.choice(['Pequeno', 'Médio', 'Grande']),
        fake.date_of_birth(minimum_age=0, maximum_age=20),  # Data de nascimento
        fake.address().replace('\n', ' ')  # Endereço
    )

def generate_book_data():
    return (
        fake.name(),
        fake.sentence(nb_words=3),
        random.choice(['Ficção', 'Não Ficção', 'Romance', 'Aventura', 'Mistério']),
        random.choice(['Editora A', 'Editora B', 'Editora C']),
        random.randint(100, 1000),  # Número de páginas
        random.randint(1900, 2023),  # Ano de publicação
        random.choice(['Novo', 'Usado']),
        fake.language_name(),
        round(random.uniform(10.0, 150.0), 2),  # Preço
        fake.isbn13()  # ISBN
    )

def generate_movie_data():
    return (
        fake.sentence(nb_words=1),
        fake.name(),
        random.randint(1900, 2023),  # Ano de lançamento
        random.choice(['Ação', 'Comédia', 'Drama', 'Suspense', 'Terror']),
        random.choice(['2D', '3D', 'IMAX']),
        random.choice(['PG', 'PG-13', 'R', 'NC-17']),
        fake.sentence(nb_words=3),  # Sinopse
        round(random.uniform(50.0, 200.0), 2),  # Orçamento
        round(random.uniform(1.0, 300.0), 2),  # Duração em minutos
        fake.name()  # Diretor
    )

def generate_sport_data():
    return (
        fake.word(),
        random.choice(['Futebol', 'Basketball', 'Tênis', 'Vôlei', 'Rugby']),
        fake.date_this_decade(),
        random.choice(['Profissional', 'Amador']),
        random.choice(['Internacional', 'Nacional']),
        random.choice(['Sim', 'Não']),
        random.randint(1, 100000),  # Público estimado
        random.choice(['Equipe A', 'Equipe B']),
        fake.name(),  # Árbitro
        round(random.uniform(50000, 500000), 2)  # Patrocínio
    )

def generate_football_data():
    return (
        fake.word(),
        random.choice(['Atacante', 'Meio-campo', 'Defensor', 'Goleiro']),
        random.choice(['Ala', 'Centro', 'Ponta']),
        random.choice(['Brasil', 'Argentina', 'Alemanha', 'França', 'Itália']),
        random.randint(18, 40),  # Idade
        fake.name(),  # Clube
        random.choice(['Sim', 'Não']),  # Jogador Internacional
        random.randint(1, 100),  # Gols marcados
        round(random.uniform(10000, 500000), 2),  # Salário
        random.choice(['FIFA', 'UEFA', 'CONMEBOL'])  # Federação
    )

def generate_computer_data():
    return (
        fake.word(),
        random.choice(['Intel', 'AMD']),
        random.choice(['NVIDIA', 'AMD']),
        random.randint(4, 64),  # RAM
        random.choice(['SSD', 'HDD']),
        random.randint(128, 2000),  # Armazenamento
        random.choice(['Windows', 'Linux', 'MacOS']),
        random.choice(['Desktop', 'Notebook']),
        random.randint(1000, 50000),  # Preço
        fake.date_this_decade()  # Data de lançamento
    )

def generate_watch_data():
    return (
        fake.word(),
        random.choice(['Analógico', 'Digital', 'Smartwatch']),
        random.choice(['Apple', 'Casio', 'Rolex', 'Seiko']),
        random.choice(['Feminino', 'Masculino']),
        random.randint(100, 5000),  # Preço
        random.choice(['Couro', 'Aço inoxidável', 'Plástico']),
        fake.color_name(),  # Cor
        random.randint(1, 100),  # Resistencia à água
        fake.date_this_decade(),  # Data de fabricação
        fake.word()  # Tipo de movimento
    )

# Definir as tabelas e as funções para gerar os dados
tables_and_columns = [
    ("carros", ["marca TEXT", "modelo TEXT", "ano INTEGER", "tipo TEXT", "preco REAL", "combustivel TEXT", "quilometragem INTEGER", "condicao TEXT", "data_fabricacao TEXT", "cor TEXT"], generate_car_data),
    ("pessoas", ["nome TEXT", "email TEXT", "telefone TEXT", "endereco TEXT", "cidade TEXT", "estado TEXT", "idade INTEGER", "profissao TEXT", "data_nascimento TEXT", "estado_civil TEXT"], generate_person_data),
    ("clientes", ["empresa TEXT", "nome TEXT", "endereco TEXT", "cidade TEXT", "estado TEXT", "telefone TEXT", "email TEXT", "data_compra TEXT", "valor_compra INTEGER", "status TEXT"], generate_client_data),
    ("animais", ["nome TEXT", "sobrenome TEXT", "tipo TEXT", "idade INTEGER", "sexo TEXT", "raca TEXT", "cor TEXT", "tamanho TEXT", "data_nascimento TEXT", "endereco TEXT"], generate_animal_data),
    ("livros", ["autor TEXT", "titulo TEXT", "genero TEXT", "editora TEXT", "paginas INTEGER", "ano_publicacao INTEGER", "condicao TEXT", "idioma TEXT", "preco REAL", "isbn TEXT"], generate_book_data),
    ("filmes", ["titulo TEXT", "diretor TEXT", "ano_lancamento INTEGER", "genero TEXT", "formato TEXT", "classificacao TEXT", "sinopse TEXT", "orcamento REAL", "duracao REAL", "diretor_nome TEXT"], generate_movie_data),
    ("esportes", ["nome TEXT", "tipo TEXT", "data_evento TEXT", "nivel TEXT", "categoria TEXT", "interesse_estrangeiro TEXT", "publico_estimado INTEGER", "time TEXT", "arbitro TEXT", "patrocinio REAL"], generate_sport_data),
    ("futebol", ["jogador TEXT", "posicao TEXT", "funcao TEXT", "nacionalidade TEXT", "idade INTEGER", "clube TEXT", "internacional TEXT", "gols INTEGER", "salario REAL", "federacao TEXT"], generate_football_data),
    ("computadores", ["modelo TEXT", "processador TEXT", "gpu TEXT", "ram INTEGER", "armazenamento TEXT", "disco INTEGER", "sistema_operacional TEXT", "tipo TEXT", "preco INTEGER", "data_lancamento TEXT"], generate_computer_data),
    ("relogios", ["modelo TEXT", "tipo TEXT", "marca TEXT", "genero TEXT", "preco INTEGER", "material_braçadeira TEXT", "cor TEXT", "resistencia_agua INTEGER", "data_fabricacao TEXT", "movimento TEXT"], generate_watch_data),
]

# Criar o banco de dados com todas as tabelas
create_db('all_data.db', tables_and_columns)

print("Banco de dados 'all_data.db' criado com sucesso com todas as tabelas!")
