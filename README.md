# 🧭 CareerCompass AI

Assistente multiagente de carreira desenvolvido para apoiar análise de perfil, descoberta de caminhos profissionais, avaliação de compatibilidade com vagas e preparação para entrevistas.

## Visão geral

O CareerCompass AI utiliza uma arquitetura multiagente composta por quatro papéis principais:

- **Maestro** — orquestra o fluxo e direciona cada tarefa ao agente adequado.
- **Scout** — identifica funções profissionais com maior aderência ao perfil.
- **Curator** — compara o perfil do usuário com uma vaga específica.
- **Coach** — conduz uma entrevista simulada em seis etapas e fornece feedback estruturado.

O projeto começou como uma arquitetura conversacional baseada em personas e protocolos de handoff e evoluiu para um MVP funcional em Streamlit.

## MVP funcional

A aplicação possui três fluxos principais.

### 🔎 Scout — Descobrir oportunidades

Analisa o perfil profissional carregado e gera um ranking de funções com maior aderência.

O resultado apresenta:

- percentual de aderência;
- classificação;
- competências encontradas no perfil;
- ranking das funções analisadas.

### 🎯 Curator — Analisar compatibilidade

Recebe a descrição de uma vaga e compara os requisitos identificados com as competências registradas no perfil.

O resultado apresenta:

- percentual de compatibilidade;
- classificação geral;
- aderências identificadas;
- pontos sem evidência no perfil;
- detalhamento técnico das competências analisadas.

### 🎤 Coach — Simular entrevista

Conduz uma entrevista simulada em seis etapas:

1. Apresentação profissional
2. Experiência e trajetória
3. Competências relacionadas à função
4. Situação ou problema profissional
5. Motivação e aderência
6. Encerramento

Cada resposta recebe feedback sobre:

- clareza;
- presença de evidências;
- nível de desenvolvimento;
- recomendação de melhoria.

A aplicação preserva o estado da entrevista durante a sessão.

## Arquitetura do projeto

```text
CareerCompass-AI/
│
├── app/
│   ├── main.py
│   ├── scout_engine.py
│   ├── curator_engine.py
│   └── coach_engine.py
│
├── data/
│   ├── personality-quiz.md
│   └── user-profile.md
│
├── personas/
│   ├── maestro.md
│   ├── scout.md
│   ├── curator.md
│   └── coach.md
│
├── skills/
│   └── dispatch.md
│
├── AGENTS.md
├── CareerCompass-icon.png
├── README.md
└── requirements.txt

## Tecnologias

Python
Streamlit
Pandas
Git
GitHub

## Como executar

Clone o repositório:

git clone https://github.com/MCLG1661/CareerCompass-AI.git

Entre na pasta:

cd CareerCompass-AI

Instale as dependências:

python -m pip install -r requirements.txt

Execute a aplicação:

python -m streamlit run app/main.py

Depois acesse:

http://localhost:8501
Estado atual

O MVP atual inclui:

arquitetura multiagente;
roteamento entre Maestro, Scout, Curator e Coach;
persistência de perfil em Markdown;
análise de compatibilidade;
ranking de funções;
entrevista simulada multi-etapas;
tratamento básico de estado da sessão;
interface funcional em Streamlit.
Limitações atuais

Esta versão utiliza mecanismos determinísticos para análise e matching.

Ainda não fazem parte do MVP atual:

autenticação;
banco de dados;
persistência entre sessões;
integração completa com modelos de linguagem;
busca online de vagas em produção;
scoring semântico avançado;
deploy público definitivo.
Próximas evoluções
integração com LLM para análises mais contextuais;
melhoria dos algoritmos de scoring;
integração estável com fontes externas de vagas;
histórico de análises e entrevistas;
personalização por usuário;
evolução da interface;
deploy público.
Objetivo do projeto

O CareerCompass AI busca demonstrar como uma arquitetura multiagente pode ser aplicada a um problema real de carreira, combinando orientação profissional, análise de dados, matching e preparação para processos seletivos.

Status: MVP funcional
