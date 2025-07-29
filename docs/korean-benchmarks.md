# Korean Language Benchmarks Guide

This guide provides detailed information about running Korean language benchmarks with SND-Bench.

## Available Korean Benchmarks

### 1. KoBEST (Korean Balanced Evaluation of Significant Tasks)

KoBEST is a comprehensive Korean NLU benchmark suite consisting of 5 tasks:

- **kobest_boolq** - Boolean Questions: Yes/no question answering
- **kobest_copa** - Choice of Plausible Alternatives: Commonsense causal reasoning
- **kobest_hellaswag** - Sentence completion: Commonsense NLI
- **kobest_sentineg** - Sentiment Negation: Sentiment analysis with negation
- **kobest_wic** - Words in Context: Word sense disambiguation

Example:
```bash
./run-benchmark.sh --model gpt2 --tasks kobest_boolq,kobest_copa,kobest_hellaswag
```

### 2. KMMLU (Korean Massive Multitask Language Understanding)

Korean version of MMLU covering 45 subjects across STEM, humanities, social sciences, and more:

- **kmmlu** - Full KMMLU benchmark (45 subjects)
- **kmmlu_direct** - Direct answer generation variant
- **kmmlu_hard** - Subset of difficult questions
- **kmmlu_hard_direct** - Hard questions with direct generation
- **kmmlu_hard_cot** - Hard questions with chain-of-thought prompting

Subject-specific tasks (examples):
- **kmmlu_accounting** - Accounting
- **kmmlu_biology** - Biology
- **kmmlu_chemistry** - Chemistry
- **kmmlu_computer_science** - Computer Science
- **kmmlu_economics** - Economics
- **kmmlu_history** - History
- **kmmlu_law** - Law
- **kmmlu_mathematics** - Mathematics
- **kmmlu_medicine** - Medicine
- **kmmlu_physics** - Physics

Example:
```bash
# Run full KMMLU
./run-benchmark.sh --model meta-llama/Llama-2-7b-hf --tasks kmmlu

# Run specific subjects
./run-benchmark.sh --model gpt2 --tasks kmmlu_computer_science,kmmlu_mathematics
```

### 3. KLUE (Korean Language Understanding Evaluation)

KLUE benchmark tasks for various Korean NLU capabilities:

- **klue_nli** - Natural Language Inference
- **klue_sts** - Semantic Textual Similarity
- **klue_ynat** - YNAT Topic Classification
- **klue_re** - Relation Extraction (if available)
- **klue_dp** - Dependency Parsing (if available)
- **klue_mrc** - Machine Reading Comprehension (if available)
- **klue_ner** - Named Entity Recognition (if available)

Example:
```bash
./run-benchmark.sh --model gpt2 --tasks klue_nli,klue_sts,klue_ynat
```

### 4. Other Korean Benchmarks

- **nsmc** - Naver Sentiment Movie Corpus: Movie review sentiment classification
- **kohatespeech** - Korean Hate Speech Detection
- **kohatespeech_apeach** - Hate Speech variant with APEACH dataset
- **kohatespeech_gen_bias** - Gender bias detection in Korean
- **korunsmile** - Korean Unsmile: Detecting uncomfortable/toxic content
- **pawsx_ko** - Korean portion of PAWS-X paraphrase identification

Example:
```bash
./run-benchmark.sh --model gpt2 --tasks nsmc,kohatespeech
```

## Interactive Mode

The easiest way to run Korean benchmarks is using the interactive mode:

```bash
./run-benchmark.sh
```

This will present a menu where you can:
1. Select your model
2. Choose from categorized Korean benchmarks
3. Use pre-configured Korean benchmark suites

## Quick Start Examples

### Basic Korean Evaluation
```bash
# Run core Korean benchmarks
./run-benchmark.sh --model gpt2 --tasks kobest_boolq,kobest_copa,kmmlu

# With W&B tracking
export WANDB_API_KEY=your-key
./run-benchmark.sh --model gpt2 --tasks kobest_hellaswag,klue_nli
```

### Advanced Evaluation
```bash
# Comprehensive Korean evaluation
./run-benchmark.sh \
  --model meta-llama/Llama-2-7b-hf \
  --tasks kobest_boolq,kobest_copa,kobest_hellaswag,kobest_sentineg,kobest_wic,kmmlu,klue_nli,klue_sts,nsmc \
  --wandb-project korean-llm-bench

# Compare multiple models
./run-benchmark.sh \
  --model gpt2 \
  --compare "gpt2-medium,EleutherAI/polyglot-ko-1.3b" \
  --tasks kobest_hellaswag,kmmlu
```

## Checking Available Korean Tasks

To see which Korean benchmarks are available in your installation:

```bash
# Check Korean benchmark availability
python scripts/check-korean-benchmarks.py

# List all tasks
lm_eval --tasks list | grep -E "ko|klue|kmmlu"
```

## Model Recommendations for Korean

For best results with Korean benchmarks, consider using:

1. **Multilingual Models**:
   - `meta-llama/Llama-2-7b-hf` - Good multilingual capabilities
   - `mistralai/Mistral-7B-v0.1` - Strong performance
   - `gpt2` - Baseline, limited Korean understanding

2. **Korean-Specific Models** (if available on HuggingFace):
   - `EleutherAI/polyglot-ko-*` series
   - `skt/kogpt2-*` series
   - Korean-finetuned variants

## Performance Considerations

1. **Batch Size**: Korean text may require different tokenization, adjust batch size if needed:
   ```bash
   export DEFAULT_BATCH_SIZE=4
   ./run-benchmark.sh --model large-model --tasks kmmlu
   ```

2. **Memory**: Korean benchmarks may use more tokens due to subword tokenization:
   - Monitor GPU/CPU memory usage
   - Reduce batch size if OOM errors occur

3. **Evaluation Time**: Some benchmarks like KMMLU are extensive:
   - Full KMMLU: ~45 subjects, can take hours
   - Consider running subsets first

## Results Interpretation

Korean benchmark results include:
- **Accuracy**: Main metric for most tasks
- **F1 Score**: For tasks like hate speech detection
- **Perplexity**: For language modeling tasks
- **Task-specific metrics**: Check individual task documentation

Results are saved in:
- `results/` - Raw benchmark outputs
- `runs/` - Organized by timestamp with summaries
- W&B dashboard - If configured

## Troubleshooting

### Korean Text Display Issues
If you see encoding issues in outputs:
```bash
export PYTHONIOENCODING=utf-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

### Missing Korean Benchmarks
If Korean tasks are not available:
```bash
# Update lm-evaluation-harness
pip install --upgrade lm-eval

# Or install specific version known to have Korean tasks
pip install lm-eval>=0.4.0
```

### Model Loading Issues
For Korean-specific models:
```bash
# Ensure HuggingFace token is set for gated models
export HUGGING_FACE_HUB_TOKEN=your-token

# Use trust_remote_code for custom models
./run-benchmark.sh \
  --model "skt/kogpt2-base-v2" \
  --model-args "trust_remote_code=True" \
  --tasks kobest_hellaswag
```

## Contributing

To add new Korean benchmarks:
1. Check if the dataset is available in lm-evaluation-harness
2. Update the task list in `run-benchmark.sh`
3. Add documentation here
4. Submit a PR with examples

## Resources

- [KoBEST Paper](https://arxiv.org/abs/2204.11744)
- [KMMLU Repository](https://github.com/HAETAE-project/KMMLU)
- [KLUE Benchmark](https://klue-benchmark.com/)
- [lm-evaluation-harness Documentation](https://github.com/EleutherAI/lm-evaluation-harness)