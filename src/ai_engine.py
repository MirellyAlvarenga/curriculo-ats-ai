from google import genai
from google.genai import types
from src.schemas import CurriculoMestre, CurriculoAdaptado


SYSTEM_INSTRUCTION = """
Você é um Especialista Sênior em Recrutamento Técnico (Tech Recruiter) e Otimização de Currículos para sistemas ATS (Gupy, Greenhouse, Lever, Workday).
Sua tarefa é adaptar o Currículo Mestre da candidata para uma vaga específica de tecnologia/dados, maximizando a aderência semântica e de palavras-chave, mantendo o currículo conciso para caber em 1 PÁGINA.

REGRAS INVIOLÁVEIS (ANTI-ALUCINAÇÃO E FORMATAÇÃO):
1. ZERO INVENÇÃO: É estritamente proibido inventar ferramentas, linguagens, frameworks, cargos, empresas, datas, certificações ou métricas numéricas que não estejam explicitamente presentes no JSON do Currículo Mestre.
2. ADAPTAÇÃO HONESTA: Selecione, reordene e reescreva as experiências e projetos reais usando a terminologia exata da descrição da vaga. Mantenha os bullets diretos e objetivos (máximo de 2 linhas por bullet).
3. CONCISÃO PARA 1 PÁGINA:
   - Resumo profissional: máximo de 3 a 4 linhas.
   - Projetos: selecione os 3 destaques técnicos mais aderentes à vaga para cada projeto (em vez de listar todos).
   - Competências categorizadas: crie no máximo 2 categorias compactas (ex: 'Dados & BI' e 'Engenharia & Automação') listando apenas as 12 a 16 hard skills principais exigidas na vaga (não inclua soft skills nesta lista).
   - Certificações: selecione as 4 a 6 certificações mais relevantes para a vaga.
4. PROIBIDO MARKDOWN: Nenhum campo retornado pode conter asteriscos (`*` ou `**`), crases (`` ` ``), hashtags (`#`) ou marcadores de lista (`- ` ou `• `) dentro das strings.
5. IDIOMA DE SAÍDA:
   - Se a instrução pedir 'Detectar automaticamente pelo idioma da vaga', identifique o idioma predominante da descrição da vaga (Português ou Inglês) e gere TODO o currículo, diagnóstico e textos auxiliares nesse mesmo idioma.
   - Se o idioma final for Inglês (EN), traduza com precisão técnica todos os cargos, períodos, descrições, categorias e educação (ex: 'Estágio em Desenvolvimento de Software' -> 'Software Development Intern'). Nunca traduza nomes próprios de empresas, instituições (PUC Minas, IFMG) ou projetos (Climate Data Lake, B2G Market Radar).
6. LIMITE DE CARACTERES GUPY: O campo `texto_apresentacao_gupy` deve ser escrito em primeira pessoa, tom profissional e direto, com NO MÁXIMO 580 caracteres.
"""


def adaptar_curriculo(
    api_key: str,
    curriculo_mestre: CurriculoMestre,
    descricao_vaga: str,
    idioma_selecionado: str
) -> CurriculoAdaptado:
    """Executa a chamada estruturada ao Gemini 2.5 Flash para adaptar o currículo."""
    client = genai.Client(api_key=api_key)

    prompt_usuario = f"""
### CONFIGURAÇÃO DE IDIOMA SOLICITADA:
{idioma_selecionado}

### CURRÍCULO MESTRE (FONTE ÚNICA DA VERDADE EM JSON):
{curriculo_mestre.model_dump_json(indent=2)}

### DESCRIÇÃO DA VAGA ALVO:
{descricao_vaga}

Analise a vaga e gere o JSON estruturado do currículo adaptado seguindo rigorosamente todas as regras do sistema.
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt_usuario,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=CurriculoAdaptado,
            temperature=0.2,  # Baixa temperatura para máxima fidelidade factual
        ),
    )

    # Valida e converte o JSON retornado diretamente no modelo Pydantic
    if response.parsed:
        return response.parsed
    
    return CurriculoAdaptado.model_validate_json(response.text)