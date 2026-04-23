# AgentCompany Label Evaluation System

A multi-agent system for evaluating and refining labels on text data using the smolagent framework. The system employs a manager-worker architecture where multiple agents collaborate to reach consensus on label quality.

## Features

- **Manager Agent**: Analyzes dataset, assesses difficulty, creates worker agents with specific roles
- **Worker Agents**: Evaluate labels with diverse personas and perspectives
- **Consensus Engine**: Multiple strategies for resolving disagreements
- **Dynamic Agent Generation**: Manager decides how many workers to create and their specific roles
- **Hybrid Resolution**: Discussion first, then manager tie-break if needed
- **Pydantic Validation**: Type-safe input/output with Pydantic models
- **Retry Logic**: Automatic retry with exponential backoff for API calls
- **Parallel Processing**: Process multiple items concurrently with `ThreadPoolExecutor`

## Supported Task Types

- Classification (sentiment, category, etc.)
- Translation Selection (choosing best translation)
- Keyword Extraction
- Custom label types (user-defined)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Input JSON File                      │
│  { "task_config": {...}, "items": [...] }               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  MANAGER AGENT (smolagent)              │
│  • Samples items to assess difficulty                  │
│  • Creates worker agents with specific roles           │
│  • Plans evaluation strategy                           │
│  • Tie-breaker when consensus fails                    │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌───────────┐   ┌───────────┐   ┌───────────┐
    │  Worker 1 │   │  Worker 2 │   │  Worker N │
    │ (strict)  │◄──┤ (creative)│◄──┤ (domain)  │
    └───────────┘   └───────────┘   └───────────┘
          │               │               │
          └───────────────┴───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  CONSENSUS ENGINE                       │
│  • Check consensus threshold (configurable, default 60%)│
│  • Resolve via majority vote, union, or discussion     │
│  • Manager tie-break if still disagreement             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Output JSON File                      │
│  [{ "id": "...", "labels": {...}, "evaluation": {...} }]│
└─────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install -r requirements.txt
```

**Requirements:**
- Python 3.10+
- smolagents
- openai
- pydantic
- tqdm

## Quick Start

### 1. Prepare Input File

Create an input JSON file with `task_config` and `items`:

```json
{
  "task_config": {
    "description": "Evaluate whether the assigned categories and sentiments are accurate",
    "evaluation_criteria": ["accuracy", "consistency", "completeness"],
    "consensus_strategy": "discussion_then_vote",
    "consensus_threshold": 0.6,
    "max_discussion_rounds": 2
  },
  "items": [
    {
      "id": "sample_001",
      "text": "The recent advancement in AI has revolutionized healthcare diagnostics.",
      "labels": {
        "category": "technology",
        "sentiment": "positive"
      }
    }
  ]
}
```

### 2. Run Evaluation

```bash
python main.py input.json -o output.json --mock  # Test with mock model
python main.py input.json -o output.json --endpoint http://localhost:8000/v1 --model llama-3.1-8b
```

## Configuration

### Command Line Arguments

| Argument | Description |
|----------|-------------|
| `input` | Input JSON file path (required) |
| `-o, --output` | Output JSON file path |
| `--endpoint` | vLLM/OpenAI-compatible endpoint |
| `--model` | Model identifier |
| `--mock` | Use mock model for testing |
| `--parallel` | Max parallel workers for item processing (default: 4) |

### Task Config Options

| Field | Default | Description |
|-------|---------|-------------|
| `description` | "Evaluate labels for accuracy and quality" | Task description |
| `evaluation_criteria` | ["accuracy", "reasonableness"] | What to evaluate |
| `consensus_strategy` | "discussion_then_vote" | Resolution strategy |
| `consensus_threshold` | 0.6 | Threshold for consensus (0.0-1.0) |
| `max_discussion_rounds` | 2 | Max rounds before tie-break |

### Consensus Strategies

| Strategy | Description |
|----------|-------------|
| `majority_vote` | Simple majority wins |
| `discussion_then_vote` | Discuss until threshold agreement, then vote |
| `full_consensus` | Require unanimous agreement |
| `union` | Combine all extractions (for keywords) |

## Project Structure

```
agentic_eval_team/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration
│   ├── models/
│   │   ├── manager.py         # Manager agent
│   │   ├── worker.py          # Worker agents (with retry logic)
│   │   ├── tools.py           # Manager tools (assess_difficulty, plan_evaluation_strategy)
│   │   ├── schema.py          # Pydantic models (TaskConfig, DataItem, InputData)
│   │   └── mock_model.py      # Mock model for testing
│   ├── consensus/
│   │   ├── engine.py          # Consensus orchestration
│   │   └── strategies.py      # Resolution strategies
│   ├── evaluation/
│   │   └── runner.py          # Parallel processing runner
│   ├── tasks/
│   │   ├── router.py          # Task type detection
│   │   └── prompts.py          # Prompt templates
│   └── utils/
│       ├── io.py              # JSON I/O utilities
│       ├── retry.py           # Retry decorator with exponential backoff
│       └── errors.py          # Custom exception types
├── samples/
│   └── input_sample.json      # Sample input
└── tests/
    └── test_core.py           # Unit tests
```

## Testing

```bash
python -m unittest tests.test_core -v
```

### Mock Testing

Use `--mock` flag to test without a running LLM server:

```bash
python main.py samples/input_sample.json -o output.json --mock --parallel 2
```

## Key Improvements

### Retry Logic
Worker agents automatically retry failed API calls with exponential backoff:
- Max retries: 3 (configurable)
- Initial delay: 1 second
- Backoff factor: 2x per retry
- Graceful fallback to error response if all retries fail

### Parallel Processing
Items can be processed in parallel using `ThreadPoolExecutor`:
```bash
python main.py input.json --parallel 4  # Process 4 items concurrently
```

### Configurable Consensus Threshold
The `consensus_threshold` in `task_config` controls when consensus is reached:
- 0.6 = 60% agreement required
- 1.0 = full consensus required

## How It Works

### 1. Manager Analysis

The manager samples items from the dataset and assesses:
- Difficulty level (low/medium/high)
- Recommended strategies
- Number of discussion rounds

### 2. Agent Generation

Based on difficulty and task, workers are created with specific roles:
- `strict_evaluator`: Focuses on accuracy and correctness
- `creative_reviewer`: Looks for edge cases and alternatives
- `domain_expert`: Checks technical/domain accuracy (for high difficulty)
- `lenient_reviewer`: Evaluates practical acceptability (for high difficulty)

### 3. Evaluation Loop

For each item:
1. All workers independently evaluate the labels
2. Consensus is checked against the threshold
3. If no consensus, all workers discuss and re-evaluate
4. After max rounds, manager tie-breaks if still disagreement

### 4. Output

Each item in the output includes:
- Original `id` and `text`
- Final `labels` (possibly modified)
- `evaluation_summary` with consensus info

## Example Output

```json
{
  "id": "sample_001",
  "text": "The recent advancement in AI...",
  "labels": {
    "category": "technology",
    "sentiment": "positive"
  },
  "evaluation_summary": {
    "consensus": "correct",
    "reasoning": "Threshold reached: correct (2/2 >= 0.6)",
    "resolved_by": "workers",
    "worker_count": 2,
    "discussion_rounds": 0
  }
}
```
