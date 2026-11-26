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
7. ESTIMATIVA SALARIAL (CLT E PJ): Analise o nível real de exigência da vaga, o modelo (remoto, híbrido, presencial) e a região/moeda. Estime uma faixa realista de mercado no Brasil (em BRL) ou exterior (em USD, se a vaga for internacional em dólar). Para o cálculo PJ, aplique um fator de conversão entre 1,45x e 1,6x sobre o bruto CLT para cobrir impostos, férias, 13º, FGTS e benefícios. Forneça um valor alvo único tanto para CLT quanto para PJ.
"""

# Modelos mais rápidos primeiro (flash-lite tem latência baixíssima para JSON estruturado)
MODELOS_PRIORIDADE = [
    "gemini-3.8-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
]


def adaptar_curriculo(
    api_key: str,
    curriculo_mestre: CurriculoMestre,
    descricao_vaga: str,
    idioma_selecionado: str
) -> CurriculoAdaptado:
    """Executa a chamada estruturada ao Gemini com baixa latência, thinking desligado e fallback rápido."""
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=45_000)  # Timeout máximo de 45s por tentativa
    )

    prompt_usuario = (
        f"IDIOMA SOLICITADO: {idioma_selecionado}\n\n"
        f"CURRÍCULO MESTRE:\n{curriculo_mestre.model_dump_json()}\n\n"
        f"DESCRIÇÃO DA VAGA:\n{descricao_vaga}"
    )

    ultimo_erro = None

    for modelo in MODELOS_PRIORIDADE:
        for tentativa in range(2):  # Máximo 2 tentativas rápidas por modelo
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt_usuario,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        response_schema=CurriculoAdaptado,
                        temperature=0.2,
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                    ),
                )

                if response.parsed:
                    return response.parsed

                return CurriculoAdaptado.model_validate_json(response.text)

            except APIError as e:
                ultimo_erro = e
                if e.code == 404:
                    break
                if e.code in (503, 429):
                    time.sleep(1.5)
                    continue
                raise e
            except Exception as e:
                # Captura timeouts de rede e tenta o próximo modelo imediatamente
                ultimo_erro = e
                break

    raise RuntimeError(
        f"Os servidores do Gemini demoraram a responder. Tente novamente em alguns segundos. Detalhe: {ultimo_erro}"
    )