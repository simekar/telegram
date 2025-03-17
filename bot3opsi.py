import os
import re
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Token Bot dan Password
TOKEN = "7219779593:AAHhZ0NTDl3KgPUe1GavTPY5Er9rHqY-tao"
PASSWORD = "Faizganteng"
user_data = {}

async def start(update: Update, context: CallbackContext):
    """Memulai bot dan meminta password."""
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {"authenticated": False, "mode": None, "numbers": [], "txt_file": None, "vcf_file": None}
    
    await update.message.reply_text(
        "🔒 Masukkan password untuk mengakses bot:",
        reply_markup=ReplyKeyboardRemove()
    )

async def check_password(update: Update, context: CallbackContext):
    """Memeriksa password yang dimasukkan user."""
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in user_data and user_data[user_id]["authenticated"]:
        await update.message.reply_text("✅ Anda sudah login. Gunakan perintah:\n - `/convert`\n - `/split`\n - `/pesan_to_vcf`")
        return

    if text == PASSWORD:
        user_data[user_id]["authenticated"] = True
        user_data[user_id]["mode"] = None
        await update.message.reply_text("✅ Password benar! Gunakan perintah:\n - `/convert`\n - `/split`\n - `/pesan_to_vcf`")
    else:
        await update.message.reply_text("❌ Password salah! Coba lagi.")

async def pesan_to_vcf(update: Update, context: CallbackContext):
    """Memulai mode Pesan To VCF."""
    user_id = update.effective_user.id
    if user_id not in user_data or not user_data[user_id]["authenticated"]:
        await update.message.reply_text("🔒 Masukkan password terlebih dahulu dengan perintah /start")
        return

    user_data[user_id]["mode"] = "pesan_to_vcf"
    user_data[user_id]["numbers"] = []
    await update.message.reply_text("📌 Silahkan ketik nomor yang mau dijadikan VCF.")

async def convert(update: Update, context: CallbackContext):
    """Mengatur mode konversi TXT ke VCF."""
    user_id = update.effective_user.id
    if user_id not in user_data or not user_data[user_id]["authenticated"]:
        await update.message.reply_text("🔒 Masukkan password terlebih dahulu dengan perintah /start")
        return

    user_data[user_id]["mode"] = "convert"
    await update.message.reply_text("📂 Kirim file .txt yang berisi daftar nomor telepon.")

async def split(update: Update, context: CallbackContext):
    """Mengatur mode pemisahan VCF."""
    user_id = update.effective_user.id
    if user_id not in user_data or not user_data[user_id]["authenticated"]:
        await update.message.reply_text("🔒 Masukkan password terlebih dahulu dengan perintah /start")
        return

    user_data[user_id]["mode"] = "split"
    await update.message.reply_text("📂 Kirim file .vcf yang ingin dipisah.")

async def handle_document(update: Update, context: CallbackContext):
    """Menerima dan memproses file TXT atau VCF."""
    user_id = update.effective_user.id
    if user_id not in user_data or not user_data[user_id]["authenticated"]:
        await update.message.reply_text("🔒 Masukkan password terlebih dahulu dengan perintah /start")
        return

    mode = user_data[user_id].get("mode")
    if mode not in ["convert", "split"]:
        await update.message.reply_text("⚠️ Pilih mode terlebih dahulu dengan perintah /convert atau /split")
        return

    file = update.message.document
    file_name = file.file_name.lower()
    file_path = f"{user_id}_{file_name}"

    new_file = await context.bot.get_file(file.file_id)
    await new_file.download_to_drive(file_path)

    if mode == "convert" and file_name.endswith(".txt"):
        user_data[user_id]["txt_file"] = file_path
        await update.message.reply_text("📌 Masukkan nama kontak untuk file VCF.")

    elif mode == "split" and file_name.endswith(".vcf"):
        user_data[user_id]["vcf_file"] = file_path
        await update.message.reply_text("📌 Masukkan nama baru untuk kontak dalam file VCF yang dipisah.")

    else:
        await update.message.reply_text("❌ File tidak valid. Kirim file yang sesuai dengan mode yang dipilih.")

async def handle_text(update: Update, context: CallbackContext):
    """Memproses input teks dari user."""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id in user_data and not user_data[user_id]["authenticated"]:
        await check_password(update, context)
        return

    mode = user_data[user_id].get("mode")

    if mode == "pesan_to_vcf":
        if not user_data[user_id]["numbers"]:
            numbers = text.split()  # Bisa menerima lebih dari satu nomor
            user_data[user_id]["numbers"] = numbers
            await update.message.reply_text("📌 Mau dikasih nama apa?")
        else:
            name = text
            numbers = user_data[user_id]["numbers"]
            vcf_file = f"{user_id}_pesan_to_vcf.vcf"

            with open(vcf_file, "w") as vcf:
                for i, number in enumerate(numbers, start=1):
                    vcf.write(f"BEGIN:VCARD\nVERSION:3.0\nFN:{name} {i}\nTEL:{number}\nEND:VCARD\n")

            await update.message.reply_document(document=open(vcf_file, "rb"), filename=f"{name}.vcf")
            os.remove(vcf_file)
            user_data[user_id]["mode"] = None
            user_data[user_id]["numbers"] = []

    elif mode == "convert" and user_data[user_id].get("txt_file"):
        txt_file = user_data[user_id]["txt_file"]
        vcf_file = f"{user_id}_contacts.vcf"

        with open(txt_file, "r") as f, open(vcf_file, "w") as vcf:
            numbers = f.read().splitlines()
            for i, number in enumerate(numbers, start=1):
                vcf.write(f"BEGIN:VCARD\nVERSION:3.0\nFN:{text} {i}\nTEL:{number}\nEND:VCARD\n")

        await update.message.reply_document(document=open(vcf_file, "rb"), filename=f"{text}.vcf")
        os.remove(txt_file)
        os.remove(vcf_file)
        user_data[user_id]["mode"] = None

    elif mode == "split" and user_data[user_id].get("vcf_file"):
        vcf_file = user_data[user_id]["vcf_file"]
        with open(vcf_file, "r") as f:
            contacts = f.read().split("END:VCARD\n")
            contacts = [c + "END:VCARD\n" for c in contacts if c.strip()]

        split_files = []
        for i in range(0, len(contacts), 50):
            part_file = f"{user_id}_part_{i//50 + 1}.vcf"
            with open(part_file, "w") as part:
                for contact in contacts[i:i+50]:
                    part.write(contact)
            split_files.append(part_file)

        for i, file in enumerate(split_files, start=1):
            await update.message.reply_document(document=open(file, "rb"), filename=f"{text}_{i}.vcf")
            os.remove(file)

        os.remove(vcf_file)
        user_data[user_id]["mode"] = None

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("convert", convert))
    app.add_handler(CommandHandler("split", split))
    app.add_handler(CommandHandler("pesan_to_vcf", pesan_to_vcf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()

if __name__ == "__main__":
    main()