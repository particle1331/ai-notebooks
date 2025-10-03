
the future is agentic

lect 1: AI agents

agenda:
1. what is AI? 
2. what are AI agents? / Agentic AI
3. how will we be learning

AI is a set of tech that mimic human capabilities

current AI: excels at structured tasks
future: focus on general tasks

rule based => machine learning => DL => genAI

humans provide:
task, data, tools, approach => task, data, tools => task, data => task

gen ai = machines provide more, humans provide less

motivation for using agentic ai: genai is limited by pre-training and prompts
- hallucination genai learns abstract representation not memorization, so it can hallucinate facts
- performance differences between different tasks (e.g. GPQA, MMLU, HumanEval, MATH) which system should I use? not obv
- prompt sizes are not infinite in size (i.e. token limit)
    - 10M token limit (llama 4)
    - vs. ~38B tokens for wikipedia
    - exponential growth of context length (artfish.ai)
    - more text doesnt always help: LLM reasoning drops as input grows 250 -> 3000 tokens (adding irrelevant context)

these limitations motivate the development of AI agents = LLM + planning + tooling

planning and tooling help address many of the deficiencies of LLMs alone

AI workflow (non-agentic): query -> f(query) -> response
Agentic workflow:
    user query -> plan -> execute with tools -> reflect -> response
                    |__________<___________________|

[img source: weaviate.io]

systems like chatgpt are actually AI agents

Example. Actual AI agent (NORA scenario paper)

user requests plan trip from seattle
to vancouver for 3 days.visit 2 attractions per day, fit 3 people on 300$ per day

-> tools reasoning multi-step -> agent response -> evaluation

evaluation: constraint-satisfaction framework. check whether each constraint is satisfied (e.g. assign score)

#3 
we can then orchestrate multiple AI agents to get an **agentic system**.

[src medium.com/@pallavisinha12]

agents can complete most basic technical tasks automatically with 80% success rate

[metr.org]

task duration for humans vs AI systems

google trends AI agents, agentic AI

Q: how to study agentic systems?
A: systems engineering. 
    - goal oriented design (specific objectives, careful planning, system capabilities)
    - system integration - seamless interaction reliable performance
    - software development
    - human-centered design
    - iterative development
