import io
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from PIL import Image

TOKEN = "8250598286:AAEFQVWC205YdEALmAzEITO6kKxwZQDlfx8"

def get_predominant_color(img):
    # Converte para RGB e reduz a 1 pixel para pegar a cor média/predominante
    img_temp = img.convert('RGB').resize((1, 1), resample=Image.Resampling.LANCZOS)
    return img_temp.getpixel((0, 0))

async def processar_layout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    legenda = update.message.caption or ""
    foto = update.message.photo

    if legenda.strip().upper() == "TEMA" and foto:
        await update.message.reply_text("Removendo fundo e ajustando bordas... Aguarde.")

        # 1. Baixar a foto
        arquivo_foto = await foto[-1].get_file()
        foto_bytes = await arquivo_foto.download_as_bytearray()
        
        # 2. REMOÇÃO DE FUNDO
        # Transforma os bytes em imagem e remove o background
        img_input = Image.open(io.BytesIO(foto_bytes))
        img_sem_fundo = remove(img_input) # Retorna imagem com transparência (RGBA)

        # 3. Configurações A4 (150 DPI)
        LARGURA_A4 = 1240
        ALTURA_A4 = 1754
        ALTURA_RET = 295  # 5cm
        ESPESSURA_BORDA = 30 # ~5mm em 150 DPI
        RESPIRO = 20 # Espaço interno para o logo não colar na borda

        # 4. Criar Folha Branca Total
        folha = Image.new('RGB', (LARGURA_A4, ALTURA_A4), (255, 255, 255))
        draw = ImageDraw.Draw(folha)

        # 5. Obter cor predominante (do logo já sem fundo)
        cor_borda = get_predominant_color(img_sem_fundo)

        # 6. Desenhar a BORDA de 5mm (Retângulo oco com fundo branco)
        # O retângulo vai de (0,0) até a largura total e 5cm de altura
        draw.rectangle([0, 0, LARGURA_A4, ALTURA_RET], outline=cor_borda, width=ESPESSURA_BORDA)

        # 7. Redimensionar o logo proporcionalmente para caber DENTRO da borda
        largura_max = LARGURA_A4 - (ESPESSURA_BORDA * 2) - (RESPIRO * 2)
        altura_max = ALTURA_RET - (ESPESSURA_BORDA * 2) - (RESPIRO * 2)
        
        img_sem_fundo.thumbnail((largura_max, altura_max), Image.Resampling.LANCZOS)

        # 8. Centralizar o logo dentro do retângulo branco
        pos_x = (LARGURA_A4 - img_sem_fundo.width) // 2
        pos_y = (ALTURA_RET - img_sem_fundo.height) // 2
        
        # Colar usando o canal alpha como máscara para manter a transparência
        folha.paste(img_sem_fundo, (pos_x, pos_y), img_sem_fundo)

        # 9. Salvar e Enviar
        output = io.BytesIO()
        folha.save(output, format="JPEG", quality=95)
        output.seek(0)
        
        await update.message.reply_document(
            document=output, 
            filename="layout_final_com_borda.jpg",
            caption="Tema criado: Fundo limpo, retângulo branco e borda de 5mm."
        )
    else:
        await update.message.reply_text("Comando inválido. Envie a foto com a legenda TEMA.")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL, processar_layout))
    application.run_polling()
