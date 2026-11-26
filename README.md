# 📄 ATS Resume Tailor — AI-Powered Career Optimization

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-3.8_Flash-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-Structured_Outputs-E92063?style=for-the-badge&logo=pydantic&logoColor=white)

Aplicação web desenvolvida em **Python** e **Streamlit** que utiliza **LLMs com Structured Outputs (`google-genai` + `Pydantic`)** para adaptar automaticamente um currículo mestre em JSON às exigências de vagas de tecnologia e dados, gerando um PDF limpo, de coluna única e otimizado para sistemas de triagem **ATS (Applicant Tracking Systems)**.

---

## 🎯 Problema & Solução

Recrutadores e plataformas como **Gupy, Greenhouse, Lever e LinkedIn** utilizam parsers automáticos que frequentemente penalizam currículos com layouts complexos (múltiplas colunas, gráficos, tabelas) ou falta de aderência semântica às palavras-chave da vaga.

Este projeto resolve esse gargalo separando **dados estruturados (Fonte Única da Verdade)** da **camada de apresentação**, aplicando engenharia de prompt com travas anti-alucinação para:
1. **Flexibilidade Multi-Usuário (Upload & Template):** Permite utilizar um perfil padrão pré-carregado ou fazer upload de qualquer currículo customizado em `.json` (validado em tempo real via Pydantic), além de disponibilizar o download direto do template estruturado.
2. **Diagnóstico ATS:** Avalia a aderência real do perfil frente à vaga (Score estimado de 0 a 100%, *keywords* principais e dicas sobre requisitos ausentes).
3. **Adaptação Semântica Bilíngue:** Reordena e adapta a redação de experiências e projetos reais usando a terminologia exata da descrição da vaga (com detecção automática de idioma ou seleção explícita entre **Português** e **Inglês**).
4. **Human-in-the-Loop:** Permite editar todos os campos adaptados diretamente na interface antes da exportação.
5. **Exportação Instantânea:** Gera um PDF ATS-friendly 100% em Python (`fpdf2`) com nomenclatura dinâmica e blocos copiáveis prontos para formulários web.

---

## 🏗️ Arquitetura do Projeto

```text
curriculo-ats-ai/
├── app.py                     # Interface Streamlit, upload/validação de JSON, preview editável e download
├── requirements.txt           # Dependências do projeto
├── .env.example               # Template de variáveis de ambiente
├── data/
│   └── curriculo_mestre.json  # Base estruturada padrão (experiências, projetos, stack e educação)
└── src/
    ├── __init__.py
    ├── schemas.py             # Contratos de dados Pydantic (Validação de Entrada e Structured Output do LLM)
    ├── ai_engine.py           # Integração com Gemini 3.8 Flash e regras estritas anti-alucinação
    └── pdf_generator.py       # Motor de renderização PDF em coluna única (fpdf2)
```

### Destaques Técnicos

* **Multi-Tenant via Upload Validado (`app.py` + `src/schemas.py`):** Visitantes podem baixar o `template_curriculo_mestre.json` na barra lateral, preencher com seus próprios dados e realizar o upload. O schema `CurriculoMestre` garante integridade estrutural com fallback seguro para o perfil padrão em caso de erro de formatação.
* **Zero Alucinação & Determinismo (`src/ai_engine.py`):** O modelo opera com temperatura reduzida (`0.2`) e instruções explícitas que proíbem a invenção de ferramentas, métricas, datas ou cargos ausentes no JSON de origem.
* **Garantia de Contrato com Structured Outputs (`src/schemas.py`):** O retorno do `gemini-3.8-flash` é validado diretamente contra schemas `Pydantic`, eliminando erros de parsing JSON e bloqueando marcações Markdown indesejadas (`**`, `#`, `*`) que sujam PDFs e formulários ATS.
* **Geração de PDF Pure-Python (`src/pdf_generator.py`):** Construído com `fpdf2` sem dependências nativas externas (como GTK/Cairo), garantindo portabilidade total entre Windows, Linux e Streamlit Community Cloud, com sanitização automática de nomes de arquivo.
* **Human-in-the-Loop:** Todos os textos adaptados (Título, Resumo, Experiências e Projetos) são carregados em campos editáveis antes da geração do arquivo final.

---

## 🚀 Como Executar Localmente

### Pré-requisitos
* Python 3.10 ou superior
* Uma chave de API gratuita do [Google AI Studio](https://aistudio.google.com/)

### Passo a passo (Windows PowerShell)

```powershell
# 1. Clonar o repositório
git clone https://github.com/MirellyAlvarenga/curriculo-ats-ai.git
cd curriculo-ats-ai

# 2. Criar e ativar o ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar a chave da API
Copy-Item .env.example .env
# Abra o arquivo .env e insira sua GEMINI_API_KEY="sua_chave_aqui"

# 5. Executar a aplicação
streamlit run app.py
```

*(Nota: Caso utilize Linux/macOS, ative o ambiente virtual com `source .venv/bin/activate` e copie o `.env` com `cp .env.example .env`).*

---

## ☁️ Deploy no Streamlit Community Cloud

A aplicação suporta leitura híbrida de credenciais: busca primeiro no input manual da barra lateral, depois no arquivo `.env` local e, por fim, em `st.secrets`.

Para publicar gratuitamente no Streamlit Cloud:
1. Faça push deste repositório para o seu GitHub (certifique-se de que o `.env` está no `.gitignore`).
2. Acesse [share.streamlit.io](https://share.streamlit.io/) e conecte o repositório apontando para `app.py`.
3. Caso queira deixar uma chave padrão no servidor privado, adicione em **App Settings > Secrets**:
   ```toml
   GEMINI_API_KEY = "sua_chave_api_do_google_ai_studio"
   ```
   *(Em deploys públicos de portfólio, recomenda-se deixar os Secrets vazios para que cada visitante insira sua própria API Key e faça upload do seu próprio JSON na barra lateral).*

---

## 👩‍💻 Autora

**Mirelly Alvarenga** — Analista de Dados Júnior | Engenharia de Dados & BI  
* [Portfólio](https://portfolio-mirelly-alvarenga.vercel.app)
* [LinkedIn](https://www.linkedin.com/in/mirelly-pego-cordeiro-de-alvarenga/)
* [GitHub](https://github.com/MirellyAlvarenga)