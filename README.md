<p align="center">
  <img src="CareerCompass-icon.png" alt="CareerCompass AI" width="160">
</p>

<h1 align="center">CareerCompass AI</h1>

<p align="center">
  <strong>Career Intelligence Platform</strong>
</p>

<p align="center">
  Plataforma multiagente para análise de perfil profissional, descoberta de oportunidades, avaliação de compatibilidade com vagas, preparação para entrevistas e geração de assessment profissional.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-App-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/Architecture-Multi--Agent-6C63FF?style=flat-square" alt="Multi-Agent">
  <img src="https://img.shields.io/badge/Status-MVP-00A67E?style=flat-square" alt="Status">
</p>

---

## 🧭 Sobre o CareerCompass AI

O **CareerCompass AI** é uma plataforma de inteligência de carreira desenvolvida para transformar informações profissionais em análises estruturadas que apoiem decisões relacionadas a **recolocação, desenvolvimento profissional e processos seletivos**.

A plataforma permite utilizar um perfil profissional padrão ou carregar um currículo em **PDF ou DOCX**. A partir desse conteúdo, diferentes módulos especializados analisam competências, experiências, senioridade, ferramentas, evidências profissionais e aderência a oportunidades.

A proposta vai além de um analisador de currículo isolado.

O CareerCompass AI foi estruturado como uma **arquitetura multiagente**, na qual diferentes componentes assumem responsabilidades específicas dentro da jornada profissional do candidato.

---

## ✨ Principais funcionalidades

### 📄 Upload e análise de currículo

O usuário pode carregar seu próprio currículo em:

- PDF
- DOCX

O conteúdo é extraído e transformado em um perfil profissional utilizado pelos demais módulos da plataforma.

Também existe um **perfil padrão** para demonstração e testes do sistema.

---

### 🧠 Profile Engine

O **Profile Engine** transforma o conteúdo textual do currículo em uma representação estruturada do perfil profissional.

Entre as dimensões analisadas estão:

- áreas profissionais;
- senioridade;
- hard skills;
- ferramentas e tecnologias;
- competências de gestão;
- metodologias;
- idiomas;
- evidências de atuação e resultados.

Esse perfil estruturado funciona como uma camada de inteligência compartilhada pelos demais módulos.

---

### 🔎 Scout — Radar de Oportunidades

O **Scout** analisa as competências presentes no perfil ativo e identifica caminhos profissionais com maior aderência.

O módulo gera um ranking inicial considerando a relação entre o perfil detectado e diferentes funções profissionais.

Exemplos de resultados:

- cargo ou caminho profissional;
- percentual de aderência;
- classificação;
- competências encontradas;
- justificativa da recomendação.

O objetivo é responder:

> **Onde este perfil profissional pode gerar mais valor?**

---

### 🎯 Curator — Análise de Fit

O **Curator** compara o perfil profissional com uma oportunidade específica.

O usuário fornece a descrição de uma vaga e a plataforma identifica:

- compatibilidade geral;
- competências analisadas;
- aderências;
- pontos sem evidência no currículo;
- detalhamento técnico do matching.

O objetivo é apoiar uma decisão anterior à candidatura:

> **Quanto meu perfil realmente combina com esta oportunidade?**

---

### 🎤 Coach — Simulador de Entrevistas

O **Coach** conduz uma simulação estruturada de entrevista profissional em múltiplas etapas.

Cada resposta é analisada considerando elementos como:

- clareza;
- presença de evidências;
- nível de detalhamento;
- uso de exemplos concretos;
- indicadores e resultados;
- qualidade da narrativa profissional.

Após cada etapa, o candidato recebe feedback e recomendações para melhorar suas respostas.

O objetivo é transformar experiências registradas no currículo em uma narrativa mais estruturada para processos seletivos.

---

### 📋 Assessment — Relatório Profissional

O módulo de **Relatório Profissional** consolida as informações detectadas no currículo em um diagnóstico estruturado do candidato.

O assessment pode apresentar:

- resumo do candidato;
- fonte analisada;
- senioridade identificada;
- áreas profissionais;
- hard skills;
- ferramentas;
- competências de gestão;
- metodologias;
- idiomas;
- evidências profissionais;
- principais forças;
- pontos de atenção;
- caminhos profissionais;
- recomendações.

O relatório pode ser utilizado como base para processos de:

- recolocação profissional;
- orientação de carreira;
- preparação para entrevistas;
- revisão de currículo;
- identificação de competências;
- planejamento de desenvolvimento profissional.

---

## 🧩 Arquitetura multiagente

O CareerCompass AI utiliza módulos especializados que compartilham o perfil profissional como contexto central.

```text
                    ┌───────────────────────┐
                    │      CURRÍCULO        │
                    │      PDF / DOCX       │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    Resume Parser      │
                    │   Extração de texto   │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    Profile Engine     │
                    │ Perfil estruturado    │
                    └───────────┬───────────┘
                                │
               ┌────────────────┼────────────────┐
               │                │                │
               ▼                ▼                ▼
        ┌────────────┐    ┌────────────┐   ┌────────────┐
        │   Scout    │    │  Curator   │   │   Coach    │
        │   Radar    │    │  Job Fit   │   │ Interview  │
        └────────────┘    └────────────┘   └────────────┘
               │                │                │
               └────────────────┼────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    Report Engine      │
                    │ Professional Report   │
                    └───────────────────────┘
```

---

## 🤖 Agentes e componentes

| Componente | Responsabilidade |
|---|---|
| **Resume Parser** | Extrair conteúdo de currículos PDF e DOCX |
| **Profile Engine** | Estruturar competências e características profissionais |
| **Scout** | Identificar caminhos profissionais aderentes |
| **Curator** | Comparar candidato e oportunidade |
| **Coach** | Simular entrevistas e avaliar respostas |
| **Report Engine** | Consolidar o diagnóstico profissional |
| **Maestro AI** | Conceito de coordenação dos módulos especializados |

---

## 🛠️ Tecnologias

O projeto utiliza:

- **Python**
- **Streamlit**
- **Pandas**
- **python-docx**
- **pypdf**
- **Git**
- **GitHub**

A arquitetura foi organizada de forma modular para permitir a evolução independente dos diferentes componentes de inteligência.

---

## 📁 Estrutura do projeto

```text
CareerCompass-AI/
│
├── app/
│   ├── main.py
│   ├── coach_engine.py
│   ├── curator_engine.py
│   ├── profile_engine.py
│   ├── report_engine.py
│   ├── resume_parser.py
│   └── scout_engine.py
│
├── data/
│   ├── personality-quiz.md
│   └── user-profile.md
│
├── personas/
│   ├── coach.md
│   ├── curator.md
│   ├── maestro.md
│   └── scout.md
│
├── skills/
│   └── dispatch.md
│
├── AGENTS.md
├── CareerCompass-icon.png
├── README.md
├── requirements.txt
├── .gitignore
└── .env
```

> O arquivo `.env` deve permanecer fora do versionamento e não deve conter credenciais públicas no repositório.

---

## 🚀 Como executar

### 1. Clone o repositório

```bash
git clone https://github.com/MCLG1661/CareerCompass-AI.git
```

### 2. Entre na pasta

```bash
cd CareerCompass-AI
```

### 3. Crie um ambiente virtual

Windows:

```powershell
python -m venv .venv
```

### 4. Ative o ambiente virtual

PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Instale as dependências

```powershell
pip install -r requirements.txt
```

### 6. Execute a aplicação

```powershell
python -m streamlit run app/main.py
```

### 7. Acesse no navegador

```text
http://localhost:8501
```

---

## 🔄 Fluxo de utilização

```text
Carregar currículo
       ↓
Extração do conteúdo
       ↓
Estruturação do perfil
       ↓
Diagnóstico profissional
       ↓
┌───────────────────────────────┐
│ Radar de Oportunidades        │
│ Análise de Fit                │
│ Simulação de Entrevistas      │
│ Relatório Profissional        │
└───────────────────────────────┘
       ↓
Insights para tomada de decisão
```

O mesmo perfil ativo é utilizado pelos diferentes módulos, criando continuidade entre as etapas da jornada.

---

## 🎯 Visão de produto

O CareerCompass AI foi concebido como uma **Career Intelligence Platform**, e não apenas como uma ferramenta de análise de currículo.

A evolução do projeto busca conectar quatro dimensões principais:

**Perfil → Mercado → Oportunidade → Preparação**

Isso permite que diferentes análises compartilhem contexto e contribuam para uma visão mais completa da trajetória profissional do candidato.

---

## 🗺️ Roadmap

Entre as evoluções previstas estão:

- [x] Interface Streamlit
- [x] Arquitetura modular
- [x] Perfil profissional padrão
- [x] Upload de currículo
- [x] Leitura de PDF
- [x] Leitura de DOCX
- [x] Profile Engine
- [x] Detecção de senioridade
- [x] Detecção estruturada de competências
- [x] Scout — Radar de Oportunidades
- [x] Curator — Análise de Fit
- [x] Coach — Simulador de Entrevistas
- [x] Assessment profissional
- [x] Identidade visual própria
- [ ] Career Fit Score multidimensional
- [ ] Análise semântica avançada
- [ ] Integração com modelos de IA generativa
- [ ] Geração avançada de recomendações
- [ ] Histórico de análises
- [ ] Comparação entre múltiplas vagas
- [ ] Exportação avançada de relatórios
- [ ] Dashboard de evolução profissional
- [ ] Persistência de candidatos
- [ ] Autenticação de usuários
- [ ] Deploy público
- [ ] Camada administrativa para consultorias de carreira

---

## 💼 Aplicações potenciais

O CareerCompass AI pode evoluir para diferentes cenários de utilização:

**Candidato individual**

Análise de currículo, identificação de oportunidades, preparação para entrevistas e planejamento profissional.

**Consultoria de recolocação**

Assessment inicial, análise estruturada de candidatos e apoio ao processo de orientação profissional.

**Career Coach**

Ferramenta complementar para diagnóstico, preparação e acompanhamento de clientes.

**Outplacement**

Apoio estruturado a programas de transição e recolocação profissional.

**Talent & Career Intelligence**

Base tecnológica para futuras aplicações relacionadas à análise de competências, mobilidade profissional e desenvolvimento de carreira.

---

## ⚠️ Limitações atuais

O CareerCompass AI encontra-se em evolução.

As análises atuais são baseadas principalmente em regras, termos, evidências textuais e estruturas definidas pelos módulos do sistema.

Os percentuais de aderência devem ser interpretados como **indicadores de compatibilidade do modelo**, e não como probabilidades reais de contratação ou aprovação em processos seletivos.

A plataforma não substitui a avaliação de recrutadores, consultores de carreira ou profissionais de Recursos Humanos.

---

## 🔐 Privacidade

Currículos podem conter dados pessoais e profissionais sensíveis.

Na versão atual executada localmente, o processamento ocorre no ambiente da aplicação. Evoluções futuras envolvendo persistência, autenticação, APIs externas ou modelos de IA deverão considerar requisitos adicionais de segurança, privacidade e proteção de dados.

---

## 📌 Status

**MVP funcional em desenvolvimento**

A plataforma já possui fluxo integrado para:

**Currículo → Perfil estruturado → Radar → Fit → Entrevista → Assessment**

O projeto continua evoluindo em direção a uma plataforma mais robusta de **Career Intelligence**.

---

## 👨‍💻 Autor

**Marcus Guedes**

Projeto desenvolvido como iniciativa de aplicação de **Inteligência Artificial, Data Analytics, arquitetura multiagente e tecnologia aplicada a problemas de negócio**.

---

<p align="center">
  <img src="CareerCompass-icon.png" alt="CareerCompass AI" width="80">
</p>

<p align="center">
  <strong>CareerCompass AI</strong><br>
  Career Intelligence Platform
</p>
