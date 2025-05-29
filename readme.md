# Arquivo: README.md
# Simulador de Futebol

Um simulador de partidas de futebol estilo Brasfoot/Soccer Manager, desenvolvido em Python com interface em Streamlit.

## Funcionalidades

- Simulação de partidas com animação em tempo real
- Estatísticas detalhadas de cada partida
- Histórico de partidas
- Tabela de classificação
- Artilharia individual

## Como Executar

### Requisitos

- Python 3.8 ou superior
- Dependências listadas em `requirements.txt`

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/simulador-futebol.git
cd simulador-futebol

# Instale as dependências
pip install -r requirements.txt
```

### Execução

```bash
# Opção 1: Usando o script run.py
python run.py

# Opção 2: Usando o comando Streamlit diretamente
streamlit run app/main.py

# Opção 3: Em Windows, use o arquivo batch
executar.bat

# Opção 3: Em Linux/Mac, use o shell script
./executar.sh
```

## Estrutura do Projeto

```
simulador_futebol/
│
├── app/                      # Código principal da aplicação
│   ├── __init__.py
│   ├── main.py               # Ponto de entrada principal do Streamlit
│   ├── simulacao.py          # Funções de simulação de partidas
│   ├── estatisticas.py       # Funções relacionadas a estatísticas
│   └── classificacao.py      # Funções para gerar classificação
│
├── data/                     # Diretório para arquivos de dados
│   ├── clubes_utf8.csv       # Dados dos clubes
│   ├── jogadores_utf8.csv    # Dados dos jogadores
│   └── historico_partidas.csv # Histórico de resultados
│
├── utils/                    # Utilitários compartilhados
│   ├── __init__.py
│   └── io.py                 # Funções de entrada/saída (carregar/salvar dados)
│
├── static/                   # Recursos estáticos (imagens, CSS)
│   └── favicon.ico           # Ícone da aplicação
│
├── requirements.txt          # Dependências do projeto
├── README.md                 # Documentação do projeto
└── run.py                    # Script para iniciar a aplicação
```

## Contribuição

Sinta-se à vontade para contribuir com o projeto! Abra uma issue ou envie um pull request.