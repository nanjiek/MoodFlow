# MoodFlow 情绪分类实验阶段总结

更新日期：2026-05-17

## 1. 本阶段目标

本阶段围绕两条路线做了验证：

1. 分类器路线：清洗训练数据后，继续训练/微调多个分类模型。
2. 大模型路线：本地开源 LLM + prompt 约束输出 8 分类。

本阶段优先关注 `accuracy`，同时记录 `macro_f1`、`weighted_f1`、推理延迟和典型错误。

---

## 2. 数据清洗

### 2.1 清洗策略

新增脚本：`model_service/training/clean_dataset.py`

主要规则：

- 删除超短高歧义文本
- 删除明显冲突的关键词-标签样本
- 标记但保留长文本中的复杂冲突
- 标记风险上下文词：`明天 / 放假 / 假期 / 休息 / 旅行 / 计划 / 期待`
- 生成：
  - `cleaned`
  - `flagged`
  - `dropped`
  - 固定 `train/test`
  - `llm_eval` 小评测集

### 2.2 迭代结果

清洗一共做了 `v1 -> v4` 四轮，最终采用 `clean_v4`。

`clean_v4` 结果：

| 指标 | 数值 |
|---|---:|
| input_rows | 115785 |
| cleaned_rows | 104840 |
| flagged_rows | 5983 |
| dropped_rows | 10945 |
| train_size | 89114 |
| test_size | 15726 |
| llm_eval_rows | 77 |

主要清洗原因计数：

| 原因 | 数量 |
|---|---:|
| generic_short_text | 10814 |
| ultra_short_text | 2280 |
| ambiguous_short_text | 1246 |
| plain_label_with_strong_emotion_keyword | 1426 |
| mixed_emotion_keywords | 1321 |
| positive_keyword_vs_negative_label | 1103 |
| negative_keyword_vs_positive_label | 944 |
| risky_context_keyword | 1652 |

典型被清掉的脏样本：

- `发烧,expecting,cped_train_split.csv`

最终清洗产物：

- `data/processed/clean_v4/moodflow_emotions_cleaned_v1.csv`
- `data/processed/clean_v4/moodflow_emotions_flagged_v1.csv`
- `data/processed/clean_v4/moodflow_emotions_dropped_v1.csv`

---

## 3. 分类器路线

### 3.1 训练脚本调整

为保证可比性，训练脚本改为支持固定 `train/test`：

- `model_service/training/train_baseline.py`
- `model_service/training/train_transformer.py`

新增：

- `model_service/training/train_linear_svm.py`

### 3.2 训练指标对比

说明：

- `baseline`：原始 TF-IDF + LogisticRegression 产物
- `baseline-clean-v4`：在 `clean_v4` 上重训
- `linear-svm-clean-v4`：在 `clean_v4` 上训练 TF-IDF + LinearSVC
- `transformer-rbt3-clean-v4` / `transformer-rbt6-clean-v4`：在 `clean_v4` 上做轻量微调

| 模型 | 训练集 | accuracy | macro_f1 | weighted_f1 | train_size | test_size |
|---|---|---:|---:|---:|---:|---:|
| baseline | 原始 processed | 0.5181 | 0.5643 | 0.5403 | 92628 | 23157 |
| baseline-clean-v1 | clean_v1 | 0.5364 | 0.5738 | 0.5564 | 87463 | 15433 |
| baseline-clean-v4 | clean_v4 | 0.5356 | 0.5703 | 0.5572 | 89110 | 15725 |
| linear-svm-clean-v4 | clean_v4 | 0.5868 | 0.5755 | 0.5912 | 89110 | 15725 |
| transformer-rbt3-local | 原始 processed 子集 | 0.6015 | 0.3328 | 0.5284 | 12000 | 2000 |
| transformer-rbt3-clean-v4 | clean_v4 | 0.6040 | 0.3249 | 0.5319 | 8000 | 15726 |
| transformer-rbt6-clean-v4 | clean_v4 | 0.6304 | 0.3728 | 0.5653 | 8000 | 15726 |

### 3.3 用实际服务推理逻辑跑完整 clean_v4 测试集

说明：这里不是看训练脚本内部指标，而是直接走 `EmotionPredictor`，更接近真实服务行为。

评测脚本：

- `scripts/benchmark_emotion_models.py`

评测集：

- `data/processed/clean_v4/moodflow_emotions_cleaned_v1_test.csv`

| 模型 | full-test accuracy | avg_latency_ms | p95_latency_ms |
|---|---:|---:|---:|
| baseline | 0.6408 | 1.47 | 1.80 |
| baseline_clean_v4 | 0.5351 | 1.44 | 1.78 |
| linear_svm_clean_v4 | 0.5868 | 0.38 | 0.67 |
| transformer_rbt3_clean_v4 | 0.6065 | 5.60 | 10.14 |
| transformer_rbt6_clean_v4 | 0.6310 | 10.62 | 19.28 |

### 3.4 分类器路线观察

1. `LinearSVC` 是本阶段最好的“传统重训模型”：
   - 训练指标比 `baseline-clean-v4` 明显更强
   - 推理速度还是最快
2. `rbt6` 把训练阶段 accuracy 拉到了最高，但：
   - `macro_f1` 仍然明显低
   - `calm / anxious / expecting / tired` 表现不平衡
   - 在完整服务评测里仍略低于原始 `baseline`
3. 最重要的一点：
   - **当前实际部署逻辑下，原始 `baseline` 仍是本阶段 accuracy 最高的分类器**
   - 这说明“清洗后重训”在训练指标上有收益，但还没有稳定转化成部署端全面超越

---

## 4. 大模型 + Prompt 路线

### 4.1 脚本与策略

新增脚本：

- `scripts/evaluate_llm_prompt_emotion.py`

尝试模型：

- `Qwen/Qwen2.5-0.5B-Instruct`
- `Qwen/Qwen2.5-1.5B-Instruct`

Prompt 做了两轮：

1. 初版：标签定义 + JSON 输出
2. 改进版：增加判别规则和 few-shot 示例，明确：
   - 没有明确疲惫线索时不要判 `tired`
   - 没有明显未来导向时不要判 `expecting`
   - 不确定默认回到 `plain`

### 4.2 LLM 路线结果

| 模型 / 设置 | rows | accuracy | avg_latency_ms | p95_latency_ms |
|---|---:|---:|---:|---:|
| Qwen2.5-0.5B-Instruct 初版 smoke | 16 | 0.0625 | 2684.73 | 3430.71 |
| Qwen2.5-0.5B-Instruct 改进 prompt smoke | 16 | 0.2500 | 4530.56 | 4931.41 |
| Qwen2.5-1.5B-Instruct smoke | 16 | 0.3125 | 14389.68 | 15983.03 |
| Qwen2.5-1.5B-Instruct full llm_eval | 77 | 0.3377 | 14705.61 | 15840.45 |

### 4.3 大模型路线观察

1. Prompt 改进确实有帮助，但提升有限。
2. `1.5B` 比 `0.5B` 更稳，但仍远低于当前分类器。
3. 主要问题：
   - 对 `expecting` 判断明显偏弱
   - 会把部分 `irritable` 误读成 `anxious` 或 `sad`
   - 会把不少 `plain` / `calm` 读成带情绪的句子
4. 在本机 CPU 环境下，**推理延迟约 14~15 秒/条**，对当前项目来说过慢。

结论：

- **当前本机开源 LLM + prompt 不适合作为主分类器。**

---

## 5. 混合架构可行性验证

目标：验证“主分类器低置信度时转大模型”是否值得做。

方法：

- 从 `baseline` 在 `llm_eval` 上挑出低置信度或 top1/top2 差距很小的样本
- 共得到 `33` 条
- 先测 `baseline` 自己在这 33 条上的准确率
- 再测 `Qwen2.5-1.5B-Instruct`

结果：

| 方法 | rows | accuracy | avg_latency_ms |
|---|---:|---:|---:|
| baseline 低置信度子集 | 33 | 0.3939 | 约 1~2 ms |
| Qwen2.5-1.5B-Instruct 同子集 | 33 | 0.2121 | 14295.92 |

结论：

- **当前这版本地 LLM 不仅没有救起低置信度样本，反而比 baseline 自己更差。**
- 因此，本阶段不建议直接接入“低置信度转 LLM”。

---

## 6. 本阶段最终结论

### 6.1 最重要的结论

1. **大模型不一定比分类器准。**
2. **在当前本机条件和当前 prompt 设计下，LLM 路线明显不如分类器路线。**
3. **在真实服务逻辑上，当前原始 `baseline` 仍然是 accuracy 最高的已测方案。**

### 6.2 目前最推荐的方案

短期建议：

- 继续以当前 `baseline` 作为主分类器
- 不要把本地 LLM 直接接进主推理链路

中期建议：

1. 继续优化 `clean_v4` 数据集，尤其是：
   - `expecting`
   - `calm`
   - `plain`
   - `tired`
2. 继续试更强但仍适合分类的模型：
   - 可以继续沿着 `LinearSVC`
   - 或者再尝试更充分微调的 encoder 模型
3. 如果未来还想做混合架构：
   - 先换更强的本地 LLM 或远程 API
   - 再专门验证“低置信度样本是否真的被救起”

### 6.3 当前阶段推荐排序

按“当前可落地程度 + accuracy 优先”排序：

1. `baseline`（当前部署逻辑下最好）
2. `transformer-rbt6-clean-v4`（accuracy 高，但类别失衡明显）
3. `linear-svm-clean-v4`（轻量、快、作为后续改进主线很值得继续）
4. `baseline-clean-v4`
5. `transformer-rbt3-clean-v4`
6. `Qwen2.5-1.5B-Instruct + prompt`

---

## 7. 相关文件

### 数据清洗

- `model_service/training/clean_dataset.py`
- `data/processed/clean_v4/cleaning_report_v1.json`

### 分类器训练

- `model_service/training/train_baseline.py`
- `model_service/training/train_linear_svm.py`
- `model_service/training/train_transformer.py`

### 评测脚本

- `scripts/benchmark_emotion_models.py`
- `scripts/evaluate_llm_prompt_emotion.py`

### 关键日志

- `tmp/clean-dataset-v4.log`
- `tmp/train-baseline-clean-v4.log`
- `tmp/train-linear-svm-clean-v4.log`
- `tmp/train-transformer-rbt3-clean-v4.log`
- `tmp/train-transformer-rbt6-clean-v4.log`
- `tmp/benchmark-clean-v4-full-test.json`
- `tmp/benchmark-clean-v4-llm-eval-v2.json`
- `tmp/llm-prompt-eval-qwen-1.5b-full.json`
- `tmp/llm-prompt-eval-qwen-1.5b-low-confidence.json`
