# AgentCompany Label Evaluation System

A multi-agent system for evaluating and refining labels on text data using smolagent framework.

## Features

- **Manager Agent**: Analyzes tasks, determines group sizes, and resolves tie-breaks
- **Worker Agents**: Evaluate labels with diverse personas (strict, creative, analytical)
- **Consensus Engine**: Implements task-specific consensus strategies
- **Task Router**: Automatically detects task types and estimates difficulty

## Supported Task Types

- Classification
- Translation Choice
- Keyword Extraction
- Other label types

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py <input.json> [-o output.json] [--endpoint http://localhost:8000/v1] [--model model-id]
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VLLM_ENDPOINT` | http://localhost:8000/v1 | vLLM server endpoint |
| `VLLM_API_KEY` | dummy | API key for authentication |
| `MODEL_ID` | meta-llama/Llama-3.1-8B-Instruct | Model identifier |
| `MAX_WORKERS` | 5 | Maximum concurrent workers |
| `DISCUSSION_ROUNDS` | 2 | Max discussion rounds before tie-break |
| `OUTPUT_DIR` | ./output | Output directory |

## Architecture

1. **Input**: JSON file with text data and labels
2. **Manager**: Analyzes dataset, assigns worker groups
3. **Workers**: Evaluate items with independent reasoning
4. **Discussion**: Workers debate when consensus isn't reached
5. **Tie-break**: Manager resolves remaining disagreements
6. **Output**: JSON file with refined labels

## Example

```bash
python main.py samples/input_sample.json -o output.json
```