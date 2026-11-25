from google import genai
from google.genai import types
from src.schemas import CurriculoMestre, CurriculoAdaptado


SYSTEM_INSTRUCTION = """
Você é um Especialista Sênior em Recrutamento Técnico (Tech Recruiter) e Otimização de Currículos para sistemas ATS (Gupy, Greenhouse, Lever, Workday).
Sua tarefa é adaptar o Currículo Mestre da candidata para uma vaga específica de tecnologia/dados, maximizando a aderência semântica e de palavras-chave.

REGRAS INVIOLÁVEIS (ANTI-ALUCINAÇÃO E FORMATAÇÃO):
1. ZERO INVENÇÃO: É estritamente proibido inventar ferramentas, linguagens, frameworks, cargos, empresas, datas, certificações ou métricas numéricas que não estejam explicitamente presentes no JSON do Currículo Mestre.
2. ADAPTAÇÃO HONESTA: Você deve apenas selecionar, reordenar e reescrever as experiências e projetos reais usando a terminologia exata da descrição da vaga (ex: se o currículo diz "pipelines de ETL" e a vaga pede "ingestão e transformação de dados", ajuste a redação mantendo a veracidade técnica).
3. PROIBIDO MARKDOWN: Nenhum campo retornado pode conter asteriscos (`*` ou `**`), crases (`` ` ``), hashtags (`#`) ou marcadores de lista (`- ` ou `• `) dentro das strings. O texto deve ser limpo para renderização direta em PDF e colagem em formulários web.
4. IDIOMA DE SAÍDA:
   - Se a instrução pedir 'Detectar automaticamente pelo idioma da vaga', identifique o idioma predominante da descrição da vaga (Português ou Inglês) e gere TODO o currículo, diagnóstico e textos auxiliares nesse mesmo idioma.
   - Se o idioma final for Inglês (EN), traduza com precisão técnica todos os cargos, períodos, descrições, categorias e educação (ex: 'Graduanda em Engenharia de Software' -> 'B.Sc. Student in Software Engineering'). Nunca traduza nomes próprios de empresas, instituições (PUC Minas, IFMG) ou projetos (Climate Data Lake, B2G Market Radar).
5. LIMITE DE CARACTERES GUPY: O campo `texto_apresentacao_gupy` deve ser escrito em primeira pessoa, tom profissional e direto, com NO MÁXIMO 580 caracteres (margem de segurança abaixo do limite de 600 caracteres).
6. ORDENAÇÃO POR RELEVÂNCIA: Ordene projetos, bullets de experiência e listas de competências colocando primeiro o que tem maior impacto para a vaga alvo.
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
        model="gemini-2.5-flash",
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