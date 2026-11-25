from fpdf import FPDF
from src.schemas import CurriculoMestre, CurriculoAdaptado


class ATSResumePDF(FPDF):
    """Gerador de PDF em coluna única, limpo e 100% legível por parsers ATS."""

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(left=15, top=14, right=15)
        self.set_auto_page_break(auto=True, margin=14)
        self.cor_primaria = (20, 45, 85)      # Azul marinho sóbrio e corporativo
        self.cor_texto = (30, 30, 30)         # Cinza quase preto (melhor leitura que #000 puro)
        self.cor_secundaria = (90, 95, 105)   # Cinza médio para datas/metadados
        self.cor_linha = (200, 205, 215)      # Divisor sutil

    def limpar_texto(self, texto: str) -> str:
        """
        Garante compatibilidade total com fontes padrão Latin-1 (Helvetica) do fpdf2,
        substituindo caracteres Unicode especiais por equivalentes seguros.
        """
        substituicoes = {
            "—": "-",
            "–": "-",
            "•": "-",
            "·": "|",
            "“": '"',
            "”": '"',
            "‘": "'",
            "’": "'",
            "…": "...",
            "\u00a0": " ",
        }
        for orig, dest in substituicoes.items():
            texto = texto.replace(orig, dest)
        return texto.encode("latin-1", errors="replace").decode("latin-1")

    def secao_titulo(self, titulo: str):
        """Renderiza o cabeçalho de seção com linha horizontal limpa."""
        self.ln(3)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*self.cor_primaria)
        self.cell(0, 6, self.limpar_texto(titulo.upper()), new_x="LMARGIN", new_y="NEXT")
        
        y_atual = self.get_y()
        self.set_draw_color(*self.cor_linha)
        self.set_line_width(0.3)
        self.line(15, y_atual, 195, y_atual)
        self.ln(2)

    def render_bullet(self, texto: str):
        """Renderiza um bullet point com recuo alinhado."""
        self.set_font("Helvetica", "", 9.2)
        self.set_text_color(*self.cor_texto)
        
        x_inicial = self.get_x()
        self.cell(4, 4.5, "-", new_x="RIGHT", new_y="TOP")
        self.multi_cell(0, 4.5, self.limpar_texto(texto), new_x="LMARGIN", new_y="NEXT")
        self.set_x(x_inicial)


def gerar_pdf_ats(mestre: CurriculoMestre, adaptado: CurriculoAdaptado) -> bytes:
    """Constrói o PDF ATS-friendly a partir dos dados mestres e adaptados."""
    pdf = ATSResumePDF()
    pdf.add_page()
    dp = mestre.dados_pessoais
    is_en = adaptado.idioma_final == "EN"

    # Rótulos bilíngues de seção
    labels = {
        "resumo": "PROFESSIONAL SUMMARY" if is_en else "RESUMO PROFISSIONAL",
        "experiencia": "WORK EXPERIENCE" if is_en else "EXPERIÊNCIA PROFISSIONAL",
        "projetos": "KEY TECHNICAL PROJECTS" if is_en else "PROJETOS EM DESTAQUE",
        "competencias": "TECHNICAL SKILLS & TOOLS" if is_en else "COMPETÊNCIAS TÉCNICAS",
        "educacao": "EDUCATION" if is_en else "FORMAÇÃO ACADÊMICA",
        "certificacoes": "CERTIFICATIONS" if is_en else "CERTIFICAÇÕES",
        "stack": "Tech Stack" if is_en else "Tecnologias",
    }

    # --- CABEÇALHO ---
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*pdf.cor_primaria)
    pdf.cell(0, 7, pdf.limpar_texto(dp.nome_exibicao.upper()), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*pdf.cor_texto)
    pdf.cell(0, 5.5, pdf.limpar_texto(adaptado.titulo_profissional_adaptado), new_x="LMARGIN", new_y="NEXT")

    # Linha de contatos
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*pdf.cor_secundaria)
    contato_l1 = f"{dp.localizacao}  |  {dp.telefone}  |  {dp.email}"
    pdf.cell(0, 4.5, pdf.limpar_texto(contato_l1), new_x="LMARGIN", new_y="NEXT")

    contato_l2 = f"LinkedIn: {dp.linkedin}  |  GitHub: {dp.github}"
    pdf.cell(0, 4.5, pdf.limpar_texto(contato_l2), new_x="LMARGIN", new_y="NEXT")

    contato_l3 = f"Portfolio: {dp.portfolio}  |  Live Dashboard: {dp.dashboard_producao}"
    pdf.cell(0, 4.5, pdf.limpar_texto(contato_l3), new_x="LMARGIN", new_y="NEXT")

    # --- RESUMO PROFISSIONAL ---
    pdf.secao_titulo(labels["resumo"])
    pdf.set_font("Helvetica", "", 9.3)
    pdf.set_text_color(*pdf.cor_texto)
    pdf.multi_cell(0, 4.6, pdf.limpar_texto(adaptado.resumo_profissional), new_x="LMARGIN", new_y="NEXT")

    # --- EXPERIÊNCIA PROFISSIONAL ---
    pdf.secao_titulo(labels["experiencia"])
    for exp in adaptado.experiencias:
        pdf.set_font("Helvetica", "B", 9.8)
        pdf.set_text_color(*pdf.cor_texto)
        cabecalho_exp = f"{exp.cargo} - {exp.empresa}"
        
        # Cargo/Empresa à esquerda e Período à direita
        largura_periodo = 45
        pdf.cell(180 - largura_periodo, 5, pdf.limpar_texto(cabecalho_exp), new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "I", 8.8)
        pdf.set_text_color(*pdf.cor_secundaria)
        pdf.cell(largura_periodo, 5, pdf.limpar_texto(exp.periodo), align="R", new_x="LMARGIN", new_y="NEXT")

        for item in exp.realizacoes:
            pdf.render_bullet(item)

        if exp.tecnologias:
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(*pdf.cor_secundaria)
            tech_str = f"{labels['stack']}: {', '.join(exp.tecnologias)}"
            pdf.cell(0, 4.5, pdf.limpar_texto(tech_str), new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(1.8)

    # --- PROJETOS EM DESTAQUE ---
    pdf.secao_titulo(labels["projetos"])
    for proj in adaptado.projetos:
        pdf.set_font("Helvetica", "B", 9.8)
        pdf.set_text_color(*pdf.cor_texto)
        pdf.cell(0, 5, pdf.limpar_texto(proj.nome), new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9.1)
        pdf.multi_cell(0, 4.4, pdf.limpar_texto(proj.descricao), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.8)

        for destaque in proj.destaques_tecnicos:
            pdf.render_bullet(destaque)

        if proj.stack:
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(*pdf.cor_secundaria)
            stack_str = f"{labels['stack']}: {', '.join(proj.stack)}"
            pdf.cell(0, 4.5, pdf.limpar_texto(stack_str), new_x="LMARGIN", new_y="NEXT")

        pdf.ln(1.8)

    # --- COMPETÊNCIAS TÉCNICAS ---
    pdf.secao_titulo(labels["competencias"])
    for cat in adaptado.competencias_categorizadas:
        pdf.set_font("Helvetica", "B", 9.1)
        pdf.set_text_color(*pdf.cor_texto)
        prefixo = f"{cat.categoria}: "
        largura_prefixo = pdf.get_string_width(pdf.limpar_texto(prefixo)) + 1
        
        pdf.cell(largura_prefixo, 4.6, pdf.limpar_texto(prefixo), new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "", 9.1)
        pdf.multi_cell(0, 4.6, pdf.limpar_texto(", ".join(cat.itens)), new_x="LMARGIN", new_y="NEXT")

    # --- FORMAÇÃO ACADÊMICA ---
    pdf.secao_titulo(labels["educacao"])
    for edu in adaptado.educacao:
        pdf.set_font("Helvetica", "B", 9.3)
        pdf.set_text_color(*pdf.cor_texto)
        curso_inst = f"{edu.curso} - {edu.instituicao}"
        pdf.cell(140, 4.8, pdf.limpar_texto(curso_inst), new_x="RIGHT", new_y="TOP")
        
        pdf.set_font("Helvetica", "I", 8.8)
        pdf.set_text_color(*pdf.cor_secundaria)
        pdf.cell(40, 4.8, pdf.limpar_texto(edu.periodo), align="R", new_x="LMARGIN", new_y="NEXT")

    # --- CERTIFICAÇÕES ---
    if adaptado.certificacoes_selecionadas:
        pdf.secao_titulo(labels["certificacoes"])
        pdf.set_font("Helvetica", "", 8.8)
        pdf.set_text_color(*pdf.cor_texto)
        certs_texto = "  |  ".join(adaptado.certificacoes_selecionadas)
        pdf.multi_cell(0, 4.5, pdf.limpar_texto(certs_texto), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())