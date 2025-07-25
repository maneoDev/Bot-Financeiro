# 🤖 Bot Gestor Financeiro para Telegram

Bem-vindo ao repositório do Bot Gestor Financeiro! Este é um bot para o Telegram, desenvolvido em Python, que ajuda a rastrear despesas diárias de forma simples e direta pelo chat.

O bot se conecta a um banco de dados [Supabase](https://supabase.com/) para armazenar e consultar todos os lançamentos financeiros de forma segura.

---

## ✨ Funcionalidades

O bot atualmente suporta os seguintes comandos:

* **/start**: Exibe uma mensagem de boas-vindas e a lista de todos os comandos disponíveis.
* **/adicionar `valor` `tag` `data` `comentário`**: Adiciona um novo registro de despesa.
    * **Exemplo:** `/adicionar 45.50 gasolina 25/07/2025 abasteci o carro`
* **/total**: Mostra um histórico completo de todas as despesas registradas, ordenadas por data, e exibe a soma total dos gastos.
* **/relatorio**: Gera um relatório consolidado que agrupa os gastos por categoria (tag), mostrando o valor total e a porcentagem de cada categoria em relação ao gasto total.
* **/tags**: Lista todas as categorias de despesas válidas que podem ser usadas no comando `/adicionar`.
* **/limpar**: Apaga **todos** os registros de despesas do usuário que executou o comando.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python
* **Biblioteca do Bot:** [python-telegram-bot](https://python-telegram-bot.org/)
* **Banco de Dados:** [Supabase](https://supabase.com/) (PostgreSQL)
* **Hospedagem:** [Render](https://render.com/) (Background Worker)

---

## 🚀 Como Rodar o Projeto

### Configuração Local

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/maneoDev/Bot-Financeiro.git](https://github.com/maneoDev/Bot-Financeiro.git)
    cd Bot-Financeiro
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    * Crie um arquivo chamado `.env` na raiz do projeto.
    * Adicione as seguintes chaves dentro do arquivo, substituindo pelos seus valores:
        ```
        TELEGRAM_TOKEN="SEU_TOKEN_AQUI"
        SUPABASE_URL="SUA_URL_DO_SUPABASE_AQUI"
        SUPABASE_KEY="SUA_CHAVE_ANON_DO_SUPABASE_AQUI"
        ```

5.  **Execute o bot:**
    ```bash
    python main.py
    ```