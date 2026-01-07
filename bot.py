import io
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from PIL import Image

TOKEN = "8250598286:AAEFQVWC205YdEALmAzEITO6kKxwZQDlfx8"

def get_predominant_color(img):
    # Reduz a imagem para encontrar a cor principal mais rápido
    img_temp = img.copy().convert('RGB')
    img_temp = img_temp.resize((1, 1), resample=Image.Resampling.LANCZOS)
    return img_temp.getpixel((0, 0))

async def processar_layout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    legenda = update.message.caption or ""
    foto = update.message.photo

    if legenda.strip().upper() == "TEMA" and foto:
        await update.message.reply_text("Criando tema personalizado...")

        # 1. Baixar a foto
        arquivo_foto = await foto[-1].get_file()
        foto_bytes = await arquivo_foto.download_as_bytearray()
        img_usuario = Image.open(io.BytesIO(foto_bytes)).convert("RGBA")

        # 2. Configurações A4 (150 DPI)
        LARGURA_A4 = 1240
        ALTURA_A4 = 1754
        ALTURA_CABECALHO = 295  # 5cm
        RESPIRO_INTERNO = 40    # Espaço para o logo não encostar na borda do retângulo

        # 3. Descobrir a cor predominante para o fundo do retângulo
        cor_fundo = get_predominant_color(img_usuario)

        # 4. Criar Folha Base (Branca)
        folha = Image.new('RGB', (LARGURA_A4, ALTURA_A4), (255, 255, 255))

        # 5. Criar o Retângulo de 5cm com a cor predominante
        retangulo_colorido = Image.new('RGB', (LARGURA_A4, ALTURA_CABECALHO), cor_fundo)
        folha.paste(retangulo_colorido, (0, 0))

        # 6. Redimensionar o logo proporcionalmente para caber dentro do retângulo (com respiro)
        largura_max = LARGURA_A4 - (RESPIRO_INTERNO * 2)
        altura_max = ALTURA_CABECALHO - (RESPIRO_INTERNO * 2)
        
        # Redimensiona mantendo a proporção original
        img_usuario.thumbnail((largura_max, altura_max), Image.Resampling.LANCZOS)

        # 7. Centralizar o logo sobre o retângulo colorido
        pos_x = (LARGURA_A4 - img_usuario.width) // 2
        pos_y = (ALTURA_CABECALHO - img_usuario.height) // 2
        
        # Usar a própria imagem como máscara para preservar transparências se houver
        folha.paste(img_usuario, (pos_x, pos_y), img_usuario)

        # 8. Salvar e Enviar
        output = io.BytesIO()
        folha.save(output, format="JPEG", quality=95)
        output.seek(0)
        
        await update.message.reply_document(
            document=output, 
            filename="tema_personalizado.jpg",
            caption="Tema criado com sucesso."
        )
    else:
        await update.message.reply_text("Comando inválido. Envie a foto com a legenda TEMA.")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL, processar_layout))
    application.run_polling()
