import os
import comtypes.client

def converter_todos_para_pdf(pasta_arquivos):
    word = comtypes.client.CreateObject('Word.Application')
    word.Visible = False

    for arquivo in os.listdir(pasta_arquivos):
        if arquivo.endswith(('.doc', '.docx')):
            caminho_completo = os.path.join(pasta_arquivos, arquivo)
            nome_base = os.path.splitext(arquivo)[0]
            caminho_pdf = os.path.join(pasta_arquivos, nome_base + '.pdf')

            print(f"Convertendo: {arquivo} -> {nome_base}.pdf")

            doc = word.Documents.Open(caminho_completo)
            doc.SaveAs(caminho_pdf, FileFormat=17)  # 17 = PDF
            doc.Close()

    word.Quit()
    print("Conversão concluída com sucesso.")

# Caminho relativo para a pasta com arquivos Word
pasta = r'Base\words'
converter_todos_para_pdf(pasta)




