from typing import List, Literal
from pydantic import BaseModel, Field


# ==========================================
# SCHEMAS DE ENTRADA (Currículo Mestre JSON)
# ==========================================

class DadosPessoais(BaseModel):
    nome_exibicao: str
    nome_completo: str
    titulo_base: str
    localizacao: str
    email: str
    portfolio: str
    dashboard_producao: str
    linkedin: str
    github: str
    telefone: str


class ExperienciaMestre(BaseModel):
    cargo: str
    empresa: str
    periodo: str
    modelo: str = ""
    realizacoes: List[str]
    tecnologias: List[str]


class ProjetoMestre(BaseModel):
    nome: str
    subtitulo: str
    descricao: str
    destaques_tecnicos: List[str]
    stack: List[str]


class CompetenciasMestre(BaseModel):
    engenharia_de_dados: List[str]
    bi_e_analise: List[str]
    automacao_e_desenvolvimento: List[str]
    soft_skills: List[str]
    idiomas: List[str]


class CertificacaoMestre(BaseModel):
    titulo: str
    emissor: str
    data: str


class EducacaoMestre(BaseModel):
    curso: str
    instituicao: str
    periodo: str


class CurriculoMestre(BaseModel):
    dados_pessoais: DadosPessoais
    perfil_base: str
    experiencias: List[ExperienciaMestre]
    projetos: List[ProjetoMestre]
    competencias: CompetenciasMestre
    certificacoes: List[CertificacaoMestre]
    educacao: List[EducacaoMestre]


# ==========================================
# SCHEMAS DE SAÍDA (Structured Outputs Gemini)
# ==========================================

class DiagnosticoATS(BaseModel):
    score_aderencia: int = Field(
        description="Score estimado de aderência entre 0 e 100 baseado estritamente nas evidências reais do currículo mestre frente à vaga."
    )
    palavras_chave_vaga: List[str] = Field(
        description="Lista das 8 a 15 principais hard skills, ferramentas e conceitos exigidos na descrição da vaga."
    )
    gaps_e_dicas: List[str] = Field(
        description="Lista curta (2 a 4 itens) apontando requisitos da vaga que não constam no currículo mestre e dicas honestas de como contornar."
    )


class ExperienciaAdaptada(BaseModel):
    cargo: str = Field(description="Cargo exato ou traduzido fielmente conforme o idioma de saída.")
    empresa: str
    periodo: str = Field(description="Período exato ou traduzido fielmente (ex: 'Ago 2026 - Presente' ou 'Aug 2026 - Present').")
    realizacoes: List[str] = Field(
        description="Bullet points adaptados e reordenados para destacar aderência à vaga, sem asteriscos ou Markdown."
    )
    tecnologias: List[str]


class ProjetoAdaptado(BaseModel):
    nome: str
    descricao: str = Field(description="Resumo objetivo do projeto adaptado ao foco da vaga, sem Markdown.")
    destaques_tecnicos: List[str] = Field(
        description="3 a 5 bullets técnicos selecionados e adaptados com os termos exatos da vaga, sem Markdown."
    )
    stack: List[str]


class CategoriaCompetenciaAdaptada(BaseModel):
    categoria: str = Field(description="Nome da categoria (ex: 'Engenharia de Dados', 'BI & Análise de Dados' ou equivalente em inglês).")
    itens: List[str] = Field(description="Ferramentas e habilidades reais ordenadas por relevância para a vaga.")


class EducacaoAdaptada(BaseModel):
    curso: str
    instituicao: str
    periodo: str
class EstimativaSalarial(BaseModel):
    senioridade_inferida: str = Field(
        description="Nível inferido pela descrição da vaga (ex: Júnior, Pleno, Estágio)."
    )
    moeda: str = Field(
        description="Moeda da estimativa (ex: 'BRL (R$)' para vagas no Brasil ou 'USD ($)' para vagas internacionais)."
    )
    clt_faixa: str = Field(
        description="Faixa salarial mensal bruta estimada no regime CLT (ex: 'R$ 4.500 a R$ 5.800')."
    )
    clt_sugerido_alvo: str = Field(
        description="Valor único recomendado para preencher em formulários CLT (ex: 'R$ 5.200')."
    )
    pj_faixa: str = Field(
        description="Faixa mensal estimada no regime PJ considerando multiplicador de ~1.45x a 1.6x sobre o CLT (ex: 'R$ 6.800 a R$ 8.800')."
    )
    pj_sugerido_alvo: str = Field(
        description="Valor único recomendado para preencher em formulários PJ (ex: 'R$ 7.800')."
    )
    justificativa: str = Field(
        description="Explicação objetiva (2 a 3 linhas) dos fatores da vaga que basearam essa faixa (stack, senioridade, remoto/híbrido, porte)."
    )
class CurriculoAdaptado(BaseModel):
    idioma_final: Literal["PT-BR", "EN"] = Field(
        description="Idioma utilizado na geração de todo o conteúdo adaptado."
    )
    diagnostico_ats: DiagnosticoATS
    titulo_profissional_adaptado: str = Field(
        description="Título profissional alinhado à vaga (ex: 'Analista de Dados Júnior | Engenharia de Dados & BI'), sem inventar senioridade."
    )
    resumo_profissional: str = Field(
        description="Parágrafo único (3 a 5 linhas) conectando a formação e experiência real da candidata às necessidades da vaga. Sem Markdown."
    )
    experiencias: List[ExperienciaAdaptada]
    projetos: List[ProjetoAdaptado]
    competencias_categorizadas: List[CategoriaCompetenciaAdaptada]
    educacao: List[EducacaoAdaptada]
    certificacoes_selecionadas: List[str] = Field(
        description="Lista das certificações mais relevantes para a vaga no formato 'Título — Emissor (Data)'."
    )
    texto_apresentacao_gupy: str = Field(
        description="Texto em primeira pessoa para o campo 'Apresente-se!' da Gupy/LinkedIn. MÁXIMO ESTRITO DE 600 CARACTERES. Sem Markdown."
    )
    competencias_gupy_linkedin: List[str] = Field(
        description="Lista plana das 15 a 25 principais competências reais para colar separadas por vírgula em formulários."
    )
    estimativa_salarial: EstimativaSalarial