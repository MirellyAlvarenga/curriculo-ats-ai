from fpdf import FPDF
from src.schemas import CurriculoMestre, CurriculoAdaptado


class ATSResumePDF(FPDF):
    """Gerador de PDF em coluna única, 1 página, limpo e 100% legível por parsers ATS."""

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(left=12, top=10, right=12)
        self.set_auto_page_break(auto=True, margin=10)
        self.cor_primaria = (20, 45, 85)      # Azul marinho corporativo
        self.cor_texto = (30, 30, 30)         # Cinza escuro
        self.cor_secundaria = (90, 95, 105)   # Cinza médio para metadados
        self.cor_linha = (200, 205, 215)      # Divisor sutil

    def limpar_texto(self, texto: str) -> str:
        """Garante compatibilidade total com fontes padrão Latin-1 (Helvetica) do fpdf2."""
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
        """Renderiza o cabeçalho de seção com linha horizontal e espaçamento correto."""
        self.ln(2.2)
        self.set_font("Helvetica", "B", 9.8)
        self.set_text_color(*self.cor_primaria)
        self.cell(0, 5, self.limpar_texto(titulo.upper()), new_x="LMARGIN", new_y="NEXT")
        
        y_atual = self.get_y()
        self.set_draw_color(*self.cor_linha)
        self.set_line_width(0.25)
        self.line(12, y_atual, 198, y_atual)
        self.ln(1.8)

    def render_bullet(self, texto: str):
        """Renderiza um bullet point com recuo alinhado."""
        self.set_font("Helvetica", "", 8.7)
        self.set_text_color(*self.cor_texto)
        
        x_inicial = self.get_x()
        self.cell(3.5, 4.0, "-", new_x="RIGHT", new_y="TOP")
        self.multi_cell(0, 4.0, self.limpar_texto(texto), new_x="LMARGIN", new_y="NEXT")
        self.set_x(x_inicial)


def gerar_pdf_ats(mestre: CurriculoMestre, adaptado: CurriculoAdaptado) -> bytes:
    """Constrói o PDF ATS-friendly compacto de 1 página."""
    pdf = ATSResumePDF()
    pdf.add_page()
    dp = mestre.dados_pessoais
    is_en = adaptado.idioma_final == "EN"

    labels = {
        "resumo": "PROFESSIONAL SUMMARY" if is_en else "RESUMO PROFISSIONAL",
        "experiencia": "WORK EXPERIENCE" if is_en else "EXPERIÊNCIA PROFISSIONAL",
        "projetos": "KEY TECHNICAL PROJECTS" if is_en else "PROJETOS EM DESTAQUE",
        "competencias": "TECHNICAL SKILLS" if is_en else "COMPETÊNCIAS TÉCNICAS",
        "educacao": "EDUCATION" if is_en else "FORMAÇÃO ACADÊMICA",
        "certificacoes": "CERTIFICATIONS" if is_en else "CERTIFICAÇÕES",
        "stack": "Tech Stack" if is_en else "Tecnologias",
    }

    # --- CABEÇALHO ---
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*pdf.cor_primaria)
    pdf.cell(0, 6.2, pdf.limpar_texto(dp.nome_exibicao.upper()), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 9.8)
    pdf.set_text_color(*pdf.cor_texto)
    pdf.cell(0, 4.8, pdf.limpar_texto(adaptado.titulo_profissional_adaptado), new_x="LMARGIN", new_y="NEXT")

    # Contatos (omite telefone se for vazio ou placeholder)
    pdf.set_font("Helvetica", "", 8.2)
    pdf.set_text_color(*pdf.cor_secundaria)
    
    partes_contato = [dp.localizacao]
    if dp.telefone and dp.telefone.strip() not in ("", "(00) 00000-0000"):
        partes_contato.append(dp.telefone.strip())
    partes_contato.append(dp.email)
    
    pdf.cell(0, 4.0, pdf.limpar_texto("  |  ".join(partes_contato)), new_x="LMARGIN", new_y="NEXT")

    contato_l2 = f"LinkedIn: {dp.linkedin}  |  GitHub: {dp.github}"
    pdf.cell(0, 4.0, pdf.limpar_texto(contato_l2), new_x="LMARGIN", new_y="NEXT")

    contato_l3 = f"Portfolio: {dp.portfolio}  |  Live Dashboard: {dp.dashboard_producao}"
    pdf.cell(0, 4.0, pdf.limpar_texto(contato_l3), new_x="LMARGIN", new_y="NEXT")

    # --- RESUMO PROFISSIONAL ---
    pdf.secao_titulo(labels["resumo"])
    pdf.set_font("Helvetica", "", 8.8)
    pdf.set_text_color(*pdf.cor_texto)
    pdf.multi_cell(0, 4.1, pdf.limpar_texto(adaptado.resumo_profissional), new_x="LMARGIN", new_y="NEXT")

    # --- EXPERIÊNCIA PROFISSIONAL ---
    pdf.secao_titulo(labels["experiencia"])
    largura_util = 186  # 210mm (A4) - 24mm (margens)
    for exp in adaptado.experiencias:
        pdf.set_font("Helvetica", "B", 9.2)
        pdf.set_text_color(*pdf.cor_texto)
        cabecalho_exp = f"{exp.cargo} - {exp.empresa}"
        
        largura_periodo = 42
        pdf.cell(largura_util - largura_periodo, 4.5, pdf.limpar_texto(cabecalho_exp), new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "I", 8.4)
        pdf.set_text_color(*pdf.cor_secundaria)
        pdf.cell(largura_periodo, 4.5, pdf.limpar_texto(exp.periodo), align="R", new_x="LMARGIN", new_y="NEXT")

        for item in exp.realizacoes:
            pdf.render_bullet(item)

        if exp.tecnologias:
            pdf.set_font("Helvetica", "I", 8.1)
            pdf.set_text_color(*pdf.cor_secundaria)
            tech_str = f"{labels['stack']}: {', '.join(exp.tecnologias)}"
            pdf.cell(0, 4.0, pdf.limpar_texto(tech_str), new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(1.2)

    # --- PROJETOS EM DESTAQUE ---
    pdf.secao_titulo(labels["projetos"])
    for proj in adaptado.projetos:
        pdf.set_font("Helvetica", "B", 9.2)
        pdf.set_text_color(*pdf.cor_texto)
        pdf.cell(0, 4.5, pdf.limpar_texto(proj.nome), new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 8.6)
        pdf.multi_cell(0, 3.9, pdf.limpar_texto(proj.descricao), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.5)

        for destaque in proj.destaques_tecnicos:
            pdf.render_bullet(destaque)

        if proj.stack:
            pdf.set_font("Helvetica", "I", 8.1)
            pdf.set_text_color(*pdf.cor_secundaria)
            stack_str = f"{labels['stack']}: {', '.join(proj.stack)}"
            pdf.cell(0, 4.0, pdf.limpar_texto(stack_str), new_x="LMARGIN", new_y="NEXT")

        pdf.ln(1.2)

    # --- COMPETÊNCIAS TÉCNICAS (Compacta, sem sobreposição) ---
    pdf.secao_titulo(labels["competencias"])
    for cat in adaptado.competencias_categorizadas:
        pdf.set_font("Helvetica", "", 8.6)
        pdf.set_text_color(*pdf.cor_texto)
        linha_cat = f"{cat.categoria}: {', '.join(cat.itens)}"
        pdf.multi_cell(0, 4.0, pdf.limpar_texto(linha_cat), new_x="LMARGIN", new_y="NEXT")

    # --- FORMAÇÃO ACADÊMICA ---
    pdf.secao_titulo(labels["educacao"])
    for edu in adaptado.educacao:
        pdf.set_font("Helvetica", "B", 8.8)
        pdf.set_text_color(*pdf.cor_texto)
        curso_inst = f"{edu.curso} - {edu.instituicao}"
        pdf.cell(largura_util - 38, 4.3, pdf.limpar_texto(curso_inst), new_x="RIGHT", new_y="TOP")
        
        pdf.set_font("Helvetica", "I", 8.4)
        pdf.set_text_color(*pdf.cor_secundaria)
        pdf.cell(38, 4.3, pdf.limpar_texto(edu.periodo), align="R", new_x="LMARGIN", new_y="NEXT")

    # --- CERTIFICAÇÕES ---
    if adaptado.certificacoes_selecionadas:
        pdf.secao_titulo(labels["certificacoes"])
        pdf.set_font("Helvetica", "", 8.2)
        pdf.set_text_color(*pdf.cor_texto)
        certs_texto = "  |  ".join(adaptado.certificacoes_selecionadas)
        pdf.multi_cell(0, 3.9, pdf.limpar_texto(certs_texto), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())