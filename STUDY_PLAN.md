# Study Plan: ai-notebooks

109 notebooks across two parallel tracks over ~42 weeks.
Prep track runs at full speed; heavy foundational notebooks get 2-week slots.

- **Prep track:** Applied AI engineering, production systems, agents, apps
- **Foundational track:** Deep learning, LLM internals, RL, architecture from scratch

| Wk | Prep | Foundational | Milestone |
|----|------|--------------|-----------|
| 01 | [ ] `prep/01` LLM APIs & Chat Completions | [ ] `deep/01` Softmax Regression | |
| | [ ] `prep/02` Prompt Engineering | | |
| 02 | [ ] `prep/03` RAG: Embeddings, Retrieval & Chunking | [ ] `deep/02` Neural Networks | |
| | [ ] `prep/04` LLM Evaluation Concepts | | |
| 03 | [ ] `prep/05` ReAct & Tool Orchestration | [ ] `deep/03` Automatic Differentiation | |
| | [ ] `prep/06` Prompt Management & Observability | | (deep/03 continued) | |
| 04 | [ ] `prep/07` Production RAG Pipeline | [ ] `deep/04` Optimizers: SGD to AdamW | |
| | [ ] `prep/08` LangGraph & Multi-Agent Systems | | |
| 05 | [ ] `prep/09` Fine-Tuning & Model Selection | [ ] `deep/05` Activations and Gradients | |
| | [ ] `prep/10` Model Serving & Deployment | [ ] `deep/06` Convolutional Networks | **Core RAG + agents + eval + serving working** |
| 06 | [ ] `prep/11` Cost Optimization for LLM Workloads | [ ] `deep/07` Language Modeling | |
| | [ ] `prep/12` Docker, Kubernetes & IaC | [ ] `deep/08` Recurrent Neural Networks | |
| 07 | [ ] `prep/13` Capstone: Compliance Document Reviewer | [ ] `deep/09` Attention and Transformers | **Core prep complete** |
| 08 | [ ] `prep/dd/01` Advanced RAG | | (deep/09 continued) | |
| | [ ] `prep/dd/02` Automated Eval Pipelines | | |
| 09 | [ ] `prep/dd/03` Agent Memory | [ ] `deep/adv/13` Machine Translation | |
| | [ ] `prep/dd/04` Resilience Patterns | | |
| 10 | [ ] `prep/dd/05` MLOps: CI/CD for AI | [ ] `deep/adv/14` Generative Models (VAEs & GANs) | |
| | [ ] `prep/dd/06` AI Security & Compliance | | |
| 11 | [ ] `prep/dd/07` Advanced Embeddings | [ ] `deep/adv/15` Diffusion Models | |
| | [ ] `prep/dd/08` Multimodal LLMs | | |
| 12 | [ ] `prep/dd/09` IaC & Container Orchestration | | (deep/adv/15 continued) | **All prep deep dives complete** |
| 13 | [ ] `agents/00` Using LLMs as Agents | [ ] `deep/adv/16` Semantic Segmentation | |
| | [ ] `agents/01` Giving Agents Access to Tools | [ ] `deep/adv/17` Image Captioning | |
| 14 | [ ] `agents/02` Chain-of-Thought & Reasoning | [ ] `deep/11-app` Activation Patterns & Expressivity | |
| | [ ] `agents/03` Building and Running an Agent Loop | [ ] `deep/12-app` ResNet from Scratch | |
| 15 | [ ] `agents/04` Managing What the Agent Sees | [ ] `deep/18-app` Double Descent | **DL foundations complete** |
| | [ ] `agents/05` Long-Term Memory | | |
| 16 | [ ] `agents/06` Keeping Agents Safe in Production | [ ] `llm/01` Building a GPT from Scratch | |
| | [ ] `agents/07` Evaluating Agent Behavior | | |
| 17 | [ ] `agents/08` Structured Workflows vs Full Autonomy | | (llm/01 continued) | |
| | [ ] `agents/09` Multi-Agent Coordination | | |
| 18 | [ ] `agents/10` MCP and Plugin Architectures | [ ] `llm/02` Byte Pair Encoding & Vocabulary Design | **Full agent lifecycle mastered** |
| 19 | [ ] `apps/01` Flet I: Basics | [ ] `llm/03` Data Pipelines for LM Pretraining | |
| | [ ] `apps/03` Flet II: Declarative UI | [ ] `llm/04` Pretraining Loop: Optimizer, Schedule, Mixed Precision | |
| 20 | [ ] `apps/05` FastAPI Fundamentals | [ ] `llm/05` Gradient and Activation Diagnostics | |
| | [ ] `apps/06` Docker & Local Infrastructure | [ ] `llm/06` Pretraining nanoGPT on TinyShakespeare | |
| 21 | [ ] `apps/07` Database Design & ORM | | (llm/06 continued) | |
| | [ ] `apps/08` S3 Integration & Batch Pipelines | | |
| 22 | [ ] `apps/09` Embeddings & Vector Search | [ ] `llm/07` Multi-GPU Training with DDP and FSDP | |
| | [ ] `apps/10` People Clustering (MTCNN + FaceNet) | | |
| 23 | [ ] `apps/11` Connecting Flet to FastAPI | | (llm/07 continued) | **Can pretrain an LLM from scratch on multiple GPUs** |
| | [ ] `apps/12` Realtime Data & WebSockets | | |
| 24 | [ ] `apps/13` AI Summaries & Multimodal Queries | [ ] `llm/08` Instruction Tuning with SFT and LoRA | |
| | [ ] `apps/14` Photo App: End-to-End | [ ] `llm/09` DPO and Reward Modeling | **Photo app shipped** |
| 25 | [ ] `apps/cda/01` Streaming LLM Client | [ ] `llm/10` GRPO: RL from Verifiable Rewards | |
| | [ ] `apps/cda/02` The Tool System | | (llm/10 continued) | |
| 26 | [ ] `apps/cda/03` The Agent Loop | [ ] `llm/11` Knowledge Distillation | **Can fine-tune and align LLMs** |
| | [ ] `apps/cda/04` Hardening the Agent | [ ] `llm/12` INT8/INT4 Quantization | |
| 27 | [ ] `apps/cda/05` GUI 1: Chat Interface | [ ] `llm/13` KV Cache, Flash Attention, Speculative Decoding | |
| | [ ] `apps/cda/06` GUI 2: Persistence & Slash Commands | [ ] `llm/14` Inference-Time Scaling: Search & Self-Consistency | |
| 28 | [ ] `apps/cda/07` GUI 3: MCP Integration | [ ] `llm/15` End-to-End Reasoning Model Training | **Coding agent complete** |
| 29 | [ ] `apps/nbx/01` Platform Architecture | | (llm/15 continued) | |
| | [ ] `apps/nbx/02` Machine Registry & Dashboard | | |
| 30 | [ ] `apps/nbx/03` Job Packaging & Execution | [ ] `llm/ds/01` DeepSeek: MLA & Mixture of Experts | |
| | [ ] `apps/nbx/04` Task Queue & Multi-Provider Dispatch | [ ] `llm/ds/02` Training NanoDeepSeek | |
| 31 | [ ] `apps/nbx/05` Log Streaming & Artifact Retrieval | [ ] `llm/ds/03` The Engram Layer | **All apps complete; full LLM lifecycle including frontier architectures** |
| 32 | | [ ] `tooling/06` RL Foundations: MDPs & Dynamic Programming | |
| | | [ ] `tooling/07` Policy Gradients: REINFORCE to Actor-Critic | |
| 33 | | [ ] `tooling/08` Proximal Policy Optimization | |
| 34 | | | (tooling/08 continued) | |
| 35 | | [ ] `tooling/09` RL for Language Models: PPO to GRPO | **Can derive and implement RL behind RLHF/GRPO** |
| 36 | | [ ] `classical/01` Bias, Variance & Regularization | |
| | | [ ] `classical/02` Tree-Based Methods | |
| 37 | | [ ] `classical/03` Bayesian Thinking | |
| | | [ ] `classical/04` Feature Engineering & Unsupervised Learning | |
| 38 | | [ ] `classical/05` Evaluation & Causal Reasoning | |
| | | [ ] `classical/06` Tabular Deep Learning | **Classical ML complete** |
| 39 | | [ ] `tooling/01` RunPod Environment Setup | |
| | | [ ] `tooling/02` OpenCode: AI Coding Agent in Terminal | |
| | | [ ] `tooling/03` Singular Value Decomposition | |
| 40 | | [ ] `tooling/04` MCP Servers with FastMCP | |
| | | [ ] `tooling/05` Security Tooling for Developers | |
| 41 | | [x] `tooling/10` Weak Supervision | |
| | | [ ] `tooling/11` Generating Exercise Notebooks | **All 109 notebooks complete** |
