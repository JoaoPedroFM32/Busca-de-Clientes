import pyodbc
import logging
from prettytable import PrettyTable
from flask import Flask, request, render_template_string

# Configuração básica do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Página HTML simples para exibir os resultados
HTML_TEMPLATE = '''
<!doctype html>
<html lang="pt">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>CPF Contratos Ativos</title>
    <style>
      body {
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 14px;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        height: 100vh;
        margin: 0;
        background-color: #e9edf5;
      }
      .container {
        width: 100%;
        flex: 1;
        padding: 30px;
        background-color: #ffffff;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        overflow-x: auto;
        margin-top: 50px;
        margin-bottom: 50px;
      }
      .footer-top, .footer-bottom {
        width: 100%;
        height: 50px;
        position: fixed;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        font-weight: bold;
        font-family: "arial";
      }
      .footer-top {
        background-color: #002c61;
        top: 0;
      }
      .footer-bottom {
        background-color: #002c61;
        bottom: 0;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        text-align: center;
      }
      .logo {
        font-weight: bold;
        color: white;
        font-size: 40px; /* Ajuste o tamanho da fonte conforme necessário */
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
        font-family: "arial"
      }
      h1 {
        text-align: center;
        margin-bottom: 30px;
        margin-top: 80px; /* Adiciona um espaçamento superior para não sobrepor o rodapé */
      }
      form {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 30px;
      }
      input[type="text"] {
        width: 300px;
        padding: 10px;
        font-size: 16px;
        border-radius: 12px;
        border: 1px solid #ccc;
        margin-right: 10px;
        box-sizing: border-box;
      }
      input[type="text"]::placeholder {
        color: rgba(0, 0, 0, 0.5); /* Cor preta com 50% de transparência */
      }
      button {
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        border-radius: 12px;
        background-color: #4CAF50;
        color: white;
        cursor: pointer;
      }
      button:hover {
        background-color: #45a049;
      }
      table {
        width: 98%; /* Define a largura da tabela */
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 20px;
        margin-left: auto;
        margin-right: auto; /* Centraliza a tabela horizontalmente */
        table-layout: auto;
        word-wrap: break-word;
        border-radius: 8px; /* Reduzi o arredondamento das bordas da tabela para 8px */
        box-shadow: 5px 5px 15px rgba(0, 0, 0, 0.3);
        overflow: hidden;
      }
      table, th, td {
        border: 1px solid black;
      }
      th, td {
        padding: 10px;
        text-align: left;
      }
      th {
        background-color: #002c61;
        color: white; /* Adicionei a cor branca para o texto no cabeçalho */
      }
      td {
        font-size: 13px;
        white-space: nowrap;
      }
      tr:nth-child(even) td {
        background-color: #d1cfcf;
      }
      tr:nth-child(odd) td {
        background-color: #f9f9f9;
      }
      tr:hover td {
        background-color: #002c61; /* Cor de fundo ao passar o mouse */
        color: white; /* Cor do texto ao passar o mouse */
      }
      tr.clicked td {
        background-color: #1E90FF; /* Cor de fundo ao clicar */
        color: white; /* Cor do texto ao clicar */
      }
      .message {
        margin-top: 20px;
        font-size: 18px;
        color: red;
      }
      /* Round corners for table */
      table tr:first-child th:first-child {
        border-top-left-radius: 5px;
      }
      table tr:first-child th:last-child {
        border-top-right-radius: 5px;
      }
      table tr:last-child td:first-child {
        border-bottom-left-radius: 5px;
      }
      table tr:last-child td:last-child {
        border-bottom-right-radius: 5px;
      }
    </style>
  </head>
  <body>
    <div class="footer-top">
      <span class="logo">HBC Business</span>
    </div>
    <div class="container">
      <h1>CPF Contratos Ativos - Localizar</h1>
      <form method="post">
        <input type="text" id="documento" name="documento" placeholder="Documento" required>
        <button type="submit">Buscar</button>
      </form>
      {% if table %}
        <div>{{ table | safe }}</div>
      {% endif %}
    </div>
    <div class="footer-bottom">
      HBC Business Holding Business Corporate LTDA 46.221.302/0001-90
    </div>
    <script>
      document.addEventListener("DOMContentLoaded", function() {
        const rows = document.querySelectorAll("table tr");
        
        rows.forEach(row => {
          row.addEventListener("click", function() {
            // Remover a classe 'clicked' de todas as linhas
            rows.forEach(r => r.classList.remove("clicked"));
            
            // Adicionar a classe 'clicked' na linha clicada
            this.classList.add("clicked");
          });
        });
      });
    </script>
  </body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def buscar_por_documento():
    table_html = None
    if request.method == 'POST':
        documento = request.form['documento']
        try:
            # Configuração do banco de dados
            server = 'financob.database.windows.net'  # Substitua pelo seu servidor
            database = 'financob_db'  # Substitua pelo seu banco de dados
            username = 'adm_cobfiles'  # Substitua pelo seu usuário
            password = '123456*dbx'  # Substitua pela sua senha
            driver = '{ODBC Driver 17 for SQL Server}'  # Certifique-se de ter o driver ODBC adequado instalado

            # String de conexão
            connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
            
            # Estabelecer a conexão utilizando um gerenciador de contexto
            with pyodbc.connect(connection_string) as conn:
                logging.info("Conexão com o banco de dados estabelecida com sucesso.")
                
                # Criar um cursor
                cursor = conn.cursor()

                # Executar a consulta para buscar o documento específico
                cursor.execute("SELECT Documento, Nome, Agencia, Conta, Digito, Valor, Data_Debito, Parceiro FROM PARCELAS_PAGAS WHERE Documento = ?", (documento,))
                logging.info("Consulta executada com sucesso para o documento: %s", documento)

                # Buscar os resultados
                rows = cursor.fetchall()

                # Verificar se algum resultado foi encontrado
                if rows:
                    # Criar uma tabela com PrettyTable
                    table = PrettyTable()
                    table.field_names = ['Documento', 'Nome', 'Agência', 'Conta', 'Dígito', 'Valor', 'Vencimento', 'Parceiro']

                    # Adicionar linhas à tabela
                    for row in rows:
                        table.add_row(row)

                    # Converter a tabela para HTML
                    table_html = table.get_html_string(attributes={"class": "pretty-table"})
                else:
                    table_html = "<p class='message'>Nenhum resultado encontrado para o documento {}</p>".format(documento)
                    logging.info("Nenhum resultado encontrado para o documento: %s", documento)

        except pyodbc.Error as db_err:
            logging.error(f"Erro ao conectar ou consultar o banco de dados: {db_err}")
            table_html = "<p class='message'>Erro ao conectar ao banco de dados. Por favor, tente novamente mais tarde.</p>"
        except Exception as e:
            logging.error(f"Erro inesperado: {e}")
            table_html = "<p class='message'>Ocorreu um erro inesperado. Por favor, tente novamente mais tarde.</p>"

    return render_template_string(HTML_TEMPLATE, table=table_html)

if __name__ == '__main__':
    app.run(debug=True)
