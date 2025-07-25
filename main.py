import os
import logging
import asyncio
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client, Client

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração de logging para depuração
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÃO DO SUPABASE E BOT ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Tags permitidas
ALLOWED_TAGS = [
    'lazer', 'mercantil', 'gasolina', 'gás', 'luz', 'casa',
    'água', 'emprestimo', 'fies', 'academia', 'contas'
]

# --- FUNÇÕES DO BOT ---


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem de boas-vindas quando o comando /start é emitido."""
    user = update.effective_user
    welcome_message = (
        f"Olá, {user.first_name}! Eu sou seu assistente financeiro pessoal.\n\n"
        "Aqui estão os comandos que você pode usar:\n"
        "/adicionar `valor tag data comentário` - Adiciona uma nova despesa\n"
        "(Ex: /adicionar 50.99 mercantil 25/07/2025 compras)\n"
        "/total - Mostra o histórico completo de gastos.\n"
        "/relatorio - Exibe um relatório de gastos por tag.\n"
        "/tags - Mostra as categorias de despesas permitidas.\n"
        "/limpar - Apaga TODOS os seus dados de despesas."
    )
    await update.message.reply_text(welcome_message)


async def adicionar_despesa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adiciona uma nova despesa com data e comentário."""
    user_id = update.effective_user.id

    # Precisamos de no mínimo 4 argumentos: valor, tag, data, e pelo menos uma palavra de comentário
    if len(context.args) < 4:
        await update.message.reply_text(
            "Uso incorreto! O formato agora é:\n"
            "/adicionar valor tag DD/MM/AAAA comentário\n\n"
            "Exemplo: /adicionar 43.54 mercantil 23/04/2025 compra de mês"
        )
        return

    valor_str = context.args[0]
    tag = context.args[1].lower()
    data_str = context.args[2]
    # O comentário é tudo o que vem depois da data
    comentario = " ".join(context.args[3:])

    # Validação da tag (continua igual)
    if tag not in ALLOWED_TAGS:
        await update.message.reply_text(f"Tag '{tag}' inválida.")
        return

    # Validação do valor (continua igual)
    try:
        valor = float(valor_str.replace(',', '.'))
        if valor <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("O valor deve ser um número positivo.")
        return

    # Validação da data
    try:
        # Converte o texto da data (DD/MM/AAAA) para um formato que o banco entende (AAAA-MM-DD)
        data_despesa = datetime.strptime(
            data_str, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        await update.message.reply_text("Formato de data inválido. Por favor, use DD/MM/AAAA.")
        return

    # Inserir no Supabase com os novos campos
    try:
        data, count = supabase.table('despesas').insert({
            'user_id': user_id,
            'amount': valor,
            'tag': tag,
            'expense_date': data_despesa,  # Novo campo
            'comment': comentario         # Novo campo
        }).execute()

        await update.message.reply_text(f"✅ Despesa adicionada com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao inserir no Supabase: {e}")
        await update.message.reply_text("Ocorreu um erro ao salvar sua despesa.")


async def historico_total(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra um histórico completo de todas as despesas e o total."""
    user_id = update.effective_user.id

    try:
        # Selecionamos todos os campos necessários e ordenamos pela data da despesa
        data, count = supabase.table('despesas').select(
            'amount, tag, expense_date, comment'
        ).eq('user_id', user_id).order('expense_date', desc=True).execute()

        despesas = data[1]
        if not despesas:
            await update.message.reply_text("Você ainda não tem despesas registradas.")
            return

        total_geral = 0.0
        # Começamos a montar a mensagem do histórico
        mensagem_historico = "Aqui está seu histórico de compras até o momento:\n\n"

        for despesa in despesas:
            total_geral += float(despesa['amount'])

            # Formata a data de AAAA-MM-DD para DD/MM/AAAA para exibição
            data_formatada = datetime.strptime(
                despesa['expense_date'], '%Y-%m-%d').strftime('%d/%m/%Y')

            # Monta a linha do histórico
            mensagem_historico += (
                f"{despesa['amount']:.2f} {despesa['tag'].upper()} {data_formatada} {despesa['comment']}\n"
            )

        mensagem_historico += f"\nTotal de tudo: R$ {total_geral:.2f}"

        await update.message.reply_text(mensagem_historico)

    except Exception as e:
        logger.error(f"Erro ao gerar histórico: {e}")
        await update.message.reply_text("Ocorreu um erro ao gerar seu histórico.")


async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera um relatório de gastos por tag, em texto simples."""
    user_id = update.effective_user.id

    try:
        # Esta parte de buscar e calcular os dados não muda
        data, count = supabase.table('despesas').select(
            'amount, tag', count='exact').eq('user_id', user_id).execute()

        despesas = data[1]
        if not despesas:
            await update.message.reply_text("Você ainda não possui despesas registradas. Use /adicionar para começar.")
            return

        gastos_por_tag = defaultdict(float)
        total_geral = 0.0
        for despesa in despesas:
            gastos_por_tag[despesa['tag']] += float(despesa['amount'])
            total_geral += float(despesa['amount'])

        tags_ordenadas = sorted(gastos_por_tag.items(),
                                key=lambda item: item[1], reverse=True)

        # --- NOVA ESTRUTURA DA MENSAGEM (TEXTO SIMPLES) ---
        mensagem_relatorio = "Aqui está o relatorio:\n\n"
        for tag, valor in tags_ordenadas:
            porcentagem = (valor / total_geral) * 100

            # Monta a linha no formato que você pediu: TAG : R$ 00.00 - XX.X%
            mensagem_relatorio += f"{tag.upper()} : R$ {valor:.2f} - {porcentagem:.1f}%\n"

        mensagem_relatorio += f"\nTOTAL GERAL : R$ {total_geral:.2f}"

        # Enviamos a mensagem como texto puro, removendo o 'parse_mode'
        await update.message.reply_text(mensagem_relatorio)

    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        await update.message.reply_text("Ocorreu um erro ao gerar seu relatório. Tente novamente.")


async def limpar_dados(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Apaga todos os registros de despesas do usuário."""
    user_id = update.effective_user.id
    try:
        data, count = supabase.table('despesas').delete().eq(
            'user_id', user_id).execute()
        await update.message.reply_text("🗑️ Todos os seus dados de despesas foram apagados com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao limpar dados: {e}")
        await update.message.reply_text("Ocorreu um erro ao apagar seus dados. Tente novamente.")


async def tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra a lista de tags de despesas permitidas."""
    # Junta todos os itens da lista ALLOWED_TAGS em uma única string, separados por vírgula e espaço
    tags_formatadas = ", ".join(ALLOWED_TAGS)

    mensagem = (
        "🏷️ Estas são as categorias de despesas que você pode usar:\n\n"
        f"`{tags_formatadas}`"
    )

    await update.message.reply_text(mensagem, parse_mode='MarkdownV2')


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Loga os erros causados por updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)


# --- CÓDIGO FINAL E CORRIGIDO ---

# Na função main, substitua o final dela por isto:

async def main() -> None:
    """Inicia o bot e o mantém rodando de forma assíncrona e correta."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adiciona os handlers dos comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("adicionar", adicionar_despesa))
    # AQUI ESTÁ A MUDANÇA: /total agora chama a nova função
    application.add_handler(CommandHandler("total", historico_total))
    application.add_handler(CommandHandler("relatorio", relatorio))
    application.add_handler(CommandHandler("limpar", limpar_dados))
    application.add_handler(CommandHandler("tags", tags))
    application.add_error_handler(error_handler)

    print("Bot iniciando...")

    # Inicia o bot em modo não-bloqueante
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
