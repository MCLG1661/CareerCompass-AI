# CareerCompass AI — Protocolo de Despacho e Handoff

## Objetivo

Definir como o Maestro delega tarefas aos agentes especializados do CareerCompass AI e como os resultados retornam ao orquestrador.

## Roteamento

1. Opção: A
   Agente: Scout
   Responsabilidade: Buscar vagas compatíveis com o perfil do usuário.

2. Opção: B
   Agente: Curator
   Responsabilidade: Identificar lacunas de habilidades e buscar cursos adequados.

3. Opção: C
   Agente: Coach
   Responsabilidade: Conduzir a simulação de entrevista.
   Regra: A entrevista completa utiliza 6 despachos sequenciais.

4. Opção: D
   Agente: Maestro
   Responsabilidade: Refazer o quiz, sobrescrever `data/personality-quiz.md` e regenerar `data/user-profile.md`.

## Envelope de Despacho

O Maestro deve construir o seguinte prompt antes de utilizar `spawn_agent`:

## DESPACHO: [NOME_DO_AGENTE]

### referencia_persona

[Conteúdo completo de `personas/<nome_do_agente_minusculo>.md`]

### tarefa

[Uma frase descrevendo exatamente o que o agente deve fazer]

### perfil_usuario

[Conteúdo de `data/user-profile.md`]

### contexto

[Contexto específico necessário para executar a tarefa]

### saida_esperada

[Formato exato em que o agente deve retornar o resultado]

## Envelope de Resposta

Todo agente despachado deve retornar:

## RESPOSTA: [NOME_DO_AGENTE]

### estado

[sucesso | erro]

### resumo

[Resumo legível de 2 a 3 frases para o usuário]

### dados

[Resultados apresentados como listas numeradas com pares chave-valor. Não utilizar tabelas Markdown.]

### erros

[Preencher apenas quando `estado` for `erro`, descrevendo exatamente o que falhou.]

## Handoff — Scout

1. Maestro carrega `data/user-profile.md`.

2. Maestro carrega `personas/scout.md`.

3. Maestro valida se o perfil contém as informações necessárias para a busca:
   - funções-alvo;
   - localização;
   - preferência de trabalho;
   - nível profissional;
   - habilidades atuais.

4. Maestro constrói o Envelope de Despacho do Scout definindo explicitamente:
   - Adzuna API como fonte primária;
   - função-alvo principal como primeira consulta;
   - país `br`;
   - máximo de 5 vagas no resultado final;
   - proibição de fallback automático para buscas abertas na web.

5. O campo `### tarefa` deve instruir o Scout a buscar vagas reais e atuais compatíveis com o perfil profissional do usuário utilizando a Adzuna API.

6. O campo `### contexto` deve conter os critérios relevantes extraídos do perfil, sem incluir credenciais da API.

7. As credenciais da Adzuna nunca devem ser inseridas pelo Maestro no Envelope de Despacho. O Scout deve obtê-las exclusivamente das variáveis de ambiente:
   - `ADZUNA_APP_ID`
   - `ADZUNA_APP_KEY`

8. Maestro despacha exclusivamente uma instância do Scout para cada solicitação de busca.

9. Scout executa a consulta à Adzuna API conforme as regras definidas em `personas/scout.md`.

10. Scout avalia a aderência dos resultados ao perfil e seleciona no máximo 5 vagas.

11. Scout não deve iniciar buscas em Google, Bing, LinkedIn, Indeed, Glassdoor ou outras fontes como fallback automático.

12. Scout retorna obrigatoriamente o Envelope de Resposta definido neste protocolo.

13. Maestro valida o Envelope de Resposta verificando:
    - presença de `### estado`;
    - presença de `### resumo`;
    - presença de `### dados`;
    - presença de `### erros` quando `estado` for `erro`;
    - ausência de credenciais ou outros segredos;
    - máximo de 5 vagas.

14. Se `estado` for `sucesso`, Maestro apresenta as vagas ao usuário e retorna ao menu principal.

15. Se `estado` for `erro`, Maestro apresenta claramente a falha informada pelo Scout, preserva o perfil existente e retorna o controle ao usuário.

16. Após receber o Envelope de Resposta, Maestro não deve iniciar uma nova busca automaticamente.
 
## Handoff — Curator

1. Maestro carrega `data/user-profile.md`.
2. Maestro carrega a persona do Curator.
3. Maestro fornece as habilidades ou lacunas que devem ser analisadas.
4. Curator executa exclusivamente a tarefa delegada.
5. Curator retorna o Envelope de Resposta.
6. Maestro valida e apresenta o resultado ao usuário.

## Handoff — Coach

1. Maestro carrega `data/user-profile.md`.
2. Maestro carrega a persona do Coach.
3. Maestro fornece o contexto da vaga ou função-alvo.
4. Coach executa uma etapa da entrevista por despacho.
5. Maestro realiza 6 despachos sequenciais para completar a entrevista.
6. Cada resposta deve preservar o contexto necessário para o despacho seguinte.
7. Após o sexto despacho, Maestro consolida o resultado e apresenta o feedback ao usuário.

## Tratamento de Erros

1. Se `spawn_agent` falhar:
   estado: erro
   erros: Registrar a falha exata retornada pela ferramenta.

2. Se um arquivo necessário não existir:
   estado: erro
   erros: Informar exatamente qual arquivo não foi encontrado.

3. Se o perfil do usuário estiver incompleto:
   estado: erro
   erros: Informar quais informações obrigatórias estão ausentes.

4. Nunca inventar dados para substituir informações ausentes.

5. Nunca ocultar uma falha.

6. Não continuar silenciosamente após uma falha que impeça a execução da tarefa.

7. O Maestro deve apresentar o erro ao usuário de maneira clara e preservar o estado existente.
