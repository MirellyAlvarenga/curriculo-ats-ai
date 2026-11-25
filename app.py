import json
import os
import re
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

from src.schemas import CurriculoMestre, CurriculoAdaptado
from src.ai_engine import adaptar_curriculo
from src.pdf_generator import gerar_pdf_ats

# Carrega variáveis do .env local (Windows/Linux/Mac)
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="ATS Resume Tailor | Mirelly Alvarenga",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS minimalista para melhorar legibilidade
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stMetric { background-color: #f8f9fa; padding: 12px; border-radius: 8px; border: 1px solid #e9ecef; }
    </style>
""", unsafe_allow_html=True)


def obter_api_key(chave_manual: str) -> str:
    """Resolve a API Key com prioridade: Input manual -> .env -> st.secrets."""
    if chave_manual and chave_manual.strip():
        return chave_manual.strip()
    
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key.strip()
    
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"].strip()
    except Exception:
        pass
        
    return ""


@st.cache_data
def carregar_curriculo_mestre(caminho: str = "data/curriculo_mestre.json") -> CurriculoMestre:
    """Carrega e valida o JSON mestre usando Pydantic."""
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return CurriculoMestre(**dados)


def sanitizar_nome_arquivo(texto: str) -> str:
    """Limpa o nome da empresa/vaga para gerar um nome de arquivo válido no Windows."""
    if not texto.strip():
        return "Geral"
    limpo = re.sub(r'[\\/*?:"<>|]', "", texto)
    limpo = re.sub(r'\s+', "_", limpo.strip())
    return limpo[:40]


def main():
    # --- SIDEBAR: Configurações ---
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        api_key_input = st.text_input(
            "Gemini API Key (Opcional se no .env)",
            type="password",
            help="Se já configurou GEMINI_API_KEY no arquivo .env ou st.secrets, deixe em branco."
        )
        api_key = obter_api_key(api_key_input)
        
        if api_key:
            st.success("API Key detectada e pronta.", icon="✅")
        else:
            st.warning("API Key não encontrada. Insira acima ou configure no .env.", icon="⚠️")
            
        st.divider()
        st.subheader("📂 Base de Dados")
        try:
            curriculo_mestre = carregar_curriculo_mestre()
            st.info(
                f"**Perfil carregado:** {curriculo_mestre.dados_pessoais.nome_exibicao}\n\n"
                f"• {len(curriculo_mestre.experiencias)} experiências\n"
                f"• {len(curriculo_mestre.projetos)} projetos\n"
                f"• {len(curriculo_mestre.certificacoes)} certificações"
            )
        except Exception as e:
            st.error(f"Erro ao carregar `data/curriculo_mestre.json`: {e}")
            st.stop()

    # --- ÁREA PRINCIPAL ---
    st.title("📄 ATS Resume Tailor — Engenharia & Análise de Dados")
    st.caption("Adaptação inteligente de currículo baseada em evidências reais, otimizada para filtros ATS (Gupy, Greenhouse, Lever, LinkedIn).")

    col_entrada, col_resultado = st.columns([1, 1.25], gap="large")

    # --- COLUNA 1: Entrada da Vaga ---
    with col_entrada:
        st.subheader("1. Dados da Vaga")
        
        nome_empresa_vaga = st.text_input(
            "Nome da Empresa ou Título da Vaga",
            placeholder="Ex: Nubank - Analytics Engineer"
        )
        
        idioma_saida = st.selectbox(
            "Idioma de Saída do Currículo",
            options=[
                "Detectar automaticamente pelo idioma da vaga",
                "Português (PT-BR)",
                "Inglês (EN)"
            ]
        )
        
        descricao_vaga = st.text_area(
            "Descrição Completa da Vaga",
            height=340,
            placeholder="Cole aqui os requisitos, responsabilidades e diferenciais da vaga..."
        )
        
        btn_adaptar = st.button("🚀 Adaptar Currículo", type="primary", use_container_width=True)

        if btn_adaptar:
            if not api_key:
                st.error("Por favor, configure sua `GEMINI_API_KEY` antes de continuar.")
            elif len(descricao_vaga.strip()) < 30:
                st.warning("Cole uma descrição de vaga mais completa para uma análise precisa.")
            else:
                with st.spinner("Analisando requisitos da vaga e estruturando currículo sem alucinações..."):
                    try:
                        resultado = adaptar_curriculo(
                            api_key=api_key,
                            curriculo_mestre=curriculo_mestre,
                            descricao_vaga=descricao_vaga,
                            idioma_selecionado=idioma_saida
                        )
                        st.session_state["resultado_adaptado"] = resultado
                        st.session_state["empresa_vaga"] = nome_empresa_vaga
                    except Exception as e:
                        st.error(f"Falha na comunicação com a API do Gemini: {e}")

    # --- COLUNA 2: Diagnóstico, Edição e Download ---
    with col_resultado:
        st.subheader("2. Diagnóstico ATS & Revisão")
        
        if "resultado_adaptado" not in st.session_state:
            st.info("👈 Preencha os dados da vaga ao lado e clique em **Adaptar Currículo** para gerar a versão otimizada.")
        else:
            res: CurriculoAdaptado = st.session_state["resultado_adaptado"]
            
            # 1. Diagnóstico ATS
            m1, m2 = st.columns([1, 2])
            with m1:
                st.metric("Aderência Estimada (ATS)", f"{res.diagnostico_ats.score_aderencia}%")
            with m2:
                st.markdown("**Palavras-chave da vaga identificadas:**")
                st.write(", ".join(res.diagnostico_ats.palavras_chave_vaga))
            
            if res.diagnostico_ats.gaps_e_dicas:
                with st.expander("💡 Pontos de atenção e requisitos ausentes no currículo base", expanded=True):
                    for dica in res.diagnostico_ats.gaps_e_dicas:
                        st.markdown(f"- {dica}")

            st.divider()

            # 2. Revisão Rápida (Human-in-the-loop)
            st.markdown("### ✏️ Revisão Rápida (Editável antes do PDF)")
            st.caption("Qualquer alteração feita nos campos abaixo será refletida imediatamente no PDF baixado.")

            titulo_editado = st.text_input("Título Profissional", value=res.titulo_profissional_adaptado)
            resumo_editado = st.text_area("Resumo Profissional", value=res.resumo_profissional, height=110)

            # Edição de Experiências
            experiencias_editadas = []
            with st.expander("💼 Experiências Profissionais Adaptadas", expanded=False):
                for idx, exp in enumerate(res.experiencias):
                    st.markdown(f"**{exp.cargo} | {exp.empresa}** ({exp.periodo})")
                    bullets_texto = "\n".join(exp.realizacoes)
                    novo_bullets = st.text_area(
                        f"Realizações ({exp.cargo})",
                        value=bullets_texto,
                        height=100,
                        key=f"exp_{idx}",
                        label_visibility="collapsed"
                    )
                    exp_copia = exp.model_copy()
                    exp_copia.realizacoes = [linha.strip() for linha in novo_bullets.split("\n") if linha.strip()]
                    experiencias_editadas.append(exp_copia)

            # Edição de Projetos
            projetos_editados = []
            with st.expander("🚀 Projetos em Destaque Adaptados", expanded=False):
                for idx, proj in enumerate(res.projetos):
                    st.markdown(f"**{proj.nome}**")
                    nova_desc = st.text_area(
                        f"Descrição ({proj.nome})",
                        value=proj.descricao,
                        height=70,
                        key=f"proj_desc_{idx}"
                    )
                    destaques_texto = "\n".join(proj.destaques_tecnicos)
                    novos_destaques = st.text_area(
                        f"Destaques Técnicos ({proj.nome})",
                        value=destaques_texto,
                        height=110,
                        key=f"proj_dest_{idx}"
                    )
                    proj_copia = proj.model_copy()
                    proj_copia.descricao = nova_desc.strip()
                    proj_copia.destaques_tecnicos = [linha.strip() for linha in novos_destaques.split("\n") if linha.strip()]
                    projetos_editados.append(proj_copia)

            # Atualiza objeto final com as edições do usuário
            curriculo_final = res.model_copy()
            curriculo_final.titulo_profissional_adaptado = titulo_editado.strip()
            curriculo_final.resumo_profissional = resumo_editado.strip()
            curriculo_final.experiencias = experiencias_editadas
            curriculo_final.projetos = projetos_editados

            # 3. Geração e Download do PDF
            pdf_bytes = gerar_pdf_ats(curriculo_mestre, curriculo_final)
            sufixo_arquivo = sanitizar_nome_arquivo(st.session_state.get("empresa_vaga", ""))
            nome_arquivo_pdf = f"Curriculo_Mirelly_Alvarenga_{sufixo_arquivo}.pdf"

            st.download_button(
                label=f"⬇️ Baixar PDF Pronto para ATS ({nome_arquivo_pdf})",
                data=pdf_bytes,
                file_name=nome_arquivo_pdf,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

            st.divider()

            # 4. Blocos Copiáveis para Gupy / LinkedIn
            st.markdown("### 📋 Textos Rápidos para Gupy & LinkedIn")
            
            chars_apresentacao = len(res.texto_apresentacao_gupy)
            st.markdown(f"**Apresente-se!** ({chars_apresentacao}/600 caracteres)")
            st.code(res.texto_apresentacao_gupy, language=None)
            
            st.markdown("**Competências / Palavras-chave (separadas por vírgula):**")
            st.code(", ".join(res.competencias_gupy_linkedin), language=None)


if __name__ == "__main__":
    main()