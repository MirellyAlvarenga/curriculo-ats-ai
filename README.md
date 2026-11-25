# 📄 ATS Resume Tailor — AI-Powered Career Optimization

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-Structured_Outputs-E92063?style=for-the-badge&logo=pydantic&logoColor=white)

Aplicação web desenvolvida em **Python** e **Streamlit** que utiliza **LLMs com Structured Outputs (`google-genai` + `Pydantic`)** para adaptar automaticamente um currículo mestre em JSON às exigências de vagas de tecnologia e dados, gerando um PDF limpo, de coluna única e otimizado para sistemas de triagem **ATS (Applicant Tracking Systems)**.

---

## 🎯 Problema & Solução

Recrutadores e plataformas como **Gupy, Greenhouse, Lever e LinkedIn** utilizam parsers automáticos que frequentemente penalizam currículos com layouts complexos (múltiplas colunas, gráficos, tabelas) ou falta de aderência semântica às palavras-chave da vaga.

Este projeto resolve esse gargalo separando **dados estruturados (Fonte Única da Verdade)** da **camada de apresentação**, aplicando engenharia de prompt com travas anti-alucinação para:
1. Diagnosticar a aderência real do perfil frente à vaga (Score ATS, *keywords* e *gaps*).
2. Reordenar e adaptar a redação de experiências e projetos reais usando a terminologia exata da descrição da vaga (em **Português** ou **Inglês**).
3. Permitir revisão humana (*Human-in-the-loop*) antes da exportação.
4. Gerar instantaneamente um PDF ATS-friendly 100% em Python (`fpdf2`) e blocos prontos para formulários web.

---

## 🏗️ Arquitetura do Projeto

```text
curriculo-ats-ai/
├── app.py                     # Interface Streamlit, gestão de estado, preview editável e download
├── requirements.txt           # Dependências do projeto
├── .env.example               # Template de variáveis de ambiente
├── data/
│   └── curriculo_mestre.json  # Base estruturada com experiências, projetos, stack e educação
└── src/
    ├── __init__.py
    ├── schemas.py             # Contratos de dados Pydantic (Entrada e Structured Output do LLM)
    ├── ai_engine.py           # Integração com Gemini 2.5 Flash e regras estritas anti-alucinação
    └── pdf_generator.py       # Motor de renderização PDF em coluna única (fpdf2)