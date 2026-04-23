The main idea of ​​this project is to implement a labeled data evaluation system called AgentCompany. In this company, the data structure and the task description are first given. Then an agent structures the data and selects some random samples from it and then decides what should be planned for such a task in order to perform a quality evaluation. This manager agent designs a path for evaluating, reviewing and improving the labels. Based on this, it designs a group of agents that can exchange ideas and finally reach the best result for the label of each data. These groups work on the data one by one (simultaneously but with a managed number of concurrency) and finally, the output of their work will be the same input data with modified labels.

Questions
1. Data type: What kind of data are you labeling? (images, text, audio, structured data, etc.)
2. Label types: What kind of labels are being evaluated? (classification, bounding boxes, sentiment, etc.)
3. Group size: How many worker agents should participate in the discussion to reach consensus per data item?
4. smolagent integration: Do you want to use smolagent for both the manager and worker agents, or just specific components?
5. Deployment: Should this run locally (script/API) or as a hosted service?
6. Output format: Should the final output be a JSON file, database, or something else?

my data are all texts. labels are different. it include classification, choosing best translation, keyword extraction and other labels related to LLMs and other transformer models. the group size should be chosen based on the task and the difficulty. it's up to the manager agent. using smolagent is up to you. I have an LLM served by vllm. which has openai endpoint. the output should be json file. I should mention that the input is a json file too

### Architecture
- **Manager Agent** (smolagent CodeAgent): Analyzes dataset, determines group sizes, tie-breaks disagreements
- **Worker Agents** (smolagent CodeAgent): Evaluate labels with diverse personas
- **Consensus Engine**: Task-specific resolution (majority vote, discussion, union)
- **Task Router**: Auto-detects task types (classification, translation_choice, keyword_extraction)

### Consensus Strategy: Hybrid
1. Workers independently evaluate
2. Discussion rounds if no consensus (60% threshold)
3. Manager tie-break if still disagreement

### File Structure
```
├── main.py                 # Entry point
├── src/
│   ├── config.py           # Configuration
│   ├── models/
│   │   ├── manager.py      # Manager agent
│   │   └── worker.py       # Worker agents
│   ├── consensus/
│   │   ├── engine.py      # Consensus logic
│   │   └── strategies.py   # Per-task strategies
│   └── tasks/
│       ├── router.py       # Task detection
│       └── prompts.py      # Prompt templates
├── tests/test_core.py      # Unit tests
└── samples/input_sample.json
```

### Usage
```bash
python main.py <input.json> [-o output.json] [--endpoint http://localhost:8000/v1]
```

