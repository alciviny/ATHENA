from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def criar_curriculo():
    # Nome do arquivo de saída
    filename = "Curriculo_Alcionis_Vinicius.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=20, bottomMargin=20)

    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo Personalizado para o Nome
    style_nome = ParagraphStyle(
        'Nome',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.darkblue
    )
    
    # Estilo para Subtítulo (Cargo)
    style_cargo = ParagraphStyle(
        'Cargo',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=12
    )

    # Estilo para Contato
    style_contato = ParagraphStyle(
        'Contato',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=10
    )

    # Estilo para Títulos de Seção
    style_secao = ParagraphStyle(
        'Secao',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=8,
        spaceAfter=6,
        textColor=colors.darkblue,
        borderPadding=2,
        borderColor=colors.lightgrey,
        borderWidth=0,
        backColor=None
    )

    # Estilo Normal
    style_normal = styles['Normal']
    style_normal.spaceAfter = 6
    style_normal.fontSize = 11

    # Estilo para Bullet Points
    style_bullet = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=11,
        leftIndent=15,
        bulletIndent=5,
        spaceAfter=3,
    )

    story = []

    # --- Cabeçalho ---
    story.append(Paragraph("ALCIONIS VINICIUS DOS SANTOS SILVA", style_nome))
    story.append(Paragraph("Assistente Administrativo | Auxiliar Administrativo | Departamento Pessoal", style_cargo))
    story.append(Paragraph("São Luís - MA | Telefone: 98989025862", style_contato))
    story.append(Paragraph("Email: alcionisviniciusdossantossilva@gmail.com", style_contato))
    
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceBefore=5, spaceAfter=5))

    # --- Objetivo ---
    story.append(Paragraph("OBJETIVO PROFISSIONAL", style_secao))
    texto_objetivo = ("Profissional da área administrativa com experiência em Departamento Pessoal e rotinas administrativas, "
                      "atuando na organização de processos, controle de informações e apoio à gestão. "
                      "Possuo conhecimentos em tecnologia e desenvolvimento de sistemas aplicados à automação de tarefas "
                      "administrativas e melhoria da eficiência operacional.")
    story.append(Paragraph(texto_objetivo, style_normal))

    # --- Experiência ---
    story.append(Paragraph("EXPERIÊNCIA PROFISSIONAL", style_secao))
    
    # Empresa 1
    story.append(Paragraph("<b>Emko Construtora</b> – Jovem Aprendiz / Assistente de Departamento Pessoal", style_normal))
    story.append(Paragraph("<i>2024 – 2025</i>", style_normal))
    
    atividades = [
        "Manutenção e controle de ponto dos colaboradores",
        "Entrega de rescisões e acompanhamento de férias",
        "Atendimento e contato direto com colaboradores",
        "Organização, arquivamento e gestão documental",
        "Elaboração de ASOs e apoio às rotinas de Departamento Pessoal"
    ]
    for item in atividades:
        story.append(Paragraph(f"• {item}", style_bullet))

    # --- Formação ---
    story.append(Paragraph("FORMAÇÃO", style_secao))
    story.append(Paragraph("• <b>Ensino Médio</b> – Centro de Ensino Nerval Lebre Santiago", style_bullet))
    story.append(Paragraph("• <b>Curso Técnico em Administração</b> – Grau Técnico", style_bullet))

    # --- Cursos Complementares ---
    story.append(Paragraph("CURSOS COMPLEMENTARES", style_secao))
    cursos = [
        "Rotinas Administrativas – FIEMA/IEL",
        "Desenvolvimento de Sistemas – SENAI",
        "Informática – WR Cursos"
    ]
    for curso in cursos:
        story.append(Paragraph(f"• {curso}", style_bullet))

    # --- Habilidades ---
    story.append(Paragraph("HABILIDADES", style_secao))
    
    story.append(Paragraph("<b>Administrativas:</b>", style_normal))
    story.append(Paragraph("• Boas práticas arquivológicas", style_bullet))
    story.append(Paragraph("• Organização de documentos e informações", style_bullet))
    
    story.append(Spacer(1, 3))
    story.append(Paragraph("<b>Tecnológicas:</b>", style_normal))
    story.append(Paragraph("• Excel e análise de dados com Pandas", style_bullet))
    story.append(Paragraph("• Criação de sistemas e dashboards administrativos", style_bullet))
    story.append(Paragraph("• Automação de processos administrativos", style_bullet))

    story.append(Spacer(1, 3))
    story.append(Paragraph("<b>Comportamentais:</b>", style_normal))
    story.append(Paragraph("• Ótima escrita", style_bullet))
    story.append(Paragraph("• Boa comunicação e oratória", style_bullet))
    story.append(Paragraph("• Facilidade em relações interpessoais", style_bullet))

    # --- Diferencial ---
    story.append(Paragraph("DIFERENCIAL", style_secao))
    texto_diferencial = ("Conhecimentos em tecnologia aplicados ao setor administrativo, com experiência em "
                         "automações de notas fiscais, organização de dados empresariais e cálculo automático "
                         "de folha de ponto e folha trabalhista.")
    story.append(Paragraph(texto_diferencial, style_normal))

    # Gerar PDF
    doc.build(story)
    print(f"PDF '{filename}' gerado com sucesso!")

if __name__ == "__main__":
    criar_curriculo()
