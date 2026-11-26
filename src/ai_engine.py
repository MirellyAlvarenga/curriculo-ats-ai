import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
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
7. ESTIMATIVA SALARIAL (CLT E PJ): Analise o nível real de exigência da vaga (não apenas o título, mas a complexidade das ferramentas pedidas), o modelo (remoto, híbrido, presencial) e a região/moeda. Estime uma faixa realista de mercado no Brasil (em BRL) ou exterior (em USD, se a vaga for internacional em dólar). Para o cálculo PJ, aplique um fator de conversão entre 1,45x e 1,6x sobre o bruto CLT para cobrir impostos (Simples Nacional), férias, 13º, FGTS e benefícios. Forneça um valor alvo único tanto para CLT quanto para PJ para facilitar o preenchimento direto em formulários como a Gupy.
"""

# Ordem de prioridade atualizada para a geração 3.8 + fallback automático
MODELOS_PRIORIDADE = [
    "gemini-3.8-flash",
    "gemini-3.8-flash-lite",
    "gemini-3.5-flash",
]


def adaptar_curriculo(
    api_key: str,
    curriculo_mestre: CurriculoMestre,
    descricao_vaga: str,
    idioma_selecionado: str
) -> CurriculoAdaptado:
    """Executa a chamada estruturada ao Gemini com retry exponencial e fallback de modelo."""
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

    ultimo_erro = None

    for modelo in MODELOS_PRIORIDADE:
        for tentativa in range(3):  # Até 3 tentativas por modelo
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt_usuario,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        response_schema=CurriculoAdaptado,
                        temperature=0.2,
                    ),
                )

                if response.parsed:
                    return response.parsed

                return CurriculoAdaptado.model_validate_json(response.text)

            except APIError as e:
                ultimo_erro = e
                # 404 (modelo indisponível/descontinuado): pula direto para o próximo modelo da lista
                if e.code == 404:
                    break
                # 503 (sobrecarga) ou 429 (rate limit): aguarda e tenta novamente
                if e.code in (503, 429):
                    tempo_espera = 2 ** (tentativa + 1)  # 2s, 4s, 8s
                    time.sleep(tempo_espera)
                    continue
                # Erros definitivos (ex: 400 API Key inválida, 403 permissão) interrompem imediatamente
                raise e

    raise RuntimeError(
        f"Nenhum modelo Gemini pôde processar a requisição no momento. Detalhe: {ultimo_erro}"
    )